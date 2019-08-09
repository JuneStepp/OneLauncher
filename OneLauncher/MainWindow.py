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
import os
import sys
import xml.dom.minidom
import zlib
from qtpy import QtCore, QtGui, QtWidgets, uic
import qdarkstyle
from .SettingsWindow import SettingsWindow
from .SetupWizard import SetupWizard
from .PatchWindow import PatchWindow
from .StartGame import StartGame
from .Settings import Settings
from .Updater import BuiltInPrefix
from .OneLauncherUtils import DetermineOS, DetermineGame, LanguageConfig
from .OneLauncherUtils import BaseConfig, GLSDataCentre, WorldQueueConfig
from .OneLauncherUtils import AuthenticateUser, JoinWorldQueue, GetText, WebConnection
from . import Information
from pkg_resources import resource_filename
import keyring

class MainWindow(QtWidgets.QMainWindow):
    app = QtWidgets.QApplication(sys.argv)

    ReturnLog = QtCore.Signal("QString")
    ReturnBaseConfig = QtCore.Signal("PyQt_PyObject")
    ReturnGLSDataCentre = QtCore.Signal("PyQt_PyObject")
    ReturnWorldQueueConfig = QtCore.Signal("PyQt_PyObject")
    ReturnNews = QtCore.Signal("QString")
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

        uifile = resource_filename(__name__, 'ui' + os.sep + 'winMain.ui')

        # Create the main window and set all text so that translations are handled via gettext
        Ui_winMain, base_class = uic.loadUiType(uifile)
        self.winMain = QtWidgets.QMainWindow(self)
        self.setWindowFlags(QtCore.Qt.Dialog)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.uiMain = Ui_winMain()
        self.uiMain.setupUi(self)

        # Set window style
        self.app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())

        # Centre window on screen
        self.center()

        self.dragPos = self.pos()

        # Sets some widgets to WA_NoMousePropagation to avoid window dragging issues
        mouse_ignore_list = [self.uiMain.btnAbout, self.uiMain.btnExit, self.uiMain.btnLogin,
                            self.uiMain.btnMinimize, self.uiMain.btnOptions,
                            self.uiMain.btnSwitchGame,
                             self.uiMain.cboRealm, self.uiMain.chkSaveSettings]
        for widget in mouse_ignore_list:
            widget.setAttribute(QtCore.Qt.WA_NoMousePropagation)

        # Connect signals to functions
        self.uiMain.btnLogin.clicked.connect(self.btnLoginClicked)
        self.uiMain.txtAccount.returnPressed.connect(self.txtAccountEnter)
        self.uiMain.txtPassword.returnPressed.connect(self.txtPasswordEnter)
        self.uiMain.btnExit.clicked.connect(self.close)
        self.uiMain.btnMinimize.clicked.connect(self.showMinimized)
        self.uiMain.btnAbout.clicked.connect(self.btnAboutSelected)
        self.uiMain.btnLoginMenu = QtWidgets.QMenu()
        self.uiMain.btnLoginMenu.addAction(self.uiMain.actionPatch)
        self.uiMain.actionPatch.triggered.connect(self.actionPatchSelected)
        self.uiMain.btnLogin.setMenu(self.uiMain.btnLoginMenu)
        self.uiMain.btnOptions.setIcon(QtGui.QIcon(resource_filename(__name__,
                                        "images" + os.sep + "SettingsGear.png")))
        self.uiMain.btnOptions.clicked.connect(self.btnOptionsSelected)
        self.uiMain.btnSwitchGame.clicked.connect(self.btnSwitchGameClicked)
        self.uiMain.btnSwitchGameMenu = QtWidgets.QMenu()
        self.uiMain.btnSwitchGameMenu.addAction(self.uiMain.actionLOTROTest)
        self.uiMain.actionLOTROTest.triggered.connect(self.SwitchToLOTROTest)
        self.uiMain.btnSwitchGameMenu.addAction(self.uiMain.actionDDOTest)
        self.uiMain.actionDDOTest.triggered.connect(self.SwitchToDDOTest)
        self.uiMain.btnSwitchGameMenu.addAction(self.uiMain.actionLOTRO)
        self.uiMain.actionLOTRO.triggered.connect(self.SwitchToLOTRO)
        self.uiMain.btnSwitchGameMenu.addAction(self.uiMain.actionDDO)
        self.uiMain.actionDDO.triggered.connect(self.SwitchToDDO)
        self.uiMain.btnSwitchGame.setMenu(self.uiMain.btnSwitchGameMenu)

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
        self.uiMain.btnLogin.setEnabled(False)
        self.uiMain.chkSaveSettings.setEnabled(False)

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
        if self.uiMain.txtAccount.text() == "":
            self.uiMain.txtAccount.setFocus()
        elif self.uiMain.txtPassword.text() == "":
            self.uiMain.txtPassword.setFocus()

    def center(self):
        qr = self.frameGeometry()
        cp = QtWidgets.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    # The two functions below handle dragging the window
    def mousePressEvent(self, event):
        self.dragPos = event.globalPos()

    def mouseMoveEvent(self, event):
        self.move(self.pos() + event.globalPos() - self.dragPos)
        self.dragPos = event.globalPos()

    def btnAboutSelected(self):
        dlgAbout = QtWidgets.QDialog(self, QtCore.Qt.FramelessWindowHint)

        uifile = resource_filename(__name__, 'ui' + os.sep + 'winAbout.ui')

        Ui_dlgAbout, base_class = uic.loadUiType(uifile)
        ui = Ui_dlgAbout()
        ui.setupUi(dlgAbout)
        ui.lblDescription.setText(Information.LongDescription)
        ui.lblWebsite.setText(Information.Website)
        ui.lblCopyright.setText(Information.Copyright)
        ui.lblVersion.setText("<b>Version:</b> " + Information.Version)
        ui.lblPyLotROReference.setText(Information.PyLotROReference)
        ui.lblCLIReference.setText(Information.CLIReference)
        ui.lblLotROLinuxReference.setText(Information.LotROLinuxReference)

        dlgAbout.exec_()
        self.resetFocus()

    def manageBuiltInPrefix(self):
        if self.settings.builtInPrefixEnabled and not self.osType.usingWindows:
            winBuiltInPrefix = BuiltInPrefix(self.settings.settingsDir,
                                                self.settings.winePrefix, self)

            self.settings.wineProg = winBuiltInPrefix.Run()
            self.settings.SaveSettings(saveAccountDetails=self.uiMain.chkSaveSettings.isChecked(),
                                        savePassword=self.uiMain.chkSavePassword.isChecked())

    def actionPatchSelected(self):
        self.manageBuiltInPrefix()

        winPatch = PatchWindow(self.dataCentre.patchServer, self.worldQueueConfig.patchProductCode,
                               self.settings.language, self.settings.gameDir, self.settings.patchClient,
                               self.settings.wineProg, self.settings.hiResEnabled, self.gameType.iconFile,
                               self.valHomeDir, self.settings.winePrefix, self.osType, self.rootDir, self)

        winPatch.Run(self.app)
        self.resetFocus()

    def btnOptionsSelected(self):
        winSettings = SettingsWindow(self.settings.hiResEnabled, self.settings.x86Enabled,
                                     self.settings.wineProg, self.settings.wineDebug, self.settings.patchClient,
                                     self.settings.winePrefix, self.settings.gameDir,
                                     self.valHomeDir, self.osType, self.settings, LanguageConfig,
                                      self)

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

            self.settings.SaveSettings(saveAccountDetails=self.uiMain.chkSaveSettings.isChecked(),
                                        savePassword=self.uiMain.chkSavePassword.isChecked())
            self.resetFocus()
            self.InitialSetup()
        else:
            if winSettings.getSetupWizardClicked():
                self.settings_wizard_called()
            else: self.resetFocus()

    def settings_wizard_called(self):
        winWizard = SetupWizard(self.winMain, self.valHomeDir, self.osType, self.rootDir)
        self.hide()

        if winWizard.Run() == QtWidgets.QDialog.Accepted:
            default_game =  winWizard.getGame()
            if default_game:
                game_list = ["LOTRO", "DDO", "LOTRO.Test", "DDO.Test"]
                game_list.append(game_list.pop(game_list.index(default_game)))
                for game in game_list:
                    dir = winWizard.getGameDir(game)
                    if dir:
                        self.settings.gameDir = dir
                        self.settings.hiResEnabled = winWizard.getHiRes(self.settings.gameDir)
                        self.settings.winePrefix = ""
                        self.settings.SaveSettings(game=game)

                self.InitialSetup()
        self.show()

    def btnSwitchGameClicked(self):
        if self.settings.currentGame == "DDO":
            self.currentGame = "LOTRO"
        else: self.currentGame = "DDO"
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
        if self.uiMain.txtAccount.text() == "" or self.uiMain.txtPassword.text() == "":
            self.AddLog("<font color=\"Khaki\">Please enter account name and password</font>")
        else:
            if self.uiMain.chkSaveSettings.isChecked():
                self.settings.account = self.uiMain.txtAccount.text()
                self.settings.realm = self.uiMain.cboRealm.currentText()

                self.settings.SaveSettings(saveAccountDetails=self.uiMain.chkSaveSettings.isChecked(),
                        savePassword=self.uiMain.chkSavePassword.isChecked())

                if self.uiMain.chkSavePassword.isChecked():
                    if self.settings.currentGame.startswith("DDO"):
                        keyring.set_password("OneLauncherDDO", self.uiMain.txtAccount.text(),
                                                self.uiMain.txtPassword.text())
                    else:
                        keyring.set_password("OneLauncherLOTRO", self.uiMain.txtAccount.text(),
                                                self.uiMain.txtPassword.text())
                else:
                    try:
                        if self.settings.currentGame.startswith("DDO"):
                            keyring.delete_password("OneLauncherDDO", self.uiMain.txtAccount.text())
                        else:
                            keyring.delete_password("OneLauncherLOTRO", self.uiMain.txtAccount.text())
                    except:
                        pass

            self.AuthAccount()

    def txtAccountEnter(self):
        self.uiMain.txtPassword.setFocus()

    def txtPasswordEnter(self):
        self.btnLoginClicked()

    def AuthAccount(self):
        self.AddLog("Checking account details...")

        # Force a small display to ensure message above is displayed
        # as program can look like it is not responding while validating
        for loop in range(1, 5):
            self.app.processEvents()

        self.account = AuthenticateUser(self.dataCentre.authServer, self.uiMain.txtAccount.text(),
                                        self.uiMain.txtPassword.text(), self.baseConfig.gameName, self.valHomeDir, self.osType)

        # don't keep password longer in memory than required
        if not self.uiMain.chkSavePassword.isChecked():
            self.uiMain.txtPassword.clear()

        if self.account.authSuccess:
            self.AddLog("Account authenticated")

            tempRealm = ""

            if len(self.account.gameList) > 1:
                dlgChooseAccount = QtWidgets.QDialog(self, QtCore.Qt.FramelessWindowHint)

                uifile = resource_filename(
                    __name__, 'ui' + os.sep + 'winSelectAccount.ui')

                Ui_dlgChooseAccount, base_class = uic.loadUiType(uifile)
                ui = Ui_dlgChooseAccount()
                ui.setupUi(dlgChooseAccount)
                ui.lblMessage.setText(
                    "Multiple game accounts found\n\nPlease select the required game")

                for game in self.account.gameList:
                    ui.comboBox.addItem(game.description)

                if dlgChooseAccount.exec_() == QtWidgets.QDialog.Accepted:
                    self.accNumber = self.account.gameList[ui.comboBox.currentIndex(
                    )].name
                    self.resetFocus()
                else:
                    self.resetFocus()
                    self.AddLog("No game selected - aborting")
                    return
            else:
                self.accNumber = self.account.gameList[0].name

            tempRealm = self.dataCentre.realmList[self.uiMain.cboRealm.currentIndex(
            )]
            tempRealm.CheckRealm(self.valHomeDir, self.osType)

            if tempRealm.realmAvailable:
                self.urlChatServer = tempRealm.urlChatServer
                self.urlLoginServer = tempRealm.loginServer

                if tempRealm.queueURL == "":
                    self.LaunchGame()
                else:
                    self.EnterWorldQueue(tempRealm.queueURL)
            else:
                self.AddLog("[E10] Error getting realm status")
        else:
            self.AddLog(self.account.messError)

    def LaunchGame(self):
        self.manageBuiltInPrefix()

        game = StartGame(self.worldQueueConfig.gameClientFilename, self.settings.x86Enabled,
                         self.worldQueueConfig.gameClientArgTemplate, self.accNumber, self.urlLoginServer,
                         self.account.ticket, self.urlChatServer, self.settings.language,
                         self.settings.gameDir, self.settings.wineProg, self.settings.wineDebug,
                         self.settings.winePrefix, self.settings.hiResEnabled, self.settings.builtInPrefixEnabled
                         , self.osType, self.valHomeDir, self.gameType.iconFile, self.rootDir,
                         self.worldQueueConfig.crashreceiver, self.worldQueueConfig.DefaultUploadThrottleMbps,
                         self.worldQueueConfig.bugurl, self.worldQueueConfig.authserverurl,
                         self.worldQueueConfig.supporturl, self.worldQueueConfig.supportserviceurl,
                         self.worldQueueConfig.glsticketlifetime,
                         self.uiMain.cboRealm.currentText(),
                         self.uiMain.txtAccount.text(), self)
        self.hide()
        game.Run()

    def EnterWorldQueue(self, queueURL):
        self.worldQueue = JoinWorldQueue(self.worldQueueConfig.worldQueueParam,
                                         self.accNumber, self.account.ticket, queueURL, self.worldQueueConfig.worldQueueURL, self.valHomeDir, self.osType)

        if self.worldQueue.joinSuccess:
            self.AddLog("Joined world queue")

            displayQueueing = True

            while self.worldQueue.number > self.worldQueue.serving and self.worldQueue.joinSuccess:
                if displayQueueing:
                    self.AddLog("Currently queueing, please wait...")
                    displayQueueing = False

                self.worldQueue = JoinWorldQueue(self.worldQueueConfig.worldQueueParam,
                                                 self.accNumber, self.account.ticket, queueURL, self.worldQueueConfig.worldQueueURL,
                                                 self.valHomeDir, self.osType)

                if not self.worldQueue.joinSuccess:
                    self.AddLog("[E10] Error getting realm status")

        if self.worldQueue.joinSuccess:
            self.LaunchGame()
        else:
            self.AddLog("[E11] Error joining world queue")

    def InitialSetup(self):
        self.gameDirExists = False
        self.uiMain.txtAccount.setEnabled(False)
        self.uiMain.txtPassword.setEnabled(False)
        self.uiMain.btnLogin.setEnabled(False)
        self.uiMain.chkSaveSettings.setEnabled(False)
        self.uiMain.chkSavePassword.setEnabled(False)
        self.valHomeDir = self.GetHomeDir()

        if self.settings is None:
            self.settings = Settings(self.valHomeDir, self.osType)

        self.uiMain.txtAccount.setText("")
        self.uiMain.txtPassword.setText("")
        self.uiMain.cboRealm.clear()
        self.ClearLog()
        self.ClearNews()

        self.AddLog("Initialising, please wait...")

        settings_load_success = self.settings.LoadSettings(self.currentGame)
        if settings_load_success and settings_load_success != True:
            self.AddLog(settings_load_success)
        elif not settings_load_success:
            #Checks if the user is running OneLauncher for the first time and calls the setup Wizard
            if not os.path.exists(self.settings.settingsDir):
                self.settings_wizard_called()
                return None
            else:
                self.AddLog("[E01] Error loading settings")
        else:
            if self.settings.focusAccount:
                self.uiMain.txtAccount.setFocus()
                self.uiMain.chkSaveSettings.setChecked(False)
            else:
                self.uiMain.txtAccount.setText(self.settings.account)
                self.uiMain.chkSaveSettings.setChecked(True)

                self.uiMain.chkSavePassword.setChecked(False)

                if self.settings.savePassword:
                    self.uiMain.chkSavePassword.setChecked(True)
                    if self.settings.currentGame.startswith("DDO"):
                        self.uiMain.txtPassword.setText(keyring.get_password(
                                        "OneLauncherDDO", self.settings.account))
                    else:
                        self.uiMain.txtPassword.setText(keyring.get_password(
                                        "OneLauncherLOTRO", self.settings.account))
                else: self.uiMain.txtPassword.setFocus()

        self.gameType.GetSettings(self.settings.currentGame)

        pngFile = resource_filename(
            __name__, self.gameType.pngFile.replace("\\", "/"))
        iconFile = resource_filename(
            __name__, self.gameType.iconFile.replace("\\", "/"))

        self.uiMain.imgMain.setPixmap(QtGui.QPixmap(pngFile))
        self.setWindowTitle(self.gameType.title)
        self.setWindowIcon(QtGui.QIcon(iconFile))

        #Set icon and dropdown options of switch game button acording to game running
        if self.settings.currentGame == "DDO":
            self.uiMain.btnSwitchGame.setIcon(QtGui.QIcon(resource_filename(__name__,
                                        "images" + os.sep + "LOTROSwitchIcon.png")))
            self.uiMain.actionLOTROTest.setEnabled(False)
            self.uiMain.actionLOTROTest.setVisible(False)
            self.uiMain.actionDDOTest.setEnabled(True)
            self.uiMain.actionDDOTest.setVisible(True)
            self.uiMain.actionLOTRO.setEnabled(False)
            self.uiMain.actionLOTRO.setVisible(False)
            self.uiMain.actionDDO.setEnabled(False)
            self.uiMain.actionDDO.setVisible(False)
        elif self.settings.currentGame == "DDO.Test":
            self.uiMain.btnSwitchGame.setIcon(QtGui.QIcon(resource_filename(__name__,
                                        "images" + os.sep + "LOTROSwitchIcon.png")))
            self.uiMain.actionLOTROTest.setEnabled(False)
            self.uiMain.actionLOTROTest.setVisible(False)
            self.uiMain.actionDDOTest.setEnabled(False)
            self.uiMain.actionDDOTest.setVisible(False)
            self.uiMain.actionLOTRO.setEnabled(False)
            self.uiMain.actionLOTRO.setVisible(False)
            self.uiMain.actionDDO.setEnabled(True)
            self.uiMain.actionDDO.setVisible(True)
        elif self.settings.currentGame == "LOTRO.Test":
            self.uiMain.btnSwitchGame.setIcon(QtGui.QIcon(resource_filename(__name__,
                                        "images" + os.sep + "DDOSwitchIcon.png")))
            self.uiMain.actionLOTROTest.setEnabled(False)
            self.uiMain.actionLOTROTest.setVisible(False)
            self.uiMain.actionDDOTest.setEnabled(False)
            self.uiMain.actionDDOTest.setVisible(False)
            self.uiMain.actionLOTRO.setEnabled(True)
            self.uiMain.actionLOTRO.setVisible(True)
            self.uiMain.actionDDO.setEnabled(False)
            self.uiMain.actionDDO.setVisible(False)
        else:
            self.uiMain.btnSwitchGame.setIcon(QtGui.QIcon(resource_filename(__name__,
                                        "images" + os.sep + "DDOSwitchIcon.png")))
            self.uiMain.actionDDOTest.setEnabled(False)
            self.uiMain.actionDDOTest.setVisible(False)
            self.uiMain.actionLOTROTest.setEnabled(True)
            self.uiMain.actionLOTROTest.setVisible(True)
            self.uiMain.actionLOTRO.setEnabled(False)
            self.uiMain.actionLOTRO.setVisible(False)
            self.uiMain.actionDDO.setEnabled(False)
            self.uiMain.actionDDO.setVisible(False)

        self.configFile = "%s%s" % (
            self.settings.gameDir, self.gameType.configFile)
        self.configFileAlt = "%s%s" % (
            self.settings.gameDir, self.gameType.configFileAlt)
        self.gameDirExists = os.path.exists(self.settings.gameDir)

        if not self.gameDirExists:
            self.AddLog("[E13] Game Directory not found")

        self.configThread = MainWindowThread()
        self.configThread.SetUp(self.settings, self.configFile, self.configFileAlt,
                                self.valHomeDir, self.osType, self.ReturnLog,
                                self.ReturnBaseConfig, self.ReturnGLSDataCentre,
                                self.ReturnWorldQueueConfig, self.ReturnNews)
        self.configThread.start()

    def GetBaseConfig(self, baseConfig):
        self.baseConfig = baseConfig

    def GetGLSDataCentre(self, dataCentre):
        self.dataCentre = dataCentre

        setPos = 0

        for realm in self.dataCentre.realmList:
            self.uiMain.cboRealm.addItem(realm.name)
            if realm.name == self.settings.realm:
                self.uiMain.cboRealm.setCurrentIndex(setPos)

            setPos += 1

    def GetWorldQueueConfig(self, worldQueueConfig):
        self.worldQueueConfig = worldQueueConfig

        self.uiMain.actionPatch.setEnabled(True)
        self.uiMain.actionPatch.setVisible(True)
        self.uiMain.btnLogin.setEnabled(True)
        self.uiMain.chkSaveSettings.setEnabled(True)
        self.uiMain.chkSavePassword.setEnabled(True)
        self.uiMain.txtAccount.setEnabled(True)
        self.uiMain.txtPassword.setEnabled(True)

        if self.settings.focusAccount:
            self.uiMain.txtAccount.setFocus()
            self.uiMain.chkSaveSettings.setChecked(False)
        else:
            self.uiMain.txtAccount.setText(self.settings.account)
            self.uiMain.chkSaveSettings.setChecked(True)
            if not self.uiMain.chkSavePassword.isChecked():
                self.uiMain.txtPassword.setFocus()

    def GetNews(self, news):
        self.uiMain.txtFeed.setHtml(news)

    def GetHomeDir(self):
        temp = os.environ.get('HOME')

        if temp is None:
            temp = os.environ.get('APPDATA')

        if not temp.endswith(os.sep):
            temp += os.sep

        return temp

    def ClearLog(self):
        self.uiMain.txtStatus.setText("")

    def ClearNews(self):
        self.uiMain.txtFeed.setText("")

    def AddLog(self, message):
        for line in message.splitlines():
            if line.startswith("[E"):
                line = ("<font color=\"red\">" + message + "</font>")
            self.uiMain.txtStatus.append(line)

class MainWindowThread(QtCore.QThread):
    def SetUp(self, settings, configFile, configFileAlt, baseDir,
            osType, ReturnLog, ReturnBaseConfig,
            ReturnGLSDataCentre, ReturnWorldQueueConfig, ReturnNews):

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
                self.baseConfig.GLSDataCentreService, self.baseConfig.gameName)
        else:
            self.baseConfig = BaseConfig(self.configFileAlt)

            if self.baseConfig.isConfigOK:
                self.ReturnBaseConfig.emit(self.baseConfig)

                self.AccessGLSDataCentre(
                    self.baseConfig.GLSDataCentreService, self.baseConfig.gameName)
            else:
                self.ReturnLog.emit("[E03] Error reading launcher configuration file.")

    def AccessGLSDataCentre(self, urlGLS, gameName):
        self.dataCentre = GLSDataCentre(
            urlGLS, gameName, self.baseDir, self.osType)

        if self.dataCentre.loadSuccess:
            self.ReturnLog.emit("Fetched details from GLS data centre.")
            self.ReturnGLSDataCentre.emit(self.dataCentre)
            self.ReturnLog.emit("Realm list obtained.")

            self.GetWorldQueueConfig(self.dataCentre.launchConfigServer)
        else:
            self.ReturnLog.emit("[E04] Error accessing GLS data centre.")

    def GetWorldQueueConfig(self, urlWorldQueueServer):
        self.worldQueueConfig = WorldQueueConfig(
            urlWorldQueueServer, self.baseDir, self.osType,
            self.settings.gameDir, self.settings.x86Enabled)

        if self.worldQueueConfig.message:
            self.ReturnLog.emit(self.worldQueueConfig.message)

        if self.worldQueueConfig.loadSuccess:
            self.ReturnLog.emit("World queue configuration read")
            self.ReturnWorldQueueConfig.emit(self.worldQueueConfig)

            self.GetNews()
        else:
            self.ReturnLog.emit("[E05] Error getting world queue configuration")

    def GetNews(self):
        try:
            href = ""

            webservice, post = WebConnection(
                self.worldQueueConfig.newsStyleSheetURL)

            webservice.putrequest("GET", post)
            webservice.putheader("Accept-Encoding", "gzip")
            webservice.endheaders()

            webresp = webservice.getresponse()

            if webresp.getheader('Content-Encoding', '') == 'gzip':
                tempxml = zlib.decompress(webresp.read(), 16 + zlib.MAX_WBITS)
            else:
                tempxml = webresp.read()

            doc = xml.dom.minidom.parseString(tempxml)

            nodes = doc.getElementsByTagName("div")
            for node in nodes:
                if node.nodeType == node.ELEMENT_NODE:
                    if node.attributes.item(0).firstChild.nodeValue == "launcherNewsItemDate":
                        timeCode = GetText(node.childNodes).strip()
                        timeCode = timeCode.replace("\t", "").replace(
                            ",", "").replace("-", "")
                        if len(timeCode) > 0:
                            timeCode = " %s" % (timeCode)

            links = doc.getElementsByTagName("link")
            for link in links:
                if link.nodeType == link.ELEMENT_NODE:
                    href = link.attributes["href"]

            # Ignore broken href (as of 3/30/16) in the style sheet and use Launcher.NewsFeedCSSUrl defined in launcher.config
            href.value = self.worldQueueConfig.newsFeedCSSURL

            HTMLTEMPLATE = '<html><head><link rel="stylesheet" type="text/css" href="'
            HTMLTEMPLATE += href.value
            HTMLTEMPLATE += '"/><base target="_blank"/></head><body><div class="launcherNewsItemsContainer" style="width:auto">'

            urlNewsFeed = self.worldQueueConfig.newsFeedURL.replace("{lang}", self.settings.language.lower())

            webservice, post = WebConnection(urlNewsFeed)

            webservice.putrequest("GET", post)
            webservice.putheader("Accept-Encoding", "gzip")
            webservice.endheaders()

            webresp = webservice.getresponse()

            if webresp.getheader('Content-Encoding', '') == 'gzip':
                tempxml = zlib.decompress(webresp.read(), 16 + zlib.MAX_WBITS)
            else:
                tempxml = webresp.read()

            if len(tempxml) == 0:
                webservice, post = WebConnection(webresp.getheader("location"))
                webservice.putrequest("GET", post)
                webservice.putheader("Accept-Encoding", "gzip")
                webservice.endheaders()
                webresp = webservice.getresponse()

                if webresp.getheader('Content-Encoding', '') == 'gzip':
                    tempxml = zlib.decompress(
                        webresp.read(), 16 + zlib.MAX_WBITS)
                else:
                    tempxml = webresp.read()

            result = HTMLTEMPLATE

            doc = xml.dom.minidom.parseString(tempxml)

            items = doc.getElementsByTagName("item")
            for item in items:
                title = ""
                description = ""
                date = ""

                for node in item.childNodes:
                    if node.nodeType == node.ELEMENT_NODE:
                        if node.nodeName == "title":
                            title = "<font color=\"gold\"><div class=\"launcherNewsItemTitle\">%s</div></font>" % (
                                GetText(node.childNodes))
                        elif node.nodeName == "description":
                            description = "<div class=\"launcherNewsItemDescription\">%s</div>" % (
                                GetText(node.childNodes))
                        elif node.nodeName == "pubDate":
                            tempDate = GetText(node.childNodes)
                            dispDate = "%s %s %s %s%s" % (tempDate[8:11], tempDate[5:7], tempDate[12:16],
                                                          tempDate[17:22], timeCode)
                            date = "<small><i><div align=\"right\"class=\"launcherNewsItemDate\">%s</div></i></small>" % (
                                dispDate)

                result += "<div class=\"launcherNewsItemContainer\">%s%s%s%s</div>" % (
                    title, date, description, "<hr>")

            result += "</div></body></html>"

            self.ReturnNews.emit(result)
        except:
            self.ReturnLog.emit("[E12] Error gettings news")
