import contextlib
from enum import Enum
from uuid import UUID, uuid4

from .game import Game, GameType
from .game_launcher_local_config import (
    GameLauncherLocalConfig,
    GameLauncherLocalConfigParseError)
from .utilities import CaseInsensitiveAbsolutePath


class GamesSortingMode(Enum):
    """
    - priority: The manual order the user set in the setup wizard.
    - alphabetical: Alphabetical order.
    - last_used: Order of the most recently played games.
    """
    PRIORITY = "priority"
    LAST_USED = "last_used"
    ALPHABETICAL = "alphabetical"


class GamesSorted():
    def __init__(
        self,
        games: list[Game],
    ) -> None:
        self.games = {game.uuid: game for game in games}

    def get_games_by_game_type(self, game_type: GameType) -> list[Game]:
        return [game for game in self.games.values() if game.game_type ==
                game_type]

    def get_games_sorted_by_priority(
            self, game_type: GameType | None = None) -> list[Game]:
        games = self.get_games_by_game_type(
            game_type) if game_type else self.games.values()
        # Sort games by sorting_priority. Games with sorting_priority of -1 are
        # put at end of list
        return sorted(
            games,
            key=lambda game: "Z" if game.sorting_priority == -
            1 else str(
                game.sorting_priority))

    def get_games_sorted_by_last_played(
            self, game_type: GameType | None = None) -> list[Game]:
        games = set(
            self.get_games_by_game_type(game_type)) if game_type else set(
            self.games.values())
        games_never_played = {
            game for game in games if game.last_played is None}
        games_played = games - games_never_played
        # Get list of played games sorted by when they were last played
        games_played_sorted = sorted(
            games_played,
            key=lambda game: game.last_played,  # type: ignore
            reverse=True)
        # Games never played should be at end of list
        return games_played_sorted + list(games_never_played)

    def get_sorted_games_list(
            self,
            sorting_mode: GamesSortingMode,
            game_type: GameType | None = None) -> list[Game]:
        match sorting_mode:
            case GamesSortingMode.PRIORITY:
                return self.get_games_sorted_by_priority(game_type)
            case GamesSortingMode.LAST_USED:
                return self.get_games_sorted_by_last_played(game_type)
            case GamesSortingMode.ALPHABETICAL:
                return self.get_games_sorted_alphabetically(game_type)

    def get_games_sorted_alphabetically(
            self, game_type: GameType | None) -> list[Game]:
        games = self.get_games_by_game_type(
            game_type) if game_type else self.games.values()
        return sorted(games, key=lambda game: game.name)

    def get_new_uuid(self) -> UUID:
        """Return UUID that doesn't already exist in `self.games.values()`"""
        current_uuids = list(self.games)

        uuid = None
        while uuid in current_uuids or not uuid:
            uuid = uuid4()

        return uuid


def get_launcher_config_paths(
        search_dir: CaseInsensitiveAbsolutePath,
        game_type: GameType | None = None
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
                if file.name.lower(
                ) == f"{other_game_type.lower()}.launcherconfig":
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
                file.name.lower() == f"{game_type.lower()}.launcherconfig"):
            return 0
        elif file.suffix.lower() == ".launcherconfig":
            return 1
        elif file.name.lower() == "TurbineLauncher.exe.config".lower():
            return 2
        else:
            return 3

    return tuple(sorted(config_files, key=config_files_sorting_key))


def find_game_dir_game_type(
        game_dir: CaseInsensitiveAbsolutePath) -> GameType | None:
    """Attempt to find the game type associated with a given folder.
       Will return None, if `game_dir` appears to not be a valid game directory.

    Returns:
        GameType | None: Game type of `game_dir` or `None`,
                         if `game_dir` isn't a valid game directory.
    """
    # Find any launcher config files. One is required for a game folder to be
    # valid.
    launcher_config_paths = get_launcher_config_paths(game_dir, None)
    if not launcher_config_paths:
        return None
    launcher_config_path = launcher_config_paths[0]

    # Try determining game type from launcher config filename
    with contextlib.suppress(ValueError):
        return GameType(launcher_config_path.stem.upper())

    # Try determing game type from datacenter game name
    try:
        launcher_config = GameLauncherLocalConfig.from_config_xml(
            launcher_config_path.read_text())
        return GameType(launcher_config.datacenter_game_name)
    except (GameLauncherLocalConfigParseError, ValueError):
        return None
