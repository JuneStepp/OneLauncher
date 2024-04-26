import contextlib

from .game_config import GameType
from .game_launcher_local_config import (
    GameLauncherLocalConfig,
    GameLauncherLocalConfigParseError,
)
from .utilities import CaseInsensitiveAbsolutePath


def get_launcher_config_paths(
    search_dir: CaseInsensitiveAbsolutePath, game_type: GameType | None = None
) -> tuple[CaseInsensitiveAbsolutePath, ...]:
    """
    Return all launcher config files from search_dir sorted by relevance.
    File names matching a different game type from `game_type` won't be
    returned.
    """
    config_files = list(search_dir.glob("*.launcherconfig"))

    if game_type is not None:
        # Remove launcher config files that are for other game types
        other_game_types = set(GameType) - {game_type}
        for file in config_files:
            for other_game_type in other_game_types:
                if file.name.lower() == f"{other_game_type.lower()}.launcherconfig":
                    config_files.remove(file)

    # Add legacy launcher config files to `config_files`
    legacy_config_names = ["TurbineLauncher.exe.config"]
    if game_type == GameType.DDO or game_type is None:
        legacy_config_names.append("DNDLauncher.exe.config")
    for config_name in legacy_config_names:
        legacy_path = search_dir / config_name
        if legacy_path.exists():
            config_files.append(legacy_path)

    def config_files_sorting_key(file: CaseInsensitiveAbsolutePath) -> int:
        if game_type is not None and (
            file.name.lower() == f"{game_type.lower()}.launcherconfig"
        ):
            return 0
        elif file.suffix.lower() == ".launcherconfig":
            return 1
        elif file.name.lower() == "TurbineLauncher.exe.config".lower():
            return 2
        else:
            return 3

    return tuple(sorted(config_files, key=config_files_sorting_key))


class InvalidGameDirError(ValueError):
    """Path is not a valid game directory"""


def find_game_dir_game_type(game_dir: CaseInsensitiveAbsolutePath) -> GameType:
    """Attempt to find the game type associated with a given folder.
       Will return None, if `game_dir` appears to not be a valid game directory.

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

    # Try determing game type from datacenter game name
    try:
        launcher_config = GameLauncherLocalConfig.from_config_xml(
            launcher_config_path.read_text()
        )
        return GameType(launcher_config.datacenter_game_name)
    except (GameLauncherLocalConfigParseError, ValueError) as e:
        raise InvalidGameDirError("Game dir launcher config file wasn't valid") from e
