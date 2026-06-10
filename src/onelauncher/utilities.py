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
# (C) 2019-2026 June Stepp <contact@JuneStepp.me>
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
import sys
from collections.abc import Generator, Iterator
from math import log, trunc
from pathlib import Path, PurePath
from typing import (
    Literal,
    Self,
    assert_never,
    override,
)
from xml.etree.ElementTree import Element

import attrs
from defusedxml import ElementTree  # type: ignore[import-untyped]

logger = logging.getLogger(__name__)


@attrs.frozen(kw_only=True)
class RelativePathError(ValueError):
    msg: str = "Path is not absolute"


type StrPath = str | os.PathLike[str]


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

    Raises:
        RelativePathError: Path is not absolute
    """

    def __init__(
        self, *args: StrPath, known_to_exist_base_path: Path | None = None
    ) -> None:
        normal_path = Path(*args)
        if not normal_path.is_absolute():
            raise RelativePathError()

        path = self._get_real_path_from_fully_case_insensitive_path(
            normal_path, known_to_exist_base_path=known_to_exist_base_path
        )
        self._raw_paths = path._raw_paths  # type: ignore[attr-defined]

    @classmethod
    def _get_real_path_from_fully_case_insensitive_path(
        cls: type[Self], start_path: Path, known_to_exist_base_path: Path | None = None
    ) -> Path:
        """Return any found path that matches base_path when ignoring case"""
        parts = list(start_path.parts)
        if known_to_exist_base_path is None:
            if not os.path.exists(parts[0]):
                # If root doesn't exist, nothing else can be checked.
                return start_path

            # Range starts at 1 to ignore root which has just been checked.
            start_index = 1
        else:
            start_index = len(known_to_exist_base_path.parts)

        for i in range(start_index, len(parts)):
            current_path_parts = parts if i == len(parts) - 1 else parts[: i + 1]
            real_path_name = cls._get_real_path_name_from_case_insensitive_path_name(
                case_insensitive_name=current_path_parts[-1],
                parent_dir=os.path.sep.join(current_path_parts[:-1]),
            )
            # No version exists, so the original is just returned.
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

    @override
    def with_segments(self, *pathsegments: StrPath) -> Self:
        # This is assuming that this function gets called with no other absolute paths
        # when `self` is the first path segment
        if pathsegments[0] is self and self.exists():
            return type(self)(*pathsegments, known_to_exist_base_path=self)
        else:
            return type(self)(*pathsegments)

    @override
    @classmethod
    def home(cls: type[Self]) -> Self:
        return cls(os.path.expanduser("~"))

    if sys.version_info >= (3, 13):

        @override
        def glob(
            self,
            pattern: str,
            *,
            case_sensitive: bool | None = None,
            recurse_symlinks: bool = False,
        ) -> Iterator[Self]:
            for path in Path(self).glob(
                pattern,
                # `CaseInsensitiveAbsolutePath` should always be case insensitive.
                case_sensitive=False,
                recurse_symlinks=recurse_symlinks,
            ):
                yield type(self)(path, known_to_exist_base_path=path)

        @override
        def rglob(
            self,
            pattern: str,
            *,
            case_sensitive: bool | None = None,
            recurse_symlinks: bool = False,
        ) -> Iterator[Self]:
            for path in Path(self).rglob(
                pattern,
                # `CaseInsensitiveAbsolutePath` should always be case insensitive.
                case_sensitive=False,
                recurse_symlinks=recurse_symlinks,
            ):
                yield type(self)(path, known_to_exist_base_path=path)

        @override
        def full_match(
            self, pattern: StrPath, *, case_sensitive: bool | None = None
        ) -> bool:
            return PurePath(self).full_match(
                pattern,
                # `CaseInsensitiveAbsolutePath` should always be case insensitive.
                case_sensitive=False,
            )

    else:

        @override
        def glob(
            self, pattern: str, *, case_sensitive: bool | None = None
        ) -> Generator[Self]:
            for path in Path(self).glob(
                pattern,
                # `CaseInsensitiveAbsolutePath` should always be case insensitive.
                case_sensitive=False,
            ):
                yield type(self)(path, known_to_exist_base_path=path)

        @override
        def rglob(
            self, pattern: str, *, case_sensitive: bool | None = None
        ) -> Generator[Self]:
            for path in Path(self).rglob(
                pattern,
                # `CaseInsensitiveAbsolutePath` should always be case insensitive.
                case_sensitive=False,
            ):
                yield type(self)(path, known_to_exist_base_path=path)

    @override
    def match(self, path_pattern: str, *, case_sensitive: bool | None = None) -> bool:
        return PurePath(self).match(
            path_pattern,
            # `CaseInsensitiveAbsolutePath` should always be case insensitive.
            case_sensitive=False,
        )

    @override
    def relative_to(self, *other: StrPath) -> Path:  # type: ignore[override]
        return Path(self).relative_to(*other)


@attrs.define(eq=False)
class ProgressItem:
    completed: int = 0
    total: int = 0


@attrs.frozen
class CurrentProgress:
    completed: int
    total: int
    progress_text: str


@attrs.define
class Progress:
    progress_items: list[ProgressItem] = attrs.Factory(list)
    unit_type: Literal["byte"] | None = None
    progress_text_suffix: str = ""

    def reset(self) -> None:
        self.progress_items = []
        self.unit_type = None
        self.progress_text_suffix = ""

    def _pick_unit_and_suffix(
        self, size: int, suffixes: tuple[str, ...], base: int
    ) -> tuple[int, str]:
        if not suffixes:
            return 1, ""

        ideal_exponent = trunc(log(size, base))
        exponent = min(ideal_exponent, len(suffixes) - 1)
        return base**exponent, suffixes[exponent]

    def get_current_progress(self) -> CurrentProgress:
        sum_completed = 0
        sum_total = 0
        for progress_item in self.progress_items:
            sum_completed += progress_item.completed
            sum_total += progress_item.total

        # Don't want >100%.
        sum_completed = min(sum_completed, sum_total)

        if sum_total == 0:
            return CurrentProgress(
                completed=0, total=0, progress_text=self.progress_text_suffix
            )

        if self.unit_type is None:
            unit, suffix = 1, ""
        elif self.unit_type == "byte":
            unit, suffix = self._pick_unit_and_suffix(
                size=sum_total,
                suffixes=("bytes", "kB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"),
                base=1000,
            )
        else:
            assert_never()
        precision = 0 if unit == 1 else 1
        completed_str = f"{sum_completed / unit:,.{precision}f}"
        total_str = f"{sum_total / unit:,.{precision}f}"
        progress_text = f"{sum_completed / sum_total:.0%} ({completed_str}/{total_str} {suffix}){self.progress_text_suffix}"

        return CurrentProgress(
            # Using 0 to 10,000 instead of 0 to `current_progress.total` to prevent
            # overflow errors.
            completed=round(sum_completed / sum_total * 10000),
            total=10000,
            progress_text=progress_text,
        )


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


def nuitka_ignore[T](func: T) -> T:
    """
    Don't compile decorated function with Nuitka. It will stay bytecode.

    This decorator returns the input function unchanged. Nuitka
    just checks for any decorator called "nuitka_ignore".
    """
    return func
