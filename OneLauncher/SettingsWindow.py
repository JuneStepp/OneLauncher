# coding=utf-8
###########################################################################
# Settings window for OneLauncher.
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
from .CheckConfig import CheckConfig
from .SetupWizard import SetupWizard
import os.path
import glob
from pkg_resources import resource_filename


class SettingsWindow:
    def __init__(self, hiRes, app, x86, wineProg, wineDebug, patchClient, usingDND,
                 winePrefix, gameDir, homeDir, osType, rootDir, settings):

        self.homeDir = homeDir
        self.osType = osType
        self.app = app
        self.winePrefix = winePrefix
        self.rootDir = rootDir
        self.settings = settings

        self.winSettings = QtWidgets.QDialog()
        self.winSettings.setWindowFlags(QtCore.Qt.FramelessWindowHint)

        if self.osType.usingWindows:
            uifile = resource_filename(__name__, 'ui' + os.sep + 'winSettingsNative.ui')
        else:
            uifile = resource_filename(__name__, 'ui' + os.sep + 'winSettings.ui')

        Ui_dlgSettings, base_class = uic.loadUiType(uifile)
        self.uiSettings = Ui_dlgSettings()
        self.uiSettings.setupUi(self.winSettings)
        screen = QtWidgets.QDesktopWidget().screenGeometry()
        size = self.winSettings.geometry()
        self.winSettings.move(
            (screen.width() - size.width()) / 2, (screen.height() - size.height()) / 2)
        self.winSettings.setWindowTitle("Game Settings")

        if not self.osType.usingWindows:
            self.uiSettings.cboApplication.addItem("Wine")
            self.uiSettings.cboApplication.addItem("Crossover Games")
            self.uiSettings.cboApplication.addItem("Crossover Office")
            self.uiSettings.txtPrefix.setText(winePrefix)
            self.uiSettings.txtDebug.setText(wineDebug)
            self.uiSettings.txtProgram.setText(wineProg)
            self.uiSettings.txtProgram.setEnabled(False)

        self.uiSettings.txtGameDir.setText(gameDir)
        self.uiSettings.cboGraphics.addItem("Enabled")
        self.uiSettings.cboGraphics.addItem("Disabled")
        self.uiSettings.chkAdvanced.setChecked(False)
        self.uiSettings.txtPatchClient.setText(patchClient)
        self.uiSettings.txtPatchClient.setEnabled(False)

        if not self.osType.usingWindows:
            if app == "Wine":
                self.uiSettings.lblPrefix.setText("WINEPREFIX")
                self.uiSettings.txtPrefix.setVisible(True)
                self.uiSettings.cboBottle.setVisible(False)
                self.uiSettings.cboApplication.setCurrentIndex(0)
            else:
                self.uiSettings.lblPrefix.setText("Bottle")
                if app == "CXGames":
                    self.uiSettings.cboApplication.setCurrentIndex(1)
                else:
                    self.uiSettings.cboApplication.setCurrentIndex(2)
                self.uiSettings.txtPrefix.setVisible(False)
                self.uiSettings.cboBottle.setVisible(True)
                self.ShowBottles(winePrefix)

        if hiRes:
            self.uiSettings.cboGraphics.setCurrentIndex(0)
        else:
            self.uiSettings.cboGraphics.setCurrentIndex(1)

        # Only enables and sets up check box if 64-bit client is available
        if (os.path.exists(gameDir + os.sep + "x64" + os.sep + "lotroclient64.exe") and usingDND == False or
                usingDND and os.path.exists(gameDir + os.sep + "x64" + os.sep + "dndclient64.exe")):
            if x86:
                self.uiSettings.chkx86.setChecked(True)
            else:
                self.uiSettings.chkx86.setChecked(False)
        else:
            self.uiSettings.chkx86.setEnabled(False)

        self.uiSettings.btnSetupWizard.clicked.connect(self.btnSetupWizardClicked)
        self.uiSettings.btnGameDir.clicked.connect(self.btnGameDirClicked)
        self.uiSettings.txtGameDir.textChanged.connect(self.txtGameDirChanged)
        self.uiSettings.chkAdvanced.clicked.connect(self.chkAdvancedClicked)

        if not self.osType.usingWindows:
            if self.app == "Wine":
                self.uiSettings.btnCheckPrefix.setText("Check Prefix")
            else:
                self.uiSettings.btnCheckPrefix.setText("Check Bottle")

            self.uiSettings.btnCheckPrefix.clicked.connect(self.btnCheckPrefixClicked)
            self.uiSettings.btnPrefixDir.clicked.connect(self.btnPrefixDirClicked)
            self.uiSettings.txtPrefix.textChanged.connect(self.txtPrefixChanged)
            self.uiSettings.cboBottle.currentIndexChanged.connect(self.cboBottleChanged)
            self.uiSettings.cboBottle.currentIndexChanged.connect(self.cboBottleChanged)
            self.uiSettings.cboApplication.currentIndexChanged.connect(
                self.cboApplicationChanged)

        self.usingDND = usingDND

    def ShowBottles(self, defaultBottle=None):
        self.uiSettings.cboBottle.clear()

        tempdir = self.homeDir

        if self.uiSettings.cboApplication.currentIndex() == 1:
            tempdir += self.osType.settingsCXG
        else:
            tempdir += self.osType.settingsCXO

        currPos = 0

        for name in glob.glob("%s/*" % (tempdir)):
            if os.path.exists(name + "/drive_c"):
                tempBottle = name.replace(tempdir + "/", "")
                self.uiSettings.cboBottle.addItem(tempBottle)
                if tempBottle == defaultBottle:
                    self.uiSettings.cboBottle.setCurrentIndex(currPos)
                currPos += 1

    def cboApplicationChanged(self):
        if self.uiSettings.cboApplication.currentIndex() == 0:
            self.uiSettings.lblPrefix.setText("WINEPREFIX")
            self.uiSettings.txtPrefix.setVisible(True)
            self.uiSettings.btnPrefixDir.setVisible(True)
            self.uiSettings.cboBottle.setVisible(False)
            self.uiSettings.btnCheckPrefix.setText("Check Prefix")
            self.winePrefix = self.uiSettings.txtPrefix.text()

        else:
            self.uiSettings.lblPrefix.setText("Bottle")
            self.uiSettings.txtPrefix.setVisible(False)
            self.uiSettings.btnPrefixDir.setVisible(False)
            self.uiSettings.cboBottle.setVisible(True)
            self.ShowBottles()
            self.uiSettings.btnCheckPrefix.setText("Check Bottle")
            if self.uiSettings.cboBottle.currentText() == "":
                self.winePrefix = ""

    def cboBottleChanged(self):
        self.winePrefix = self.winSettings.cboBottle.currentText()

    def chkAdvancedClicked(self):
        if self.osType.usingWindows:
            if self.uiSettings.chkAdvanced.isChecked():
                self.uiSettings.txtPatchClient.setEnabled(True)
            else:
                self.uiSettings.txtPatchClient.setEnabled(False)
        else:
            if self.uiSettings.chkAdvanced.isChecked():
                self.uiSettings.txtProgram.setEnabled(True)
                self.uiSettings.txtPatchClient.setEnabled(True)
            else:
                self.uiSettings.txtProgram.setEnabled(False)
                self.uiSettings.txtPatchClient.setEnabled(False)

    def btnGameDirClicked(self):
        tempdir = self.uiSettings.txtGameDir.text()

        if tempdir == "":
            if self.osType.usingWindows:
                tempdir = os.environ.get('ProgramFiles')
            else:
                tempdir = self.homeDir

        filename = QtWidgets.QFileDialog.getExistingDirectory(
            self.winSettings, "Game Directory", tempdir)

        if filename != "":
            self.uiSettings.txtGameDir.setText(filename)

    def txtGameDirChanged(self, text):
        if text != "":
            if (os.path.exists(text + os.sep + "x64" + os.sep + "lotroclient64.exe") and self.usingDND == False or
                    self.usingDND and os.path.exists(text + os.sep + "x64" + os.sep + "dndclient64.exe")):
                self.uiSettings.chkx86.setEnabled(True)
            else:
                self.uiSettings.chkx86.setEnabled(False)

    def btnPrefixDirClicked(self):
        tempdir = self.uiSettings.txtPrefix.text()

        if tempdir == "":
            tempdir = self.homeDir

        filename = QtWidgets.QFileDialog.getExistingDirectory(
            self.winSettings, "Prefix Directory", tempdir)

        if filename != "":
            self.uiSettings.txtPrefix.setText(filename)

    def btnSetupWizardClicked(self):
        winWizard = SetupWizard(self.homeDir, self.osType, self.rootDir)

        if winWizard.Run() == QtWidgets.QDialog.Accepted:
            self.settings.usingDND = winWizard.getUsingDND()
            self.settings.usingTest = winWizard.getUsingTest()
            self.settings.hiResEnabled = winWizard.getHiRes()
            self.settings.app = winWizard.getApp()
            self.settings.wineProg = winWizard.getProg()
            self.settings.wineDebug = winWizard.getDebug()
            self.settings.patchClient = winWizard.getPatchClient()
            self.settings.winePrefix = winWizard.getPrefix()
            self.settings.gameDir = winWizard.getGameDir()
            self.settings.SaveSettings(self.uiMain.chkSaveSettings.isChecked())
            self.InitialSetup()

    def txtPrefixChanged(self, text):
        self.winePrefix = text

    def btnCheckPrefixClicked(self):
        confCheck = CheckConfig(
            self.app, self.winePrefix, self.homeDir, self.osType, self.rootDir)

        confCheck.Run()

    def getApp(self):
        if self.osType.usingWindows:
            return "Native"
        else:
            if self.uiSettings.cboApplication.currentIndex() == 0:
                return "Wine"
            elif self.uiSettings.cboApplication.currentIndex() == 1:
                return "CXGames"
            else:
                return "CXOffice"

    def getPrefix(self):
        if self.uiSettings.cboApplication.currentIndex() == 0:
            return self.uiSettings.txtPrefix.text()
        else:
            return self.uiSettings.cboBottle.currentText()

    def getProg(self):
        return self.uiSettings.txtProgram.text()

    def getDebug(self):
        return self.uiSettings.txtDebug.text()

    def getPatchClient(self):
        return self.uiSettings.txtPatchClient.text()

    def getGameDir(self):
        return self.uiSettings.txtGameDir.text()

    def getHiRes(self):
        if self.uiSettings.cboGraphics.currentIndex() == 0:
            return True
        else:
            return False

    def getx86(self):
        if self.uiSettings.chkx86.isChecked():
            return True
        else:
            return False

    def Run(self):
        return self.winSettings.exec_()
