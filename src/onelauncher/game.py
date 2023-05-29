from datetime import datetime
from enum import StrEnum
from typing import Dict, Optional
from uuid import UUID

from.config import platform_dirs
from.game_launcher_local_config import GameLauncherLocalConfig
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
        self.launcher_local_config: GameLauncherLocalConfig

    @property
    def gls_datacenter_service(self) -> str:
        return self.launcher_local_config.gls_datacenter_service

    @property
    def datacenter_game_name(self) -> str:
        return self.launcher_local_config.datacenter_game_name

    @property
    def documents_config_dir(self) -> CaseInsensitiveAbsolutePath:
        """
        The folder in the user documents dir that the game stores information in.
        This includes addons, screenshots, user config files, ect
        """
        return CaseInsensitiveAbsolutePath(
            platform_dirs.user_documents_path /
            self.launcher_local_config.documents_config_dir_name)
