# coding=utf-8
###########################################################################
# Name:   SettingsWizard
# Author: Alan Jackson
# Date:   4th April 2009
#
# Settings wizard for the Linux/OS X based launcher
# for the game Lord of the Rings Online
#
# Based on a script by SNy <SNy@bmx-chemnitz.de>
# Python port of LotROLinux by AJackson <ajackson@bcs.org.uk>
#
# (C) 2009 AJackson <ajackson@bcs.org.uk>
#
# This file is part of PyLotRO
#
# PyLotRO is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# PyLotRO is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with PyLotRO.  If not, see <http://www.gnu.org/licenses/>.
###########################################################################
from PyQt5 import QtCore, QtGui, QtWidgets, uic
from .PyLotROUtils import DetermineOS
import os.path
import glob

# small Python 2.x + PyQt4 backwards-compatibility function for QVariant


def toString(val):
    if isinstance(val, str):
        return val
    else:
        return val.toString()


class SettingsWizard:
    def __init__(self, parent, homeDir, osType, rootDir):

        self.homeDir = homeDir
        self.osType = osType
        self.prefix = ""
        self.gameDir = ""

        self.winSettings = QtWidgets.QDialog(parent)
        self.winSettings.setPalette(parent.palette())

        uifile = None

        if self.osType.usingWindows:
            try:
                from pkg_resources import resource_filename
                uifile = resource_filename(
                    __name__, 'ui/winGameWizardNative.ui')
            except:
                uifile = os.path.join(rootDir, "ui", "winGameWizardNative.ui")
        else:
            try:
                from pkg_resources import resource_filename
                uifile = resource_filename(__name__, 'ui/winGameWizard.ui')
            except:
                uifile = os.path.join(rootDir, "ui", "winGameWizard.ui")

        Ui_winGameWizard, base_class = uic.loadUiType(uifile)
        self.uiWizard = Ui_winGameWizard()
        self.uiWizard.setupUi(self.winSettings)
        screen = QtWidgets.QDesktopWidget().screenGeometry()
        size = self.winSettings.geometry()
        self.winSettings.move(
            (screen.width() - size.width()) / 2, (screen.height() - size.height()) / 2)
        self.winSettings.setWindowTitle("Game Settings")

        self.model = QtGui.QStandardItemModel(0, 3, self.winSettings)
        self.model.setHeaderData(0, QtCore.Qt.Horizontal, "Prefix")
        self.model.setHeaderData(1, QtCore.Qt.Horizontal, "Game Directory")
        self.model.setHeaderData(2, QtCore.Qt.Horizontal, "Game Directory")
        self.uiWizard.tblGame.setModel(self.model)

        if self.osType.usingWindows:
            self.uiWizard.tblGame.setColumnWidth(0, 0)
            self.uiWizard.tblGame.setColumnWidth(1, 0)
            self.uiWizard.tblGame.setColumnWidth(2, 650)
        else:
            self.uiWizard.tblGame.setColumnWidth(0, 260)
            self.uiWizard.tblGame.setColumnWidth(1, 390)
            self.uiWizard.tblGame.setColumnWidth(2, 0)
            self.uiWizard.cboApplication.addItem("Wine")
            self.uiWizard.cboApplication.addItem("Crossover Games")
            self.uiWizard.cboApplication.addItem("Crossover Office")

        self.uiWizard.cboGame.addItem("Lord of the Rings Online")
        self.uiWizard.cboGame.addItem("Lord of the Rings Online (Test)")
        self.uiWizard.cboGame.addItem("Dungeons & Dragons Online")
        self.uiWizard.cboGame.addItem("Dungeons & Dragons Online (Test)")

        self.ClearGameTable()

        self.uiWizard.btnFind.clicked.connect(self.btnFindClicked)

        if not self.osType.usingWindows:
            self.uiWizard.cboApplication.currentIndexChanged.connect(self.ClearGameTable)

        self.uiWizard.cboGame.currentIndexChanged.connect(self.ClearGameTable)
        self.uiWizard.tblGame.clicked.connect(self.GameSelected)

    def GameSelected(self):
        self.uiWizard.btnBoxOptions.setStandardButtons(
            QtWidgets.QDialogButtonBox.Apply | QtWidgets.QDialogButtonBox.Cancel)

        currIndex = self.uiWizard.tblGame.currentIndex()

        self.prefix = toString(self.model.data(currIndex.sibling(
            self.uiWizard.tblGame.currentIndex().row(), 0)))

        gameDir1 = toString(self.model.data(currIndex.sibling(
            self.uiWizard.tblGame.currentIndex().row(), 1)))
        gameDir2 = toString(self.model.data(currIndex.sibling(
            self.uiWizard.tblGame.currentIndex().row(), 2)))
        self.gameDir = gameDir2

    def ClearGameTable(self):
        self.uiWizard.btnBoxOptions.setStandardButtons(
            QtWidgets.QDialogButtonBox.Cancel)
        self.model.removeRows(0, self.model.rowCount(
            QtCore.QModelIndex()), QtCore.QModelIndex())

    def btnFindClicked(self):
        self.ClearGameTable()

        if self.uiWizard.cboGame.currentIndex() == 0 or self.uiWizard.cboGame.currentIndex() == 1:
            self.client = "lotroclient.exe"
        else:
            self.client = "dndclient.exe"

        if self.osType.usingWindows:
            startDir = "C:\\"
            prefix = ""
            self.trawl(os.path.join(startDir, "Program Files"),
                       prefix, os.path.join(startDir, "Program Files"))
        else:
            if self.uiWizard.cboApplication.currentIndex() == 0:
                startDir = self.homeDir + ".*"
            elif self.uiWizard.cboApplication.currentIndex() == 1:
                startDir = self.homeDir + self.osType.settingsCXG + "/*"
            else:
                startDir = self.homeDir + self.osType.settingsCXO + "/*"

            for name in glob.glob(startDir):
                if os.path.isdir(name):
                    if os.path.exists(os.path.join(name, "drive_c")):
                        prefix = ""
                        path = os.path.join(name, "drive_c", "Program Files")

                        if self.osType.usingWindows:
                            prefix = name
                        elif self.uiWizard.cboApplication.currentIndex() == 0:
                            prefix = name
                        elif self.uiWizard.cboApplication.currentIndex() == 1:
                            prefix = name.replace(
                                self.homeDir + self.osType.settingsCXG + "/", "")
                        else:
                            prefix = name.replace(
                                self.homeDir + self.osType.settingsCXO + "/", "")

                        self.trawl(path, prefix, os.path.join(
                            name, "drive_c", "Program Files"))

    def trawl(self, path, prefix, directory):
        for name in glob.glob(directory + os.sep + "*"):
            if name.lower().find(self.client) >= 0:
                row = self.model.rowCount(QtCore.QModelIndex())
                self.model.insertRows(row, 1, QtCore.QModelIndex())
                self.model.setData(self.model.index(
                    row, 0, QtCore.QModelIndex()), prefix)

                dirName = os.path.dirname(name.replace(path + os.sep, ""))

                self.model.setData(self.model.index(
                    row, 1, QtCore.QModelIndex()), dirName)
                self.model.setData(self.model.index(
                    row, 2, QtCore.QModelIndex()), (path + os.sep + dirName))

            if os.path.isdir(name):
                if not name.upper().endswith(os.sep + "BACKUP"):
                    self.trawl(path, prefix, name)

    def getApp(self):
        if self.osType.usingWindows:
            return "Native"
        elif self.uiWizard.cboApplication.currentIndex() == 0:
            return "Wine"
        elif self.uiWizard.cboApplication.currentIndex() == 1:
            return "CXGames"
        else:
            return "CXOffice"

    def getUsingDND(self):
        if self.uiWizard.cboGame.currentIndex() == 0 or self.uiWizard.cboGame.currentIndex() == 1:
            return False
        else:
            return True

    def getUsingTest(self):
        if self.uiWizard.cboGame.currentIndex() == 0 or self.uiWizard.cboGame.currentIndex() == 2:
            return False
        else:
            return True

    def getPrefix(self):
        return self.prefix

    def getProg(self):
        return "wine"

    def getDebug(self):
        return "fixme-all"

    def getPatchClient(self):
        return "patchclient.dll"

    def getGameDir(self):
        return self.gameDir

    def getHiRes(self):
        if os.path.exists(self.gameDir + os.sep + "client_highres.dat"):
            return True
        else:
            return False

    def Run(self):
        return self.winSettings.exec_()
