#!/usr/bin/env python3
###########################################################################
# Patching progress analyzer for OneLauncher.
#
# Based on PyLotRO
# (C) 2009 AJackson <ajackson@bcs.org.uk>
#
# Based on LotROLinux
# (C) 2007-2008 AJackson <ajackson@bcs.org.uk>
#
#
# (C) 2019-2025 June Stepp <contact@JuneStepp.me>
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

from typing import Literal

import attrs


@attrs.frozen
class PatchingProgress:
    total_iterations: int
    current_iterations: int


class PatchingProgressMonitor:
    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.patching_type = None

    @property
    def patching_type(self) -> Literal["file", "data"] | None:
        return self._patching_type

    @patching_type.setter
    def patching_type(self, patching_type: Literal["file", "data"] | None) -> None:
        self._patching_type = patching_type
        self.total_iterations: int = 0
        self.current_iterations: int = 0
        self.applying_forward_iterations: bool = False

    def get_patching_progress(self) -> PatchingProgress:
        return PatchingProgress(
            total_iterations=self.total_iterations,
            current_iterations=self.current_iterations,
        )

    def feed_line(self, line: str) -> PatchingProgress:
        cleaned_line = line.strip().lower()

        # Beginning of a patching type
        if cleaned_line.startswith("checking files"):
            self.patching_type = "file"
            return self.get_patching_progress()
        elif cleaned_line.startswith("checking data"):
            self.patching_type = "data"
            return self.get_patching_progress()
        # Right after a patching type begins. Find out how many iterations there will be.
        if cleaned_line.startswith("files to patch:"):
            self.total_iterations = int(
                cleaned_line.split("files to patch:")[1].strip().split()[0]
            )
        elif cleaned_line.startswith("data patches:"):
            self.total_iterations = int(
                cleaned_line.split("data patches:")[1].strip().split()[0]
            )
        # Data patching has two parts.
        # "Applying x forward iterations....(continues for x dots)" and the actual file
        # downloading which is the originally set `self.total_iterations`
        elif (
            self.patching_type == "data"
            and cleaned_line.startswith("applying")
            and "forward iterations" in cleaned_line
        ):
            self.applying_forward_iterations = True
            self.total_iterations += int(
                cleaned_line.split("applying")[1].strip().split("forward iterations")[0]
            )

        if cleaned_line.startswith("downloading"):
            self.applying_forward_iterations = False
            self.current_iterations += 1
        # During forward iterations, each "." represents one iteration
        elif self.applying_forward_iterations and "." in cleaned_line:
            self.current_iterations += len(cleaned_line.split("."))

        return self.get_patching_progress()
