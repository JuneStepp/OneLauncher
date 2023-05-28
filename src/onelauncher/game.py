from datetime import datetime
from enum import StrEnum
from typing import Dict, Optional
from uuid import UUID
from xml.etree import ElementTree

from .config import platform_dirs
from .game_account import GameAccount
from .resources import OneLauncherLocale
from .utilities import CaseInsensitiveAbsolutePath


class ClientType(StrEnum):
    WIN64 = "WIN64"
    WIN32 = "WIN32"
    WIN32_LEGACY = "WIN32Legacy"
    WIN32Legacy = "WIN32Legacy"


class GameType(StrEnum):
    LOTRO = "LOTRO"
    DDO = "DDO"


class Game():
    def __init__(self,
                 uuid: UUID,
                 sorting_priority: int,
                 game_type: GameType,
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

    def load_launcher_config(self):
        """
        Load launcher config data from game_directory.
        This includes game documents settings dir and data that is used during login.
        This function should be re-run if something in the launcher config has changed.

        Raises:
            FileNotFoundError: No launcher config file found
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

