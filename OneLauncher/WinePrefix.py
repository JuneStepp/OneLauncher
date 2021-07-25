# coding=utf-8
###########################################################################
# Main window for OneLauncher.
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
from OneLauncher import Settings
import urllib

# Imports for extracting function
import lzma
import tarfile
from shutil import move, rmtree

import errno
from PySide6 import QtCore, QtWidgets
from pathlib import Path
import logging


class BuiltInPrefix:
    # To use Proton, replace link with Proton build and uncomment
    # `self.documents_symlinker()` in wine_setup
    WINE_URL = "https://github.com/Kron4ek/Wine-Builds/releases/download/6.7/wine-6.7-staging-tkg-amd64.tar.xz"
    DXVK_URL = (
        "https://github.com/doitsujin/dxvk/releases/download/v1.8.1/dxvk-1.8.1.tar.gz"
    )

    def __init__(self, winePrefix: Path, documentsDir: Path, parent):
        self.winePrefix = winePrefix
        self.documentsDir = documentsDir
        self.logger = logging.getLogger("main")

        (Settings.platform_dirs.user_data_path/"wine").mkdir(parents=True, exist_ok=True)

        self.dlgDownloader = QtWidgets.QProgressDialog(
            "Checking for updates...",
            "",
            0,
            100,
            parent,
            QtCore.Qt.FramelessWindowHint,
        )
        self.dlgDownloader.setWindowModality(QtCore.Qt.WindowModal)
        self.dlgDownloader.setAutoClose(False)
        self.dlgDownloader.setCancelButton(None)

    def wine_setup(self):
        """Sets wine program and downloads wine if it is not there or a new version is needed"""

        # Uncomment line below when using Proton
        # self.proton_documents_symlinker()

        self.latest_wine_version = self.WINE_URL.split(
            "/download/")[1].split("/")[0]
        latest_wine_path = Settings.platform_dirs.user_data_path / \
            ("wine/wine-"+self.latest_wine_version)

        if latest_wine_path.exists():
            return latest_wine_path/"bin/wine"

        self.dlgDownloader.setLabelText("Downloading Wine...")
        latest_wine_path_tar = latest_wine_path.parent / \
            (latest_wine_path.name+".tar.xz")
        if self.downloader(self.WINE_URL, latest_wine_path_tar):
            self.dlgDownloader.reset()
            self.dlgDownloader.setLabelText("Extracting Wine...")
            self.dlgDownloader.setValue(99)
            self.wine_extractor(latest_wine_path_tar)
            self.dlgDownloader.setValue(100)

            return (
                Settings.platform_dirs.user_data_path /
                ("wine/wine-"+self.latest_wine_version)/"bin/wine"
            )
        else:
            return False

    def dxvk_setup(self):
        self.latest_dxvk_version = self.DXVK_URL.split(
            "download/v")[1].split("/")[0]
        self.latest_dxvk_path = (
            Settings.platform_dirs.user_data_path/("wine/dxvk-"+self.latest_dxvk_version)
        )

        if not self.latest_dxvk_path.exists():
            self.dlgDownloader.setLabelText("Downloading DXVK...")
            latest_dxvk_path_tar = (self.latest_dxvk_path.parent /
                                    (self.latest_dxvk_path.name+".tar.gz"))
            if self.downloader(self.DXVK_URL, latest_dxvk_path_tar):
                self.dlgDownloader.reset()
                self.dlgDownloader.setLabelText("Extracting DXVK...")
                self.dlgDownloader.setValue(99)
                self.dxvk_extracor(latest_dxvk_path_tar)
                self.dlgDownloader.setValue(100)

                self.dxvk_injector()

        elif not (self.winePrefix/"drive_c/windows/system32/d3d11.dll").is_symlink():
            self.dxvk_injector()

    def downloader(self, url, path: Path) -> bool:
        """Downloads file from url to path and shows progress with self.handle_download_progress"""
        try:
            urllib.request.urlretrieve(
                url, str(path), self.handle_download_progress
            )  # nosec
            return True
        except (urllib.error.URLError, urllib.error.HTTPError) as error:
            self.logger.error(error.reason, exc_info=True)
            return False

    def handle_download_progress(self, index, frame, size):
        """Updates progress bar with download progress"""
        percent = 100 * index * frame // size
        self.dlgDownloader.setValue(percent)

    def wine_extractor(self, path: Path):
        path_no_suffix = path.parent / \
            (path.with_suffix("").with_suffix(""))

        # Extracts tar.xz file
        with lzma.open(path) as file:
            with tarfile.open(fileobj=file) as tar:
                tar.extractall(path_no_suffix)

        # Moves files from nested directory to main one
        source_dir = [path for path in path_no_suffix.glob("*")
                      if path.is_dir()][0]
        move(source_dir, Settings.platform_dirs.user_data_path/"wine")
        source_dir = Settings.platform_dirs.user_data_path/"wine"/source_dir.name
        path_no_suffix.rmdir()
        source_dir.rename(source_dir.parent/path_no_suffix.name)

        # Removes downloaded tar.xz
        path.unlink()

        # Removes old wine versions
        for dir in (Settings.platform_dirs.user_data_path/"wine").glob("*"):
            if not dir.is_dir():
                continue

            if dir.name.startswith("wine") and not dir.name.endswith(self.latest_wine_version):
                rmtree(dir)

    def dxvk_extracor(self, path: Path):
        path_no_suffix = path.parent / \
            (path.with_suffix("").with_suffix(""))

        # Extracts tar.gz file
        with tarfile.open(path, "r:gz") as file:
            file.extractall(path_no_suffix.with_name(
                path_no_suffix.name+"_TEMP"))

        # Moves files from nested directory to main one
        source_dir = [dir for dir in path_no_suffix.with_name(
            path_no_suffix.name+"_TEMP").glob("*") if dir.is_dir()][0]
        move(
            path_no_suffix.with_name(
                path_no_suffix.name + "_TEMP")/source_dir, Settings.platform_dirs.user_data_path/"wine",
        )
        path_no_suffix.with_name(path_no_suffix.name+"_TEMP").rmdir()

        # Removes downloaded tar.gz
        path.unlink()

        # Removes old dxvk versions
        for dir in (Settings.platform_dirs.user_data_path/"wine").glob("*"):
            if not dir.is_dir():
                continue

            if str(dir.name).startswith("dxvk") and not str(dir.name).endswith(self.latest_dxvk_version):
                rmtree(dir)

    def dxvk_injector(self):
        """Adds dxvk to the wine prefix"""
        # Makes directories for dxvk dlls in case wine prefix hasn't been run yet
        (self.winePrefix/"drive_c/windows/system32").mkdir(parents=True, exist_ok=True)
        (self.winePrefix/"drive_c/windows/syswow64").mkdir(parents=True, exist_ok=True)

        dll_list = ["dxgi.dll", "d3d10core.dll", "d3d11.dll", "d3d9.dll"]

        
        for dll in dll_list:
            system32_dll = self.winePrefix/"drive_c/windows/system32"/dll
            syswow64_dll = self.winePrefix/"drive_c/windows/syswow64"/dll
            
            # Removes current dlls
            (system32_dll).unlink(missing_ok=True)
            (syswow64_dll).unlink(missing_ok=True)

            # Symlinks dxvk dlls in to wine prefix
            system32_dll.symlink_to(self.latest_dxvk_path/"x64"/dll)
            syswow64_dll.symlink_to(self.latest_dxvk_path/"x32"/dll)

    def proton_documents_symlinker(self):
        """
        Symlinks prefix documents folder to system documents folder.path
        This is needed for Proton.
        """
        prefix_documents_folder = self.winePrefix / \
            "drive_c/users/steamuser/My Documents"

        # Will assume that the user has set something else up for now if the folder already exists
        if prefix_documents_folder.exists():
            return

        # Make sure system documents folder and prefix documents root folder exists
        self.documentsDir.mkdir(exist_ok=True)
        prefix_documents_folder.parent.mkdir(exist_ok=True, parents=True)

        # Make symlink to system documents folder
        self.documentsDir.symlink_to(
            prefix_documents_folder, target_is_directory=True)

    def Run(self) -> Path:
        wineProg = self.wine_setup()
        self.dlgDownloader.reset()
        self.dxvk_setup()
        self.dlgDownloader.close()
        return wineProg
