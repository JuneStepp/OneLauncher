from datetime import datetime
from enum import StrEnum
from uuid import UUID

import attrs

from .config import platform_dirs
from .game_account import GameAccount
from .game_launcher_local_config import GameLauncherLocalConfig
from .official_clients import (is_gls_url_for_preview_client,
                               is_official_game_server)
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


@attrs.define(eq=False)
class Game():
    uuid: UUID
    sorting_priority: int
    game_type: GameType
    game_directory: CaseInsensitiveAbsolutePath
    locale: OneLauncherLocale
    client_type: ClientType
    high_res_enabled: bool
    patch_client_filename: str
    name: str
    description: str
    accounts: list[GameAccount]
    newsfeed: str | None = None
    last_played: datetime | None = None
    standard_game_launcher_filename: str | None = None
    launcher_local_config: GameLauncherLocalConfig = attrs.field(init=False)

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

    @property
    def is_official_client(self) -> bool:
        return is_official_game_server(self.gls_datacenter_service)

    @property
    def is_official_preview_client(self) -> bool:
        return is_gls_url_for_preview_client(self.gls_datacenter_service)
