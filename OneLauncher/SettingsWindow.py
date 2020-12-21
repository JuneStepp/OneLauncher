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


class SettingsWindow:
    def __init__(
        self,
        hiRes,
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
        data_folder,
    ):

        self.homeDir = homeDir
        self.osType = osType
        self.winePrefix = winePrefix
        self.settings = settings
        self.LanguageConfig = LanguageConfig

        ui_file = QtCore.QFile(
            os.path.join(data_folder, "ui", "winSettings.ui")
        )

        ui_file.open(QtCore.QFile.ReadOnly)
        loader = QUiLoader()
        self.winSettings = loader.load(ui_file, parentWidget=parent)
        ui_file.close()

        self.winSettings.setWindowFlags(
            QtCore.Qt.Dialog | QtCore.Qt.FramelessWindowHint
        )

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
        self.winSettings.cboClient.addItem("32-bit")
        self.winSettings.cboClient.addItem("32-bit Legacy")
        self.winSettings.chkAdvanced.setChecked(False)
        self.winSettings.txtPatchClient.setText(patchClient)
        self.winSettings.txtPatchClient.setVisible(False)
        self.winSettings.lblPatchClient.setVisible(False)

        if hiRes:
            self.winSettings.cboGraphics.setCurrentIndex(0)
        else:
            self.winSettings.cboGraphics.setCurrentIndex(1)

        # Only enables 64-bit if client is available
        if settings.checkGameClient64():
            self.winSettings.cboClient.addItem("64-bit")

        if settings.client == "WIN32":
            self.winSettings.cboClient.setCurrentIndex(0)
        elif settings.client == "WIN32Legacy":
            self.winSettings.cboClient.setCurrentIndex(1)
        elif settings.client == "WIN64":
            self.winSettings.cboClient.setCurrentIndex(2)


        self.winSettings.btnEN.setIcon(
            QtGui.QIcon(os.path.join(data_folder, "images", "EN-US.png"))
        )

        self.winSettings.btnDE.setIcon(
            QtGui.QIcon(os.path.join(data_folder, "images", "DE.png"))
        )

        self.winSettings.btnFR.setIcon(
            QtGui.QIcon(os.path.join(data_folder, "images", "FR.png"))
        )

        self.setLanguageButtons()

        self.winSettings.btnSetupWizard.clicked.connect(self.btnSetupWizardClicked)
        self.start_setup_wizard = False
        self.winSettings.btnGameDir.clicked.connect(self.btnGameDirClicked)
        self.winSettings.txtGameDir.textChanged.connect(self.txtGameDirChanged)
        self.winSettings.chkAdvanced.clicked.connect(self.chkAdvancedClicked)

        if not self.osType.usingWindows:
            self.winSettings.btnPrefixDir.clicked.connect(self.btnPrefixDirClicked)
            self.winSettings.txtPrefix.textChanged.connect(self.txtPrefixChanged)

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
        starting_dir = self.winSettings.txtGameDir.text()

        if starting_dir == "":
            if self.osType.usingWindows:
                starting_dir = os.environ.get("ProgramFiles")
            else:
                starting_dir = self.homeDir

        filename = QtWidgets.QFileDialog.getExistingDirectory(
            self.winSettings,
            "Game Directory",
            starting_dir,
            options=QtWidgets.QFileDialog.ShowDirsOnly,
        )

        if filename != "":
            self.winSettings.txtGameDir.setText(filename)

    def txtGameDirChanged(self, text):
        if text != "":
            if self.settings.checkGameClient64(text):
                if self.winSettings.cboClient.count() < 3:
                    self.winSettings.cboClient.addItem("64-bit")
            else:
                if self.winSettings.cboClient.currentIndex() == 2:
                    self.winSettings.cboClient.setCurrentIndex(0)
                self.winSettings.cboClient.removeItem(2)

            self.setLanguageButtons()

    def btnPrefixDirClicked(self):
        starting_dir = self.winSettings.txtPrefix.text()

        if starting_dir == "":
            starting_dir = self.homeDir

        filename = QtWidgets.QFileDialog.getExistingDirectory(
            self.winSettings,
            "Prefix Directory",
            starting_dir,
            options=QtWidgets.QFileDialog.ShowDirsOnly,
        )

        if filename != "":
            self.winSettings.txtPrefix.setText(filename)

    def btnSetupWizardClicked(self):
        self.start_setup_wizard = True
        self.winSettings.reject()

    def getSetupWizardClicked(self):
        return bool(self.start_setup_wizard)

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
        return self.winSettings.cboGraphics.currentIndex() == 0

    def getClient(self):
        if self.winSettings.cboClient.currentIndex() == 0:
            return "WIN32"
        elif self.winSettings.cboClient.currentIndex() == 1:
            return "WIN32Legacy"
        elif self.winSettings.cboClient.currentIndex() == 2:
            return "WIN64"

    def Run(self):
        return self.winSettings.exec_()
