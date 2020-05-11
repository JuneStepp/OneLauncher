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
# (C) 2019-2020 June Stepp <git@junestepp.me>
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
import defusedxml.minidom
import zlib
from PySide2 import QtCore, QtGui, QtWidgets
from PySide2.QtUiTools import QUiLoader
import qdarkstyle
from .SettingsWindow import SettingsWindow
from .AddonManager import AddonManager
from .SetupWizard import SetupWizard
from .PatchWindow import PatchWindow
from .StartGame import StartGame
from .Settings import Settings
from .WinePrefix import BuiltInPrefix
from .OneLauncherUtils import DetermineOS, DetermineGame, LanguageConfig
from .OneLauncherUtils import BaseConfig, GLSDataCentre, WorldQueueConfig
from .OneLauncherUtils import (
    AuthenticateUser,
    JoinWorldQueue,
    GetText,
    WebConnection,
)
from . import Information
from pkg_resources import resource_filename
import keyring


class MainWindow(QtWidgets.QMainWindow):
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_ShareOpenGLContexts)
    app = QtWidgets.QApplication(sys.argv)

    ReturnLog = QtCore.Signal(str)
    ReturnBaseConfig = QtCore.Signal(BaseConfig)
    ReturnGLSDataCentre = QtCore.Signal(BaseConfig)
    ReturnWorldQueueConfig = QtCore.Signal(BaseConfig)
    ReturnNews = QtCore.Signal(str)

    def __init__(self):
        super().__init__()
        # Determine where module is located (needed for finding ICO & PNG files)
        try:
            test = sys.frozen
            self.rootDir = os.path.dirname(sys.executable)
        except:
            self.rootDir = __file__.replace("library.zip", "")
            if os.path.islink(self.rootDir):
                self.rootDir = os.path.realpath(self.rootDir)
            self.rootDir = os.path.dirname(os.path.abspath(self.rootDir))

        ui_file = QtCore.QFile(
            resource_filename(__name__, "ui" + os.sep + "winMain.ui")
        )

        # Create the main window and set all text so that translations are handled via gettext
        ui_file.open(QtCore.QFile.ReadOnly)
        loader = QUiLoader()
        self.winMain = loader.load(ui_file, parentWidget=self)
        ui_file.close()
        self.winMain.setWindowFlags(QtCore.Qt.Dialog)
        self.winMain.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setFixedSize(790, 470)

        # Set window style
        self.app.setStyleSheet(qdarkstyle.load_stylesheet_pyside2())

        # Centre window on screen
        self.center()

        self.dragPos = self.pos()

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
            QtGui.QIcon(
                resource_filename(
                    __name__, "images" + os.sep + "SettingsGear.png"
                )
            )
        )
        self.winMain.btnOptions.clicked.connect(self.btnOptionsSelected)
        self.winMain.btnAddonManager.setIcon(
            QtGui.QIcon(
                resource_filename(
                    __name__, "images" + os.sep + "AddonManager.png"
                )
            )
        )
        self.winMain.btnAddonManager.clicked.connect(
            self.btnAddonManagerSelected
        )
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
        self.ReturnGLSDataCentre = self.ReturnGLSDataCentre
        self.ReturnGLSDataCentre.connect(self.GetGLSDataCentre)
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

        self.InitialSetup()

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
        cp = QtWidgets.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    # The two functions below handle dragging the window
    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.dragPosition = (
                event.globalPos() - self.frameGeometry().topLeft()
            )
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == QtCore.Qt.LeftButton:
            self.move(event.globalPos() - self.dragPosition)
            event.accept()

    def btnAboutSelected(self):
        ui_file = QtCore.QFile(
            resource_filename(__name__, "ui" + os.sep + "winAbout.ui")
        )

        ui_file.open(QtCore.QFile.ReadOnly)
        loader = QUiLoader()
        dlgAbout = loader.load(ui_file, parentWidget=self)
        ui_file.close()

        dlgAbout.setWindowFlags(QtCore.Qt.Popup)

        dlgAbout.lblDescription.setText(Information.LongDescription)
        dlgAbout.lblWebsite.setText(Information.Website)
        dlgAbout.lblCopyright.setText(Information.Copyright)
        dlgAbout.lblVersion.setText("<b>Version:</b> " + Information.Version)
        dlgAbout.lblPyLotROReference.setText(Information.PyLotROReference)
        dlgAbout.lblCLIReference.setText(Information.CLIReference)
        dlgAbout.lblLotROLinuxReference.setText(
            Information.LotROLinuxReference
        )

        dlgAbout.exec_()
        self.resetFocus()

    def manageBuiltInPrefix(self):
        if self.settings.builtInPrefixEnabled and not self.osType.usingWindows:
            winBuiltInPrefix = BuiltInPrefix(
                self.settings.settingsDir, self.settings.winePrefix, self
            )

            self.settings.wineProg = winBuiltInPrefix.Run()
            self.settings.SaveSettings(
                saveAccountDetails=self.winMain.chkSaveSettings.isChecked(),
                savePassword=self.winMain.chkSavePassword.isChecked(),
            )

    def actionPatchSelected(self):
        self.manageBuiltInPrefix()

        winPatch = PatchWindow(
            self.dataCentre.patchServer,
            self.worldQueueConfig.patchProductCode,
            self.settings.language,
            self.settings.gameDir,
            self.settings.patchClient,
            self.settings.wineProg,
            self.settings.hiResEnabled,
            self.gameType.iconFile,
            self.valHomeDir,
            self.settings.winePrefix,
            self.osType,
            self.rootDir,
            self,
        )

        winPatch.Run(self.app)
        self.resetFocus()

    def btnOptionsSelected(self):
        winSettings = SettingsWindow(
            self.settings.hiResEnabled,
            self.settings.x86Enabled,
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
        )

        if winSettings.Run() == QtWidgets.QDialog.Accepted:
            self.settings.hiResEnabled = winSettings.getHiRes()
            self.settings.x86Enabled = winSettings.getx86()
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
        )

        winAddonManager.Run()
        self.resetFocus()

    def settingsWizardCalled(self):
        winWizard = SetupWizard(self.valHomeDir, self.osType, self.rootDir)
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
        if self.settings.currentGame == "DDO":
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
            if self.winMain.chkSaveSettings.isChecked():
                current_account = self.winMain.cboAccount.currentText()
                current_world = self.winMain.cboWorld.currentText()

                # Account is deleted first, because accounts are in order of
                # the most recently played at the end.
                try:
                    del self.settings.accountsDictionary[current_account]
                except KeyError:
                    pass

                self.settings.accountsDictionary[current_account] = [
                    current_world
                ]

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
                    except:
                        pass

            self.manageBuiltInPrefix()
            self.AuthAccount()

    def cboAccountChanged(self):
        self.winMain.txtPassword.setFocus()

    def txtPasswordEnter(self):
        self.btnLoginClicked()

    def AuthAccount(self):
        self.AddLog("Checking account details...")

        # Force a small display to ensure message above is displayed
        # as program can look like it is not responding while validating
        for i in range(4):
            self.app.processEvents()

        self.account = AuthenticateUser(
            self.dataCentre.authServer,
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

            tempWorld = ""

            if len(self.account.gameList) > 1:
                ui_file = QtCore.QFile(
                    resource_filename(
                        __name__, "ui" + os.sep + "winSelectAccount.ui"
                    )
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

            tempWorld = self.dataCentre.worldList[
                self.winMain.cboWorld.currentIndex()
            ]
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
            self.settings.x86Enabled,
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
            self.rootDir,
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
        )
        self.hide()
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
            self.AddLog("[E11] Error joining world queue")

    def InitialSetup(self):
        self.gameDirExists = False
        self.winMain.cboAccount.setEnabled(False)
        self.winMain.txtPassword.setEnabled(False)
        self.winMain.btnLogin.setEnabled(False)
        self.winMain.chkSaveSettings.setEnabled(False)
        self.winMain.chkSavePassword.setEnabled(False)
        self.winMain.btnOptions.setEnabled(False)
        self.winMain.btnSwitchGame.setEnabled(False)
        self.valHomeDir = self.GetHomeDir()

        if self.settings is None:
            self.settings = Settings(self.valHomeDir, self.osType)

        self.winMain.cboAccount.clear()
        self.winMain.cboAccount.setCurrentText("")
        self.winMain.txtPassword.setText("")
        self.winMain.cboWorld.clear()
        self.ClearLog()
        self.ClearNews()

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
                self.winMain.cboAccount.setCurrentText(
                    list(self.settings.accountsDictionary.keys())[-1]
                )
                self.winMain.chkSaveSettings.setChecked(True)

                self.winMain.chkSavePassword.setChecked(False)

                if self.settings.savePassword:
                    self.winMain.chkSavePassword.setChecked(True)
                    if self.settings.currentGame.startswith("DDO"):
                        self.winMain.txtPassword.setText(
                            keyring.get_password(
                                "OneLauncherDDO",
                                list(self.settings.accountsDictionary.keys())[
                                    -1
                                ],
                            )
                        )
                    else:
                        self.winMain.txtPassword.setText(
                            keyring.get_password(
                                "OneLauncherLOTRO",
                                list(self.settings.accountsDictionary.keys())[
                                    -1
                                ],
                            )
                        )
                else:
                    self.winMain.txtPassword.setFocus()

        self.gameType.GetSettings(self.settings.currentGame)

        pngFile = resource_filename(
            __name__, self.gameType.pngFile.replace("\\", "/")
        )
        iconFile = resource_filename(
            __name__, self.gameType.iconFile.replace("\\", "/")
        )

        self.winMain.imgMain.setPixmap(QtGui.QPixmap(pngFile))
        self.setWindowTitle(self.gameType.title)
        self.setWindowIcon(QtGui.QIcon(iconFile))

        # Set icon and dropdown options of switch game button according to game running
        if self.settings.currentGame == "DDO":
            self.winMain.btnSwitchGame.setIcon(
                QtGui.QIcon(
                    resource_filename(
                        __name__, "images" + os.sep + "LOTROSwitchIcon.png"
                    )
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
                    resource_filename(
                        __name__, "images" + os.sep + "LOTROSwitchIcon.png"
                    )
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
                    resource_filename(
                        __name__, "images" + os.sep + "DDOSwitchIcon.png"
                    )
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
                    resource_filename(
                        __name__, "images" + os.sep + "DDOSwitchIcon.png"
                    )
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
            self.ReturnGLSDataCentre,
            self.ReturnWorldQueueConfig,
            self.ReturnNews,
        )
        self.configThread.start()

    def GetBaseConfig(self, baseConfig):
        self.baseConfig = baseConfig

    def GetGLSDataCentre(self, dataCentre):
        self.dataCentre = dataCentre

        setPos = 0

        for world in self.dataCentre.worldList:
            self.winMain.cboWorld.addItem(world.name)

            account_world = ""

            accounts = list(self.settings.accountsDictionary.keys())
            if accounts:
                last_account = accounts[-1]
                account_world = self.settings.accountsDictionary[last_account][
                    0
                ]

            if world.name == account_world:
                self.winMain.cboWorld.setCurrentIndex(setPos)

            setPos += 1

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
            self.winMain.cboAccount.setCurrentText(
                list(self.settings.accountsDictionary.keys())[-1]
            )
            self.winMain.chkSaveSettings.setChecked(True)
            if not self.winMain.chkSavePassword.isChecked():
                self.winMain.txtPassword.setFocus()

    def GetNews(self, news):
        self.winMain.txtFeed.setHtml(news)

        self.configThreadFinished()

    def GetHomeDir(self):
        temp = os.environ.get("HOME")

        if temp is None:
            temp = os.environ.get("APPDATA")

        if not temp.endswith(os.sep):
            temp += os.sep

        return temp

    def ClearLog(self):
        self.winMain.txtStatus.setText("")

    def ClearNews(self):
        self.winMain.txtFeed.setText("")

    def AddLog(self, message):
        for line in message.splitlines():
            if line.startswith("[E"):
                line = '<font color="red">' + message + "</font>"
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
        ReturnGLSDataCentre,
        ReturnWorldQueueConfig,
        ReturnNews,
    ):

        self.settings = settings
        self.configFile = configFile
        self.configFileAlt = configFileAlt
        self.osType = osType
        self.baseDir = baseDir

        self.ReturnLog = ReturnLog
        self.ReturnBaseConfig = ReturnBaseConfig
        self.ReturnGLSDataCentre = ReturnGLSDataCentre
        self.ReturnWorldQueueConfig = ReturnWorldQueueConfig
        self.ReturnNews = ReturnNews

    def run(self):
        self.LoadLanguageList()

    def LoadLanguageList(self):
        if os.path.exists(self.settings.gameDir):
            langConfig = LanguageConfig(self.settings.gameDir)

            if langConfig.langFound:
                self.ReturnLog.emit("Available languages checked.")

                self.LoadLauncherConfig()
            else:
                self.ReturnLog.emit("[E02] No language files found.")

    def LoadLauncherConfig(self):
        self.baseConfig = BaseConfig(self.configFile)

        if self.baseConfig.isConfigOK:
            self.ReturnBaseConfig.emit(self.baseConfig)

            self.AccessGLSDataCentre(
                self.baseConfig.GLSDataCentreService, self.baseConfig.gameName
            )
        else:
            self.baseConfig = BaseConfig(self.configFileAlt)

            if self.baseConfig.isConfigOK:
                self.ReturnBaseConfig.emit(self.baseConfig)

                self.AccessGLSDataCentre(
                    self.baseConfig.GLSDataCentreService,
                    self.baseConfig.gameName,
                )
            else:
                self.ReturnLog.emit(
                    "[E03] Error reading launcher configuration file."
                )

    def AccessGLSDataCentre(self, urlGLS, gameName):
        self.dataCentre = GLSDataCentre(
            urlGLS, gameName, self.baseDir, self.osType
        )

        if self.dataCentre.loadSuccess:
            self.ReturnLog.emit("Fetched details from GLS data centre.")
            self.ReturnGLSDataCentre.emit(self.dataCentre)
            self.ReturnLog.emit("World list obtained.")

            self.GetWorldQueueConfig(self.dataCentre.launchConfigServer)
        else:
            self.ReturnLog.emit("[E04] Error accessing GLS data centre.")

    def GetWorldQueueConfig(self, urlWorldQueueServer):
        self.worldQueueConfig = WorldQueueConfig(
            urlWorldQueueServer,
            self.baseDir,
            self.osType,
            self.settings.gameDir,
            self.settings.x86Enabled,
        )

        if self.worldQueueConfig.message:
            self.ReturnLog.emit(self.worldQueueConfig.message)

        if self.worldQueueConfig.loadSuccess:
            self.ReturnLog.emit("World queue configuration read")
            self.ReturnWorldQueueConfig.emit(self.worldQueueConfig)

            self.GetNews()
        else:
            self.ReturnLog.emit(
                "[E05] Error getting world queue configuration"
            )

    def GetNews(self):
        try:
            href = ""

            webservice, post = WebConnection(
                self.worldQueueConfig.newsStyleSheetURL
            )

            webservice.putrequest("GET", post)
            webservice.putheader("Accept-Encoding", "gzip")
            webservice.endheaders()

            webresp = webservice.getresponse()

            if webresp.getheader("Content-Encoding", "") == "gzip":
                tempxml = zlib.decompress(webresp.read(), 16 + zlib.MAX_WBITS)
            else:
                tempxml = webresp.read()

            doc = defusedxml.minidom.parseString(
                tempxml, forbid_entities=False
            )

            nodes = doc.getElementsByTagName("div")
            for node in nodes:
                if node.nodeType == node.ELEMENT_NODE:
                    if (
                        node.attributes.item(0).firstChild.nodeValue
                        == "launcherNewsItemDate"
                    ):
                        timeCode = GetText(node.childNodes).strip()
                        timeCode = (
                            timeCode.replace("\t", "")
                            .replace(",", "")
                            .replace("-", "")
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

            HTMLTEMPLATE = (
                '<html><head><link rel="stylesheet" type="text/css" href="'
            )
            HTMLTEMPLATE += href.value
            HTMLTEMPLATE += (
                '"/><base target="_blank"/></head><body><div '
                'class="launcherNewsItemsContainer" style="width:auto">'
            )

            urlNewsFeed = self.worldQueueConfig.newsFeedURL.replace(
                "{lang}", self.settings.language.lower()
            )

            webservice, post = WebConnection(urlNewsFeed)

            webservice.putrequest("GET", post)
            webservice.putheader("Accept-Encoding", "gzip")
            webservice.endheaders()

            webresp = webservice.getresponse()

            if webresp.getheader("Content-Encoding", "") == "gzip":
                tempxml = zlib.decompress(webresp.read(), 16 + zlib.MAX_WBITS)
            else:
                tempxml = webresp.read()

            if len(tempxml) == 0:
                webservice, post = WebConnection(webresp.getheader("location"))
                webservice.putrequest("GET", post)
                webservice.putheader("Accept-Encoding", "gzip")
                webservice.endheaders()
                webresp = webservice.getresponse()

                if webresp.getheader("Content-Encoding", "") == "gzip":
                    tempxml = zlib.decompress(
                        webresp.read(), 16 + zlib.MAX_WBITS
                    )
                else:
                    tempxml = webresp.read()

            result = HTMLTEMPLATE

            doc = defusedxml.minidom.parseString(tempxml)

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

                result += (
                    '<div class="launcherNewsItemContainer">%s%s%s%s</div>'
                    % (title, date, description, "<hr>")
                )

            result += "</div></body></html>"

            self.ReturnNews.emit(result)
        except:
            self.ReturnLog.emit("[E12] Error gettings news")
