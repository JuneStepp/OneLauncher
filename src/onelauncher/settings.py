# coding=utf-8
###########################################################################
# Class to handle loading and saving game settings
# for OneLauncher.
#
# Based on PyLotRO
# (C) 2009 AJackson <ajackson@bcs.org.uk>
#
# Based on LotROLinux
# (C) 2007-2008 AJackson <ajackson@bcs.org.uk>
#
#
# (C) 2019-2021 June Stepp <contact@JuneStepp.me>
#
# This file is part of OneLauncher
#
# OneLauncher is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# OneLauncher is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with OneLauncher.  If not, see <http://www.gnu.org/licenses/>.
###########################################################################
import contextlib
import logging
import os
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set
from uuid import UUID, uuid4
from xml.etree import ElementTree

import rtoml

import onelauncher
from onelauncher.config import platform_dirs
from onelauncher.game_accounts import GameAccount
from onelauncher.resources import (OneLauncherLocale, available_locales,
                                   system_locale)
from onelauncher.utilities import CaseInsensitiveAbsolutePath


class ProgramSettings():
    def __init__(self, config_path: Optional[Path] = None) -> None:
        if not config_path:
            config_path = platform_dirs.user_config_path / \
                f"{onelauncher.__title__}.toml"
        self.config_path = config_path
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        self.load()

        self.ui_locale: OneLauncherLocale = self.default_locale

    @property
    def games_sorting_mode(self) -> str:
        return self._games_sorting_mode

    @games_sorting_mode.setter
    def games_sorting_mode(self, new_value: str) -> None:
        """
        Games sorting mode.

        priority: The manual order the user set in the setup wizard.
        alphabetical: Alphabetical order.
        last_used: Order of the most recently played games.
        """
        accepted_values = ["priority", "alphabetical", "last_used"]
        if new_value not in accepted_values:
            raise ValueError(f"{new_value} is not a valid games sorting mode.")

        self._games_sorting_mode = new_value

    @property
    def default_locale(self) -> OneLauncherLocale:
        """Locale for OneLauncher UI. This is changed by __init__.py"""
        return self._default_locale

    @default_locale.setter
    def default_locale(self, new_value: OneLauncherLocale):
        self._default_locale = new_value

        set_ui_locale()

    @property
    def always_use_default_language_for_ui(self) -> bool:
        return self._always_use_default_language_for_ui

    @always_use_default_language_for_ui.setter
    def always_use_default_language_for_ui(self, new_value: bool):
        self._always_use_default_language_for_ui = new_value

        set_ui_locale()

    def load(self):
        # Defaults will be used if the settings file doesn't exist
        if self.config_path.exists():
            settings_dict = rtoml.load(self.config_path)
        else:
            settings_dict = {}

        if "default_language" in settings_dict:
            self._default_locale = available_locales[settings_dict["default_language"]]
        elif system_locale:
            self._default_locale = system_locale
        else:
            self._default_locale = available_locales["en-US"]

        self._always_use_default_language_for_ui: bool = settings_dict.get(
            "always_use_default_language_for_ui", False)
        self.save_accounts = settings_dict.get("save_accounts", False)
        self.save_accounts_passwords = settings_dict.get(
            "save_accounts_passwords", False)
        self.games_sorting_mode = settings_dict.get(
            "games_sorting_mode", "priority")

    def save(self):
        settings_dict = {
            "onelauncher_version": onelauncher.__version__,
            "default_language": self.default_locale.lang_tag,
            "always_use_default_language_for_ui": self.always_use_default_language_for_ui,
            "save_accounts": self.save_accounts,
            "save_accounts_passwords": self.save_accounts_passwords,
            "games_sorting_mode": self.games_sorting_mode,
        }

        rtoml.dump(settings_dict, self.config_path, pretty=True)


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
        self._locale = locale
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

    @property
    def locale(self) -> OneLauncherLocale:
        return self._locale

    @locale.setter
    def locale(self, new_val: OneLauncherLocale):
        self._locale = new_val

        set_ui_locale()

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


class GamesSettings():
    def __init__(self, config_path: Optional[Path] = None) -> None:
        if not config_path:
            config_path = platform_dirs.user_config_path / \
                "games.toml"
        self.config_path = config_path
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        self.games: Dict[UUID, Game] = {}

        # These are all in the format of the lower the index the more important
        self.lotro_games_priority_sorted: List[Game] = []
        self.lotro_games_last_used_sorted: List[Game] = []
        self.lotro_games_alphabetical_sorted: List[Game] = []
        self.ddo_games_priority_sorted: List[Game] = []
        self.ddo_games_last_used_sorted: List[Game] = []
        self.ddo_games_alphabetical_sorted: List[Game] = []

        self.load()

    def get_game_name(self, game_directory: Path, uuid: UUID) -> str:
        return f"{game_directory.name} ({uuid})"

    def uuid_str_list_to_game_list(self, uuid_list: List[str]) -> List[Game]:
        return [self.games[UUID(uuid_str)] for uuid_str in uuid_list if UUID(
            uuid_str) in self.games]

    def load(self):
        if not self.config_path.exists():
            return

        settings_dict = rtoml.load(self.config_path)
        if "games" not in settings_dict or len(settings_dict["games"]) < 1:
            return
        games_dicts = settings_dict["games"]
        for game_dict in games_dicts:
            self.load_game(game_dict)

        # Load games sorting lists
        if "lotro_games_priority_sorted" in settings_dict:
            self.lotro_games_priority_sorted = self.uuid_str_list_to_game_list(
                settings_dict["lotro_games_priority_sorted"])
        else:
            self.lotro_games_priority_sorted = [
                game for game in self.games.values() if game.game_type == "LOTRO"]
        if "lotro_games_last_used_sorted" in settings_dict:
            self.lotro_games_last_used_sorted = self.uuid_str_list_to_game_list(
                settings_dict["lotro_games_last_used_sorted"])
        else:
            self.lotro_games_last_used_sorted = [
                game for game in self.games.values() if game.game_type == "LOTRO"]
        if "ddo_games_priority_sorted" in settings_dict:
            self.ddo_games_priority_sorted = self.uuid_str_list_to_game_list(
                settings_dict["ddo_games_priority_sorted"])
        else:
            self.ddo_games_priority_sorted = [
                game for game in self.games.values() if game.game_type == "DDO"]
        if "ddo_games_last_used_sorted" in settings_dict:
            self.ddo_games_last_used_sorted = self.uuid_str_list_to_game_list(
                settings_dict["ddo_games_last_used_sorted"])
        else:
            self.ddo_games_last_used_sorted = [
                game for game in self.games.values() if game.game_type == "DDO"]

        self.lotro_games_alphabetical_sorted = self.lotro_games_priority_sorted.copy()
        self.ddo_games_alphabetical_sorted = self.ddo_games_priority_sorted.copy()
        self.sort_alphabetical_sorting_lists()

        self.lotro_sorting_modes = {
            "priority": self.lotro_games_priority_sorted,
            "last_used": self.lotro_games_last_used_sorted,
            "alphabetical": self.lotro_games_alphabetical_sorted}
        self.ddo_sorting_modes = {
            "priority": self.ddo_games_priority_sorted,
            "last_used": self.ddo_games_last_used_sorted,
            "alphabetical": self.ddo_games_alphabetical_sorted}

        if ("last_used_game_uuid" in settings_dict and
                UUID(settings_dict["last_used_game_uuid"]) in self.games):
            self._current_game = self.games[UUID(
                settings_dict["last_used_game_uuid"])]
        elif self.lotro_games_priority_sorted:
            self._current_game = self.lotro_games_priority_sorted[0]
        elif self.ddo_games_priority_sorted:
            self._current_game = self.ddo_games_priority_sorted[0]
        elif self.lotro_games_last_used_sorted:
            self._current_game = self.lotro_games_last_used_sorted[0]
        elif self.ddo_games_last_used_sorted:
            self._current_game = self.ddo_games_last_used_sorted[0]
        else:
            self._current_game = list(self.games.values())[0]

    def load_game(self, game_dict: dict[str, Any]):
        uuid = UUID(game_dict["uuid"])
        game_directory = CaseInsensitiveAbsolutePath(
            game_dict["game_directory"])

        # Deal with missing sections
        game_dict["info"] = game_dict.get("info", {})
        game_dict["wine"] = game_dict.get("wine", {})
        game_dict["accounts"] = game_dict.get("accounts", [])

        # Deal with Paths
        wine_path = None
        if "wine_path" in game_dict["wine"]:
            wine_path = Path(game_dict["wine"]["wine_path"])

        prefix_path = None
        if "prefix_path" in game_dict["wine"]:
            prefix_path = Path(game_dict["wine"]["prefix_path"])

        self.games[uuid] = Game(uuid,
                                game_dict["game_type"],
                                game_directory,
                                available_locales[game_dict.get("language",
                                                                str(program_settings.default_locale))],
                                ClientType(game_dict.get("client_type",
                                                         "WIN64")),
                                game_dict.get("high_res_enabled",
                                              True),
                                game_dict.get("patch_client_filename",
                                              "patchclient.dll"),
                                [Path(script) for script in game_dict.get("startup_scripts", [])],
                                game_dict["info"].get("name",
                                                      self.get_game_name(game_directory,
                                                                         uuid)),
                                game_dict["info"].get("description",
                                                      ""),
                                game_dict["info"].get("newsfeed",
                                                      None),
                                game_dict.get("standard_game_launcher_filename", None),
                                wine_path,
                                game_dict["wine"].get("builtin_prefix_enabled",
                                                      True),
                                prefix_path,
                                game_dict["wine"].get("debug_level",
                                                      None),
                                {account["account_name"]: GameAccount(account["account_name"],
                                                                      uuid,
                                                                      account["last_used_world_name"])
                                    for account in game_dict["accounts"]},
                                on_name_change_function=self.sort_alphabetical_sorting_lists,
                                )

    def sort_alphabetical_sorting_lists(self) -> None:
        self.lotro_games_alphabetical_sorted.sort(key=lambda game: game.name)
        self.ddo_games_alphabetical_sorted.sort(key=lambda game: game.name)

    def save(self):
        settings_dict: Dict[str, Any] = {}
        with contextlib.suppress(AttributeError):
            if self.current_game.uuid in self.games:
                if self.current_game.game_type == "LOTRO":
                    last_used_sorted = self.lotro_games_last_used_sorted
                elif self.current_game.game_type == "DDO":
                    last_used_sorted = self.ddo_games_last_used_sorted
                else:
                    raise TypeError(
                        "Settings current_game saving doesn't recognize "
                        f"{self.current_game.game_type} as a game type")

                # Move current game to front of list
                last_used_sorted.remove(self.current_game)
                last_used_sorted.insert(0, self.current_game)

                settings_dict["last_used_game_uuid"] = str(
                    self.current_game.uuid)
        settings_dict["lotro_games_priority_sorted"] = [
            str(game.uuid) for game in self.lotro_games_priority_sorted]
        settings_dict["lotro_games_last_used_sorted"] = [
            str(game.uuid) for game in self.lotro_games_last_used_sorted]
        settings_dict["ddo_games_priority_sorted"] = [
            str(game.uuid) for game in self.ddo_games_priority_sorted]
        settings_dict["ddo_games_last_used_sorted"] = [
            str(game.uuid) for game in self.ddo_games_last_used_sorted]

        games_list: List[Dict[str, Any]] = []
        settings_dict["games"] = games_list
        for game in self.games.values():
            game_dict: Dict[str, Any] = {
                "uuid": str(
                    game.uuid),
                "game_type": game.game_type,
                "game_directory": str(
                    game.game_directory),
                "language": game.locale.lang_tag,
                "client_type": game.client_type.value,
                "high_res_enabled": game.high_res_enabled,
                "patch_client_filename": game.patch_client_filename,
            }
            if game.standard_game_launcher_filename:
                game_dict["standard_game_launcher_filename"] = game.standard_game_launcher_filename

            if game.startup_scripts:
                game_dict["startup_scripts"] = [
                    str(script) for script in game.startup_scripts]

            if os.name != "nt":  # WINE is not needed on Windows
                wine_settings_dict = {}
                if game.builtin_wine_prefix_enabled is not None:
                    wine_settings_dict["builtin_prefix_enabled"] = game.builtin_wine_prefix_enabled

                if game.wine_path is not None:
                    wine_settings_dict["wine_path"] = str(game.wine_path)

                if game.wine_prefix_path is not None:
                    wine_settings_dict["prefix_path"] = str(
                        game.wine_prefix_path)

                if game.wine_debug_level is not None:
                    wine_settings_dict["debug_level"] = game.wine_debug_level

                game_dict["wine"] = wine_settings_dict

            info_settings_dict = {
                "name": game.name,
                "description": game.description}
            if game.newsfeed is not None:
                info_settings_dict["newsfeed"] = game.newsfeed
            game_dict["info"] = info_settings_dict

            if game.accounts:
                game_dict["accounts"] = [
                    {"account_name": account.username,
                     "last_used_world_name": account.last_used_world_name}
                    for account in game.accounts.values()]

            games_list.append(game_dict)

        rtoml.dump(settings_dict, self.config_path, pretty=True)

    @property
    def current_game(self) -> Game:
        return self._current_game

    @current_game.setter
    def current_game(self, new_value: Game):
        self._current_game = new_value

        set_ui_locale()

    def get_new_uuid(self) -> UUID:
        """Return UUID that doesn't already exist in the games config"""
        current_uuids = list(self.games)

        uuid = None
        while uuid in current_uuids or not uuid:
            uuid = uuid4()

        return uuid


def set_ui_locale():
    """Set locale for OneLauncher UI"""
    if (
        not program_settings.always_use_default_language_for_ui
        and game_settings.games
    ):
        program_settings.ui_locale = game_settings.current_game.locale
    else:
        program_settings.ui_locale = program_settings.default_locale


logger = logging.getLogger("main")
program_settings = ProgramSettings()
game_settings = GamesSettings()
