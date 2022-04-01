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
import os
import logging
from pathlib import Path
import pathlib
from sys import platform
from typing import Callable, Dict, Final, List, Optional
from uuid import UUID, uuid4

import rtoml
from vkbeautify import xml as prettify_xml

import onelauncher
from onelauncher.config import platform_dirs
from onelauncher.resources import available_locales, Locale, system_locale


class ProgramSettings():
    def __init__(self, config_path: Path = None) -> None:
        if not config_path:
            config_path = platform_dirs.user_config_path / \
                f"{onelauncher.__title__}.toml"
        self.config_path = config_path
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        self.load()

        self.ui_locale = self.default_locale

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
    def default_locale(self) -> Locale:
        """Locale for OneLauncher UI. This is changed by __init__.py"""
        return self._default_locale

    @default_locale.setter
    def default_locale(self, new_value: Locale):
        self._default_locale = new_value

        onelauncher.set_ui_locale()

    @property
    def always_use_default_language_for_ui(self) -> bool:
        return self._always_use_default_language_for_ui

    @always_use_default_language_for_ui.setter
    def always_use_default_language_for_ui(self, new_value: bool):
        self._always_use_default_language_for_ui = new_value

        onelauncher.set_ui_locale()

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


class Account():
    def __init__(self, name: str, last_used_world_name: str,
                 save_subaccount_selection: bool = False) -> None:
        self._name: Final = name
        self.last_used_world_name = last_used_world_name
        self.save_subaccount_selection = save_subaccount_selection

    @property
    def name(self) -> str:
        """Account name. This is immutable."""
        return self._name


class CaseInsensitiveAbsolutePath(Path):
    _flavour = pathlib._windows_flavour if os.name == 'nt' else pathlib._posix_flavour  # type: ignore

    def __new__(cls, *pathsegments, **kwargs):
        normal_path = Path(*pathsegments, **kwargs)
        if not normal_path.is_absolute():
            raise ValueError("Path is not absolute.")
        path = cls._get_real_path_from_fully_case_insensitive_path(normal_path)
        return super().__new__(cls, path, **kwargs)

    @classmethod
    def _get_real_path_from_fully_case_insensitive_path(
            cls, base_path: Path) -> Path:
        """Return any found path that matches base_path when ignoring case"""
        # Base version already exists
        if base_path.exists():
            return base_path

        parts = list(base_path.parts)
        if not Path(parts[0]).exists():
            # If root doesn't exist, nothing else can be checked
            return base_path

        # Range starts at 1 to ingore root which has already been checked
        for i in range(1, len(parts)):
            current_path = Path(
                *(parts if i == len(parts) - 1 else parts[:i + 1]))
            real_path = cls._get_real_path_from_name_case_insensitive_path(
                current_path)
            # Second check is for if there is a file or broken symlink before
            # the end of the path. Without the check it would raise and
            # exception in cls._get_real_path_from_name_case_insensitive_path
            if real_path is None or (
                    i < len(parts)-1 and not real_path.is_dir()):
                # No version exists, so the original is just returned
                return base_path

            parts[i] = real_path.name

        return Path(*parts)

    @staticmethod
    def _get_real_path_from_name_case_insensitive_path(
            base_path: Path) -> Optional[Path]:
        """
        Return any found path where path.name == base_path.name ignoring case.
        base_path.parent has to exist. Use _get_case_sensitive_full_path if
        this is not the case.
        """
        if not base_path.parent.exists():
            raise FileNotFoundError(
                f"`{base_path.parent}` parent path does not exist")

        if base_path.exists():
            return base_path

        for path in base_path.parent.iterdir():
            if path.name.lower() == base_path.name.lower():
                return path

        return None

    def _make_child(self, args) -> Path:
        _, _, parts = super()._parse_args(args)  # type: ignore
        joined_path = super()._make_child((Path(*parts),))  # type: ignore
        return self._get_real_path_from_fully_case_insensitive_path(
            joined_path)


class Game():
    def __init__(self,
                 uuid: UUID,
                 game_type: str,
                 game_directory: CaseInsensitiveAbsolutePath,
                 locale: Locale,
                 client_type: str,
                 high_res_enabled: bool,
                 patch_client_filename: str,
                 startup_scripts: List[Path],
                 name: str,
                 description: str,
                 newsfeed: str = None,
                 wine_path: Path = None,
                 builtin_wine_prefix_enabled: bool = None,
                 wine_prefix_path: Path = None,
                 wine_debug_level: str = None,
                 accounts: Dict[str, Account] = None,
                 on_name_change_function: Callable[[], None] = None,
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
        self.wine_path = wine_path
        self.builtin_wine_prefix_enabled = builtin_wine_prefix_enabled
        self.wine_prefix_path = wine_prefix_path
        self.wine_debug_level = wine_debug_level
        self.accounts = accounts
        self.on_name_change_function = on_name_change_function

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
    def client_type(self) -> str:
        return self._client_type

    @property
    def locale(self) -> Locale:
        return self._locale

    @locale.setter
    def locale(self, new_value: Locale):
        self._locale = new_value

        onelauncher.set_ui_locale()

    @client_type.setter
    def client_type(self, new_value: str) -> None:
        """WIN32, WIN32Legacy, or WIN64"""
        valid_client_types = ["WIN32", "WIN32Legacy", "WIN64"]
        if new_value not in valid_client_types:
            raise ValueError(
                f"{new_value} is not a valid client type. Valid types are {valid_client_types}.")

        self._client_type = new_value


class GamesSettings():
    def __init__(self, config_path: Path = None) -> None:
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

    def load_game(self, game_dict: dict):
        uuid = UUID(game_dict["uuid"])
        game_directory = CaseInsensitiveAbsolutePath(
            game_dict["game_directory"])

        # Deal with missing sections
        game_dict["info"] = game_dict.get("info", {})
        game_dict["wine"] = game_dict.get("wine", {})
        game_dict["accounts"] = game_dict.get("accounts", [])

        # Deal with Paths
        if "wine_path" in game_dict["wine"]:
            wine_path = Path(game_dict["wine"]["wine_path"])
        else:
            wine_path = None
        if "prefix_path" in game_dict["wine"]:
            prefix_path = Path(game_dict["wine"]["prefix_path"])
        else:
            prefix_path = None

        self.games[uuid] = Game(
            uuid,
            game_dict["game_type"],
            game_directory,
            available_locales[
                game_dict.get(
                    "language", str(
                        onelauncher.program_settings.default_locale)
                )
            ],
            game_dict.get("client_type", "WIN64"),
            game_dict.get("high_res_enabled", True),
            game_dict.get("patch_client_filename", "patchclient.dll"),
            [Path(script) for script in game_dict.get("startup_scripts", [])],
            game_dict["info"].get(
                "name", self.get_game_name(game_directory, uuid)),
            game_dict["info"].get("description", ""),
            game_dict["info"].get("newsfeed", None),
            wine_path,
            game_dict["wine"].get("builtin_prefix_enabled", True),
            prefix_path,
            game_dict["wine"].get("debug_level", None),
            {
                account["account_name"]: Account(
                    account["account_name"], account["last_used_world_name"],
                    account["save_subaccount_selection"]
                )
                for account in game_dict["accounts"]
            },
            on_name_change_function=self.sort_alphabetical_sorting_lists,
        )

    def sort_alphabetical_sorting_lists(self) -> None:
        self.lotro_games_alphabetical_sorted.sort(key=lambda game: game.name)
        self.ddo_games_alphabetical_sorted.sort(key=lambda game: game.name)

    def save(self):
        settings_dict = {}
        try:
            if self.current_game.uuid in self.games:
                if self.current_game.game_type == "LOTRO":
                    list = self.lotro_games_last_used_sorted
                elif self.current_game.game_type == "DDO":
                    list = self.ddo_games_last_used_sorted
                else:
                    raise TypeError(
                        "Settings current_game saving doesn't recognize "
                        f"{self.current_game.game_type} as a game type")

                # Move current game to front of list
                list.remove(self.current_game)
                list.insert(0, self.current_game)

                settings_dict["last_used_game_uuid"] = str(
                    self.current_game.uuid)
        except AttributeError:
            pass

        settings_dict["lotro_games_priority_sorted"] = [
            str(game.uuid) for game in self.lotro_games_priority_sorted]
        settings_dict["lotro_games_last_used_sorted"] = [
            str(game.uuid) for game in self.lotro_games_last_used_sorted]
        settings_dict["ddo_games_priority_sorted"] = [
            str(game.uuid) for game in self.ddo_games_priority_sorted]
        settings_dict["ddo_games_last_used_sorted"] = [
            str(game.uuid) for game in self.ddo_games_last_used_sorted]

        settings_dict["games"] = []
        for game in self.games.values():
            if os.name == "nt":
                wine_settings_dict = {}
            else:
                wine_settings_dict = {
                    "wine_path": str(game.wine_path),
                    "builtin_prefix_enabled": game.builtin_wine_prefix_enabled,
                    "prefix_path": str(game.wine_prefix_path),
                    "debug_level": game.wine_debug_level,
                }

            info_settings_dict = {
                "name": game.name,
                "description": game.description,
                "newsfeed": game.newsfeed,
            }

            if game.accounts:
                accounts_settings_list = [
                    {"account_name": account.name,
                        "last_used_world_name": account.last_used_world_name,
                        "save_subaccount_selection": account.save_subaccount_selection}
                    for account in game.accounts.values()]
            else:
                accounts_settings_list = []

            game_dict = {
                "uuid": str(
                    game.uuid),
                "game_type": game.game_type,
                "game_directory": str(
                    game.game_directory),
                "language": game.locale.lang_tag,
                "client_type": game.client_type,
                "high_res_enabled": game.high_res_enabled,
                "patch_client_filename": game.patch_client_filename,
                "startup_scripts": [
                    str(script) for script in game.startup_scripts],
                "wine": wine_settings_dict,
                "info": info_settings_dict,
                "accounts": accounts_settings_list,
            }
            game_dict = self.remove_empty_values_from_dict(
                game_dict, recursive=True)
            settings_dict["games"].append(game_dict)

        rtoml.dump(settings_dict, self.config_path, pretty=True)

    @property
    def current_game(self) -> Game:
        return self._current_game

    @current_game.setter
    def current_game(self, new_value: Game):
        self._current_game = new_value

        onelauncher.set_ui_locale()

    def remove_empty_values_from_dict(
            self,
            input_dict: dict,
            recursive=True) -> dict:
        input_dict = {
            key: input_dict[key] for key in input_dict if input_dict[key] and input_dict[key] not in [
                "None", "."]}

        if recursive:
            new_dict = {
                key: self.remove_empty_values_from_dict(value, recursive=True)
                if isinstance(value, dict)
                else value
                for key, value in input_dict.items()
            }
            input_dict = new_dict

        return input_dict

    def get_new_uuid(self) -> UUID:
        """Return UUID that doesn't already exist in the games config"""
        current_uuids = list(self.games)

        uuid = None
        while uuid in current_uuids or not uuid:
            uuid = uuid4()

        return uuid


logger = logging.getLogger("main")
