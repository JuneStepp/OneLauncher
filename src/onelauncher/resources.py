import logging
import sys
import tomllib
from functools import cached_property
from pathlib import Path
from typing import Self

import attrs
import babel
from PySide6.QtCore import QLocale


@attrs.define
class OneLauncherLocale:
    """
    Args:
        lang_tag (str): An IETF BCP 47 language tag for the locale.
    """

    lang_tag: str
    data_dir: Path
    display_name: str
    game_language_name: str

    def __str__(self) -> str:
        return self.lang_tag

    @classmethod
    def from_data_dir(cls, data_dir: Path) -> Self:
        file = data_dir / "language_info.toml"
        if not file.exists():
            raise FileNotFoundError(
                f"The language_info.toml file is missing for {data_dir.name}"
            )

        settings_dict = tomllib.loads(file.read_text())

        display_name = settings_dict["display_name"]
        game_language_name = settings_dict["game_language_name"]
        return cls(data_dir.name, data_dir, display_name, game_language_name)

    def get_resource(self, relative_path: Path) -> Path:
        """Returns the localized resource for path

        Args:
            relative_path (Path): Relative path from data_dir to resource.
                Example: "images/LOTRO_banner.png"

        Returns:
            Path: Full path to resource, localized if a generic version isn't
                available.
        """
        return get_resource(relative_path, self)

    @cached_property
    def flag_icon(self) -> Path:
        return self.get_resource(Path("images/flag_icon.png"))

    @cached_property
    def babel_locale(self) -> babel.Locale:
        return babel.Locale.parse(self.lang_tag, sep="-")


def _get_data_dir() -> Path:
    """Returns location equivalent to OneLauncher folder of source code."""
    if getattr(sys, "frozen", False):
        # Data location for frozen programs
        return Path(sys.executable).parent
    else:
        # This file is located in the data dir
        return Path(__file__).parent


def get_resource(relative_path: Path, locale: OneLauncherLocale) -> Path:
    """Returns the localized resource for path

    Args:
        relative_path (Path): Relative path from data_dir to resource.
            Example: "images/LOTRO_banner.png"
        locale (OneLauncherLocale): the OneLauncherLocale to get the resource
            from if there is no standard version.

    Returns:
        Path: Full path to resource, localized if a generic version isn't
            available.
    """
    generic_path = data_dir / relative_path

    localized_path = locale.data_dir / relative_path
    if localized_path.exists():
        return localized_path
    elif generic_path.exists():
        return generic_path
    else:
        raise FileNotFoundError(
            f"There is no generic or localized version of {relative_path} "
            f"for the language {locale}"
        )


def _get_available_locales(data_dir: Path) -> dict[str, OneLauncherLocale]:
    locales: dict[str, OneLauncherLocale] = {}

    for path in (data_dir / "locale").glob("*/"):
        if path.is_dir():
            lang_tag: str = path.name
            locales[lang_tag] = OneLauncherLocale.from_data_dir(path)

    return locales


def _get_system_locale(
    available_locales: dict[str, OneLauncherLocale],
) -> OneLauncherLocale | None:
    """
    Return locale from available_locales that matches the system.
    None will be returned if none match.
    """

    system_lang_tag = QLocale.system().bcp47Name()

    # Return locale for exact match if present.
    if system_lang_tag in available_locales:
        return available_locales[system_lang_tag]

    # Get locales that match the base language.
    if matching_langs := [
        locale
        for locale in available_locales.values()
        if locale.lang_tag.split("-")[0] == system_lang_tag.split("-")[0]
    ]:
        return matching_langs[0]
    else:
        return None


def get_game_dir_available_locales(game_dir: Path) -> list[OneLauncherLocale]:
    available_game_locales: list[OneLauncherLocale] = []

    available_locales_game_names = {
        locale.game_language_name: locale for locale in available_locales.values()
    }
    language_data_files = game_dir.glob("client_local_*.dat")
    for file in language_data_files:
        # remove "client_local_" (13 chars) and ".dat" (4 chars) from filename
        game_language_name = str(file.name)[13:-4]

        try:
            available_game_locales.append(
                available_locales_game_names[game_language_name]
            )
        except KeyError:
            logger.error(
                f"{game_language_name} does not match a game language name for"
                f" an available locale."
            )

    return available_game_locales


logger = logging.getLogger("main")

data_dir = _get_data_dir()
available_locales = _get_available_locales(data_dir)
system_locale = _get_system_locale(available_locales)
