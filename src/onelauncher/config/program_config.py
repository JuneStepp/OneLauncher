
from pathlib import Path
from typing import Optional

import rtoml

from .. import __title__, __version__
from ..game import Game
from ..game_utilities import GamesSortingMode
from ..resources import OneLauncherLocale, available_locales, system_locale
from . import platform_dirs


class ProgramConfig():
    def __init__(self, config_path: Optional[Path] = None) -> None:
        if not config_path:
            config_path = platform_dirs.user_config_path / \
                f"{__title__.lower()}.toml"
        self.config_path = config_path
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        self.load()

    def get_ui_locale(self, game: Optional[Game]) -> OneLauncherLocale:
        if game is None or self.always_use_default_language_for_ui:
            return self.default_locale

        return game.locale

    def load(self):
        # Defaults will be used if the settings file doesn't exist
        if self.config_path.exists():
            settings_dict = rtoml.load(self.config_path)
        else:
            settings_dict = {}

        if "default_language" in settings_dict:
            self.default_locale = available_locales[settings_dict["default_language"]]
        elif system_locale:
            self.default_locale = system_locale
        else:
            self.default_locale = available_locales["en-US"]

        self.always_use_default_language_for_ui: bool = settings_dict.get(
            "always_use_default_language_for_ui", False)
        self.save_accounts = settings_dict.get("save_accounts", False)
        self.save_accounts_passwords = settings_dict.get(
            "save_accounts_passwords", False)
        self.games_sorting_mode = GamesSortingMode(settings_dict.get(
            "games_sorting_mode", "priority"))

    def save(self):
        settings_dict = {
            "onelauncher_version": __version__,
            "default_language": self.default_locale.lang_tag,
            "always_use_default_language_for_ui": self.always_use_default_language_for_ui,
            "save_accounts": self.save_accounts,
            "save_accounts_passwords": self.save_accounts_passwords,
            "games_sorting_mode": self.games_sorting_mode.value,
        }

        rtoml.dump(settings_dict, self.config_path, pretty=True)


program_config = ProgramConfig()
