import logging
import os
import subprocess
from functools import partial
from pathlib import Path
from types import MappingProxyType
from typing import Literal, TypeAlias, assert_never

import attrs
import trio

from onelauncher.async_utils import for_each_in_stream
from onelauncher.config_manager import ConfigManager
from onelauncher.game_config import GameConfigID
from onelauncher.logs import ExternalProcessLogsFilter
from onelauncher.resources import data_dir
from onelauncher.wine_environment import get_wine_process_args

logger = logging.getLogger(__name__)
logger.addFilter(ExternalProcessLogsFilter())

PatchPhase: TypeAlias = Literal["FullPatch", "FilesOnly", "DataOnly"]

PATCH_CLIENT_RUNNER = data_dir.parent / "run_patch_client" / "run_ptch_client.exe"
"""
Executable used to run `patchclient.dll` and get output from it. This is done with a
separate program, because `patchclient.dll` is 32-bit. `rundll32.exe` can't be used,
because it doesn't expose the stdout of what it runs.
"""


@attrs.frozen
class PatchingProgress:
    total_iterations: int
    current_iterations: int


class PatchingProgressMonitor:
    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.patching_type = None

    @property
    def patching_type(self) -> Literal["file", "data"] | None:
        return self._patching_type

    @patching_type.setter
    def patching_type(self, patching_type: Literal["file", "data"] | None) -> None:
        self._patching_type = patching_type
        self.total_iterations: int = 0
        self.current_iterations: int = 0
        self.applying_forward_iterations: bool = False

    def get_patching_progress(self) -> PatchingProgress:
        return PatchingProgress(
            total_iterations=self.total_iterations,
            current_iterations=self.current_iterations,
        )

    def feed_line(self, line: str) -> PatchingProgress:
        cleaned_line = line.strip().lower()

        # Beginning of a patching type
        if cleaned_line.startswith("checking files"):
            self.patching_type = "file"
            return self.get_patching_progress()
        elif cleaned_line.startswith("checking data"):
            self.patching_type = "data"
            return self.get_patching_progress()
        # Right after a patching type begins. Find out how many iterations there will be.
        if cleaned_line.startswith("files to patch:"):
            self.total_iterations = int(
                cleaned_line.split("files to patch:")[1].strip().split()[0]
            )
        elif cleaned_line.startswith("data patches:"):
            self.total_iterations = int(
                cleaned_line.split("data patches:")[1].strip().split()[0]
            )
        # Data patching has two parts.
        # "Applying x forward iterations....(continues for x dots)" and the actual file
        # downloading which is the originally set `self.total_iterations`
        elif (
            self.patching_type == "data"
            and cleaned_line.startswith("applying")
            and "forward iterations" in cleaned_line
        ):
            self.applying_forward_iterations = True
            self.total_iterations += int(
                cleaned_line.split("applying")[1].strip().split("forward iterations")[0]
            )

        if cleaned_line.startswith("downloading"):
            self.applying_forward_iterations = False
            self.current_iterations += 1
        # During forward iterations, each "." represents one iteration
        elif self.applying_forward_iterations and "." in cleaned_line:
            self.current_iterations += len(cleaned_line.split("."))

        return self.get_patching_progress()


def get_patchclient_arguments(
    phase: PatchPhase,
    patch_server_url: str,
    game_id: GameConfigID,
    config_manager: ConfigManager,
) -> tuple[str, ...]:
    """
    Get arguments to be passed to `patchclient.dll`.
    """
    game_config = config_manager.get_game_config(game_id=game_id)

    base_arguments = (
        patch_server_url,
        "--language",
        game_config.locale.game_language_name
        if game_config.locale
        else config_manager.get_program_config().default_locale.game_language_name,
        *(("--highres",) if game_config.high_res_enabled else ()),
    )

    if phase == "FilesOnly":
        phase_arg = "--filesonly"
    elif phase == "DataOnly":
        phase_arg = "--dataonly"
    elif phase == "FullPatch":
        phase_arg = ""
    else:
        assert_never(phase)

    return (*base_arguments, phase_arg)


async def patch_game(
    patch_server_url: str,
    progress_monitor: PatchingProgressMonitor,
    game_id: GameConfigID,
    config_manager: ConfigManager,
) -> None:
    game_config = config_manager.get_game_config(game_id=game_id)

    patch_client = game_config.game_directory / game_config.patch_client_filename
    if not patch_client.exists():
        logger.error("Patch client %s not found", game_config.patch_client_filename)
        return

    command: tuple[str | Path, ...] = (
        PATCH_CLIENT_RUNNER,
        patch_client,
    )
    environment = MappingProxyType(os.environ)

    if os.name == "nt":
        # The directory with TTEPatchClient.dll has to be in the PATH for
        # patchclient.dll to find it when OneLauncher is compilled with Nuitka.
        environment = MappingProxyType(
            environment
            | {
                "PATH": f"{environment['PATH']};{game_config.game_directory}"
                if "PATH" in environment
                else f"{game_config.game_directory}"
            }
        )
    else:
        command, environment = get_wine_process_args(
            command=command, environment=environment, wine_config=game_config.wine
        )

    # Run file patching twice to avoid problems when patchclient.dll
    # self-patches.
    patch_phases: tuple[PatchPhase, ...] = (
        "FilesOnly",
        "FilesOnly",
        "DataOnly",
    )
    try:
        async with trio.open_nursery() as nursery:
            for phase in patch_phases:
                progress_monitor.reset()
                process: trio.Process = await nursery.start(
                    partial(
                        trio.run_process,
                        (
                            *command,
                            # `run_ptch_client.exe` takes everything that will get
                            # passed to `patchclient.dll` as a single argument.
                            " ".join(
                                get_patchclient_arguments(
                                    phase=phase,
                                    patch_server_url=patch_server_url,
                                    game_id=game_id,
                                    config_manager=config_manager,
                                )
                            ),
                        ),
                        check=False,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        env=environment,
                        cwd=game_config.game_directory,
                    )
                )
                if process.stdout is None or process.stderr is None:
                    raise TypeError("Process pipe is `None`")

                process_logging_adapter = logging.LoggerAdapter(logger)
                process_logging_adapter.extra = {
                    ExternalProcessLogsFilter.EXTERNAL_PROCESS_ID_KEY: process.pid
                }

                def process_output_line(line: str) -> None:
                    process_logging_adapter.debug(line)  # noqa: B023
                    progress_monitor.feed_line(line)

                nursery.start_soon(
                    partial(for_each_in_stream, process.stdout, process_output_line)
                )
                nursery.start_soon(
                    partial(
                        for_each_in_stream,
                        process.stderr,
                        process_logging_adapter.warning,
                    )
                )
                if await process.wait() != 0:
                    logger.debug(
                        "Patching process failed with %s exit status",
                        process.returncode,
                    )
                    logger.error("Patching failed")
                    return
    except* OSError:
        logger.exception("Failed to start patching")
