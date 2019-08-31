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
# (C) 2019 Jeremy Stepp <jeremy@bluetecno.com>
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
from urllib import request
#Imports for extracting function
import lzma
import tarfile
from contextlib import closing
from shutil import move, rmtree

import os, errno
from qtpy import QtCore, QtWidgets, uic
from pkg_resources import resource_filename

class BuiltInPrefix:
    WINE_URL = "https://github.com/Kron4ek/Wine-Builds/releases/download/4.13/wine-4.13-staging-improved-amd64.tar.xz"
    DXVK_URL = "https://github.com/doitsujin/dxvk/releases/download/v1.3.2/dxvk-1.3.2.tar.gz"

    def __init__(self, settingsDir, winePrefix, parent):
        self.settingsDir = settingsDir
        self.winePrefix = winePrefix

        self.dlgDownloader = QtWidgets.QProgressDialog("Checking for updates...", "",
                                        0, 100, parent, QtCore.Qt.FramelessWindowHint)
        self.dlgDownloader.setWindowModality(QtCore.Qt.WindowModal)
        self.dlgDownloader.setAutoClose(False)
        self.dlgDownloader.setCancelButton(None)

    #Sets wine program and downloads wine if it is not there or a new version is needed
    def wineSetup(self):
        self.latest_wine_version = self.WINE_URL[57:61]
        latest_wine_path = self.settingsDir + "wine/wine-" + self.latest_wine_version

        if os.path.exists(latest_wine_path):
            return (latest_wine_path + "/bin/wine")
        else:
            self.dlgDownloader.setLabelText("Downloading wine...")
            self.downloader(self.WINE_URL, latest_wine_path + ".tar.xz")

            self.dlgDownloader.reset()
            self.dlgDownloader.setLabelText("Extracting wine...")
            self.dlgDownloader.setValue(99)
            self.wine_extracter(latest_wine_path + ".tar.xz")
            self.dlgDownloader.setValue(100)

            return (self.settingsDir + "wine/wine-" +
                    self.latest_wine_version + "/bin/wine")

    def dxvkSetup(self):
        self.latest_dxvk_version = self.DXVK_URL[53:58]
        self.latest_dxvk_path = (self.settingsDir + "wine/dxvk-" +
                                    self.latest_dxvk_version)

        if not os.path.exists(self.latest_dxvk_path):
            self.dlgDownloader.setLabelText("Downloading dxvk...")
            self.downloader(self.DXVK_URL, self.latest_dxvk_path + ".tar.gz")

            self.dlgDownloader.reset()
            self.dlgDownloader.setLabelText("Extracting dxvk...")
            self.dlgDownloader.setValue(99)
            self.dxvk_extracter(self.latest_dxvk_path + ".tar.gz")
            self.dlgDownloader.setValue(100)

            self.dxvk_injecter()

        elif not os.path.islink(self.winePrefix + "/drive_c/windows/system32/d3d11.dll"):
            self.dxvk_injecter()

    def downloader(self, url, path):
        #Downloads file from url to path and shows progress with self.handleDownloadProgress
        request.urlretrieve(url, path, self.handleDownloadProgress)

    def handleDownloadProgress(self, index, frame, size):
        #Updates progress bar with download progress
        percent = 100 * index * frame // size
        self.dlgDownloader.setValue(percent)

    def wine_extracter(self, path):
        #Extracts tar.xz file
        with lzma.open(path) as file:
            with tarfile.open(fileobj=file) as tar:
                content = tar.extractall(path[:-7])

        #Moves files from nested directory to main one
        source_dir = (os.listdir(path[:-7]))[0]
        move(os.path.join(path[:-7], source_dir), self.settingsDir + "wine")
        os.rmdir(path[:-7])
        os.rename(os.path.join(self.settingsDir + "wine", source_dir), path[:-7])

        #Removes downloaded tar.xz
        os.remove(path)

        #Removes old wine versions
        for dir in os.listdir(self.settingsDir + "wine"):
            if dir.startswith("wine") and not dir.endswith(self.latest_wine_version):
                rmtree(os.path.join(self.settingsDir + "wine", dir))

    def dxvk_extracter(self, path):
        #Extracts tar.gz file
        with tarfile.open(path, "r:gz") as file:
            file.extractall(path[:-7] + "_TEMP")

        #Moves files from nested directory to main one
        source_dir = (os.listdir(path[:-7] + "_TEMP"))[0]
        move(os.path.join(path[:-7] + "_TEMP", source_dir), self.settingsDir + "wine")
        os.rmdir(path[:-7] + "_TEMP")

        #Removes downloaded tar.gz
        os.remove(path)

        #Removes old dxvk versions
        for dir in os.listdir(self.settingsDir + "wine"):
            if dir.startswith("dxvk") and not dir.endswith(self.latest_dxvk_version):
                rmtree(os.path.join(self.settingsDir + "wine", dir))

    #Adds dxvk to the wine prefix
    def dxvk_injecter(self):
        #Makes directories for dxvk dlls in case wine prefix hasn't been run yet
        os.makedirs(self.winePrefix + "/drive_c/windows/system32", exist_ok=True)
        os.makedirs(self.winePrefix + "/drive_c/windows/syswow64", exist_ok=True)

        dll_list = os.listdir(self.latest_dxvk_path + "/x64")

        #Removes current dlls
        for dll in dll_list:
            try:
                os.remove(self.winePrefix + "/drive_c/windows/system32/" + dll)
                os.remove(self.winePrefix + "/drive_c/windows/syswow64/" + dll)
            except OSError as error:
                # errno.ENOENT = no such file or directory
                if error.errno != errno.ENOENT:
                    raise

        #Symlinks dxvk dlls in to wine prefix
        for dll in dll_list:
            os.symlink(self.latest_dxvk_path + "/x64/" + dll, self.winePrefix +
                                                "/drive_c/windows/system32/" + dll)
            os.symlink(self.latest_dxvk_path + "/x32/" + dll, self.winePrefix +
                                                "/drive_c/windows/syswow64/" + dll)

    def Run(self):
        wineProg = self.wineSetup()
        self.dlgDownloader.reset()
        self.dxvkSetup()
        self.dlgDownloader.close()
        return wineProg
