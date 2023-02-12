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

GAMES_DIR: Final = platform_dirs.user_data_path / "games"


class InvalidGameUUIDError(ValueError):
    """No game config for the given game UUID exists"""


class MismatchedGameUUIDsError(Exception):
    """Game config file UUID doesn't match folder UUID"""


class GamesConfig():
    def __init__(self, games_dir: Path = GAMES_DIR) -> None:
        self.games_dir = games_dir
        self.games_dir.mkdir(parents=True, exist_ok=True)

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

    def get_game_config_dir(self, game_uuid: UUID) -> Path:
        return self.games_dir / str(game_uuid)

    def get_game_config_path(self, game_uuid: UUID) -> Path:
        return self.get_game_config_dir(game_uuid) / "config.toml"

    def _get_full_game_config(self,
                              game_uuid: UUID) -> Dict[str, Any]:
        """
        Raises: InvalidGameUUIDError: No game config exists for game_uuid
        """
        config_file = self.get_game_config_path(game_uuid)
        if not config_file.exists():
            raise InvalidGameUUIDError(game_uuid)

        config = rtoml.load(config_file)
        if config.get("uuid") != str(game_uuid):
            raise MismatchedGameUUIDsError(
                f"{game_uuid} != {config.get('uuid')}")

        return config

    def get_game_config(self,
                        game_uuid: UUID) -> Dict[str, Any]:
        """
        Raises: InvalidGameUUIDError: No game config exists for game_uuid
        """
        return self._get_game_config_without_sections(
            self._get_full_game_config(game_uuid))

    def get_all_game_configs(self) -> List[Dict[str, Any]]:
        game_configs = []
        for dir in self.games_dir.glob("*"):
            try:
                uuid = UUID(dir.name)
            except ValueError:
                continue

            game_configs.append(self.get_game_config(uuid))

        return game_configs

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
        config_path = self.get_game_config_path(game_uuid)
        config_path.parent.mkdir(exist_ok=True)
        config_path.touch(exist_ok=True)
        rtoml.dump(
            game_config,
            config_path,
            pretty=True)

    def save_game_config(self, game_uuid: UUID,
                         new_game_config: dict[str, Any]) -> None:
        """
        Save game config. This will not save any changes to game config
        sections. See `self.save_game_config_section` for that
        """
        new_game_config = self._get_game_config_without_sections(
            new_game_config)
        try:
            existing_config = self._get_full_game_config(game_uuid)
        except InvalidGameUUIDError:
            # Just save new config as it is, since there is no existing config
            self._save_full_game_config(game_uuid, new_game_config)
            return

        # Replace all values in existing config with new ones to
        # be saved. This is done one by one, to not interfere with
        # sections within the existing config.
        for key, val in new_game_config.items():
            existing_config[key] = val

        self._save_full_game_config(game_uuid, existing_config)

    def save_game_config_section(self,
                                 game_uuid: UUID,
                                 config_section_name: str,
                                 config_section: Dict[str,
                                                      Any]) -> None:
        """
        Raises: InvalidGameUUIDError: No game config exists for game_uuid
        """
        game_config = self._get_full_game_config(game_uuid)
        game_config[config_section_name] = config_section

        # Don't save empty config section
        if not config_section:
            del game_config[config_section_name]

        self._save_full_game_config(game_uuid, game_config)


logger = logging.getLogger("main")
games_config = GamesConfig()
