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
# (C) 2019 June Stepp <git@junestepp.me>
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

build_command = ("python -O -m PyInstaller RunOneLauncher --name TheOneLauncher -w -y -F "
    "--add-data OneLauncher/certificates{0}OneLauncher/certificates --add-data OneLauncher/"
    "ui{0}OneLauncher/ui --add-data OneLauncher/images{0}OneLauncher/images"
    " --hidden-import qdarkstyle".format(os.pathsep))
os.system(build_command)
