import sys
from pathlib import Path
from typing import Dict, List, Optional
import rtoml
from PySide6.QtCore import QLocale
import OneLauncher
from OneLauncher import __title__


class Locale():
    def __init__(self, lang_tag: str) -> None:
        """

        Args:
            lang_tag (str): An IETF BCP 47 language tag for the locale.
        """
        self.lang_tag = lang_tag
        self.data_dir = self._get_localized_data_dir()
        self._load_language_info()
        self.flag_icon = self._get_flag_icon()

    def __str__(self) -> str:
        """What gets shown when the print function is used on the Locale object"""
        return self.lang_tag

    def _get_localized_data_dir(self):
        localized_data_dir = data_dir/"locale"/self.lang_tag
        if localized_data_dir.exists():
            return localized_data_dir
        else:
            raise FileNotFoundError(
                f"The locale folder is missing for the lang tag: {self.lang_tag}")

    def _load_language_info(self):
        file = self.data_dir/"language_info.toml"
        if not file.exists():
            raise FileNotFoundError(
                f"The language_info.toml file is missing for the lang tag: self.lang_tag")

        settings_dict = rtoml.load(file)

        self.display_name = settings_dict["display_name"]
        self.game_language_name = settings_dict["game_language_name"]

    def get_resource(self, relative_path: Path):
        """Returns the localized resource for path

        Args:
            relative_path (Path): Relative path from data_dir to resource. Example: "images/LOTRO_banner.png"

        Returns:
            Path: Full path to resource, localized if a generic version isn't available.
        """
        return get_resource(relative_path, self)

    def _get_flag_icon(self):
        return self.get_resource(Path("images/flag_icon.png"))


def _get_data_dir() -> Path:
    """Returns location equivalent to OneLauncher folder of source code."""
    if getattr(sys, "frozen", False):
        # Data location for frozen programs
        return Path(sys.executable).parent
    else:
        # This file is located in the data dir
        return Path(__file__).parent


def get_resource(relative_path: Path, locale: Locale) -> Path:
    """Returns the localized resource for path

    Args:
        relative_path (Path): Relative path from data_dir to resource. Example: "images/LOTRO_banner.png"
        locale (Locale): the Locale to get the resource from if there is no standard version.

    Returns:
        Path: Full path to resource, localized if a generic version isn't available.
    """
    generic_path = data_dir/relative_path

    localized_path = locale.data_dir/relative_path
    if localized_path.exists():
        return localized_path
    elif generic_path.exists():
        return generic_path
    else:
        raise FileNotFoundError(
            f"There is no generic or localized version of {relative_path} for the language {locale}")


def _get_available_locales(data_dir: Path) -> Dict[str, Locale]:
    locales = {}

    for path in (data_dir/"locale").glob("*/"):
        if path.is_dir():
            lang_tag = path.name
            locales[lang_tag] = Locale(lang_tag)

    return locales


def _get_system_locale(available_locales: dict[str, Locale]) -> Optional[Locale]:
    """Returns locale from available_locales that
    matches the system. None will be returned if none match."""

    system_lang_tag = QLocale.system().bcp47Name()

    # Return locale for exact match if present.
    if system_lang_tag in available_locales:
        return available_locales[system_lang_tag]

    # Get locales that match the base language.
    matching_langs = [locale for locale in available_locales.values(
    ) if locale.lang_tag.split("-")[0] == system_lang_tag.split("-")[0]]

    if matching_langs:
        return matching_langs[0]
    else:
        return None


def get_game_dir_available_locales(game_dir: Path) -> List[Locale]:
    available_game_locales = []

    available_locales_game_names = {
        locale.game_language_name: locale for locale in available_locales.values()}
    language_data_files = game_dir.glob("client_local_*.dat")
    for file in language_data_files:
        # remove "client_local_" (13 chars) and ".dat" (4 chars) from filename
        game_language_name = str(file.name)[13:-4]

        try:
            available_game_locales.append(
                available_locales_game_names[game_language_name])
        except KeyError:
            OneLauncher.logger.error(
                f"{game_language_name} does not match a game language name for"
                f" an available locale in {__title__}")

    return available_game_locales


data_dir = _get_data_dir()
available_locales = _get_available_locales(data_dir)
system_locale = _get_system_locale(available_locales)
