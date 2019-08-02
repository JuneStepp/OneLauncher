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
import os.path
import glob
from pkg_resources import resource_filename


class SettingsWindow:
    def __init__(self, hiRes, x86, wineProg, wineDebug, patchClient, winePrefix,
                 gameDir, homeDir, osType, settings, LanguageConfig, parent):

        self.homeDir = homeDir
        self.osType = osType
        self.winePrefix = winePrefix
        self.settings = settings
        self.LanguageConfig = LanguageConfig

        self.winSettings = QtWidgets.QDialog(parent, QtCore.Qt.FramelessWindowHint)

        uifile = resource_filename(__name__, 'ui' + os.sep + 'winSettings.ui')

        Ui_dlgSettings, base_class = uic.loadUiType(uifile)
        self.uiSettings = Ui_dlgSettings()
        self.uiSettings.setupUi(self.winSettings)

        if not self.osType.usingWindows:
            self.uiSettings.txtPrefix.setText(winePrefix)
            self.uiSettings.txtDebug.setText(wineDebug)
            self.uiSettings.txtProgram.setText(wineProg)
            self.uiSettings.txtProgram.setVisible(False)
            self.uiSettings.lblProgram.setVisible(False)
        else: self.uiSettings.tabWidget.removeTab(1)

        self.uiSettings.txtGameDir.setText(gameDir)
        self.uiSettings.cboGraphics.addItem("Enabled")
        self.uiSettings.cboGraphics.addItem("Disabled")
        self.uiSettings.chkAdvanced.setChecked(False)
        self.uiSettings.txtPatchClient.setText(patchClient)
        self.uiSettings.txtPatchClient.setVisible(False)
        self.uiSettings.lblPatchClient.setVisible(False)

        if hiRes:
            self.uiSettings.cboGraphics.setCurrentIndex(0)
        else:
            self.uiSettings.cboGraphics.setCurrentIndex(1)

        # Only enables and sets up check box if 64-bit client is available
        if (os.path.exists(gameDir + os.sep + "x64" + os.sep + "lotroclient64.exe") or
                os.path.exists(gameDir + os.sep + "x64" + os.sep + "dndclient64.exe")):
            if x86:
                self.uiSettings.chkx86.setChecked(True)
            else:
                self.uiSettings.chkx86.setChecked(False)
        else:
            self.uiSettings.chkx86.setEnabled(False)

        self.uiSettings.btnEN.setIcon(QtGui.QIcon(resource_filename(__name__,
                                            "images" + os.sep + "EN.png")))

        self.uiSettings.btnDE.setIcon(QtGui.QIcon(resource_filename(__name__,
                                            "images" + os.sep + "DE.png")))

        self.uiSettings.btnFR.setIcon(QtGui.QIcon(resource_filename(__name__,
                                            "images" + os.sep + "FR.png")))

        self.setLanguageButtons()

        self.uiSettings.btnSetupWizard.clicked.connect(self.btnSetupWizardClicked)
        self.start_setup_wizard = False
        self.uiSettings.btnGameDir.clicked.connect(self.btnGameDirClicked)
        self.uiSettings.txtGameDir.textChanged.connect(self.txtGameDirChanged)
        self.uiSettings.chkAdvanced.clicked.connect(self.chkAdvancedClicked)

        if not self.osType.usingWindows:
            self.uiSettings.btnPrefixDir.clicked.connect(self.btnPrefixDirClicked)
            self.uiSettings.txtPrefix.textChanged.connect(self.txtPrefixChanged)

    def chkAdvancedClicked(self):
        if self.osType.usingWindows:
            if self.uiSettings.chkAdvanced.isChecked():
                self.uiSettings.txtPatchClient.setVisible(True)
                self.uiSettings.lblPatchClient.setVisible(True)
            else:
                self.uiSettings.txtPatchClient.setVisible(False)
                self.uiSettings.lblPatchClient.setVisible(False)
        else:
            if self.uiSettings.chkAdvanced.isChecked():
                self.uiSettings.txtProgram.setVisible(True)
                self.uiSettings.txtPatchClient.setVisible(True)
                self.uiSettings.lblProgram.setVisible(True)
                self.uiSettings.lblPatchClient.setVisible(True)
            else:
                self.uiSettings.txtProgram.setVisible(False)
                self.uiSettings.txtPatchClient.setVisible(False)
                self.uiSettings.lblProgram.setVisible(False)
                self.uiSettings.lblPatchClient.setVisible(False)

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
            if (os.path.exists(text + os.sep + "x64" + os.sep + "lotroclient64.exe") or
                    os.path.exists(text + os.sep + "x64" + os.sep + "dndclient64.exe")):
                self.uiSettings.chkx86.setEnabled(True)
            else:
                self.uiSettings.chkx86.setEnabled(False)

            self.setLanguageButtons()

    def btnPrefixDirClicked(self):
        tempdir = self.uiSettings.txtPrefix.text()

        if tempdir == "":
            tempdir = self.homeDir

        filename = QtWidgets.QFileDialog.getExistingDirectory(
            self.winSettings, "Prefix Directory", tempdir)

        if filename != "":
            self.uiSettings.txtPrefix.setText(filename)

    def btnSetupWizardClicked(self):
        self.start_setup_wizard = True
        self.winSettings.reject()

    def getSetupWizardClicked(self):
        if self.start_setup_wizard:
            return True
        else: return False

    def txtPrefixChanged(self, text):
        self.winePrefix = text

    def setLanguageButtons(self):
        #Sets up language buttons. Only buttons for available languages are enabled.
        if os.path.exists(self.uiSettings.txtGameDir.text()):
            gameDir = self.uiSettings.txtGameDir.text()
        else: gameDir = self.settings.gameDir

        for lang in self.LanguageConfig(gameDir).langList:
            if lang == "EN":
                self.uiSettings.btnEN.setEnabled(True)
                self.uiSettings.btnEN.setToolTip("English")
            elif lang == "DE":
                self.uiSettings.btnDE.setEnabled(True)
                self.uiSettings.btnDE.setToolTip("Deutsch")
            elif lang == "FR":
                self.uiSettings.btnFR.setEnabled(True)
                self.uiSettings.btnFR.setToolTip("Français")

            if lang == self.settings.language:
                if lang == "EN":
                    self.uiSettings.btnEN.setChecked(True)
                elif lang == "DE":
                    self.uiSettings.btnDE.setChecked(True)
                elif lang == "FR":
                    self.uiSettings.btnFR.setChecked(True)

    def getLanguage(self):
            if self.uiSettings.btnEN.isChecked():
                return "EN"
            elif self.uiSettings.btnDE.isChecked():
                return "DE"
            elif self.uiSettings.btnFR.isChecked():
                return "FR"

    def getPrefix(self):
        return self.uiSettings.txtPrefix.text()

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
