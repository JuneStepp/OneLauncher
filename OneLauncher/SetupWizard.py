# coding=utf-8
###########################################################################
# Settings wizard for OneLauncher.
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
from qtpy import QtCore, QtGui, QtWidgets, uic
from .OneLauncherUtils import DetermineOS
import os.path
import glob
from pkg_resources import resource_filename

def toString(val):
    if isinstance(val, str):
        return val
    else:
        return val.toString()


class SetupWizard:
    def __init__(self, parent, homeDir, osType, rootDir):

        self.homeDir = homeDir
        self.osType = osType
        self.gameDir = ""

        self.winSetupWizard = QtWidgets.QDialog(parent, QtCore.Qt.FramelessWindowHint)

        uifile = resource_filename(__name__, 'ui' + os.sep + 'winSetupWizard.ui')

        Ui_winSetupWizard, base_class = uic.loadUiType(uifile)
        self.uiWizard = Ui_winSetupWizard()
        self.uiWizard.setupUi(self.winSetupWizard)
        self.winSetupWizard.setWindowTitle("Setup Wizard")

        qr = self.winSetupWizard.frameGeometry()
        cp = QtWidgets.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.winSetupWizard.move(qr.topLeft())

        self.uiWizard.btnFindMenu = QtWidgets.QMenu()
        self.uiWizard.btnFindMenu.addAction(self.uiWizard.actionShowTest)
        self.uiWizard.btnFindMenu.addAction(self.uiWizard.actionShowNormal)
        self.uiWizard.actionShowTest.triggered.connect(self.actionShowTestSelected)
        self.uiWizard.actionShowNormal.triggered.connect(self.actionShowNormalSelected)
        self.uiWizard.btnFind.setMenu(self.uiWizard.btnFindMenu)
        self.uiWizard.btnFind_2.setMenu(self.uiWizard.btnFindMenu)

        self.uiWizard.btnFind.clicked.connect(self.btnFindClicked)
        self.uiWizard.btnFind_2.clicked.connect(self.btnFindClicked)

        self.uiWizard.btnBoxIntro.accepted.connect(self.btnBoxIntroAccepted)
        self.uiWizard.btnBoxOptions.accepted.connect(self.btnBoxOptionsAccepted)
        self.uiWizard.btnBoxOptions_2.accepted.connect(self.btnBoxOptionsAccepted)

        self.uiWizard.btnBoxIntro.rejected.connect(self.btnBoxRejected)
        self.uiWizard.btnBoxOptions.rejected.connect(self.btnBoxRejected)
        self.uiWizard.btnBoxOptions_2.rejected.connect(self.btnBoxRejected)

    def btnBoxIntroAccepted(self):
        self.uiWizard.actionShowNormal.setVisible(False)
        self.uiWizard.stackedWidget.setCurrentWidget(self.uiWizard.GameFinder)

    def btnBoxOptionsAccepted(self):
        self.winSetupWizard.accept()

    def btnBoxRejected(self):
        self.winSetupWizard.reject()

    def actionShowTestSelected(self):
        self.uiWizard.stackedWidget.setCurrentWidget(self.uiWizard.GameFinder2)
        self.uiWizard.actionShowNormal.setVisible(True)
        self.uiWizard.actionShowTest.setVisible(False)

    def actionShowNormalSelected(self):
        self.uiWizard.stackedWidget.setCurrentWidget(self.uiWizard.GameFinder)
        self.uiWizard.actionShowTest.setVisible(True)
        self.uiWizard.actionShowNormal.setVisible(False)

    def btnFindClicked(self):
        if self.osType.usingWindows:
            startDir = "C:\\"
            for client in ["lotroclient.exe", "dndclient.exe"]:
                self.client = client

                self.trawl(os.path.join(startDir, "Program Files"),
                           os.path.join(startDir, "Program Files"))
                if os.path.exists(os.path.join(startDir, "Program Files (x86)")):
                    self.trawl(os.path.join(startDir, "Program Files (x86)"),
                            os.path.join(startDir, "Program Files (x86)"))
        else:
            for dir in [self.homeDir + ".*", self.homeDir + self.osType.settingsCXG + "/*",
                    self.homeDir + self.osType.settingsCXO + "/*"]:
                startDir = dir

                for name in glob.glob(startDir):
                    if os.path.isdir(name):
                        if os.path.exists(os.path.join(name, "drive_c")):
                            for client in ["lotroclient.exe", "dndclient.exe"]:
                                self.client = client

                                self.trawl(os.path.join(name, "drive_c", "Program Files"),
                                    os.path.join(name, "drive_c", "Program Files"))

                                if os.path.exists(os.path.join(name, "drive_c", "Program Files (x86)")):
                                    self.trawl(os.path.join(name, "drive_c", "Program Files (x86)"),
                                        os.path.join(name, "drive_c", "Program Files (x86)"))

    def trawl(self, path, directory):
        for name in glob.glob(directory + os.sep + "*"):
            if name.lower().find(self.client) >= 0:
                dirName = os.path.dirname(name.replace(path + os.sep, ""))

                if self.client == "lotroclient.exe":
                    if "Bullroarer" in dirName:
                        self.uiWizard.lstLOTROTest.addItem(path + os.sep + dirName)
                    else:
                        self.uiWizard.lstLOTRO.addItem(path + os.sep + dirName)
                elif self.client == "dndclient.exe":
                    if "(Preview)" in dirName:
                        self.uiWizard.lstDDOTest.addItem(path + os.sep + dirName)
                    else:
                        self.uiWizard.lstDDO.addItem(path + os.sep + dirName)

            if os.path.isdir(name):
                if not name.upper().endswith(os.sep + "BACKUP"):
                    self.trawl(path, name)

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

    def getGameDir(self):
        return self.gameDir

    def getHiRes(self):
        if os.path.exists(self.gameDir + os.sep + "client_highres.dat"):
            return True
        else:
            return False

    def Run(self):
        return self.winSetupWizard.exec_()
