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
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

import rtoml

import onelauncher
from onelauncher.config import platform_dirs
from onelauncher.config.program_config import program_config
from onelauncher.game import ClientType, Game
from onelauncher.game_account import GameAccount
from onelauncher.resources import available_locales
from onelauncher.utilities import CaseInsensitiveAbsolutePath


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
            self.current_game = self.games[UUID(
                settings_dict["last_used_game_uuid"])]
        elif self.lotro_games_priority_sorted:
            self.current_game = self.lotro_games_priority_sorted[0]
        elif self.ddo_games_priority_sorted:
            self.current_game = self.ddo_games_priority_sorted[0]
        elif self.lotro_games_last_used_sorted:
            self.current_game = self.lotro_games_last_used_sorted[0]
        elif self.ddo_games_last_used_sorted:
            self.current_game = self.ddo_games_last_used_sorted[0]
        else:
            self.current_game = list(self.games.values())[0]

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
                                                                str(program_config.default_locale))],
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

    def get_new_uuid(self) -> UUID:
        """Return UUID that doesn't already exist in the games config"""
        current_uuids = list(self.games)

        uuid = None
        while uuid in current_uuids or not uuid:
            uuid = uuid4()

        return uuid


logger = logging.getLogger("main")
game_settings = GamesSettings()
