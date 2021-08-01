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
import os
from pathlib import Path

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtUiTools import QUiLoader

from OneLauncher import Settings


class SettingsWindow:
    def __init__(
        self,
        highRes,
        wineProg: Path,
        wineDebug,
        patchClient: Path,
        winePrefix,
        gameDir: Path,
        settings,
        LanguageConfig,
        parent,
        data_folder: Path,
    ):

        self.settings = settings
        self.LanguageConfig = LanguageConfig

        self.winSettings = QUiLoader().load(
            str(data_folder/"ui/winSettings.ui"), parentWidget=parent)

        self.winSettings.setWindowFlags(
            QtCore.Qt.Dialog | QtCore.Qt.FramelessWindowHint
        )

        if not Settings.usingWindows:
            self.winSettings.prefixLineEdit.setText(str(winePrefix))
            self.winSettings.wineDebugLineEdit.setText(wineDebug)
            self.winSettings.wineExecutableLineEdit.setText(str(wineProg))
        else:
            self.winSettings.tabWidget.removeTab(1)

        self.winSettings.txtGameDir.setText(str(gameDir))
        self.winSettings.cboClient.addItem("32-bit")
        self.winSettings.cboClient.addItem("32-bit Legacy")
        self.winSettings.txtPatchClient.setText(str(patchClient))

        self.chkAdvancedClicked()
        self.winSettings.wineFormGroupBox.setChecked(
            not self.settings.builtinPrefixEnabled)

        self.winSettings.highResCheckBox.setChecked(highRes)

        # Only adds 64-bit option if 64-bit client is available
        if settings.checkGameClient64():
            self.winSettings.cboClient.addItem("64-bit")

        if settings.client == "WIN32":
            self.winSettings.cboClient.setCurrentIndex(0)
        elif settings.client == "WIN32Legacy":
            self.winSettings.cboClient.setCurrentIndex(1)
        elif settings.client == "WIN64":
            self.winSettings.cboClient.setCurrentIndex(2)

        self.winSettings.btnEN.setIcon(
            QtGui.QIcon(str(data_folder/"images/EN-US.png"))
        )
        self.winSettings.btnDE.setIcon(
            QtGui.QIcon(str(data_folder/"images/DE.png"))
        )
        self.winSettings.btnFR.setIcon(
            QtGui.QIcon(str(data_folder/"images/FR.png"))
        )

        self.setLanguageButtons()

        self.winSettings.btnSetupWizard.clicked.connect(
            self.btnSetupWizardClicked)
        self.start_setup_wizard = False
        self.winSettings.btnGameDir.clicked.connect(self.btnGameDirClicked)
        self.winSettings.txtGameDir.textChanged.connect(self.txtGameDirChanged)
        self.winSettings.chkAdvanced.clicked.connect(self.chkAdvancedClicked)

    def chkAdvancedClicked(self):
        if Settings.usingWindows:
            if self.winSettings.chkAdvanced.isChecked():
                self.winSettings.txtPatchClient.setVisible(True)
                self.winSettings.lblPatchClient.setVisible(True)
            else:
                self.winSettings.txtPatchClient.setVisible(False)
                self.winSettings.lblPatchClient.setVisible(False)
        elif self.winSettings.chkAdvanced.isChecked():
            self.winSettings.txtPatchClient.setVisible(True)
            self.winSettings.lblPatchClient.setVisible(True)
            self.winSettings.wineAdvancedFrame.show()
        else:
            self.winSettings.txtPatchClient.setVisible(False)
            self.winSettings.lblPatchClient.setVisible(False)
            self.winSettings.wineAdvancedFrame.hide()

    def btnGameDirClicked(self):
        txtGameDir = self.winSettings.txtGameDir.text()

        if txtGameDir == "":
            if Settings.usingWindows:
                starting_dir = Path(os.environ.get("ProgramFiles"))
            else:
                starting_dir = Path("~").expanduser()
        else:
            starting_dir = Path(txtGameDir)

        filename = QtWidgets.QFileDialog.getExistingDirectory(
            self.winSettings,
            "Game Directory",
            str(starting_dir),
            options=QtWidgets.QFileDialog.ShowDirsOnly,
        )

        if filename != "":
            self.winSettings.txtGameDir.setText(filename)

    def txtGameDirChanged(self, text):
        if text != "":
            if self.settings.checkGameClient64(Path(text)):
                if self.winSettings.cboClient.count() < 3:
                    self.winSettings.cboClient.addItem("64-bit")
            else:
                if self.winSettings.cboClient.currentIndex() == 2:
                    self.winSettings.cboClient.setCurrentIndex(0)
                self.winSettings.cboClient.removeItem(2)

            self.setLanguageButtons()

    def btnSetupWizardClicked(self):
        self.start_setup_wizard = True
        self.winSettings.reject()

    def getSetupWizardClicked(self):
        return bool(self.start_setup_wizard)

    def setLanguageButtons(self):
        # Sets up language buttons. Only buttons for available languages are enabled.
        txtGameDir = self.winSettings.txtGameDir.text()

        if Path(txtGameDir).exists():
            gameDir = Path(txtGameDir)
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
        return Path(self.winSettings.prefixLineEdit.text())

    def getProg(self):
        return Path(self.winSettings.wineExecutableLineEdit.text())

    def getDebug(self):
        return self.winSettings.wineDebugLineEdit.text()

    def getPatchClient(self):
        return Path(self.winSettings.txtPatchClient.text())

    def getGameDir(self):
        return Path(self.winSettings.txtGameDir.text())

    def getHighRes(self):
        return self.winSettings.highResCheckBox.isChecked()

    def getClient(self):
        if self.winSettings.cboClient.currentIndex() == 0:
            return "WIN32"
        elif self.winSettings.cboClient.currentIndex() == 1:
            return "WIN32Legacy"
        elif self.winSettings.cboClient.currentIndex() == 2:
            return "WIN64"

    def getBuiltinPrefixEnabled(self):
        return not self.winSettings.wineFormGroupBox.isChecked()

    def Run(self):
        return self.winSettings.exec_()
