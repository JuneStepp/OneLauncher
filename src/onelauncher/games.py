
from datetime import datetime
from enum import Enum, StrEnum
from typing import Dict, List, Optional
from uuid import UUID, uuid4
from xml.etree import ElementTree

from onelauncher.config import platform_dirs
from onelauncher.game_account import GameAccount
from onelauncher.resources import OneLauncherLocale
from onelauncher.utilities import CaseInsensitiveAbsolutePath


class ClientType(StrEnum):
    WIN64 = "WIN64"
    WIN32 = "WIN32"
    WIN32_LEGACY = "WIN32Legacy"
    WIN32Legacy = "WIN32Legacy"


class Game():
    def __init__(self,
                 uuid: UUID,
                 sorting_priority: int,
                 game_type: str,
                 game_directory: CaseInsensitiveAbsolutePath,
                 locale: OneLauncherLocale,
                 client_type: ClientType,
                 high_res_enabled: bool,
                 patch_client_filename: str,
                 name: str,
                 description: str,
                 newsfeed: Optional[str] = None,
                 last_played: datetime | None = None,
                 standard_game_launcher_filename: Optional[str] = None,
                 accounts: Optional[Dict[str, GameAccount]] = None,
                 ) -> None:
        self.uuid = uuid
        self.sorting_priority = sorting_priority
        self.game_type = game_type
        self.game_directory = game_directory
        self.locale = locale
        self.client_type = client_type
        self.high_res_enabled = high_res_enabled
        self.patch_client_filename = patch_client_filename
        self.name = name
        self.description = description
        self.newsfeed = newsfeed
        self.last_played = last_played
        self.standard_game_launcher_filename = standard_game_launcher_filename
        self.accounts = accounts
        self.load_launcher_config()

    @property
    def game_type(self) -> str:
        return self._game_type

    @game_type.setter
    def game_type(self, new_value: str) -> None:
        """LOTRO or DDO"""
        valid_game_types = ["LOTRO", "DDO"]
        if new_value not in valid_game_types:
            raise ValueError(
                f"{new_value} is not a valid game type. Valid types are {valid_game_types}.")

        self._game_type = new_value

    def load_launcher_config(self):
        """
        Load launcher config data from game_directory.
        This includes game documents settings dir and data that is used during login.
        This function should be re-run if something in the launcher config has changed.
        """
        old_config_file = self.game_directory / "TurbineLauncher.exe.config"
        config_file = self.game_directory / \
            f"{self.game_type.lower()}.launcherconfig"
        if config_file.exists():
            self.load_launcher_config_file(config_file)
        elif old_config_file.exists():
            self.load_launcher_config_file(old_config_file)
        else:
            raise FileNotFoundError(
                f"`{self.game_directory}` has no launcher config file")

    def _get_launcher_config_value(
            self,
            key: str,
            app_settings_element: ElementTree.Element,
            config_file_path: CaseInsensitiveAbsolutePath) -> str:
        element = app_settings_element.find(
            f"./add[@key='{key}']")
        if element is None:
            raise KeyError(
                f"`{config_file_path}` launcher config file doesn't have `{key}` key.")

        if value := element.get("value"):
            return value
        else:
            raise KeyError(
                f"`{config_file_path}` launcher config file doesn't have `{key}` value.")

    def load_launcher_config_file(
            self,
            config_file: CaseInsensitiveAbsolutePath,) -> None:
        config = ElementTree.parse(config_file)
        app_settings = config.find("appSettings")
        if app_settings is None:
            raise KeyError(
                f"`{config_file}` launcher config file doesn't have `appSettings` element.")

        self._gls_datacenter_service = self._get_launcher_config_value(
            "Launcher.DataCenterService.GLS", app_settings, config_file)
        self._datacenter_game_name = self._get_launcher_config_value(
            "DataCenter.GameName", app_settings, config_file)
        self._documents_config_dir = CaseInsensitiveAbsolutePath(
            platform_dirs.user_documents_path /
            self._get_launcher_config_value(
                "Product.DocumentFolder",
                app_settings,
                config_file))

    @property
    def gls_datacenter_service(self) -> str:
        return self._gls_datacenter_service

    @property
    def datacenter_game_name(self) -> str:
        return self._datacenter_game_name

    @property
    def documents_config_dir(self) -> CaseInsensitiveAbsolutePath:
        """
        The folder in the user documents dir that the game stores information in.
        This includes addons, screenshots, user config files, ect
        """
        return self._documents_config_dir


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
        games: List[Game],
    ) -> None:
        self.games = {game.uuid: game for game in games}
        self._current_game = None

    @property
    def current_game(self) -> Game:
        if self._current_game:
            return self._current_game

        last_played_game = self.get_games_sorted_by_last_played()[0]
        return (
            last_played_game if last_played_game.last_played is not None
            else self.get_games_sorted_by_priority(
                last_played_game.game_type)[0])

    @current_game.setter
    def current_game(self, game: Game) -> None:
        self._current_game = game # type: ignore

    def get_games_by_game_type(self, game_type: str) -> List[Game]:
        return [game for game in self.games.values() if game.game_type ==
                game_type]

    def get_games_sorted_by_priority(
            self, game_type: str) -> List[Game]:
        games = self.get_games_by_game_type(
            game_type)
        # Sort games by sorting_priority. Games with sorting_priority of -1 are
        # put at end of list
        return sorted(
            games,
            key=lambda game: "Z" if game.sorting_priority == -
            1 else str(
                game.sorting_priority))

    def get_games_sorted_by_last_played(
            self, game_type: str | None = None) -> List[Game]:
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
            game_type: str,
            sorting_mode: GamesSortingMode) -> List[Game]:
        match sorting_mode:
            case GamesSortingMode.PRIORITY:
                return self.get_games_sorted_by_priority(game_type)
            case GamesSortingMode.LAST_USED:
                return self.get_games_sorted_by_last_played(game_type)
            case GamesSortingMode.ALPHABETICAL:
                return self.get_games_sorted_alphabetically(game_type)

    def get_games_sorted_alphabetically(
            self, game_type: str) -> List[Game]:
        return sorted(
            self.get_games_by_game_type(game_type),
            key=lambda game: game.name)

    def get_new_uuid(self) -> UUID:
        """Return UUID that doesn't already exist in `self.games.values()`"""
        current_uuids = list(self.games)

        uuid = None
        while uuid in current_uuids or not uuid:
            uuid = uuid4()

        return uuid
