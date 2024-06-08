###########################################################################
# Support classes for OneLauncher.
#
# Based on PyLotRO
# (C) 2009 AJackson <ajackson@bcs.org.uk>
#
# Based on LotROLinux
# (C) 2007-2008 AJackson <ajackson@bcs.org.uk>
#
#
# (C) 2019-2024 June Stepp <contact@JuneStepp.me>
#
# This file is part of OneLauncher
#
# OneLauncher is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# OneLauncher is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with OneLauncher.  If not, see <http://www.gnu.org/licenses/>.
###########################################################################
from __future__ import annotations

import logging
import os
import pathlib
from collections.abc import Generator
from pathlib import Path
from typing import TYPE_CHECKING, Self
from xml.etree.ElementTree import Element

from defusedxml import ElementTree

if TYPE_CHECKING:
    from _typeshed import StrPath


class CaseInsensitiveAbsolutePath(Path):
    """
    `pathlib.Path` subclass that automatically converts from the provided
    case-insensitive path a path that exists, if any. This is used for compatibility
    with Windows programs. Windows filesystems are case-insensitive by default, so
    paths of many different capitalization patterns may be encountered. Multiple paths
    that differ only in case should be avoided if they will interact with the Windows
    programs.

    LOTRO and DDO treat both patchclient.dll and PatchClient.dll the same, and both have
    been encountered in real game folders before. There are similar concerns regarding
    addon folders or anything else used by the games or in the WINE prefixes.
    """

    _flavour = (
        pathlib._windows_flavour  # type: ignore
        if os.name == "nt"
        else pathlib._posix_flavour  # type: ignore
    )

    def __new__(cls, *pathsegments: StrPath) -> Self:
        normal_path = Path(*pathsegments)
        if not normal_path.is_absolute():
            raise ValueError("Path is not absolute")
        # Windows filesystems are already case-insensitive
        if os.name == "nt":
            return super().__new__(cls, *pathsegments)
        path = cls._get_real_path_from_fully_case_insensitive_path(normal_path)
        return super().__new__(cls, path)

    @classmethod
    def _get_real_path_from_fully_case_insensitive_path(
        cls: type[Self], start_path: Path, known_to_exist_base_path: Path | None = None
    ) -> Path:
        """Return any found path that matches base_path when ignoring case"""
        parts = list(start_path.parts)
        if known_to_exist_base_path is None and not os.path.exists(parts[0]):
            # If root doesn't exist, nothing else can be checked
            return start_path

        if known_to_exist_base_path is not None:
            start_index = len(known_to_exist_base_path.parts)
        else:
            # Range starts at 1 to ingore root which has already been checked
            start_index = 1

        for i in range(start_index, len(parts)):
            current_path_parts = parts if i == len(parts) - 1 else parts[: i + 1]
            real_path_name = cls._get_real_path_name_from_case_insensitive_path_name(
                case_insensitive_name=current_path_parts[-1],
                parent_dir=os.path.sep.join(current_path_parts[:-1]),
            )
            # No version exists, so the original is just returned
            if real_path_name is None:
                return start_path

            parts[i] = real_path_name

        return Path(*parts)

    @staticmethod
    def _get_real_path_name_from_case_insensitive_path_name(
        case_insensitive_name: str, parent_dir: str
    ) -> str | None:
        """
        Return any found path where the path name == `case_insensitive_name` ignoring
        case. `parent_dir` has to exist. Use _get_case_sensitive_full_path if this may
        not be the case.
        """
        try:
            matches = tuple(
                path_name
                for path_name in os.listdir(parent_dir)
                if path_name.lower() == case_insensitive_name.lower()
            )
        except OSError:
            return None
        if len(matches) == 1:
            return matches[0]
        elif len(matches) > 1:
            try:
                exact_match_index = matches.index(case_insensitive_name)
                logger.warning(
                    "Multiple matches found for case-insensitive path name. One exact "
                    "match found. Using exact match.",
                )
                return matches[exact_match_index]
            except ValueError:
                logger.warning(
                    "Multiple matches found for case-insensitive path name with no exact "
                    "match. Using first one found."
                )
                return matches[0]
        else:
            # No matches
            return None

    def _make_child(self, args: tuple[StrPath, ...]) -> Self:
        joined_path = super()._make_child(args)  # type: ignore
        return super().__new__(
            type(self),
            self._get_real_path_from_fully_case_insensitive_path(
                start_path=joined_path,
                known_to_exist_base_path=self if self.exists() else None,
            ),
        )

    @classmethod
    def home(cls: type[Self]) -> Self:
        return cls(os.path.expanduser("~"))

    def _get_case_insensitive_glob_pattern(self, pattern: str) -> str:
        return "".join(
            [f"[{c.lower()}{c.upper()}]" if c.isalpha() else c for c in pattern]
        )

    def glob(self, pattern: str) -> Generator[Self, None, None]:
        return super().glob(self._get_case_insensitive_glob_pattern(pattern))

    def rglob(self, pattern: str) -> Generator[Self, None, None]:
        return super().rglob(self._get_case_insensitive_glob_pattern(pattern))

    def relative_to(self, *other: StrPath) -> Path: # type: ignore[override]
        return Path(self).relative_to(*other)


class AppSettingsParseError(KeyError):
    """Config doesn't follow the appSettings format"""


def verify_app_settings_config(config_text: str) -> None:
    """Verify that config_text is following the appSettings format.
       Exceptions will be raised, if there is an issue.

    Args:
        config_text (str): Text from appSettings style xml config file.
        See https://docs.microsoft.com/en-us/dotnet/framework/configure-apps/file-schema/appsettings/

    Raises:
        AppSettingsParseError: config_text doesn't follow the appSettings format.
    """
    try:
        root: Element = ElementTree.fromstring(config_text)
    except ElementTree.ParseError as e:
        raise AppSettingsParseError("Config is not valid XML") from e

    # Verify basic document structure
    if root.tag != "configuration":
        raise AppSettingsParseError("Root element is not 'configuration'")
    app_settings = root.find("./appSettings")
    if app_settings is None:
        raise AppSettingsParseError("No appSettings element found")

    # Verify 'add' elements
    for element in app_settings.iterfind("./add"):
        keys = element.keys()
        if "key" not in keys or "value" not in keys:
            raise AppSettingsParseError("'add' element doesn't have all required keys")


def parse_app_settings_config(config_text: str) -> dict[str, str]:
    """Parse the key, value pairs from config_text into a dictionary.

    Args:
        config_text (str): Text from appSettings style xml config file.
        See https://docs.microsoft.com/en-us/dotnet/framework/configure-apps/file-schema/appsettings/

    Raises:
        AppSettingsParseError: config_text doesn't follow the appSettings format.
    """
    verify_app_settings_config(config_text)
    root: Element = ElementTree.fromstring(config_text)
    config_dict = {}
    for element in root.iterfind(".appSettings/add"):
        attribs_dict = element.attrib
        config_dict[attribs_dict["key"]] = attribs_dict["value"]
    return config_dict


logger = logging.getLogger("main")
