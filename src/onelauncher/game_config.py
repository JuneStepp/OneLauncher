from datetime import datetime
from enum import StrEnum

import attrs
from packaging.version import Version
from typing_extensions import override

from .__about__ import __title__
from .config import Config, config_field
from .resources import OneLauncherLocale
from .utilities import CaseInsensitiveAbsolutePath
from .wine.config import WineConfigSection


class ClientType(StrEnum):
    WIN64 = "WIN64"
    WIN32 = "WIN32"
    WIN32_LEGACY = "WIN32Legacy"
    WIN32Legacy = "WIN32Legacy"


class GameType(StrEnum):
    LOTRO = "LOTRO"
    DDO = "DDO"


@attrs.frozen(kw_only=True)
class GameConfig(Config):
    sorting_priority: int = -1
    game_type: GameType
    is_preview_client: bool
    name: str = attrs.field()  # Default is from `self._get_name_default`
    description: str = ""
    game_directory: CaseInsensitiveAbsolutePath = config_field(
        help="The game's install directory"
    )
    locale: OneLauncherLocale = config_field(help="Language used for game")
    client_type: ClientType = config_field(
        default=ClientType.WIN64, help="Which version of the game client to use"
    )
    high_res_enabled: bool = config_field(
        default=True, help="If the high resolution game files should be used"
    )
    standard_game_launcher_filename: str | None = config_field(
        default=None,
        help=(
            "The name of the standard game launcher executable. "
            "Ex. LotroLauncher.exe"
        ),
    )
    patch_client_filename: str = config_field(
        default="patchclient.dll",
        help="Name of the dll used for game patching. Ex. patchclient.dll",
    )
    newsfeed: str | None = config_field(
        default=None, help="URL of the feed (RSS, ATOM, ect) to show in the launcher"
    )
    last_played: datetime | None = None
    wine: WineConfigSection = config_field(help="WINE is not used on Windows")

    @name.default
    def _get_name_default(self) -> str:
        return f"{self.game_type}" f"{' - Preview' if self.is_preview_client else ''}"

    @override
    @staticmethod
    def get_config_version() -> Version:
        return Version("2.0")

    @override
    @staticmethod
    def get_config_file_description() -> str:
        return f"A game config file for {__title__}"
