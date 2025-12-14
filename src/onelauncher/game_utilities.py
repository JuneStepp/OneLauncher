import contextlib

from .config import platform_dirs
from .game_config import GameConfig, GameType
from .game_launcher_local_config import (
    GameLauncherLocalConfig,
    GameLauncherLocalConfigParseError,
    get_launcher_config_paths,
)
from .utilities import CaseInsensitiveAbsolutePath


class InvalidGameDirError(ValueError):
    """Path is not a valid game directory"""


def find_game_dir_game_type(game_dir: CaseInsensitiveAbsolutePath) -> GameType:
    """Attempt to find the game type associated with a given folder.

    Raises:
        InvalidGameDirError: `game_dir` is not a valid game directory

    Returns:
        GameType: Game type of `game_dir`
    """
    # Find any launcher config files. One is required for a game folder to be
    # valid.
    launcher_config_paths = get_launcher_config_paths(game_dir, None)
    if not launcher_config_paths:
        raise InvalidGameDirError("Game dir has no valid launcher config files")
    launcher_config_path = launcher_config_paths[0]

    # Try determining game type from launcher config filename
    with contextlib.suppress(ValueError):
        return GameType(launcher_config_path.stem.upper())

    # Try determining game type from datacenter game name
    try:
        launcher_config = GameLauncherLocalConfig.from_config_xml(
            launcher_config_path.read_text(encoding="UTF-8")
        )
        return GameType(launcher_config.datacenter_game_name)
    except (GameLauncherLocalConfigParseError, ValueError) as e:
        raise InvalidGameDirError("Game dir launcher config file wasn't valid") from e


def get_default_game_settings_dir(
    launcher_local_config: GameLauncherLocalConfig,
) -> CaseInsensitiveAbsolutePath:
    """
    See `get_game_settings_dir`. This is the default for when the user has not customized it.
    """
    return CaseInsensitiveAbsolutePath(
        platform_dirs.user_documents_path
        / launcher_local_config.documents_config_dir_name
    )


def get_game_settings_dir(
    game_config: GameConfig, launcher_local_config: GameLauncherLocalConfig
) -> CaseInsensitiveAbsolutePath:
    """
    The folder in the user documents dir that the game stores information in.
    This includes addons, screenshots, user config files, etc
    """
    return game_config.game_settings_directory or get_default_game_settings_dir(
        launcher_local_config=launcher_local_config
    )
