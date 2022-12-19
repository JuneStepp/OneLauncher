
from pathlib import Path
from typing import Optional

import rtoml

import onelauncher
from onelauncher.config import platform_dirs
from onelauncher.game import Game
from onelauncher.resources import (OneLauncherLocale, available_locales,
                                   system_locale)


class ProgramConfig():
    def __init__(self, config_path: Optional[Path] = None) -> None:
        if not config_path:
            config_path = platform_dirs.user_config_path / \
                f"{onelauncher.__title__}.toml"
        self.config_path = config_path
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        self.load()

    @property
    def games_sorting_mode(self) -> str:
        return self._games_sorting_mode

    @games_sorting_mode.setter
    def games_sorting_mode(self, new_value: str) -> None:
        """
        Games sorting mode.

        priority: The manual order the user set in the setup wizard.
        alphabetical: Alphabetical order.
        last_used: Order of the most recently played games.
        """
        accepted_values = ["priority", "alphabetical", "last_used"]
        if new_value not in accepted_values:
            raise ValueError(f"{new_value} is not a valid games sorting mode.")

        self._games_sorting_mode = new_value

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
        self.games_sorting_mode = settings_dict.get(
            "games_sorting_mode", "priority")

    def save(self):
        settings_dict = {
            "onelauncher_version": onelauncher.__version__,
            "default_language": self.default_locale.lang_tag,
            "always_use_default_language_for_ui": self.always_use_default_language_for_ui,
            "save_accounts": self.save_accounts,
            "save_accounts_passwords": self.save_accounts_passwords,
            "games_sorting_mode": self.games_sorting_mode,
        }

        rtoml.dump(settings_dict, self.config_path, pretty=True)


program_config = ProgramConfig()
