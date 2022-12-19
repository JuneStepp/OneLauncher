
from enum import Enum
from pathlib import Path
from typing import Callable, Dict, List, Optional, Set
from uuid import UUID
from xml.etree import ElementTree

from onelauncher.config import platform_dirs
from onelauncher.game_account import GameAccount
from onelauncher.resources import OneLauncherLocale
from onelauncher.utilities import CaseInsensitiveAbsolutePath


# TODO: Change to StrEnum once on Python 3.11. Can then also change the
# places using the enum value to just the enum. ex. ClientType.WIN64.value
# to get "WIN64" can instead just be ClientType.WIN64. Think this would be
# helpful, as it makes it where the enum can just be used everywhere
# rather than having to know about the difference between the enum and
# game client values.
class ClientType(Enum):
    WIN64 = "WIN64"
    WIN32 = "WIN32"
    WIN32_LEGACY = "WIN32Legacy"
    WIN32Legacy = "WIN32Legacy"

class Game():
    def __init__(self,
                 uuid: UUID,
                 game_type: str,
                 game_directory: CaseInsensitiveAbsolutePath,
                 locale: OneLauncherLocale,
                 client_type: ClientType,
                 high_res_enabled: bool,
                 patch_client_filename: str,
                 startup_scripts: List[Path],
                 name: str,
                 description: str,
                 newsfeed: Optional[str] = None,
                 standard_game_launcher_filename: Optional[str] = None,
                 wine_path: Optional[Path] = None,
                 builtin_wine_prefix_enabled: Optional[bool] = None,
                 wine_prefix_path: Optional[Path] = None,
                 wine_debug_level: Optional[str] = None,
                 accounts: Optional[Dict[str, GameAccount]] = None,
                 on_name_change_function: Optional[Callable[[], None]] = None,
                 ) -> None:
        self.uuid = uuid
        self.game_type = game_type
        self.game_directory = game_directory
        self.locale = locale
        self.client_type = client_type
        self.high_res_enabled = high_res_enabled
        self.patch_client_filename = patch_client_filename
        self.startup_scripts = startup_scripts
        self._name = name
        self.description = description
        self.newsfeed = newsfeed
        self.standard_game_launcher_filename = standard_game_launcher_filename
        self.wine_path = wine_path
        self.builtin_wine_prefix_enabled = builtin_wine_prefix_enabled
        self.wine_prefix_path = wine_prefix_path
        self.wine_debug_level = wine_debug_level
        self.accounts = accounts
        self.on_name_change_function = on_name_change_function
        self.load_launcher_config()

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, new_value: str):
        self._name = new_value

        if self.on_name_change_function:
            self.on_name_change_function()

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

    @property
    def plugins_dir(self) -> CaseInsensitiveAbsolutePath:
        return self.documents_config_dir / "Plugins"

    @property
    def skins_dir(self) -> CaseInsensitiveAbsolutePath:
        return self.documents_config_dir / "ui" / "skins"

    @property
    def music_dir(self) -> CaseInsensitiveAbsolutePath:
        return self.documents_config_dir / "Music"

    def get_addons_dir(self, addon_type: str) -> CaseInsensitiveAbsolutePath:
        return {
            "Plugin": self.plugins_dir,
            "Skin": self.skins_dir,
            "Music": self.music_dir}[addon_type]
