import logging
import os
import subprocess
from functools import partial
from pathlib import Path
from types import MappingProxyType
from typing import Literal, TypeAlias, assert_never
from uuid import uuid4

import attrs
import httpx
import trio
from httpx import HTTPError, HTTPStatusError
from xmlschema import XMLSchemaValidationError

from onelauncher.async_utils import for_each_in_stream
from onelauncher.config_manager import ConfigManager
from onelauncher.game_config import GameConfigID
from onelauncher.logs import ExternalProcessLogsFilter
from onelauncher.network.akamai import (
    PatchingDownloadFile,
    PatchingDownloadList,
    SplashscreenDownloadFile,
    SplashscreenDownloadList,
)
from onelauncher.network.game_launcher_config import GameLauncherConfig
from onelauncher.network.httpx_client import get_httpx_client
from onelauncher.resources import external_dependencies_dir
from onelauncher.utilities import CaseInsensitiveAbsolutePath, Progress, ProgressItem
from onelauncher.wine_environment import get_wine_process_args

logger = logging.getLogger(__name__)
logger.addFilter(ExternalProcessLogsFilter())

PatchPhase: TypeAlias = Literal["FullPatch", "FilesOnly", "DataOnly"]

# Run file patching twice to avoid problems when patchclient.dll
# self-patches.
PATCHCLIENT_PATCH_PHASES: tuple[PatchPhase, ...] = (
    "FilesOnly",
    "FilesOnly",
    "DataOnly",
)

PATCH_CLIENT_RUNNER = external_dependencies_dir / "run_ptch_client.exe"
"""
Executable used to run `patchclient.dll` and get output from it. This is done with a
separate program, because `patchclient.dll` is 32-bit. `rundll32.exe` can't be used,
because it doesn't expose the stdout of what it runs.
"""


class PatchingProgressMonitor:
    def __init__(self, progress: Progress) -> None:
        self.progress = progress
        self.reset()

    def reset(self) -> None:
        self.patching_type = None
        self.progress.reset()
        self.progress_item = ProgressItem()
        self.progress.progress_items.append(self.progress_item)

    @property
    def patching_type(self) -> Literal["file", "data"] | None:
        return self._patching_type

    @patching_type.setter
    def patching_type(self, patching_type: Literal["file", "data"] | None) -> None:
        self._patching_type = patching_type
        self.total_iterations: int = 0
        self.current_iterations: int = 0
        self.applying_forward_iterations: bool = False

    def _update_progress(self) -> None:
        self.progress_item.total = self.total_iterations
        self.progress_item.completed = self.current_iterations

    def feed_line(self, line: str) -> None:
        cleaned_line = line.strip().lower()

        # Beginning of a patching type
        if cleaned_line.startswith("checking files"):
            self.patching_type = "file"
            self._update_progress()
            return
        elif cleaned_line.startswith("checking data"):
            self.patching_type = "data"
            self._update_progress()
            return
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

        self._update_progress()


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


async def _handle_akamai_download_file(
    download_file: PatchingDownloadFile | SplashscreenDownloadFile,
    game_directory: CaseInsensitiveAbsolutePath,
    temp_download_dir: Path,
    base_download_url: str,
    progress: Progress,
) -> None:
    """
    Always download `SplashscreenDownloadFile`. There is no hash to check on these.

    Download `PatchingDownloadFile` if it doesn't exist. The hash is not checked,
    because the file may be out of date. These files are only meant for the initial large
    download. Afterwards, `patchclient.dll` is used.
    """
    local_path = trio.Path(game_directory / download_file.relative_path)
    if isinstance(download_file, PatchingDownloadFile) and await local_path.exists():
        return

    logger.debug("Downloading %s", download_file)

    url = (
        f"{base_download_url}/{download_file.relative_url}"
        if isinstance(download_file, PatchingDownloadFile)
        else download_file.url
    )
    temp_download_path = trio.Path(
        temp_download_dir / f"{download_file.relative_path.name}-{uuid4()}"
    )

    progress_item = ProgressItem()
    progress.progress_items.append(progress_item)
    if isinstance(download_file, PatchingDownloadFile):
        # Do before the web request, since it may take a while for a spot to open up
        # in the connection pool and the web request to go through.
        progress_item.total = download_file.size

    try:
        # Using the `async with client.stream(...)` currently doesn't work with
        # Nuitka. See <https://github.com/Nuitka/Nuitka/issues/3697>.
        request = get_httpx_client(url).build_request(
            "GET", url, timeout=httpx.Timeout(6, pool=None)
        )
        response = await get_httpx_client(url).send(request, stream=True)
        try:
            response.raise_for_status()

            bytes_currently_downloaded = response.num_bytes_downloaded
            if isinstance(download_file, SplashscreenDownloadFile):
                progress_item.total = int(
                    response.headers.get("Content-Length", 300000)
                )

            async with await temp_download_path.open("wb") as temp_download_file:
                async for chunk in response.aiter_bytes():
                    if isinstance(download_file, SplashscreenDownloadFile):
                        progress_item.completed += (
                            response.num_bytes_downloaded - bytes_currently_downloaded
                        )
                        bytes_currently_downloaded = response.num_bytes_downloaded
                    else:
                        progress_item.completed += len(chunk)

                    await temp_download_file.write(chunk)
        finally:
            await response.aclose()
    except HTTPError as e:
        if (
            isinstance(e, HTTPStatusError)
            and e.response.status_code == httpx.codes.NOT_FOUND
        ):
            # Not an error, because there are always some specific files that 404.
            logger.debug("Download not found: %s", local_path.name, exc_info=True)
        else:
            logger.exception("Failed to download %s", local_path.name)
        progress.progress_items.remove(progress_item)
    else:
        await local_path.parent.mkdir(parents=True, exist_ok=True)
        await temp_download_path.rename(local_path)
    finally:
        with trio.move_on_after(5, shield=True):
            await temp_download_path.unlink(missing_ok=True)


@attrs.frozen(kw_only=True)
class AkamaiPatchingError(Exception):
    msg: str


async def akamai_patching(
    game_id: GameConfigID, config_manager: ConfigManager, progress: Progress
) -> None:
    """
    Initial download of data after installation or switching languages and
    splashscreen updates. Splashscreens are always updated. Only files that don't
    exist for the initial data download are downloaded.

    Raises:
        AkamaiPatchingFailed
    """
    progress.unit_type = "byte"

    game_config = config_manager.get_game_config(game_id=game_id)

    game_launcher_config = await GameLauncherConfig.from_game_config(game_config)
    if (
        not game_launcher_config
        or not game_launcher_config.akamai_download_url
        or not game_launcher_config.game_version
    ):
        raise AkamaiPatchingError(msg="Failed to load game launcher network config")

    file_list: tuple[PatchingDownloadFile | SplashscreenDownloadFile, ...]

    # Add patching download files to the file list.
    language = (
        game_config.locale or config_manager.get_program_config().default_locale
    ).lang_tag.split("-")[0]
    # `akamai_download_url` ussed HTTP. The domain is a CNAME to an akamai subdomain.
    # The certificate isn't valid for any of the domains involved, so this isn't being
    # coerced to use HTTPS.
    base_download_url = f"{game_launcher_config.akamai_download_url}/{game_launcher_config.game_version}"
    download_list_url = (
        f"{base_download_url}/{language}_"
        f"{'highres' if game_config.high_res_enabled else 'lowres'}_download_list.xml"
    )
    try:
        file_list = (
            await PatchingDownloadList.get_from_url(download_list_url)
        ).download_files
    except HTTPError as e:
        raise AkamaiPatchingError(
            msg="Network error while downloading patching file list"
        ) from e
    except XMLSchemaValidationError as e:
        raise AkamaiPatchingError(msg="Error parsing patching file list") from e

    # Add splashscreens to file list.
    if game_launcher_config.download_files_list_url:
        try:
            file_list = (
                file_list
                + (
                    await SplashscreenDownloadList.get_from_url(
                        game_launcher_config.download_files_list_url
                    )
                ).download_files
            )
        except HTTPError:
            logger.exception("Network error while downloading splashscreens file list")
        except XMLSchemaValidationError:
            logger.exception("Error parsing splashscreens file list")
    else:
        logger.error("Game launcher config is missing splashscreens update URL")

    # Directory where files will be downloaded before being moved to their final
    # location. This is the same directory that the official launcher uses. A normal
    # temp directory isn't used, because it might not be on the same filesystem.
    # Downloading to the same filesystem is desirable, since these are large files.
    temp_download_dir = game_config.game_directory / "downloading"
    temp_download_dir.mkdir(exist_ok=True)

    async with trio.open_nursery() as nursery:
        for download_file in file_list:
            nursery.start_soon(
                partial(
                    _handle_akamai_download_file,
                    download_file=download_file,
                    game_directory=game_config.game_directory,
                    temp_download_dir=temp_download_dir,
                    base_download_url=base_download_url,
                    progress=progress,
                )
            )


async def patch_game(
    patch_server_url: str,
    progress: Progress,
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
        # patchclient.dll to find it when OneLauncher is compiled with Nuitka.
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

    # Initial data and splashscreens phase.
    progress.progress_text_suffix = (
        f"     Phase {1}/{len(PATCHCLIENT_PATCH_PHASES) + 1}"
    )
    try:
        await akamai_patching(
            game_id=game_id, config_manager=config_manager, progress=progress
        )
    except AkamaiPatchingError as e:
        logger.exception(e.msg)
        logger.info("Skipping phase")

    try:
        async with trio.open_nursery() as nursery:
            patching_progress_monitor = PatchingProgressMonitor(progress=progress)
            for i, phase in enumerate(PATCHCLIENT_PATCH_PHASES):
                patching_progress_monitor.reset()
                progress.progress_text_suffix = (
                    f"     Phase {i + 2}/{len(PATCHCLIENT_PATCH_PHASES) + 1}"
                )
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
                    patching_progress_monitor.feed_line(line)

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
