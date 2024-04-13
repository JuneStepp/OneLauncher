import attrs
from packaging.version import Version
from typing_extensions import override

from .__about__ import __title__
from .config import Config, config_field
from .game_utilities import GamesSortingMode
from .resources import OneLauncherLocale, available_locales, system_locale


@attrs.frozen
class ProgramConfig(Config):
    default_locale: OneLauncherLocale = config_field(
        default=system_locale or available_locales["en-US"],
        help="The default language for games and UI.")
    always_use_default_locale_for_ui: bool = config_field(
        default=False,
        help="Use default language for UI regardless of game language")
    save_accounts: bool = config_field(
        default=False,
        help="Save game accounts")
    save_accounts_passwords: bool = config_field(
        default=False,
        help="Save game account passwords with Keyring")
    games_sorting_mode: GamesSortingMode = config_field(
        default=GamesSortingMode.PRIORITY,
        help="Order to show games in UI")

    @override
    @staticmethod
    def get_config_version() -> Version:
        return Version("2.0")

    @override
    @staticmethod
    def get_config_file_description() -> str:
        return (f"The primary config file for {__title__}. "
                f"Game specific configs are in separate files.")
