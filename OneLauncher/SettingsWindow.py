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
from PySide2 import QtCore, QtGui, QtWidgets
from PySide2.QtUiTools import QUiLoader
import os.path
from pkg_resources import resource_filename


class SettingsWindow:
    def __init__(
        self,
        hiRes,
        x86,
        wineProg,
        wineDebug,
        patchClient,
        winePrefix,
        gameDir,
        homeDir,
        osType,
        settings,
        LanguageConfig,
        parent,
    ):

        self.homeDir = homeDir
        self.osType = osType
        self.winePrefix = winePrefix
        self.settings = settings
        self.LanguageConfig = LanguageConfig

        ui_file = QtCore.QFile(
            resource_filename(__name__, "ui" + os.sep + "winSettings.ui")
        )

        ui_file.open(QtCore.QFile.ReadOnly)
        loader = QUiLoader()
        self.winSettings = loader.load(ui_file, parentWidget=parent)
        ui_file.close()

        self.winSettings.setWindowFlags(QtCore.Qt.Popup)

        if not self.osType.usingWindows:
            self.winSettings.txtPrefix.setText(winePrefix)
            self.winSettings.txtDebug.setText(wineDebug)
            self.winSettings.txtProgram.setText(wineProg)
            self.winSettings.txtProgram.setVisible(False)
            self.winSettings.lblProgram.setVisible(False)
            self.winSettings.txtPrefix.setVisible(False)
            self.winSettings.lblPrefix.setVisible(False)
            self.winSettings.btnPrefixDir.setVisible(False)
        else:
            self.winSettings.tabWidget.removeTab(1)

        self.winSettings.txtGameDir.setText(gameDir)
        self.winSettings.cboGraphics.addItem("Enabled")
        self.winSettings.cboGraphics.addItem("Disabled")
        self.winSettings.chkAdvanced.setChecked(False)
        self.winSettings.txtPatchClient.setText(patchClient)
        self.winSettings.txtPatchClient.setVisible(False)
        self.winSettings.lblPatchClient.setVisible(False)

        if hiRes:
            self.winSettings.cboGraphics.setCurrentIndex(0)
        else:
            self.winSettings.cboGraphics.setCurrentIndex(1)

        # Only enables and sets up check box if 64-bit client is available
        if os.path.exists(
            gameDir + os.sep + "x64" + os.sep + "lotroclient64.exe"
        ) or os.path.exists(
            gameDir + os.sep + "x64" + os.sep + "dndclient64.exe"
        ):
            if x86:
                self.winSettings.chkx86.setChecked(True)
            else:
                self.winSettings.chkx86.setChecked(False)
        else:
            self.winSettings.chkx86.setEnabled(False)

        self.winSettings.btnEN.setIcon(
            QtGui.QIcon(
                resource_filename(__name__, "images" + os.sep + "EN.png")
            )
        )

        self.winSettings.btnDE.setIcon(
            QtGui.QIcon(
                resource_filename(__name__, "images" + os.sep + "DE.png")
            )
        )

        self.winSettings.btnFR.setIcon(
            QtGui.QIcon(
                resource_filename(__name__, "images" + os.sep + "FR.png")
            )
        )

        self.setLanguageButtons()

        self.winSettings.btnSetupWizard.clicked.connect(
            self.btnSetupWizardClicked
        )
        self.start_setup_wizard = False
        self.winSettings.btnGameDir.clicked.connect(self.btnGameDirClicked)
        self.winSettings.txtGameDir.textChanged.connect(self.txtGameDirChanged)
        self.winSettings.chkAdvanced.clicked.connect(self.chkAdvancedClicked)

        if not self.osType.usingWindows:
            self.winSettings.btnPrefixDir.clicked.connect(
                self.btnPrefixDirClicked
            )
            self.winSettings.txtPrefix.textChanged.connect(
                self.txtPrefixChanged
            )

    def chkAdvancedClicked(self):
        if self.osType.usingWindows:
            if self.winSettings.chkAdvanced.isChecked():
                self.winSettings.txtPatchClient.setVisible(True)
                self.winSettings.lblPatchClient.setVisible(True)
            else:
                self.winSettings.txtPatchClient.setVisible(False)
                self.winSettings.lblPatchClient.setVisible(False)
        else:
            if self.winSettings.chkAdvanced.isChecked():
                self.winSettings.txtProgram.setVisible(True)
                self.winSettings.txtPatchClient.setVisible(True)
                self.winSettings.lblProgram.setVisible(True)
                self.winSettings.lblPatchClient.setVisible(True)
                self.winSettings.txtPrefix.setVisible(True)
                self.winSettings.lblPrefix.setVisible(True)
                self.winSettings.btnPrefixDir.setVisible(True)
            else:
                self.winSettings.txtProgram.setVisible(False)
                self.winSettings.txtPatchClient.setVisible(False)
                self.winSettings.lblProgram.setVisible(False)
                self.winSettings.lblPatchClient.setVisible(False)
                self.winSettings.txtPrefix.setVisible(False)
                self.winSettings.lblPrefix.setVisible(False)
                self.winSettings.btnPrefixDir.setVisible(False)

    def btnGameDirClicked(self):
        tempdir = self.winSettings.txtGameDir.text()

        if tempdir == "":
            if self.osType.usingWindows:
                tempdir = os.environ.get("ProgramFiles")
            else:
                tempdir = self.homeDir

        filename = QtWidgets.QFileDialog.getExistingDirectory(
            self.winSettings, "Game Directory", tempdir
        )

        if filename != "":
            self.winSettings.txtGameDir.setText(filename)

    def txtGameDirChanged(self, text):
        if text != "":
            if os.path.exists(
                text + os.sep + "x64" + os.sep + "lotroclient64.exe"
            ) or os.path.exists(
                text + os.sep + "x64" + os.sep + "dndclient64.exe"
            ):
                self.winSettings.chkx86.setEnabled(True)
            else:
                self.winSettings.chkx86.setEnabled(False)

            self.setLanguageButtons()

    def btnPrefixDirClicked(self):
        tempdir = self.winSettings.txtPrefix.text()

        if tempdir == "":
            tempdir = self.homeDir

        filename = QtWidgets.QFileDialog.getExistingDirectory(
            self.winSettings, "Prefix Directory", tempdir
        )

        if filename != "":
            self.winSettings.txtPrefix.setText(filename)

    def btnSetupWizardClicked(self):
        self.start_setup_wizard = True
        self.winSettings.reject()

    def getSetupWizardClicked(self):
        if self.start_setup_wizard:
            return True
        else:
            return False

    def txtPrefixChanged(self, text):
        self.winePrefix = text

    def setLanguageButtons(self):
        # Sets up language buttons. Only buttons for available languages are enabled.
        if os.path.exists(self.winSettings.txtGameDir.text()):
            gameDir = self.winSettings.txtGameDir.text()
        else:
            gameDir = self.settings.gameDir

        for lang in self.LanguageConfig(gameDir).langList:
            if lang == "EN":
                self.winSettings.btnEN.setEnabled(True)
                self.winSettings.btnEN.setToolTip("English")
            elif lang == "DE":
                self.winSettings.btnDE.setEnabled(True)
                self.winSettings.btnDE.setToolTip("Deutsch")
            elif lang == "FR":
                self.winSettings.btnFR.setEnabled(True)
                self.winSettings.btnFR.setToolTip("Français")

            if lang == self.settings.language:
                if lang == "EN":
                    self.winSettings.btnEN.setChecked(True)
                elif lang == "DE":
                    self.winSettings.btnDE.setChecked(True)
                elif lang == "FR":
                    self.winSettings.btnFR.setChecked(True)

    def getLanguage(self):
        if self.winSettings.btnEN.isChecked():
            return "EN"
        elif self.winSettings.btnDE.isChecked():
            return "DE"
        elif self.winSettings.btnFR.isChecked():
            return "FR"

    def getPrefix(self):
        return self.winSettings.txtPrefix.text()

    def getProg(self):
        return self.winSettings.txtProgram.text()

    def getDebug(self):
        return self.winSettings.txtDebug.text()

    def getPatchClient(self):
        return self.winSettings.txtPatchClient.text()

    def getGameDir(self):
        return self.winSettings.txtGameDir.text()

    def getHiRes(self):
        if self.winSettings.cboGraphics.currentIndex() == 0:
            return True
        else:
            return False

    def getx86(self):
        if self.winSettings.chkx86.isChecked():
            return True
        else:
            return False

    def Run(self):
        return self.winSettings.exec_()
