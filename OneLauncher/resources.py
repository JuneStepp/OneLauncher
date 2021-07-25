from pathlib import Path
import sys
from PySide6 import QtGui


class Locale():
    def __init__(self, lang_tag: str) -> None:
        """

        Args:
            lang_tag (str): An IETF BCP 47 language tag for the locale.
        """
        self.lang_tag = self._verify_lang_tag(lang_tag)
        self.data_dir = self._get_localized_data_dir(self.lang_tag)

    def __str__(self) -> str:
        """What gets shown when the print function is used on the Locale object"""
        return self.lang_tag

    def _get_localized_data_dir(self, lang_tag: str):
        return data_dir/"locale"/lang_tag

    def _verify_lang_tag(self, lang_tag: str):
        if self._get_localized_data_dir(lang_tag).exists():
            return lang_tag
        else:
            raise FileNotFoundError(
                f"There is no locale folder for the lang tag: {lang_tag}")


def get_data_dir() -> Path:
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

def get_icon_font() -> QtGui.QFont:
    # Setup font for icons
    font_file = data_dir/"fonts/Font Awesome 5 Free-Solid-900.otf"
    font_db = QtGui.QFontDatabase()
    font_id = font_db.addApplicationFont(str(font_file))
    font_family = font_db.applicationFontFamilies(font_id)
    icon_font = QtGui.QFont(font_family)
    icon_font.setHintingPreference(QtGui.QFont.PreferNoHinting)
    icon_font.setPixelSize(16)

    return icon_font

data_dir = get_data_dir()
icon_font = get_icon_font()
