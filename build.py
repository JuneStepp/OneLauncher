#!/usr/bin/env python3
# coding=utf-8
###########################################################################
# Build script for OneLauncher. Had to be run on each platform the code is
# build for.
#
# Based on PyLotRO
# (C) 2009 AJackson <ajackson@bcs.org.uk>
#
# Based on LotROLinux
# (C) 2007-2008 AJackson <ajackson@bcs.org.uk>
#
#
# (C) 2019-2020 Jeremy Stepp <mail@JeremyStepp.me>
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
import os
from sys import platform

if platform == "linux":
    binary_name = "TheOneLauncher-Linux"
elif platform == "win32":
    binary_name = "TheOneLauncher-Windows"
elif platform == "darwin":
    binary_name = "TheOneLauncher-Mac"
else:
    print(
        "Your OS is not supported by this program): If you are on Linux, Windows, or Mac you shouldn't get this error"
    )

build_command = (
    "python -O -m PyInstaller RunOneLauncher --name {name} -w -y -F "
    "--add-data OneLauncher/certificates{sep}OneLauncher/certificates --add-data OneLauncher/"
    "ui{sep}OneLauncher/ui --add-data OneLauncher/images{sep}OneLauncher/images"
    " --hidden-import qdarkstyle --hidden-import PySide2.QtXml --hidden-import pkg_resources.py2_warn"
    " --hidden-import win32timezone".format(sep=os.pathsep, name=binary_name)
)
os.system(build_command)
