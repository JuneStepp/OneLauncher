import logging
import os
import shutil
import sys
from pathlib import Path
from subprocess import CalledProcessError
from tempfile import NamedTemporaryFile
from typing import Final

import attrs
import trio
from httpx import HTTPError

from .addons.config import AddonsConfigSection
from .async_utils import TemporaryDirectoryAsyncPath
from .config_manager import ConfigManager
from .game_config import (
    GameConfig,
    GameConfigID,
    GameType,
    generate_game_config_id,
)
from .game_utilities import InvalidGameDirError, find_game_dir_game_type
from .logs import ExternalProcessLogsFilter
from .network.httpx_client import get_httpx_client
from .official_clients import get_game_icon
from .resources import data_dir, external_dependencies_dir
from .utilities import (
    CaseInsensitiveAbsolutePath,
    Progress,
    ProgressItem,
    RelativePathError,
)
from .wine.config import WineConfigSection

logger = logging.getLogger(__name__)
logger.addFilter(ExternalProcessLogsFilter())


@attrs.frozen
class GameInstaller:
    name: str
    icon_path: Path
    url: str
    game_type: GameType
    is_preview_client: bool


GAME_INSTALLERS: Final[tuple[GameInstaller, ...]] = (
    GameInstaller(
        name="The Lord of The Rings Online",
        icon_path=get_game_icon(GameType.LOTRO),
        url="https://akamai.lotro.com/lotro/lotrolive.exe",
        game_type=GameType.LOTRO,
        is_preview_client=False,
    ),
    GameInstaller(
        name="The Lord of the Rings Online - Public Preview",
        icon_path=get_game_icon(GameType.LOTRO),
        url="https://files.lotro.com/lotro/installers/preview/lotropreview.exe",
        game_type=GameType.LOTRO,
        is_preview_client=True,
    ),
    GameInstaller(
        name="Dungeons & Dragons Online",
        icon_path=get_game_icon(GameType.DDO),
        url="https://akamai.ddo.com/ddo/ddolive.exe",
        game_type=GameType.DDO,
        is_preview_client=False,
    ),
    GameInstaller(
        name="Dungeons & Dragons Online - Public Preview",
        icon_path=get_game_icon(GameType.DDO),
        url="https://files.ddo.com/ddo/installers/preview/ddopreview.exe",
        game_type=GameType.DDO,
        is_preview_client=True,
    ),
)


def get_default_game_config(
    installer: GameInstaller, config_manager: ConfigManager
) -> tuple[GameConfigID, GameConfig]:
    """
    Return a default `GameConfigID` and `GameConfig` for `installer`. The default game
    directory is in the game config directory for this `GameConfigID`. That can be
    replaced with a user selected directory if the `GameConfig` is updated.
    You have to add these to `config_manager` yourself.
    """
    game_config = GameConfig(
        game_directory=CaseInsensitiveAbsolutePath.home(),  # temporary
        game_type=installer.game_type,
        is_preview_client=installer.is_preview_client,
        addons=AddonsConfigSection(),
        wine=WineConfigSection(),
    )
    game_config_id = generate_game_config_id(game_config)
    game_config = attrs.evolve(
        game_config,
        game_directory=CaseInsensitiveAbsolutePath(
            config_manager.get_game_config_dir(game_config_id) / "game_install"
        ),
    )

    return game_config_id, game_config


@attrs.frozen(kw_only=True)
class InstallDirValidationError(ValueError):
    msg: str


def validate_user_provided_install_dir(
    install_dir_string: str,
    config_manager: ConfigManager,
    default_install_dir: CaseInsensitiveAbsolutePath,
) -> CaseInsensitiveAbsolutePath:
    """
    Validate user provided game installation directory string and return the path.
    The `.msg` of the `InstallDirValidationError` raised is meant to be shown to the
    user.

    Raises:
        InstallDirValidationError: Show `.msg` to the user.
    """
    if not install_dir_string.strip():
        return default_install_dir

    try:
        install_dir = CaseInsensitiveAbsolutePath(install_dir_string)
    except RelativePathError as e:
        raise InstallDirValidationError(
            msg="Install directory cannot be a relative path"
        ) from e

    # Default install directory as gotten from `get_default_game_config` won't exist,
    # but is still considered valid.
    if install_dir == default_install_dir:
        return install_dir

    try:
        file = install_dir.open()
        file.close()
    except PermissionError as e:
        raise InstallDirValidationError(msg="Install directory must be readable") from e
    except FileNotFoundError as e:
        raise InstallDirValidationError(msg="Install directory must exist") from e
    except IsADirectoryError:
        pass
    else:
        raise InstallDirValidationError(msg="Install directory must be a directory")

    if next(install_dir.iterdir(), None):
        raise InstallDirValidationError(msg="Install directory must be empty")

    try:
        test_file = install_dir / "tmp_test_if_dir_writable"
        test_file.write_text("(:")
        test_file.unlink()
    except OSError as e:
        raise InstallDirValidationError(msg="Install directory must be writable") from e

    if install_dir.is_relative_to(config_manager.games_dir):
        raise InstallDirValidationError(
            msg=(
                "Install directory can only be under "
                f"{config_manager.games_dir} if using the generated default path"
            ),
        )

    return CaseInsensitiveAbsolutePath(install_dir)


def get_innoextract_path() -> Path:
    """
    Raises:
        FileNotFoundError: innoextract  not found
    """
    our_innoextract_path = external_dependencies_dir / (
        "innoextract.exe" if os.name == "nt" else "innoextract"
    )
    if our_innoextract_path.exists():
        return our_innoextract_path

    system_innoextract = shutil.which("innoextract")
    if not system_innoextract:
        raise FileNotFoundError(
            "innoextract not found in filesystem or PATH", our_innoextract_path
        )

    return Path(system_innoextract)


@attrs.frozen(kw_only=True)
class InstallGameError(Exception):
    msg: str


async def install_game(
    *,
    installer: GameInstaller,
    install_dir: CaseInsensitiveAbsolutePath,
    progress: Progress,
) -> None:
    """
    Create a new game install at `install_dir` from `installer`. `install_dir` should
    be pre-validated with `validate_user_provided_install_dir` if it was user provided.

    Raises:
        InstallGameError: Error while installing the game. Show `.msg` to the user.
    """
    try:
        logger.info("Downloading %s game installer", installer.name)
        progress.unit_type = "byte"
        download_progress_item = ProgressItem()
        progress.progress_items.append(download_progress_item)
        async with (
            trio.wrap_file(NamedTemporaryFile()) as installer_file,
            TemporaryDirectoryAsyncPath() as extract_dir,
        ):
            try:
                # Using the `async with client.stream(...)` currently doesn't work with
                # Nuitka. See <https://github.com/Nuitka/Nuitka/issues/3697>.
                request = get_httpx_client(installer.url).build_request(
                    "GET", installer.url
                )
                response = await get_httpx_client(installer.url).send(
                    request, stream=True
                )
                response.raise_for_status()

                bytes_currently_downloaded = response.num_bytes_downloaded
                download_progress_item.total = int(
                    response.headers.get("Content-Length", 46000000)
                )
                async for chunk in response.aiter_bytes():
                    download_progress_item.completed += (
                        response.num_bytes_downloaded - bytes_currently_downloaded
                    )
                    bytes_currently_downloaded = response.num_bytes_downloaded
                    await installer_file.write(chunk)
            finally:
                await response.aclose()

            logger.info("Extracting %s game installer", installer.name)
            progress.reset()
            try:
                completed_process = await trio.run_process(
                    (
                        get_innoextract_path(),
                        "--exclude-temp",
                        "--output-dir",
                        extract_dir,
                        installer_file.name,
                    ),
                    # On macOS with Nuitka, dependencies of innoextract will be in
                    # the data dir parent, but the executable won't be configured
                    # properly to look for them there.
                    env={"DYLD_FALLBACK_LIBRARY_PATH": str(data_dir.parent)}
                    if sys.platform == "darwin" and "__compiled__" in globals()
                    else None,
                    capture_stdout=True,
                    capture_stderr=True,
                )
            except CalledProcessError as e:
                e.add_note("stdout: \n" + e.stdout.decode().strip())
                e.add_note("stderr: \n" + e.stderr.decode().strip())
                raise InstallGameError(msg="Installer extraction failed") from e
            logger.debug(
                "innoextract stdout: \n %s", completed_process.stdout.decode().strip()
            )

            # Verify extracted game dir.
            try:
                find_game_dir_game_type(
                    CaseInsensitiveAbsolutePath(extract_dir) / "app"
                )
            except InvalidGameDirError as e:
                raise InstallGameError(
                    msg="Installer extraction did not create a valid game directory"
                ) from e

            # Move the extracted game directory to `install_dir`.
            if install_dir.exists():
                install_dir.rmdir()
            install_dir.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(extract_dir / "app", install_dir)
    except HTTPError as e:
        raise InstallGameError(msg="Failed to download the game installer") from e
