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
import logging
from pathlib import Path
from typing import Any, Dict, Final, List
from uuid import UUID

import rtoml

from onelauncher.config import platform_dirs

CONFIG_PATH: Final = platform_dirs.user_config_path / \
    "games.toml"


class GamesConfig():
    def __init__(self, config_path: Path = CONFIG_PATH) -> None:
        self.config_path = config_path

    def _get_root_config(self) -> Dict[str, Any]:
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        root_config = rtoml.load(
            self.config_path) if self.config_path.exists() else {}

        # Ensure that there is a list for games
        if "games" not in root_config:
            root_config["games"] = []

        return root_config

    def _get_game_config_without_sections(
            self, game_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get game config without sections.
        Those should be managed/saved separately from the core game config.
        """
        return {
            key: val for key,
            val in game_config.items() if not isinstance(
                val,
                dict)}

    def _get_all_full_game_configs(self) -> List[Dict[str, Any]]:
        root_config = self._get_root_config()
        return root_config["games"]

    def get_all_game_configs(self) -> List[Dict[str, Any]]:
        return [self._get_game_config_without_sections(
            game_config) for game_config in self._get_all_full_game_configs()]

    def _get_game_config_from_list(
            self,
            game_uuid: UUID,
            game_configs: List[Dict[str, Any]]) -> Dict[str, Any]:
        for game_config in game_configs:
            if game_config.get("uuid") == str(game_uuid):
                return game_config

        raise ValueError(f"Game UUID: {game_uuid} not found in config")

    def _get_full_game_config(self,
                              game_uuid: UUID) -> Dict[str, Any]:
        game_configs = self._get_all_full_game_configs()
        return self._get_game_config_from_list(game_uuid, game_configs)

    def get_game_config(self,
                        game_uuid: UUID) -> Dict[str, Any]:
        game_configs = self.get_all_game_configs()
        return self._get_game_config_from_list(game_uuid, game_configs)

    def get_game_config_section(self,
                                game_uuid: UUID,
                                config_section_name: str) -> Dict[str, Any]:
        """
        Get config section for a game.
        Will return an empty dictionary if the section doesn't exist
        """
        game_config = self._get_full_game_config(game_uuid)
        return game_config.get(config_section_name, {})

    def _save_full_game_config(self, game_uuid: UUID,
                               game_config: dict[str, Any]) -> None:
        """Save a full game config including all sub-sections."""
        root_config = self._get_root_config()

        # Remove any existing config for this game
        for full_game_config in root_config["games"]:
            if full_game_config.get("uuid") == str(game_uuid):
                root_config["games"].remove(full_game_config)

        root_config["games"].append(game_config)
        rtoml.dump(root_config, self.config_path, pretty=True)

    def save_game_config(self, game_uuid: UUID,
                         game_config: dict[str, Any]) -> None:
        """
        Save game config. This will not save any changes to game config
        sections. See `self.save_game_config_section` for that
        """
        game_config = self._get_game_config_without_sections(game_config)
        root_config = self._get_root_config()

        for full_game_config in root_config["games"]:
            if full_game_config.get("uuid") == str(game_uuid):
                # Replace all values in full_game_config with new ones to
                # be saved. This is done one by one, to not interfere with
                # sections within the full_game_config.
                for key, val in game_config.items():
                    full_game_config[key] = val

                game_config = full_game_config

        self._save_full_game_config(game_uuid, game_config)

    def save_game_config_section(self,
                                 game_uuid: UUID,
                                 config_section_name: str,
                                 config_section: Dict[str,
                                                      Any]) -> None:
        game_config = self._get_full_game_config(game_uuid)
        game_config[config_section_name] = config_section

        # Don't save empty config section
        if not config_section:
            del game_config[config_section_name]

        self._save_full_game_config(game_uuid, game_config)


logger = logging.getLogger("main")
games_config = GamesConfig()
