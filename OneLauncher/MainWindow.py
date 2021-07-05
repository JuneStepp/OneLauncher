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
import sys
from typing import List
import defusedxml.minidom
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtUiTools import QUiLoader
from OneLauncher.SettingsWindow import SettingsWindow
from OneLauncher.AddonManager import AddonManager
from OneLauncher.SetupWizard import SetupWizard
from OneLauncher.PatchWindow import PatchWindow
from OneLauncher.StartGame import StartGame
from OneLauncher.Settings import Settings
from OneLauncher.WinePrefix import BuiltInPrefix
from OneLauncher.OneLauncherUtils import (
    checkForCertificates,
    DetermineOS,
    DetermineGame,
    LanguageConfig,
    BaseConfig,
    GLSDataCenter,
    WorldQueueConfig,
    AuthenticateUser,
    JoinWorldQueue,
    GetText,
)
from OneLauncher import Information
from pkg_resources import parse_version
import keyring
import logging
from logging.handlers import RotatingFileHandler
from platform import platform
import urllib

# For setting global timeout used by urllib
import socket
from json import loads as jsonLoads


class MainWindow(QtWidgets.QMainWindow):
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_ShareOpenGLContexts)
    app = QtWidgets.QApplication(sys.argv)

    ReturnLog = QtCore.Signal(str)
    ReturnBaseConfig = QtCore.Signal(BaseConfig)
    ReturnGLSDataCenter = QtCore.Signal(BaseConfig)
    ReturnWorldQueueConfig = QtCore.Signal(BaseConfig)
    ReturnNews = QtCore.Signal(str)

    def __init__(self):
        super().__init__()
        if getattr(sys, "frozen", False):
            # The application is frozen
            self.data_folder = os.path.dirname(sys.executable)
        else:
            self.data_folder = os.path.dirname(__file__)

        # Set default timeout used by urllib
        socket.setdefaulttimeout(6)

        ui_file = QtCore.QFile(os.path.join(self.data_folder, "ui", "winMain.ui"))

        # Create the main window and set all text so that translations are handled via gettext
        ui_file.open(QtCore.QFile.ReadOnly)
        loader = QUiLoader()
        self.winMain = loader.load(ui_file, parentWidget=self)
        ui_file.close()
        self.winMain.setWindowFlags(QtCore.Qt.Dialog)
        self.winMain.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setFixedSize(790, 470)

        # Set font size explicitly to stop OS text size options from
        # breaking the UI.
        font = QtGui.QFont()
        font.setPointSize(10)
        self.app.setFont(font)

        # center window on screen
        self.center()

        # Sets some widgets to WA_NoMousePropagation to avoid window dragging issues
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

        # Connect signals to functions
        self.winMain.btnLogin.clicked.connect(self.btnLoginClicked)
        self.winMain.cboAccount.textActivated.connect(self.cboAccountChanged)
        self.winMain.txtPassword.returnPressed.connect(self.txtPasswordEnter)
        self.winMain.btnExit.clicked.connect(self.close)
        self.winMain.btnMinimize.clicked.connect(self.showMinimized)
        self.winMain.btnAbout.clicked.connect(self.btnAboutSelected)
        self.winMain.btnLoginMenu = QtWidgets.QMenu()
        self.winMain.btnLoginMenu.addAction(self.winMain.actionPatch)
        self.winMain.actionPatch.triggered.connect(self.actionPatchSelected)
        self.winMain.btnLogin.setMenu(self.winMain.btnLoginMenu)
        self.winMain.btnOptions.setIcon(
            QtGui.QIcon(os.path.join(self.data_folder, "images", "SettingsGear.png"))
        )
        self.winMain.btnOptions.clicked.connect(self.btnOptionsSelected)
        self.winMain.btnAddonManager.setIcon(
            QtGui.QIcon(os.path.join(self.data_folder, "images", "AddonManager.png"))
        )
        self.winMain.btnAddonManager.clicked.connect(self.btnAddonManagerSelected)
        self.winMain.btnSwitchGame.clicked.connect(self.btnSwitchGameClicked)
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

        # Disable login and save settings buttons
        self.winMain.btnLogin.setEnabled(False)
        self.winMain.chkSaveSettings.setEnabled(False)

        # Initialise variables
        self.settings = None
        self.osType = DetermineOS()
        self.gameType = DetermineGame()
        self.configFile = ""
        self.currentGame = None

        self.configureKeyring()

        self.InitialSetup(first_setup=True)

    def run(self):
        self.show()
        sys.exit(self.app.exec_())

    def resetFocus(self):
        if self.winMain.cboAccount.currentText() == "":
            self.winMain.cboAccount.setFocus()
        elif self.winMain.txtPassword.text() == "":
            self.winMain.txtPassword.setFocus()

    def center(self):
        qr = self.frameGeometry()
        cp = self.app.primaryScreen().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def mousePressEvent(self, event):
        """Lets the user drag the window when left-click holding it"""
        if event.button() == QtCore.Qt.LeftButton:
            self.windowHandle().startSystemMove()
            event.accept()

    def configureKeyring(self):
        """
        Sets the propper keyring backend for the used OS. This isn't
        automatically detected correctly with Nuitka
        """
        if self.osType.usingWindows:
            from keyring.backends import Windows
            keyring.set_keyring(Windows.WinVaultKeyring())
        elif self.osType.usingMac:
            from keyring.backends import OS_X
            keyring.set_keyring(OS_X.Keyring())
        else:
            from keyring.backends import SecretService
            keyring.set_keyring(SecretService.Keyring())

    def btnAboutSelected(self):
        ui_file = QtCore.QFile(os.path.join(self.data_folder, "ui", "winAbout.ui"))

        ui_file.open(QtCore.QFile.ReadOnly)
        loader = QUiLoader()
        dlgAbout = loader.load(ui_file, parentWidget=self)
        ui_file.close()

        dlgAbout.setWindowFlags(QtCore.Qt.Popup)

        dlgAbout.lblDescription.setText(Information.LongDescription)
        dlgAbout.lblRepoWebsite.setText(Information.RepoWebsite)
        dlgAbout.lblCopyright.setText(Information.Copyright)
        dlgAbout.lblVersion.setText("<b>Version:</b> " + Information.Version)
        dlgAbout.lblPyLotROReference.setText(Information.PyLotROReference)
        dlgAbout.lblCLIReference.setText(Information.CLIReference)
        dlgAbout.lblLotROLinuxReference.setText(Information.LotROLinuxReference)

        dlgAbout.exec_()
        self.resetFocus()

    def manageBuiltInPrefix(self):
        # Only manage prefix if prefix management is enabled and the program is on Linux or Mac
        if not self.settings.builtInPrefixEnabled or self.osType.usingWindows:
            return True

        winBuiltInPrefix = BuiltInPrefix(
            self.settings.settingsDir,
            self.settings.winePrefix,
            self.osType.documentsDir,
            self,
        )

        wineProg = winBuiltInPrefix.Run()
        if wineProg:
            self.settings.wineProg = wineProg
            self.settings.SaveSettings(
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
                self.settings.hiResEnabled,
                self.gameType.iconFile,
                self.valHomeDir,
                self.settings.winePrefix,
                self.settings.wineDebug,
                self.osType,
                self,
                self.data_folder,
                self.settings.currentGame,
                self.baseConfig.gameDocumentsDir,
            )

            winPatch.Run(self.app)
            self.resetFocus()

    def btnOptionsSelected(self):
        winSettings = SettingsWindow(
            self.settings.hiResEnabled,
            self.settings.wineProg,
            self.settings.wineDebug,
            self.settings.patchClient,
            self.settings.winePrefix,
            self.settings.gameDir,
            self.valHomeDir,
            self.osType,
            self.settings,
            LanguageConfig,
            self,
            self.data_folder,
        )

        if winSettings.Run() == QtWidgets.QDialog.Accepted:
            self.settings.hiResEnabled = winSettings.getHiRes()
            self.settings.client = winSettings.getClient()
            self.settings.patchClient = winSettings.getPatchClient()
            self.settings.gameDir = winSettings.getGameDir()
            if winSettings.getLanguage():
                self.settings.language = winSettings.getLanguage()

            if not self.osType.usingWindows:
                self.settings.wineProg = winSettings.getProg()
                self.settings.wineDebug = winSettings.getDebug()
                self.settings.winePrefix = winSettings.getPrefix()

            self.settings.SaveSettings(
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
            self.osType,
            self.settings.settingsDir,
            self,
            self.data_folder,
            self.baseConfig.gameDocumentsDir,
            self.settings.startupScripts,
        )

        winAddonManager.Run()
        self.settings.SaveSettings(
            saveAccountDetails=self.winMain.chkSaveSettings.isChecked(),
            savePassword=self.winMain.chkSavePassword.isChecked(),
        )

        self.resetFocus()

    def settingsWizardCalled(self):
        winWizard = SetupWizard(self.valHomeDir, self.osType, self.data_folder, self.app)
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
                        self.settings.hiResEnabled = winWizard.getHiRes(
                            self.settings.gameDir
                        )
                        self.settings.winePrefix = ""
                        self.settings.SaveSettings(game=game)

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
                        "OneLauncherDDO",
                        self.winMain.cboAccount.currentText(),
                    )
                )
            else:
                self.winMain.txtPassword.setText(
                    keyring.get_password(
                        "OneLauncherLOTRO",
                        self.winMain.cboAccount.currentText(),
                    )
                )
        else:
            self.winMain.txtPassword.setFocus()

    def txtPasswordEnter(self):
        self.btnLoginClicked()

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
            self.valHomeDir,
            self.osType,
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

                self.settings.SaveSettings(
                    saveAccountDetails=self.winMain.chkSaveSettings.isChecked(),
                    savePassword=self.winMain.chkSavePassword.isChecked(),
                )

                if self.winMain.chkSavePassword.isChecked():
                    if self.settings.currentGame.startswith("DDO"):
                        keyring.set_password(
                            "OneLauncherDDO",
                            self.winMain.cboAccount.currentText(),
                            self.winMain.txtPassword.text(),
                        )
                    else:
                        keyring.set_password(
                            "OneLauncherLOTRO",
                            self.winMain.cboAccount.currentText(),
                            self.winMain.txtPassword.text(),
                        )
                else:
                    try:
                        if self.settings.currentGame.startswith("DDO"):
                            keyring.delete_password(
                                "OneLauncherDDO",
                                self.winMain.cboAccount.currentText(),
                            )
                        else:
                            keyring.delete_password(
                                "OneLauncherLOTRO",
                                self.winMain.cboAccount.currentText(),
                            )
                    except keyring.errors.PasswordDeleteError:
                        pass

            tempWorld = ""

            if len(self.account.gameList) > 1:
                ui_file = QtCore.QFile(
                    os.path.join(self.data_folder, "ui", "winSelectAccount.ui")
                )

                ui_file.open(QtCore.QFile.ReadOnly)
                loader = QUiLoader()
                dlgChooseAccount = loader.load(ui_file, parentWidget=self)
                ui_file.close()

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

            tempWorld = self.dataCenter.worldList[self.winMain.cboWorld.currentIndex()]
            tempWorld.CheckWorld(self.valHomeDir, self.osType)

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
            self.settings.hiResEnabled,
            self.settings.builtInPrefixEnabled,
            self.osType,
            self.valHomeDir,
            self.gameType.iconFile,
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
            self.valHomeDir,
            self.osType,
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
                    self.valHomeDir,
                    self.osType,
                )

                if not self.worldQueue.joinSuccess:
                    self.AddLog("[E10] Error getting world status.")

        if self.worldQueue.joinSuccess:
            self.LaunchGame()
        else:
            self.AddLog("[E11] Error joining world queue.")

    def setupLogging(self):
        if not os.path.exists(self.settings.settingsDir):
            os.mkdir(self.settings.settingsDir)
        # Create or get custom logger
        self.logger = logging.getLogger("OneLauncher")

        # If logger has not already been setup
        if not self.logger.hasHandlers():
            # This is for the logger globally. Different handlers
            # attached to it have their own levels.
            self.logger.setLevel(logging.DEBUG)

            # Create handlers
            stream_handler = logging.StreamHandler()
            stream_handler.setLevel(logging.WARNING)

            log_file = os.path.join(self.settings.settingsDir, "OneLauncher.log")
            file_handler = RotatingFileHandler(
                log_file,
                mode="a",
                maxBytes=10 * 1024 * 1024,
                backupCount=2,
                encoding=None,
                delay=0,
            )
            # Only log all information on dev builds
            if Information.Version.endswith("Dev"):
                file_handler.setLevel(logging.DEBUG)
            else:
                file_handler.setLevel(logging.ERROR)

            # Create formatters and add it to handlers
            stream_format = logging.Formatter(
                "%(module)s - %(levelname)s - %(message)s"
            )
            stream_handler.setFormatter(stream_format)
            file_format = logging.Formatter(
                "%(asctime)s - %(module)s - %(levelname)s - %(lineno)d - %(message)s"
            )
            file_handler.setFormatter(file_format)

            # Add handlers to the logger
            self.logger.addHandler(stream_handler)
            self.logger.addHandler(file_handler)

            self.logger.info("Logging started")
            self.logger.info("OneLauncher: " + Information.Version)
            self.logger.info(platform())

            # Setup handling of uncaught exceptions
            sys.excepthook = self.handleUncaughtExceptions

            # Setup Qt event logging
            self.ignored_qt_events = [
                QtCore.QEvent.HoverMove,
                QtCore.QEvent.MouseMove,
                QtCore.QEvent.Paint,
                QtCore.QEvent.UpdateRequest,
                QtCore.QEvent.UpdateLater,
                QtCore.QEvent.ChildAdded,
                QtCore.QEvent.ChildRemoved,
                QtCore.QEvent.ParentChange,
                QtCore.QEvent.PaletteChange,
                QtCore.QEvent.DynamicPropertyChange,
                QtCore.QEvent.FocusIn,
                QtCore.QEvent.FocusOut,
                QtCore.QEvent.FocusAboutToChange,
                QtCore.QEvent.Move,
                QtCore.QEvent.Resize,
                QtCore.QEvent.Polish,
                QtCore.QEvent.PolishRequest,
                QtCore.QEvent.ChildPolished,
                QtCore.QEvent.ShowToParent,
                QtCore.QEvent.Timer,
                QtCore.QEvent.ActivationChange,
                QtCore.QEvent.WindowDeactivate,
                QtCore.QEvent.WindowActivate,
                QtCore.QEvent.ApplicationStateChange,
                QtCore.QEvent.CursorChange,
                QtCore.QEvent.MetaCall,
                QtCore.QEvent.LayoutRequest,
                QtCore.QEvent.Enter,
                QtCore.QEvent.HoverEnter,
                QtCore.QEvent.Leave,
                QtCore.QEvent.HoverLeave,
                QtCore.QEvent.StyleChange,
                QtCore.QEvent.FontChange,
                QtCore.QEvent.ContentsRectChange,
                QtCore.QEvent.Create,
                QtCore.QEvent.Wheel,
            ]
            self.app.installEventFilter(self)

    def handleUncaughtExceptions(self, exc_type, exc_value, exc_traceback):
        """Handler for uncaught exceptions that will write to the logs"""
        if issubclass(exc_type, KeyboardInterrupt):
            # call the default excepthook saved at __excepthook__
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        self.logger.critical(
            "Uncaught exception:", exc_info=(exc_type, exc_value, exc_traceback)
        )

    def eventFilter(self, q_object, event):
        """Logs Qt events not in self.ignored_qt_events"""
        if event.type() not in self.ignored_qt_events:
            self.logger.debug(str(event.type()) + " : " + q_object.objectName())

        # standard event processing
        return QtCore.QObject.eventFilter(self, q_object, event)

    def checkForUpdate(self):
        """Notifies user if their copy of OneLauncher is out of date"""
        current_version = parse_version(Information.Version)
        repository_url = Information.repoUrl
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
            user_and_repo=repository_url.lower().split("github.com")[1].strip("/")
        )

        try:
            with urllib.request.urlopen(latest_release_url, timeout=2) as response:
                release_dictionary = jsonLoads(response.read())
        except (urllib.error.URLError, urllib.error.HTTPError) as error:
            self.AddLog("[E18] Error checking for OneLauncher updates.")
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
                f"There is a new version of OneLauncher available! {centered_href}"
            )
            messageBox.setDetailedText(description)
            self.showMessageBoxDetailsAsMarkdown(messageBox)
            messageBox.show()
        else:
            self.AddLog("OneLauncher is up to date.")

    def showMessageBoxDetailsAsMarkdown(self, messageBox: QtWidgets.QMessageBox):
        """Makes the detailed text of messageBox display in Markdown format"""
        button_box = messageBox.findChild(
            QtWidgets.QDialogButtonBox, "qt_msgbox_buttonbox"
        )
        for button in button_box.buttons():
            if (
                messageBox.buttonRole(button) == QtWidgets.QMessageBox.ActionRole
                and button.text() == "Show Details..."
            ):
                button.click()
                detailed_text_widget = messageBox.findChild(QtWidgets.QTextEdit)
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
        self.gameDirExists = False
        self.winMain.cboAccount.setEnabled(False)
        self.winMain.txtPassword.setEnabled(False)
        self.winMain.btnLogin.setEnabled(False)
        self.winMain.chkSaveSettings.setEnabled(False)
        self.winMain.chkSavePassword.setEnabled(False)
        self.winMain.btnOptions.setEnabled(False)
        self.winMain.btnSwitchGame.setEnabled(False)
        self.valHomeDir = self.GetConfigDir()

        if self.settings is None:
            self.settings = Settings(self.valHomeDir, self.osType)

        self.winMain.cboAccount.clear()
        self.winMain.cboAccount.setCurrentText("")
        self.winMain.txtPassword.setText("")
        self.winMain.cboWorld.clear()
        self.ClearLog()
        self.ClearNews()

        self.setupLogging()

        if first_setup:
            self.checkForUpdate()

            # Launch into specific game if specified in launch argument
            game = self.getLaunchArgument("--game",
                    ["LOTRO", "LOTRO.Test", "DDO", "DDO.Test"])
            if game:
                self.currentGame = game

        sslContext = checkForCertificates(self.logger)

        # Set news feed to say "Loading ..." until it is replaced by the news.
        self.winMain.txtFeed.setHtml(
            '<html><body><p style="text-align:center;">Loading ...</p></body></html>'
        )

        self.AddLog("Initializing, please wait...")

        settings_load_success = self.settings.LoadSettings(self.currentGame)
        # Prints error message from settings if present.
        if settings_load_success and settings_load_success is not True:
            self.AddLog(settings_load_success)
        elif not settings_load_success:
            # Checks if the user is running OneLauncher for the first time
            #  and calls the setup Wizard
            if not os.path.exists(self.settings.settingsFile):
                self.logger.debug("First run/no settings file found")
                self.settingsWizardCalled()

                if not os.path.exists(self.settings.settingsFile):
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

        pngFile = os.path.join(
            self.data_folder, self.gameType.pngFile.replace("\\", "/")
        )
        iconFile = os.path.join(
            self.data_folder, self.gameType.iconFile.replace("\\", "/")
        )

        self.winMain.imgMain.setPixmap(QtGui.QPixmap(pngFile))
        self.setWindowTitle(self.gameType.title)
        self.setWindowIcon(QtGui.QIcon(iconFile))

        # Set icon and dropdown options of switch game button according to game running
        if self.settings.currentGame == "DDO":
            self.winMain.btnSwitchGame.setIcon(
                QtGui.QIcon(
                    os.path.join(self.data_folder, "images", "LOTROSwitchIcon.png")
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
        elif self.settings.currentGame == "DDO.Test":
            self.winMain.btnSwitchGame.setIcon(
                QtGui.QIcon(
                    os.path.join(self.data_folder, "images", "LOTROSwitchIcon.png")
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
        elif self.settings.currentGame == "LOTRO.Test":
            self.winMain.btnSwitchGame.setIcon(
                QtGui.QIcon(
                    os.path.join(self.data_folder, "images", "DDOSwitchIcon.png")
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
                    os.path.join(self.data_folder, "images", "DDOSwitchIcon.png")
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

        self.configFile = "%s%s" % (
            self.settings.gameDir,
            self.gameType.configFile,
        )
        self.configFileAlt = "%s%s" % (
            self.settings.gameDir,
            self.gameType.configFileAlt,
        )
        self.gameDirExists = os.path.exists(self.settings.gameDir)

        if not self.gameDirExists:
            self.AddLog("[E13] Game Directory not found")

        self.configThread = MainWindowThread()
        self.configThread.SetUp(
            self.settings,
            self.configFile,
            self.configFileAlt,
            self.valHomeDir,
            self.osType,
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

    def GetConfigDir(self):
        if self.osType.usingWindows:
            config_dir = os.environ.get("APPDATA")
        else:
            config_dir = os.environ.get("HOME")

        if not config_dir.endswith(os.sep):
            config_dir += os.sep

        return config_dir

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
        configFile,
        configFileAlt,
        baseDir,
        osType,
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
        self.osType = osType
        self.baseDir = baseDir

        self.ReturnLog = ReturnLog
        self.ReturnBaseConfig = ReturnBaseConfig
        self.ReturnGLSDataCenter = ReturnGLSDataCenter
        self.ReturnWorldQueueConfig = ReturnWorldQueueConfig
        self.ReturnNews = ReturnNews
        self.sslContext = sslContext

        self.logger = logging.getLogger("OneLauncher")

    def run(self):
        self.LoadLanguageList()

    def LoadLanguageList(self):
        if os.path.exists(self.settings.gameDir):
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
                self.ReturnLog.emit("[E03] Error reading launcher configuration file.")

    def AccessGLSDataCenter(self, urlGLS, gameName):
        self.dataCenter = GLSDataCenter(urlGLS, gameName, self.baseDir, self.osType)

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
            self.baseDir,
            self.osType,
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
            self.ReturnLog.emit("[E05] Error getting world queue configuration.")

    def GetNews(self):
        try:
            with urllib.request.urlopen(self.worldQueueConfig.newsStyleSheetURL, context=self.sslContext) as xml_feed:
                doc = defusedxml.minidom.parseString(xml_feed.read(), forbid_entities=False)

            nodes = doc.getElementsByTagName("div")
            for node in nodes:
                if node.nodeType == node.ELEMENT_NODE and (
                    node.attributes.item(0).firstChild.nodeValue
                    == "launcherNewsItemDate"
                ):
                    timeCode = GetText(node.childNodes).strip()
                    timeCode = (
                        timeCode.replace("\t", "").replace(",", "").replace("-", "")
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
