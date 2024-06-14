from enum import Enum

import attrs
from packaging.version import Version
from typing_extensions import override

from .__about__ import __title__
from .config import Config, config_field
from .resources import (
    OneLauncherLocale,
    get_default_locale,
)


class GamesSortingMode(Enum):
    """
    - priority: The manual order the user set in the setup wizard.
    - alphabetical: Alphabetical order.
    - last_used: Order of the most recently played games.
    """

    PRIORITY = "priority"
    LAST_USED = "last_used"
    ALPHABETICAL = "alphabetical"


@attrs.frozen
class ProgramConfig(Config): # type: ignore[explicit-override]
    default_locale: OneLauncherLocale = config_field(
        default=get_default_locale(),
        help="The default language for games and UI.",
    )
    always_use_default_locale_for_ui: bool = config_field(
        default=False, help="Use default language for UI regardless of game language"
    )
    games_sorting_mode: GamesSortingMode = config_field(
        default=GamesSortingMode.PRIORITY, help="Order to show games in UI"
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
