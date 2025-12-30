from enum import Enum
from typing import Literal, TypeAlias

import attrs
from packaging.version import Version
from typing_extensions import override

from .__about__ import __title__
from .config import Config, config_field
from .logs import LogLevel
from .resources import (
    OneLauncherLocale,
    get_default_locale,
)


class GamesSortingMode(Enum):
    """
    - priority: The manual order the user set in the setup wizard.
    - alphabetical: Alphabetical order.
    - last_played: Order of the most recently played games.
    """

    PRIORITY = "priority"
    LAST_PLAYED = "last_played"
    ALPHABETICAL = "alphabetical"


OnGameStartAction: TypeAlias = Literal["stay", "close"]


@attrs.frozen
class ProgramConfig(Config):
    default_locale: OneLauncherLocale = config_field(
        default=get_default_locale(),
        help="Default language for games and UI",
    )
    always_use_default_locale_for_ui: bool = config_field(
        default=False, help="Use default language for UI regardless of game language"
    )
    games_sorting_mode: GamesSortingMode = config_field(
        default=GamesSortingMode.PRIORITY, help="Order to show games in UI"
    )
    on_game_start: OnGameStartAction = config_field(
        default="stay", help=f"What {__title__} should do when a game is started"
    )
    log_verbosity: LogLevel | None = config_field(
        default=None,
        help="Minimum log severity that will be shown in the console and log file",
    )

    @override
    @staticmethod
    def get_config_version() -> Version:
        return Version("2.0")

    @override
    @staticmethod
    def get_config_file_description() -> str:
        return (
            f"The primary config file for {__title__}. "
            f"Game specific configs are in separate files."
        )
