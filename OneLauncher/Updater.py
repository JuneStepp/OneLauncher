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

import os
from qtpy import QtCore, QtWidgets, uic
from pkg_resources import resource_filename

class BuiltInPrefix:
    WINE_URL = "https://github.com/Kron4ek/Wine-Builds/releases/download/4.13/wine-4.13-staging-improved-amd64.tar.xz"

    def __init__(self, settingsDir, parent):
        self.settingsDir = settingsDir

        self.dlgDownloader = QtWidgets.QProgressDialog("Checking for updates...", "",
                                        0, 100, parent, QtCore.Qt.FramelessWindowHint)
        self.dlgDownloader.setWindowModality(QtCore.Qt.WindowModal)
        self.dlgDownloader.setAutoClose(False)
        self.dlgDownloader.setCancelButton(None)

    #Sets wine program and downloads wine if it is not there or a new version is needed
    def wineSetup(self):
        self.latest_wine_version = float(self.WINE_URL[57:61])
        if os.path.exists(self.settingsDir + "wine/wine-" + str(self.latest_wine_version)):
            return (self.settingsDir + "wine/wine-" +
                    str(self.latest_wine_version) + "/bin/wine")
        else:
            self.dlgDownloader.setLabelText("Downloading wine...")
            self.downloader(self.WINE_URL, self.settingsDir + "wine/wine-" +
                            str(self.latest_wine_version) + ".tar.xz")

            self.dlgDownloader.reset()
            self.dlgDownloader.setLabelText("Extracting wine...")
            self.dlgDownloader.setValue(99)
            self.extracter(self.settingsDir + "wine/wine-" +
                            str(self.latest_wine_version) + ".tar.xz")
            self.dlgDownloader.setValue(100)

            return (self.settingsDir + "wine/wine-" +
                    str(self.latest_wine_version) + "/bin/wine")

    #def dxvkSetup(self):

    def downloader(self, url, path):
        #Downloads file from url to path and shows progress with self.handleDownloadProgress
        request.urlretrieve(url, path, self.handleDownloadProgress)

    def handleDownloadProgress(self, index, frame, size):
        #Updates progress bar with download progress
        percent = 100 * index * frame // size
        self.dlgDownloader.setValue(percent)

    def extracter(self, path):
        #Extracts tar.xz file
        with lzma.open(path) as file:
            with tarfile.open(fileobj=file) as tar:
                content = tar.extractall(path[:-7])

        #Moves files from nested directory to main one
        source_dir = (os.listdir(path[:-7]))[0]
        move(os.path.join(path[:-7], source_dir), path[:-17])
        os.rmdir(path[:-7])
        os.rename(os.path.join(path[:-17], source_dir), path[:-7])

        #Removes downloaded tar.xz
        os.remove(path)

        #Removes old wine versions
        for dir in os.listdir(path[:-17]):
            if dir.startswith("wine") and not dir.endswith(str(self.latest_wine_version)):
                rmtree(os.path.join(path[:-17], dir))

    def Run(self):
        wineProg = self.wineSetup()
        #self.dxvkSetup()
        self.dlgDownloader.close()
        return wineProg
