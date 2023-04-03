# coding=utf-8
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
# (C) 2019-2021 June Stepp <contact@JuneStepp.me>
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
import logging
import os
import pathlib
from pathlib import Path
from typing import Generator, Optional, Self
from xml.etree.ElementTree import Element

from defusedxml import ElementTree


class CaseInsensitiveAbsolutePath(Path):
    _flavour = pathlib._windows_flavour if os.name == 'nt' else pathlib._posix_flavour  # type: ignore

    def __new__(cls, *pathsegments, **kwargs):
        normal_path = Path(*pathsegments, **kwargs)
        if not normal_path.is_absolute():
            raise ValueError("Path is not absolute.")
        path = cls._get_real_path_from_fully_case_insensitive_path(normal_path)
        return super().__new__(cls, path, **kwargs)

    @classmethod
    def _get_real_path_from_fully_case_insensitive_path(
            cls, base_path: Path) -> Path:
        """Return any found path that matches base_path when ignoring case"""
        # Base version already exists
        if base_path.exists():
            return base_path

        parts = list(base_path.parts)
        if not Path(parts[0]).exists():
            # If root doesn't exist, nothing else can be checked
            return base_path

        # Range starts at 1 to ingore root which has already been checked
        for i in range(1, len(parts)):
            current_path = Path(
                *(parts if i == len(parts) - 1 else parts[:i + 1]))
            real_path = cls._get_real_path_from_name_case_insensitive_path(
                current_path)
            # Second check is for if there is a file or broken symlink before
            # the end of the path. Without the check it would raise and
            # exception in cls._get_real_path_from_name_case_insensitive_path
            if real_path is None or (
                    i < len(parts) - 1 and not real_path.is_dir()):
                # No version exists, so the original is just returned
                return base_path

            parts[i] = real_path.name

        return Path(*parts)

    @staticmethod
    def _get_real_path_from_name_case_insensitive_path(
            base_path: Path) -> Optional[Path]:
        """
        Return any found path where path.name == base_path.name ignoring case.
        base_path.parent has to exist. Use _get_case_sensitive_full_path if
        this is not the case.
        """
        if not base_path.parent.exists():
            raise FileNotFoundError(
                f"`{base_path.parent}` parent path does not exist")

        if base_path.exists():
            return base_path

        return next((path for path in base_path.parent.iterdir()
                    if path.name.lower() == base_path.name.lower()), None)

    def _make_child(self, args) -> Path:
        _, _, parts = super()._parse_args(args)  # type: ignore
        joined_path = super()._make_child((Path(*parts),))  # type: ignore
        return self._get_real_path_from_fully_case_insensitive_path(
            joined_path)

    def _get_case_insensitive_glob_pattern(self, pattern: str) -> str:
        return ''.join([
            f"[{c.lower()}{c.upper()}]"
            if c.isalpha() else c
            for c in pattern
        ])

    def glob(self, pattern: str) -> Generator[Self, None, None]:
        return super().glob(self._get_case_insensitive_glob_pattern(pattern))

    def rglob(self, pattern: str) -> Generator[Self, None, None]:
        return super().rglob(self._get_case_insensitive_glob_pattern(pattern))


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
    root: Element = ElementTree.fromstring(config_text)
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
            raise AppSettingsParseError(
                "'add' element doesn't have all required keys")


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


def string_encode(s):
    return s.encode()


def string_decode(s):
    return s.decode()


def QByteArray2str(s):
    return str(s, encoding="utf8", errors="replace")


def GetText(nodelist):
    return "".join(
        node.data
        for node in nodelist
        if node.nodeType in [node.TEXT_NODE, node.CDATA_SECTION_NODE]
    )


logger = logging.getLogger("main")
