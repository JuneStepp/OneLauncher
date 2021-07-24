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
import os
from pathlib import Path
import sys
import OneLauncher
from OneLauncher.logs import Logger
import logging
from typing import List
import defusedxml.minidom
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtUiTools import QUiLoader
from OneLauncher.SettingsWindow import SettingsWindow
from OneLauncher.AddonManager import AddonManager
from OneLauncher.SetupWizard import SetupWizard
from OneLauncher.PatchWindow import PatchWindow
from OneLauncher.StartGame import StartGame
from OneLauncher import Settings
from OneLauncher.WinePrefix import BuiltInPrefix
from OneLauncher.OneLauncherUtils import (
    checkForCertificates,
    DetermineGame,
    LanguageConfig,
    BaseConfig,
    GLSDataCenter,
    WorldQueueConfig,
    AuthenticateUser,
    JoinWorldQueue,
    GetText,
)
from pkg_resources import parse_version
import keyring
from platform import platform
import urllib

# For setting global timeout used by urllib
import socket
from json import loads as jsonLoads


class MainWindow(QtWidgets.QMainWindow):
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_ShareOpenGLContexts)
    app = QtWidgets.QApplication(sys.argv)

    # Make signals for communicating with MainWindowThread
    ReturnLog = QtCore.Signal(str)
    ReturnBaseConfig = QtCore.Signal(BaseConfig)
    ReturnGLSDataCenter = QtCore.Signal(BaseConfig)
    ReturnWorldQueueConfig = QtCore.Signal(BaseConfig)
    ReturnNews = QtCore.Signal(str)

    def __init__(self):
        super().__init__()
        # Initialise variables
        self.data_folder = self.getDataFolder()
        self.settings = None
        self.gameType = DetermineGame()
        self.configFile = ""
        self.currentGame = None

        # Create the main window and set all text so that translations are handled via gettext
        self.winMain = QUiLoader().load(
            str(self.data_folder/"ui"/"winMain.ui"), parentWidget=self)
        self.winMain.setWindowFlags(QtCore.Qt.Dialog)
        self.winMain.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setFixedSize(790, 470)
        self.centerWindow()

        # Set font size explicitly to stop OS text size options from
        # breaking the UI.
        font = QtGui.QFont()
        font.setPointSize(10)
        self.app.setFont(font)

        # Setup font for icons
        font_file = self.data_folder/"fonts/Font Awesome 5 Free-Solid-900.otf"
        font_db = QtGui.QFontDatabase()
        font_id = font_db.addApplicationFont(str(font_file))
        font_family = font_db.applicationFontFamilies(font_id)
        self.icon_font = QtGui.QFont(font_family)
        self.icon_font.setHintingPreference(QtGui.QFont.PreferNoHinting)
        self.icon_font.setPixelSize(16)

        self.handleWindowsDarkTheme()

        # Setup buttons
        self.setupBtnAbout()
        self.setupBtnMinimize()
        self.setupBtnExit()
        self.setupBtnOptions()
        self.setupBtnAddonManager()
        self.setupBtnLoginMenu()
        self.initializeBtnSwitchGame()

        # Accounts combo box item selection signal
        self.winMain.cboAccount.textActivated.connect(self.cboAccountChanged)

        # Pressing enter in password box acts like pressing login button
        self.winMain.txtPassword.returnPressed.connect(self.btnLoginClicked)

        self.connectMainWindowThreadSignals()

        self.setupMousePropagation()

        # Disable login and save settings buttons
        self.winMain.btnLogin.setEnabled(False)
        self.winMain.chkSaveSettings.setEnabled(False)

        self.configureKeyring()

        # Set default timeout used by urllib
        socket.setdefaulttimeout(6)

        self.InitialSetup(first_setup=True)

    def getDataFolder(self):
        """Returns location equivalent to OneLauncher folder of source code."""
        if getattr(sys, "frozen", False):
            # Data location for frozen programs
            return Path(sys.executable.parent)
        else:
            return Path(__file__).parent

    def run(self):
        self.show()
        sys.exit(self.app.exec_())

    def resetFocus(self):
        if self.winMain.cboAccount.currentText() == "":
            self.winMain.cboAccount.setFocus()
        elif self.winMain.txtPassword.text() == "":
            self.winMain.txtPassword.setFocus()

    def centerWindow(self):
        qr = self.frameGeometry()
        cp = self.app.primaryScreen().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def mousePressEvent(self, event):
        """Lets the user drag the window when left-click holding it"""
        if event.button() == QtCore.Qt.LeftButton:
            self.windowHandle().startSystemMove()
            event.accept()

    def setupMousePropagation(self):
        """Sets some widgets to WA_NoMousePropagation to avoid window dragging issues"""
        mouse_ignore_list = [
            self.winMain.btnAbout,
            self.winMain.btnExit,
            self.winMain.btnLogin,
            self.winMain.btnMinimize,
            self.winMain.btnOptions,
            self.winMain.btnAddonManager,
            self.winMain.btnSwitchGame,
            self.winMain.cboWorld,
            self.winMain.chkSaveSettings,
        ]
        for widget in mouse_ignore_list:
            widget.setAttribute(QtCore.Qt.WA_NoMousePropagation)

    def handleWindowsDarkTheme(self):
        if not Settings.usingWindows:
            return

        settings = QtCore.QSettings("HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize",
                                    QtCore.QSettings.NativeFormat)
        # If user has dark theme activated
        if not settings.value("AppsUseLightTheme"):
            # Use QPalette to set custom dark theme for Windows.
            # The builtin Windows dark theme for Windows is not ready
            # as of 7-5-2021
            self.app.setStyle(QtWidgets.QStyleFactory.create("Fusion"))
            dark_palette = QtGui.QPalette()
            dark_color = QtGui.QColor(45, 45, 45)
            disabled_color = QtGui.QColor(127, 127, 127)

            dark_palette.setColor(QtGui.QPalette.Window, dark_color)
            dark_palette.setColor(QtGui.QPalette.WindowText, QtCore.Qt.white)
            dark_palette.setColor(QtGui.QPalette.Base,
                                  QtGui.QColor(18, 18, 18))
            dark_palette.setColor(QtGui.QPalette.AlternateBase, dark_color)
            dark_palette.setColor(QtGui.QPalette.ToolTipBase, QtCore.Qt.white)
            dark_palette.setColor(QtGui.QPalette.ToolTipText, QtCore.Qt.white)
            dark_palette.setColor(QtGui.QPalette.Text, QtCore.Qt.white)
            dark_palette.setColor(QtGui.QPalette.Disabled,
                                  QtGui.QPalette.Text, disabled_color)
            dark_palette.setColor(QtGui.QPalette.Button, dark_color)
            dark_palette.setColor(QtGui.QPalette.ButtonText, QtCore.Qt.white)
            dark_palette.setColor(QtGui.QPalette.Disabled,
                                  QtGui.QPalette.ButtonText, disabled_color)
            dark_palette.setColor(QtGui.QPalette.BrightText, QtCore.Qt.red)
            dark_palette.setColor(QtGui.QPalette.Link,
                                  QtGui.QColor(42, 130, 218))

            dark_palette.setColor(QtGui.QPalette.Highlight,
                                  QtGui.QColor(42, 130, 218))
            dark_palette.setColor(
                QtGui.QPalette.HighlightedText, QtCore.Qt.black)
            dark_palette.setColor(QtGui.QPalette.Disabled,
                                  QtGui.QPalette.HighlightedText, disabled_color)

            self.app.setPalette(dark_palette)
            self.app.setStyleSheet(
                "QToolTip { color: #ffffff; background-color: #2a82da; border: 1px solid white; }")

    def setupBtnExit(self):
        self.winMain.btnExit.clicked.connect(self.close)

        self.winMain.btnExit.setFont(self.icon_font)
        self.winMain.btnExit.setText("\uf00d")

    def setupBtnMinimize(self):
        self.winMain.btnMinimize.clicked.connect(self.showMinimized)

        self.winMain.btnMinimize.setFont(self.icon_font)
        self.winMain.btnMinimize.setText("\uf2d1")

    def setupBtnAbout(self):
        self.winMain.btnAbout.clicked.connect(self.btnAboutSelected)

        self.winMain.btnAbout.setFont(self.icon_font)
        self.winMain.btnAbout.setText("\uf05a")

    def setupBtnOptions(self):
        self.winMain.btnOptions.clicked.connect(self.btnOptionsSelected)

        self.winMain.btnOptions.setFont(self.icon_font)
        self.winMain.btnOptions.setText("\uf013")

    def setupBtnAddonManager(self):
        self.winMain.btnAddonManager.clicked.connect(
            self.btnAddonManagerSelected)

        self.winMain.btnAddonManager.setFont(self.icon_font)
        self.winMain.btnAddonManager.setText("\uf055")

    def setupBtnLoginMenu(self):
        """Sets up signals and context menu for btnLoginMenu"""
        self.winMain.btnLogin.clicked.connect(self.btnLoginClicked)

        # Setup context menu
        self.winMain.btnLoginMenu = QtWidgets.QMenu()
        self.winMain.btnLoginMenu.addAction(self.winMain.actionPatch)
        self.winMain.actionPatch.triggered.connect(self.actionPatchSelected)
        self.winMain.btnLogin.setMenu(self.winMain.btnLoginMenu)

    def initializeBtnSwitchGame(self):
        """Sets up signals and actions for btnSwitchGame.

        It needs to later be configured for the current game with
        `self.configureBtnSwitchGameForGame`.
        """
        self.winMain.btnSwitchGame.clicked.connect(self.btnSwitchGameClicked)

        # Initialize context menu
        self.winMain.btnSwitchGameMenu = QtWidgets.QMenu()
        self.winMain.btnSwitchGameMenu.addAction(self.winMain.actionLOTROTest)
        self.winMain.actionLOTROTest.triggered.connect(self.SwitchToLOTROTest)
        self.winMain.btnSwitchGameMenu.addAction(self.winMain.actionDDOTest)
        self.winMain.actionDDOTest.triggered.connect(self.SwitchToDDOTest)
        self.winMain.btnSwitchGameMenu.addAction(self.winMain.actionLOTRO)
        self.winMain.actionLOTRO.triggered.connect(self.SwitchToLOTRO)
        self.winMain.btnSwitchGameMenu.addAction(self.winMain.actionDDO)
        self.winMain.actionDDO.triggered.connect(self.SwitchToDDO)
        self.winMain.btnSwitchGame.setMenu(self.winMain.btnSwitchGameMenu)

    def configureBtnSwitchGameForGame(self, game):
        """Set icon and dropdown options of switch game button according to game"""
        if game == "DDO":
            self.winMain.btnSwitchGame.setIcon(
                QtGui.QIcon(
                    str(self.data_folder/"images"/"LOTROSwitchIcon.png")
                )
            )
            self.winMain.actionLOTROTest.setEnabled(False)
            self.winMain.actionLOTROTest.setVisible(False)
            self.winMain.actionDDOTest.setEnabled(True)
            self.winMain.actionDDOTest.setVisible(True)
            self.winMain.actionLOTRO.setEnabled(False)
            self.winMain.actionLOTRO.setVisible(False)
            self.winMain.actionDDO.setEnabled(False)
            self.winMain.actionDDO.setVisible(False)
        elif game == "DDO.Test":
            self.winMain.btnSwitchGame.setIcon(
                QtGui.QIcon(
                    str(self.data_folder/"images"/"LOTROSwitchIcon.png")
                )
            )
            self.winMain.actionLOTROTest.setEnabled(False)
            self.winMain.actionLOTROTest.setVisible(False)
            self.winMain.actionDDOTest.setEnabled(False)
            self.winMain.actionDDOTest.setVisible(False)
            self.winMain.actionLOTRO.setEnabled(False)
            self.winMain.actionLOTRO.setVisible(False)
            self.winMain.actionDDO.setEnabled(True)
            self.winMain.actionDDO.setVisible(True)
        elif game == "LOTRO.Test":
            self.winMain.btnSwitchGame.setIcon(
                QtGui.QIcon(
                    str(self.data_folder/"images"/"DDOSwitchIcon.png")
                )
            )
            self.winMain.actionLOTROTest.setEnabled(False)
            self.winMain.actionLOTROTest.setVisible(False)
            self.winMain.actionDDOTest.setEnabled(False)
            self.winMain.actionDDOTest.setVisible(False)
            self.winMain.actionLOTRO.setEnabled(True)
            self.winMain.actionLOTRO.setVisible(True)
            self.winMain.actionDDO.setEnabled(False)
            self.winMain.actionDDO.setVisible(False)
        else:
            self.winMain.btnSwitchGame.setIcon(
                QtGui.QIcon(
                    str(self.data_folder/"images"/"DDOSwitchIcon.png")
                )
            )
            self.winMain.actionDDOTest.setEnabled(False)
            self.winMain.actionDDOTest.setVisible(False)
            self.winMain.actionLOTROTest.setEnabled(True)
            self.winMain.actionLOTROTest.setVisible(True)
            self.winMain.actionLOTRO.setEnabled(False)
            self.winMain.actionLOTRO.setVisible(False)
            self.winMain.actionDDO.setEnabled(False)
            self.winMain.actionDDO.setVisible(False)

    def connectMainWindowThreadSignals(self):
        """Connects function signals for communicating with MainWindowThread."""
        self.ReturnLog = self.ReturnLog
        self.ReturnLog.connect(self.AddLog)
        self.ReturnBaseConfig = self.ReturnBaseConfig
        self.ReturnBaseConfig.connect(self.GetBaseConfig)
        self.ReturnGLSDataCenter = self.ReturnGLSDataCenter
        self.ReturnGLSDataCenter.connect(self.GetGLSDataCenter)
        self.ReturnWorldQueueConfig = self.ReturnWorldQueueConfig
        self.ReturnWorldQueueConfig.connect(self.GetWorldQueueConfig)
        self.ReturnNews = self.ReturnNews
        self.ReturnNews.connect(self.GetNews)

    def configureKeyring(self):
        """
        Sets the propper keyring backend for the used OS. This isn't
        automatically detected correctly with Nuitka
        """
        if Settings.usingWindows:
            from keyring.backends import Windows
            keyring.set_keyring(Windows.WinVaultKeyring())
        elif Settings.usingMac:
            from keyring.backends import OS_X
            keyring.set_keyring(OS_X.Keyring())
        else:
            from keyring.backends import SecretService
            keyring.set_keyring(SecretService.Keyring())

    def btnAboutSelected(self):
        dlgAbout = QUiLoader().load(str(self.data_folder/"ui/winAbout.ui"), parentWidget=self)

        dlgAbout.setWindowFlags(QtCore.Qt.Popup)

        dlgAbout.lblDescription.setText(OneLauncher.__description__)
        dlgAbout.lblRepoWebsite.setText(f"<a href='{OneLauncher.__project_url__}'>"
                                        f"{OneLauncher.__project_url__}</a>")
        dlgAbout.lblCopyright.setText(OneLauncher.__copyright__)
        dlgAbout.lblVersion.setText(
            "<b>Version:</b> " + OneLauncher.__version__)
        dlgAbout.lblCopyrightHistory.setText(OneLauncher.__copyright_history__)

        dlgAbout.exec_()
        self.resetFocus()

    def manageBuiltInPrefix(self):
        # Only manage prefix if prefix management is enabled and the program is on Linux or Mac
        if not self.settings.builtinPrefixEnabled or Settings.usingWindows:
            return True

        winBuiltInPrefix = BuiltInPrefix(
            Settings.builtin_prefix_dir,
            Settings.documentsDir,
            self,
        )

        wineProg = winBuiltInPrefix.Run()
        if wineProg:
            self.settings.wineProg = wineProg
            self.settings.save_game_settings(
                saveAccountDetails=self.winMain.chkSaveSettings.isChecked(),
                savePassword=self.winMain.chkSavePassword.isChecked(),
            )
            return True
        else:
            self.AddLog(
                "[E19] There was an error updating the WINE prefix. "
                "You may want to check your network connection."
            )
            return False

    def actionPatchSelected(self):
        prefix_status = self.manageBuiltInPrefix()
        if prefix_status:
            winPatch = PatchWindow(
                self.dataCenter.patchServer,
                self.worldQueueConfig.patchProductCode,
                self.settings.language,
                self.settings.gameDir,
                self.settings.patchClient,
                self.settings.wineProg,
                self.settings.highResEnabled,
                self.settings.winePrefix,
                self.settings.wineDebug,
                self,
                self.data_folder,
                self.settings.currentGame,
                self.baseConfig.gameDocumentsDir,
            )

            winPatch.Run(self.app)
            self.resetFocus()

    def btnOptionsSelected(self):
        winSettings = SettingsWindow(
            self.settings.highResEnabled,
            self.settings.wineProg,
            self.settings.wineDebug,
            self.settings.patchClient,
            self.settings.winePrefix,
            self.settings.gameDir,
            self.settings,
            LanguageConfig,
            self,
            self.data_folder,
        )

        if winSettings.Run() == QtWidgets.QDialog.Accepted:
            self.settings.highResEnabled = winSettings.getHighRes()
            self.settings.client = winSettings.getClient()
            self.settings.patchClient = winSettings.getPatchClient()
            self.settings.gameDir = winSettings.getGameDir()
            if winSettings.getLanguage():
                self.settings.language = winSettings.getLanguage()

            if not Settings.usingWindows:
                self.settings.wineDebug = winSettings.getDebug()
                self.settings.builtinPrefixEnabled = winSettings.getBuiltinPrefixEnabled()
                if not self.settings.builtinPrefixEnabled:
                    self.settings.wineProg = winSettings.getProg()
                    self.settings.winePrefix = winSettings.getPrefix()

            self.settings.save_game_settings(
                saveAccountDetails=self.winMain.chkSaveSettings.isChecked(),
                savePassword=self.winMain.chkSavePassword.isChecked(),
            )
            self.resetFocus()
            self.InitialSetup()
        else:
            if winSettings.getSetupWizardClicked():
                self.settingsWizardCalled()
            else:
                self.resetFocus()

    def btnAddonManagerSelected(self):
        winAddonManager = AddonManager(
            self.settings.currentGame,
            self,
            self.data_folder,
            self.baseConfig.gameDocumentsDir,
            self.settings.startupScripts,
            self.icon_font
        )

        winAddonManager.Run()
        self.settings.save_game_settings(
            saveAccountDetails=self.winMain.chkSaveSettings.isChecked(),
            savePassword=self.winMain.chkSavePassword.isChecked(),
        )

        self.resetFocus()

    def settingsWizardCalled(self):
        winWizard = SetupWizard(
            self.data_folder, self.app)
        self.hide()

        if winWizard.Run() == QtWidgets.QDialog.Accepted:
            default_game = winWizard.getGame()
            if default_game:
                game_list = ["LOTRO", "DDO", "LOTRO.Test", "DDO.Test"]
                game_list.append(game_list.pop(game_list.index(default_game)))
                for game in game_list:
                    dir = winWizard.getGameDir(game)
                    if dir:
                        self.settings.gameDir = dir
                        self.settings.highResEnabled = winWizard.getHiRes(
                            self.settings.gameDir
                        )
                        self.settings.winePrefix = ""
                        self.settings.save_game_settings(game=game)

                self.InitialSetup()

        self.show()

    def btnSwitchGameClicked(self):
        if self.settings.currentGame.startswith("DDO"):
            self.currentGame = "LOTRO"
        else:
            self.currentGame = "DDO"
        self.InitialSetup()

    def SwitchToDDOTest(self):
        self.currentGame = "DDO.Test"
        self.InitialSetup()

    def SwitchToLOTROTest(self):
        self.currentGame = "LOTRO.Test"
        self.InitialSetup()

    def SwitchToLOTRO(self):
        self.currentGame = "LOTRO"
        self.InitialSetup()

    def SwitchToDDO(self):
        self.currentGame = "DDO"
        self.InitialSetup()

    def btnLoginClicked(self):
        if (
            self.winMain.cboAccount.currentText() == ""
            or self.winMain.txtPassword.text() == ""
        ):
            self.AddLog(
                '<font color="Khaki">Please enter account name and password</font>'
            )
        else:
            prefix_status = self.manageBuiltInPrefix()
            if prefix_status:
                self.AuthAccount()

    def cboAccountChanged(self):
        """Sets saved information for selected account."""
        self.setCurrentAccountWorld()
        self.setCurrentAccountPassword()
        self.winMain.txtPassword.setFocus()

    def loadAllSavedAccounts(self):
        accounts = list(self.settings.accountsDictionary.keys())

        # Accounts are read backwards, so they
        # are in order of most recentally played
        for account in accounts[::-1]:
            self.winMain.cboAccount.addItem(account)

    def setCurrentAccountWorld(self):
        if not self.settings.focusAccount and self.settings.accountsDictionary:
            current_account = self.winMain.cboAccount.currentText()
            account_world = self.settings.accountsDictionary[current_account][0]

            self.winMain.cboWorld.setCurrentText(account_world)

    def setCurrentAccountPassword(self):
        if self.settings.savePassword:
            self.winMain.chkSavePassword.setChecked(True)
            if self.settings.currentGame.startswith("DDO"):
                self.winMain.txtPassword.setText(
                    keyring.get_password(
                        f"{OneLauncher.__title__}DDO",
                        self.winMain.cboAccount.currentText(),
                    )
                )
            else:
                self.winMain.txtPassword.setText(
                    keyring.get_password(
                        f"{OneLauncher.__title__}LOTRO",
                        self.winMain.cboAccount.currentText(),
                    )
                )
        else:
            self.winMain.txtPassword.setFocus()

    def AuthAccount(self):
        self.AddLog("Checking account details...")

        # Force a small display to ensure message above is displayed
        # as program can look like it is not responding while validating
        for _ in range(4):
            self.app.processEvents()

        self.account = AuthenticateUser(
            self.dataCenter.authServer,
            self.winMain.cboAccount.currentText(),
            self.winMain.txtPassword.text(),
            self.baseConfig.gameName,
        )

        # don't keep password longer in memory than required
        if not self.winMain.chkSavePassword.isChecked():
            self.winMain.txtPassword.clear()

        if self.account.authSuccess:
            self.AddLog("Account authenticated")

            if self.winMain.chkSaveSettings.isChecked():
                current_account = self.winMain.cboAccount.currentText()

                # Test servers only have one world and shouldn't
                # overwrite world setting on normal servers
                if self.settings.currentGame.endswith(".Test"):
                    world = self.settings.accountsDictionary[current_account][0]
                else:
                    world = self.winMain.cboWorld.currentText()

                # Account is deleted first, because accounts are in order of
                # the most recently played at the end.
                try:
                    del self.settings.accountsDictionary[current_account]
                except KeyError:
                    pass
                self.settings.accountsDictionary[current_account] = [world]

                self.settings.save_game_settings(
                    saveAccountDetails=self.winMain.chkSaveSettings.isChecked(),
                    savePassword=self.winMain.chkSavePassword.isChecked(),
                )

                if self.winMain.chkSavePassword.isChecked():
                    if self.settings.currentGame.startswith("DDO"):
                        keyring.set_password(
                            f"{OneLauncher.__title__}DDO",
                            self.winMain.cboAccount.currentText(),
                            self.winMain.txtPassword.text(),
                        )
                    else:
                        keyring.set_password(
                            f"{OneLauncher.__title__}LOTRO",
                            self.winMain.cboAccount.currentText(),
                            self.winMain.txtPassword.text(),
                        )
                else:
                    try:
                        if self.settings.currentGame.startswith("DDO"):
                            keyring.delete_password(
                                f"{OneLauncher.__title__}DDO",
                                self.winMain.cboAccount.currentText(),
                            )
                        else:
                            keyring.delete_password(
                                f"{OneLauncher.__title__}LOTRO",
                                self.winMain.cboAccount.currentText(),
                            )
                    except keyring.errors.PasswordDeleteError:
                        pass

            tempWorld = ""

            if len(self.account.gameList) > 1:
                dlgChooseAccount = QUiLoader().load(
                    str(self.data_folder/"ui/winSelectAccount.ui"), parentWidget=self)

                dlgChooseAccount.setWindowFlags(QtCore.Qt.Popup)

                dlgChooseAccount.lblMessage.setText(
                    "Multiple game accounts found\n\nPlease select the required game"
                )

                for game in self.account.gameList:
                    dlgChooseAccount.comboBox.addItem(game.description)

                if dlgChooseAccount.exec_() == QtWidgets.QDialog.Accepted:
                    self.accNumber = self.account.gameList[
                        dlgChooseAccount.comboBox.currentIndex()
                    ].name
                    self.resetFocus()
                else:
                    self.resetFocus()
                    self.AddLog("No game selected - aborting")
                    return
            else:
                self.accNumber = self.account.gameList[0].name

            tempWorld = self.dataCenter.worldList[self.winMain.cboWorld.currentIndex(
            )]
            tempWorld.CheckWorld()

            if tempWorld.worldAvailable:
                self.urlChatServer = tempWorld.urlChatServer
                self.urlLoginServer = tempWorld.loginServer

                if tempWorld.queueURL == "":
                    self.LaunchGame()
                else:
                    self.EnterWorldQueue(tempWorld.queueURL)
            else:
                self.AddLog(
                    "[E10] Error getting world status. You may want to check "
                    "the news feed for a scheduled down time."
                )
        else:
            self.AddLog(self.account.messError)

    def LaunchGame(self):
        game = StartGame(
            self.worldQueueConfig.gameClientFilename,
            self.settings.client,
            self.worldQueueConfig.gameClientArgTemplate,
            self.accNumber,
            self.urlLoginServer,
            self.account.ticket,
            self.urlChatServer,
            self.settings.language,
            self.settings.gameDir,
            self.settings.wineProg,
            self.settings.wineDebug,
            self.settings.winePrefix,
            self.settings.highResEnabled,
            self.settings.builtinPrefixEnabled,
            self.worldQueueConfig.crashreceiver,
            self.worldQueueConfig.DefaultUploadThrottleMbps,
            self.worldQueueConfig.bugurl,
            self.worldQueueConfig.authserverurl,
            self.worldQueueConfig.supporturl,
            self.worldQueueConfig.supportserviceurl,
            self.worldQueueConfig.glsticketlifetime,
            self.winMain.cboWorld.currentText(),
            self.winMain.cboAccount.currentText(),
            self,
            self.data_folder,
            self.settings.startupScripts,
            self.baseConfig.gameDocumentsDir,
        )
        game.Run()

    def EnterWorldQueue(self, queueURL):
        self.worldQueue = JoinWorldQueue(
            self.worldQueueConfig.worldQueueParam,
            self.accNumber,
            self.account.ticket,
            queueURL,
            self.worldQueueConfig.worldQueueURL,
        )

        if self.worldQueue.joinSuccess:
            self.AddLog("Joined world queue")

            displayQueueing = True

            while (
                self.worldQueue.number > self.worldQueue.serving
                and self.worldQueue.joinSuccess
            ):
                if displayQueueing:
                    self.AddLog("Currently queueing, please wait...")
                    displayQueueing = False

                self.worldQueue = JoinWorldQueue(
                    self.worldQueueConfig.worldQueueParam,
                    self.accNumber,
                    self.account.ticket,
                    queueURL,
                    self.worldQueueConfig.worldQueueURL,
                )

                if not self.worldQueue.joinSuccess:
                    self.AddLog("[E10] Error getting world status.")

        if self.worldQueue.joinSuccess:
            self.LaunchGame()
        else:
            self.AddLog("[E11] Error joining world queue.")

    def checkForUpdate(self):
        """Notifies user if their copy of OneLauncher is out of date"""
        current_version = parse_version(OneLauncher.__version__)
        repository_url = OneLauncher.__project_url__
        if "github.com" not in repository_url.lower():
            self.logger.warning(
                "Repository URL set in Information.py is not "
                "at github.com. The system for update notifications"
                " only supports this site."
            )
            return

        latest_release_template = (
            "https://api.github.com/repos/{user_and_repo}/releases/latest"
        )
        latest_release_url = latest_release_template.format(
            user_and_repo=repository_url.lower().split("github.com")[
                1].strip("/")
        )

        try:
            with urllib.request.urlopen(latest_release_url, timeout=2) as response:
                release_dictionary = jsonLoads(response.read())
        except (urllib.error.URLError, urllib.error.HTTPError) as error:
            self.AddLog(f"[E18] Error checking for {OneLauncher.__title__} updates.")
            self.logger.error(error.reason, exc_info=True)
            return

        release_version = parse_version(release_dictionary["tag_name"])

        if release_version > current_version:
            url = release_dictionary["html_url"]
            name = release_dictionary["name"]
            description = release_dictionary["body"]

            messageBox = QtWidgets.QMessageBox(self.winMain)
            messageBox.setWindowFlag(QtCore.Qt.FramelessWindowHint)
            messageBox.setIcon(QtWidgets.QMessageBox.Information)
            messageBox.setStandardButtons(messageBox.Ok)

            centered_href = (
                f'<html><head/><body><p align="center"><a href="{url}">'
                f'<span>{name}</span></a></p></body></html>'
            )
            messageBox.setInformativeText(
                f"There is a new version of {OneLauncher.__title__} available! {centered_href}"
            )
            messageBox.setDetailedText(description)
            self.showMessageBoxDetailsAsMarkdown(messageBox)
            messageBox.show()
        else:
            self.AddLog(f"{OneLauncher.__title__} is up to date.")

    def showMessageBoxDetailsAsMarkdown(self, messageBox: QtWidgets.QMessageBox):
        """Makes the detailed text of messageBox display in Markdown format"""
        button_box = messageBox.findChild(
            QtWidgets.QDialogButtonBox, "qt_msgbox_buttonbox"
        )
        for button in button_box.buttons():
            if (
                messageBox.buttonRole(
                    button) == QtWidgets.QMessageBox.ActionRole
                and button.text() == "Show Details..."
            ):
                button.click()
                detailed_text_widget = messageBox.findChild(
                    QtWidgets.QTextEdit)
                detailed_text_widget.setMarkdown(messageBox.detailedText())
                button.click()
                return

    def getLaunchArgument(self, key: str, accepted_values: List[str]):
        launch_arguments = sys.argv
        try:
            modifier_index = launch_arguments.index(key)
        except ValueError:
            pass
        else:
            try:
                value = launch_arguments[modifier_index + 1]
            except IndexError:
                pass
            else:
                if value in accepted_values:
                    return value

    def InitialSetup(self, first_setup=False):
        self.winMain.cboAccount.setEnabled(False)
        self.winMain.txtPassword.setEnabled(False)
        self.winMain.btnLogin.setEnabled(False)
        self.winMain.chkSaveSettings.setEnabled(False)
        self.winMain.chkSavePassword.setEnabled(False)
        self.winMain.btnOptions.setEnabled(False)
        self.winMain.btnSwitchGame.setEnabled(False)

        if self.settings is None:
            self.settings = Settings.Settings()

        self.winMain.cboAccount.clear()
        self.winMain.cboAccount.setCurrentText("")
        self.winMain.txtPassword.setText("")
        self.winMain.cboWorld.clear()
        self.ClearLog()
        self.ClearNews()

        self.logger = Logger(
            Path(Settings.platform_dirs.user_log_dir), "main").logger

        if first_setup:
            self.checkForUpdate()

            # Launch into specific game if specified in launch argument
            game = self.getLaunchArgument("--game",
                                          ["LOTRO", "LOTRO.Test", "DDO", "DDO.Test"])
            if game:
                self.currentGame = game

        sslContext = checkForCertificates(self.logger, self.data_folder)

        # Set news feed to say "Loading ..." until it is replaced by the news.
        self.winMain.txtFeed.setHtml(
            '<html><body><p style="text-align:center;">Loading ...</p></body></html>'
        )

        self.AddLog("Initializing, please wait...")

        settings_load_success = self.settings.load_game_settings(
            self.currentGame)
        # Prints error message from settings if present.
        if settings_load_success and settings_load_success is not True:
            self.AddLog(settings_load_success)
        elif not settings_load_success:
            # Checks if the user is running OneLauncher for the first time
            #  and calls the setup Wizard
            if not self.settings.settingsFile.exists():
                self.logger.debug("First run/no settings file found")
                self.settingsWizardCalled()

                if not self.settings.settingsFile.exists():
                    self.AddLog(
                        "[E17] Settings file does not exist. Please "
                        "restart the program to access setup wizard."
                    )

                return False
            else:
                self.AddLog("[E01] Error loading settings")
        else:
            if self.settings.focusAccount:
                self.winMain.cboAccount.setFocus()
                self.winMain.chkSaveSettings.setChecked(False)
            else:
                self.loadAllSavedAccounts()
                if self.settings.accountsDictionary:
                    self.winMain.cboAccount.setCurrentText(
                        list(self.settings.accountsDictionary.keys())[-1]
                    )
                    self.winMain.chkSaveSettings.setChecked(True)

                    self.winMain.chkSavePassword.setChecked(False)

                    self.setCurrentAccountPassword()

        # Set specific client language if specified in launch argument
        # This is an advanced feature, so there are no checks to make
        # sure the specified language is installed. The game will
        # give an error if that is the case anyways.
        language = self.getLaunchArgument("--language", ["EN", "DE", "FR"])
        if language:
            self.settings.language = language

        self.gameType.GetSettings(self.settings.currentGame)

        pngFile = self.data_folder/self.gameType.pngFile
        iconFile = self.data_folder/self.gameType.iconFile

        self.winMain.imgMain.setPixmap(QtGui.QPixmap(str(pngFile)))
        self.setWindowTitle(self.gameType.title)
        self.setWindowIcon(QtGui.QIcon(str(iconFile)))

        # Configure btnSwitchGame for current game
        self.configureBtnSwitchGameForGame(self.settings.currentGame)

        self.configFile = self.settings.gameDir/self.gameType.configFile
        self.configFileAlt = self.settings.gameDir/self.gameType.configFileAlt

        if not self.settings.gameDir.exists():
            self.AddLog("[E13] Game Directory not found")

        self.configThread = MainWindowThread()
        self.configThread.SetUp(
            self.settings,
            self.configFile,
            self.configFileAlt,
            self.ReturnLog,
            self.ReturnBaseConfig,
            self.ReturnGLSDataCenter,
            self.ReturnWorldQueueConfig,
            self.ReturnNews,
            sslContext,
        )
        self.configThread.start()

    def GetBaseConfig(self, baseConfig):
        self.baseConfig = baseConfig

    def GetGLSDataCenter(self, dataCenter):
        self.dataCenter = dataCenter

        for world in self.dataCenter.worldList:
            self.winMain.cboWorld.addItem(world.name)

        self.setCurrentAccountWorld()

    def GetWorldQueueConfig(self, worldQueueConfig):
        self.worldQueueConfig = worldQueueConfig

        self.winMain.actionPatch.setEnabled(True)
        self.winMain.actionPatch.setVisible(True)
        self.winMain.btnLogin.setEnabled(True)
        self.winMain.chkSaveSettings.setEnabled(True)
        self.winMain.chkSavePassword.setEnabled(True)
        self.winMain.cboAccount.setEnabled(True)
        self.winMain.txtPassword.setEnabled(True)

        if self.settings.focusAccount:
            self.winMain.cboAccount.setFocus()
            self.winMain.chkSaveSettings.setChecked(False)
        else:
            if self.settings.accountsDictionary:
                self.winMain.cboAccount.setCurrentText(
                    list(self.settings.accountsDictionary.keys())[-1]
                )
                self.winMain.chkSaveSettings.setChecked(True)
                if not self.winMain.chkSavePassword.isChecked():
                    self.winMain.txtPassword.setFocus()

    def GetNews(self, news):
        self.winMain.txtFeed.setHtml(news)

        self.configThreadFinished()

    def ClearLog(self):
        self.winMain.txtStatus.setText("")

    def ClearNews(self):
        self.winMain.txtFeed.setText("")

    def AddLog(self, message):
        for line in message.splitlines():
            # Make line red if it is an error
            if line.startswith("[E"):
                self.logger.error(line)

                line = '<font color="red">' + message + "</font>"

                # Enable buttons that won't normally get re-enabled if MainWindowThread gets frozen.
                self.winMain.btnOptions.setEnabled(True)
                self.winMain.btnSwitchGame.setEnabled(True)
            else:
                self.logger.info(line)

            self.winMain.txtStatus.append(line)

    def configThreadFinished(self):
        self.winMain.btnOptions.setEnabled(True)
        self.winMain.btnSwitchGame.setEnabled(True)


class MainWindowThread(QtCore.QThread):
    def SetUp(
        self,
        settings,
        configFile: Path,
        configFileAlt,
        ReturnLog,
        ReturnBaseConfig,
        ReturnGLSDataCenter,
        ReturnWorldQueueConfig,
        ReturnNews,
        sslContext,
    ):

        self.settings = settings
        self.configFile = configFile
        self.configFileAlt = configFileAlt

        self.ReturnLog = ReturnLog
        self.ReturnBaseConfig = ReturnBaseConfig
        self.ReturnGLSDataCenter = ReturnGLSDataCenter
        self.ReturnWorldQueueConfig = ReturnWorldQueueConfig
        self.ReturnNews = ReturnNews
        self.sslContext = sslContext

        self.logger = logging.getLogger("main")

    def run(self):
        self.LoadLanguageList()

    def LoadLanguageList(self):
        if self.settings.gameDir.exists():
            langConfig = LanguageConfig(self.settings.gameDir)

            if langConfig.langFound:
                # Set language to first one detected if none are configured yet
                if not self.settings.language:
                    self.settings.language = langConfig.langList[0]

                self.ReturnLog.emit("Available languages checked.")

                self.LoadLauncherConfig()
            else:
                self.ReturnLog.emit("[E02] No language files found.")

    def LoadLauncherConfig(self):
        self.baseConfig = BaseConfig(self.configFile)

        if self.baseConfig.isConfigOK:
            self.ReturnBaseConfig.emit(self.baseConfig)

            self.AccessGLSDataCenter(
                self.baseConfig.GLSDataCenterService, self.baseConfig.gameName
            )
        else:
            self.baseConfig = BaseConfig(self.configFileAlt)

            if self.baseConfig.isConfigOK:
                self.ReturnBaseConfig.emit(self.baseConfig)

                self.AccessGLSDataCenter(
                    self.baseConfig.GLSDataCenterService,
                    self.baseConfig.gameName,
                )
            else:
                self.ReturnLog.emit(
                    "[E03] Error reading launcher configuration file.")

    def AccessGLSDataCenter(self, urlGLS, gameName):
        self.dataCenter = GLSDataCenter(
            urlGLS, gameName)

        if self.dataCenter.loadSuccess:
            self.ReturnLog.emit("Fetched details from GLS data center.")
            self.ReturnGLSDataCenter.emit(self.dataCenter)
            self.ReturnLog.emit("World list obtained.")

            self.GetWorldQueueConfig(self.dataCenter.launchConfigServer)
        else:
            self.ReturnLog.emit("[E04] Error accessing GLS data center.")

    def GetWorldQueueConfig(self, urlWorldQueueServer):
        self.worldQueueConfig = WorldQueueConfig(
            urlWorldQueueServer,
            self.settings.gameDir,
            self.settings.client,
        )

        if self.worldQueueConfig.message:
            self.ReturnLog.emit(self.worldQueueConfig.message)

        if self.worldQueueConfig.loadSuccess:
            self.ReturnLog.emit("World queue configuration read.")
            self.ReturnWorldQueueConfig.emit(self.worldQueueConfig)

            self.GetNews()
        else:
            self.ReturnLog.emit(
                "[E05] Error getting world queue configuration.")

    def GetNews(self):
        try:
            with urllib.request.urlopen(self.worldQueueConfig.newsStyleSheetURL, context=self.sslContext) as xml_feed:
                doc = defusedxml.minidom.parseString(
                    xml_feed.read(), forbid_entities=False)

            nodes = doc.getElementsByTagName("div")
            for node in nodes:
                if node.nodeType == node.ELEMENT_NODE and (
                    node.attributes.item(0).firstChild.nodeValue
                    == "launcherNewsItemDate"
                ):
                    timeCode = GetText(node.childNodes).strip()
                    timeCode = (
                        timeCode.replace("\t", "").replace(
                            ",", "").replace("-", "")
                    )
                    if len(timeCode) > 0:
                        timeCode = " %s" % (timeCode)

            links = doc.getElementsByTagName("link")
            for link in links:
                if link.nodeType == link.ELEMENT_NODE:
                    href = link.attributes["href"]

            # Ignore broken href (as of 3/30/16) in the style sheet and use Launcher.
            # NewsFeedCSSUrl defined in launcher.config
            href.value = self.worldQueueConfig.newsFeedCSSURL

            HTMLTEMPLATE = '<html><head><link rel="stylesheet" type="text/css" href="'
            HTMLTEMPLATE += href.value
            HTMLTEMPLATE += (
                '"/><base target="_blank"/></head><body><div '
                'class="launcherNewsItemsContainer" style="width:auto">'
            )

            # DDO test client doesn't provide a news feed, so one from the forums is used.
            if self.settings.currentGame == "DDO.Test":
                urlNewsFeed = (
                    "https://www.ddo.com/forums/external.php?type=RSS2&forumids=266"
                )
            else:
                urlNewsFeed = self.worldQueueConfig.newsFeedURL.replace(
                    "{lang}", self.settings.language.lower()
                )

            result = HTMLTEMPLATE

            with urllib.request.urlopen(urlNewsFeed, context=self.sslContext) as xml_feed:
                doc = defusedxml.minidom.parseString(xml_feed.read())

            items = doc.getElementsByTagName("item")
            for item in items:
                title = ""
                description = ""
                date = ""

                for node in item.childNodes:
                    if node.nodeType == node.ELEMENT_NODE:
                        if node.nodeName == "title":
                            title = (
                                '<font color="gold"><div class="launcherNewsItemTitle">%s</div></font>'
                                % (GetText(node.childNodes))
                            )
                        elif node.nodeName == "description":
                            description = (
                                '<div class="launcherNewsItemDescription">%s</div>'
                                % (GetText(node.childNodes))
                            )
                        elif node.nodeName == "pubDate":
                            tempDate = GetText(node.childNodes)
                            dispDate = "%s %s %s %s%s" % (
                                tempDate[8:11],
                                tempDate[5:7],
                                tempDate[12:16],
                                tempDate[17:22],
                                timeCode,
                            )
                            date = (
                                '<small><i><div align="right"class="launcherNewsItemDate">%s</div></i></small>'
                                % (dispDate)
                            )

                result += '<div class="launcherNewsItemContainer">%s%s%s%s</div>' % (
                    title,
                    date,
                    description,
                    "<hr>",
                )

            result += "</div></body></html>"

            self.ReturnNews.emit(result)
        except Exception as error:
            self.ReturnLog.emit("[E12] Error getting news")
            self.logger.warning(error)
