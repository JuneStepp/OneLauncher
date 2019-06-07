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
from PyQt5 import QtCore, QtGui, QtWebEngineWidgets, QtWidgets, uic
from PyQt5.QtCore import pyqtSignal, QObject
from .SettingsWindow import SettingsWindow
from .SettingsWizard import SettingsWizard
from .PatchWindow import PatchWindow
from .StartGame import StartGame
from .Settings import Settings
from .CheckConfig import CheckConfig
from .PyLotROUtils import DetermineOS, DetermineGame, LanguageConfig, Language
from .PyLotROUtils import BaseConfig, GLSDataCentre, WorldQueueConfig
from .PyLotROUtils import AuthenticateUser, JoinWorldQueue, GetText, WebConnection
from . import Information

try:
    import PyQt5.QtNetwork
    from PyQt5 import QtWebEngineWidgets, QtWidgets
except:
    pass

from http.client import HTTPConnection, HTTPSConnection


class MainWindow(QObject):
    ReturnLog = QtCore.pyqtSignal('QString')
    ReturnLangConfig = pyqtSignal("PyQt_PyObject")
    ReturnBaseConfig = pyqtSignal("PyQt_PyObject")
    ReturnGLSDataCentre = pyqtSignal("PyQt_PyObject")
    ReturnWorldQueueConfig = pyqtSignal("PyQt_PyObject")
    ReturnNews = pyqtSignal('QString')

    def __init__(self):
        super(MainWindow, self).__init__()
        # Determine where module is located (needed for finding ICO & PNG files)
        try:
            test = sys.frozen
            self.rootDir = os.path.dirname(sys.executable)
        except:
            self.rootDir = __file__.replace("library.zip", "")
            if os.path.islink(self.rootDir):
                self.rootDir = os.path.realpath(self.rootDir)
            self.rootDir = os.path.dirname(os.path.abspath(self.rootDir))

        uifile = None

        try:
            from pkg_resources import resource_filename
            uifile = resource_filename(__name__, 'ui/winMain.ui')
        except:
            uifile = os.path.join(self.rootDir, "ui", "winMain.ui")

        self.app = QtWidgets.QApplication(sys.argv)

        # Create the main window and set all text so that translations are handled via gettext
        Ui_winMain, base_class = uic.loadUiType(uifile)
        self.winMain = QtWidgets.QMainWindow()
        self.winMain.setWindowFlags(QtCore.Qt.Dialog)
        self.uiMain = Ui_winMain()
        self.uiMain.setupUi(self.winMain)

        # Set window palette
        self.palette = QtGui.QPalette()
        self.palette.setColor(QtGui.QPalette.Base, QtCore.Qt.black)
        self.palette.setColor(QtGui.QPalette.AlternateBase,
                              QtGui.QColor(22, 21, 21))
        self.palette.setColor(QtGui.QPalette.ToolTipBase,
                              QtGui.QColor(255, 255, 220))
        self.palette.setColor(QtGui.QPalette.ToolTipText, QtCore.Qt.black)
        self.palette.setColor(QtGui.QPalette.Window, QtGui.QColor(44, 43, 42))
        self.palette.setColor(QtGui.QPalette.WindowText, QtCore.Qt.white)
        self.palette.setColor(QtGui.QPalette.Text, QtCore.Qt.white)
        self.palette.setColor(QtGui.QPalette.BrightText, QtCore.Qt.white)
        self.palette.setColor(QtGui.QPalette.ButtonText, QtCore.Qt.white)
        self.palette.setColor(QtGui.QPalette.Button, QtGui.QColor(44, 43, 42))
        self.winMain.setPalette(self.palette)

        # find menubar object and save it so we can find the menus
        for child in self.winMain.children():
            if isinstance(child, QtWidgets.QMenuBar):
                self.menubar = child

        # find menu objects and set the palette on them
        for child in self.menubar.children():
            if isinstance(child, QtWidgets.QMenu):
                child.setPalette(self.palette)

        self.webMainExists = True
        try:
            self.webMain = QtWebEngineWidgets.QWebView(self.uiMain.centralwidget)
            self.webMain.setGeometry(QtCore.QRect(5, 130, 390, 280))
            self.webMain.setUrl(QtCore.QUrl("about:blank"))
        except:
            self.webMainExists = False
            self.webMain = QtWidgets.QTextBrowser(self.uiMain.centralwidget)
            self.webMain.setGeometry(QtCore.QRect(5, 130, 390, 280))
            self.webMain.setTextInteractionFlags(
                QtCore.Qt.TextSelectableByMouse)
            self.webMain.setOpenLinks(False)

        # Centre window on screen
        screen = QtWidgets.QDesktopWidget().screenGeometry()
        size = self.winMain.geometry()
        self.winMain.move((screen.width() - size.width()) / 2,
                          (screen.height() - size.height()) / 2)

        # Connect signals to functions
        self.uiMain.btnLogin.clicked.connect(self.btnLoginClicked)
        self.uiMain.txtAccount.returnPressed.connect(self.txtAccountEnter)
        self.uiMain.txtPassword.returnPressed.connect(self.txtPasswordEnter)
        self.uiMain.actionExit.triggered.connect(self.winMain.close)
        self.uiMain.actionAbout.triggered.connect(self.actionAboutSelected)
        self.uiMain.actionPatch.triggered.connect(self.actionPatchSelected)
        self.uiMain.actionOptions.triggered.connect(self.actionOptionsSelected)
        self.uiMain.actionSettings_Wizard.triggered.connect(self.actionWizardSelected)
        self.uiMain.actionSwitch_Game.triggered.connect(self.actionSwitchSelected)
        self.uiMain.actionCheck_Bottle.triggered.connect(self.actionCheckSelected)
        self.uiMain.actionHideWinMain.triggered.connect(self.actionHideWinMainSelected)

        self.winMain.ReturnLog = self.ReturnLog
        self.winMain.ReturnLog.connect(self.AddLog)
        self.winMain.ReturnLangConfig = self.ReturnLangConfig
        self.winMain.ReturnLangConfig.connect(self.GetLanguageConfig)
        self.winMain.ReturnBaseConfig = self.ReturnBaseConfig
        self.winMain.ReturnBaseConfig.connect(self.GetBaseConfig)
        self.winMain.ReturnGLSDataCentre = self.ReturnGLSDataCentre
        self.winMain.ReturnGLSDataCentre.connect(self.GetGLSDataCentre)
        self.winMain.ReturnWorldQueueConfig = self.ReturnWorldQueueConfig
        self.winMain.ReturnWorldQueueConfig.connect(self.GetWorldQueueConfig)
        self.winMain.ReturnNews = self.ReturnNews
        self.winMain.ReturnNews.connect(self.GetNews)

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
        self.winMain.show()
        sys.exit(self.app.exec_())

    def hideWinMain(self):
        if self.settings.hideWinMain:
            self.winMain.hide()

    def resetFocus(self):
        if self.settings.hideWinMain:
            self.winMain.show()

            if self.uiMain.txtAccount.text() == "":
                self.uiMain.txtAccount.setFocus()
            elif self.uiMain.txtPassword.text() == "":
                self.uiMain.txtPassword.setFocus()

    def actionHideWinMainSelected(self):
        self.settings.hideWinMain = not self.settings.hideWinMain

    def actionCheckSelected(self):
        confCheck = CheckConfig(
            self.winMain, self.settings, self.valHomeDir, self.osType, self.rootDir)

        self.hideWinMain()
        confCheck.Run()
        self.resetFocus()

    def actionAboutSelected(self):
        dlgAbout = QtWidgets.QDialog(self.winMain)
        dlgAbout.setPalette(self.winMain.palette())

        uifile = None

        try:
            from pkg_resources import resource_filename
            uifile = resource_filename(__name__, 'ui/winAbout.ui')
        except:
            uifile = os.path.join(self.rootDir, "ui", "winAbout.ui")

        Ui_dlgAbout, base_class = uic.loadUiType(uifile)
        ui = Ui_dlgAbout()
        ui.setupUi(dlgAbout)
        ui.lblDescription.setText(Information.LongDescription)
        ui.lblCopyright.setText(Information.Copyright)
        ui.lblVersion.setText("<b>Version:</b> " + Information.Version)
        ui.lblPyLotROReference.setText(Information.PyLotROReference)
        ui.lblCLIReference.setText(Information.CLIReference)
        ui.lblLotROLinuxReference.setText(Information.LotROLinuxReference)

        self.hideWinMain()
        dlgAbout.exec_()
        self.resetFocus()

    def actionPatchSelected(self):
        winPatch = PatchWindow(self.winMain, self.dataCentre.patchServer, self.worldQueueConfig.patchProductCode,
                               self.langConfig.langList[self.uiMain.cboLanguage.currentIndex(
                               )].code,
                               self.settings.gameDir, self.settings.patchClient, self.settings.wineProg,
                               self.settings.hiResEnabled, self.gameType.icoFile, self.valHomeDir, self.settings.winePrefix,
                               self.settings.app, self.osType, self.rootDir)

        self.hideWinMain()
        winPatch.Run(self.app)
        self.resetFocus()

    def actionOptionsSelected(self):
        winSettings = SettingsWindow(self.winMain, self.settings.hiResEnabled, self.settings.app, self.settings.x86Enabled,
                                     self.settings.wineProg, self.settings.wineDebug, self.settings.patchClient, self.settings.usingDND,
                                     self.settings.winePrefix, self.settings.gameDir, self.valHomeDir, self.osType, self.rootDir)

        self.hideWinMain()
        if winSettings.Run() == QtWidgets.QDialog.Accepted:
            self.settings.hiResEnabled = winSettings.getHiRes()
            self.settings.app = winSettings.getApp()
            self.settings.x86Enabled = winSettings.getx86()
            self.settings.patchClient = winSettings.getPatchClient()
            self.settings.gameDir = winSettings.getGameDir()

            if not self.osType.usingWindows:
                self.settings.wineProg = winSettings.getProg()
                self.settings.wineDebug = winSettings.getDebug()
                self.settings.winePrefix = winSettings.getPrefix()

            self.settings.SaveSettings(self.uiMain.chkSaveSettings.isChecked())
            self.resetFocus()
            self.InitialSetup()
        else:
            self.resetFocus()

    def actionWizardSelected(self):
        winWizard = SettingsWizard(
            self.winMain, self.valHomeDir, self.osType, self.rootDir)

        self.hideWinMain()
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
            self.resetFocus()
            self.InitialSetup()
        else:
            self.resetFocus()

    def actionSwitchSelected(self):
        dlgChooseAccount = QtWidgets.QDialog(self.winMain)
        dlgChooseAccount.setPalette(self.winMain.palette())

        uifile = None

        try:
            from pkg_resources import resource_filename
            uifile = resource_filename(__name__, 'ui/winSelectAccount.ui')
        except:
            uifile = os.path.join(self.rootDir, "ui", "winSelectAccount.ui")

        Ui_dlgChooseAccount, base_class = uic.loadUiType(uifile)
        ui = Ui_dlgChooseAccount()
        ui.setupUi(dlgChooseAccount)
        ui.lblMessage.setText("Please select game to switch to")
        dlgChooseAccount.setWindowTitle("Switch Game")

        ui.comboBox.addItem("Lord of the Rings Online")
        ui.comboBox.addItem("Lord of the Rings Online (Test)")
        ui.comboBox.addItem("Dungeons & Dragons Online")
        ui.comboBox.addItem("Dungeons & Dragons Online (Test)")

        self.hideWinMain()
        if dlgChooseAccount.exec_() == QtWidgets.QDialog.Accepted:
            if ui.comboBox.currentIndex() == 0:
                self.currentGame = "LOTRO"
            elif ui.comboBox.currentIndex() == 1:
                self.currentGame = "LOTRO.Test"
            elif ui.comboBox.currentIndex() == 2:
                self.currentGame = "DDO"
            elif ui.comboBox.currentIndex() == 3:
                self.currentGame = "DDO.Test"

            self.resetFocus()
            self.InitialSetup()
        else:
            self.resetFocus()

    def btnLoginClicked(self):
        if self.uiMain.txtAccount.text() == "" or self.uiMain.txtPassword.text() == "":
            self.AddLog("<font color=\"Khaki\">Please enter account name and password</font>")
        else:
            if self.uiMain.chkSaveSettings.isChecked():
                self.settings.account = self.uiMain.txtAccount.text()
                self.settings.realm = self.uiMain.cboRealm.currentText()
                self.settings.language = self.langConfig.langList[self.uiMain.cboLanguage.currentIndex(
                )].code
                self.settings.SaveSettings(
                    self.uiMain.chkSaveSettings.isChecked())

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
        self.uiMain.txtPassword.clear()

        if self.account.authSuccess:
            self.AddLog("Account authenticated")

            tempRealm = ""

            if len(self.account.gameList) > 1:
                dlgChooseAccount = QtWidgets.QDialog(self.winMain)

                uifile = None

                try:
                    from pkg_resources import resource_filename
                    uifile = resource_filename(
                        __name__, 'ui/winSelectAccount.ui')
                except:
                    uifile = os.path.join(
                        self.rootDir, "ui", "winSelectAccount.ui")

                Ui_dlgChooseAccount, base_class = uic.loadUiType(uifile)
                ui = Ui_dlgChooseAccount()
                ui.setupUi(dlgChooseAccount)
                ui.lblMessage.setText(
                    "Multiple game accounts found\n\nPlease select the required game")

                for game in self.account.gameList:
                    ui.comboBox.addItem(game.description)

                self.hideWinMain()
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
            tempRealm.CheckRealm(self.settings.usingDND,
                                 self.valHomeDir, self.osType)

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
        game = StartGame(self.winMain, self.worldQueueConfig.gameClientFilename, self.settings.x86Enabled,
                         self.worldQueueConfig.gameClientArgTemplate, self.accNumber, self.urlLoginServer,
                         self.account.ticket, self.urlChatServer,
                         self.langConfig.langList[self.uiMain.cboLanguage.currentIndex(
                         )].code,
                         self.settings.gameDir, self.settings.wineProg, self.settings.wineDebug,
                         self.settings.winePrefix, self.settings.hiResEnabled, self.settings.app,
                         self.osType, self.valHomeDir, self.gameType.icoFile, self.rootDir,
                         self.worldQueueConfig.crashreceiver, self.worldQueueConfig.DefaultUploadThrottleMbps,
                         self.worldQueueConfig.bugurl, self.worldQueueConfig.authserverurl,
                         self.worldQueueConfig.supporturl, self.worldQueueConfig.supportserviceurl,
                         self.worldQueueConfig.glsticketlifetime,
                         self.uiMain.cboRealm.currentText(),
                         self.uiMain.txtAccount.text())

        self.winMain.hide()
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
        self.uiMain.actionPatch.setEnabled(False)
        self.uiMain.actionPatch.setVisible(False)
        self.uiMain.actionCheck_Bottle.setEnabled(False)
        self.uiMain.actionCheck_Bottle.setVisible(False)
        self.uiMain.btnLogin.setEnabled(False)
        self.uiMain.chkSaveSettings.setEnabled(False)
        self.valHomeDir = self.GetHomeDir()

        if self.webMainExists:
            self.webMain.setHtml("")
        else:
            self.webMain.setText("")

        if self.settings is None:
            self.settings = Settings(self.valHomeDir, self.osType)

        self.uiMain.txtAccount.setText("")
        self.uiMain.txtPassword.setText("")
        self.uiMain.cboRealm.clear()
        self.uiMain.cboLanguage.clear()
        self.ClearLog()

        self.AddLog("Initialising, please wait...")

        if not self.settings.LoadSettings(self.currentGame):
            self.AddLog("[E01] Error loading settings")
        else:
            if self.settings.focusAccount:
                self.uiMain.txtAccount.setFocus()
                self.uiMain.chkSaveSettings.setChecked(False)
            else:
                self.uiMain.txtAccount.setText(self.settings.account)
                self.uiMain.chkSaveSettings.setChecked(True)
                self.uiMain.txtPassword.setFocus()

        self.gameType.GetSettings(
            self.settings.usingDND, self.settings.usingTest)

        pngFile = None
        icoFile = None

        try:
            from pkg_resources import resource_filename
            pngFile = resource_filename(
                __name__, self.gameType.pngFile.replace("\\", "/"))
            icoFile = resource_filename(
                __name__, self.gameType.icoFile.replace("\\", "/"))
        except:
            pngFile = os.path.join(self.rootDir, self.gameType.pngFile)
            icoFile = os.path.join(self.rootDir, self.gameType.icoFile)

        self.uiMain.imgMain.setPixmap(QtGui.QPixmap(pngFile))
        self.winMain.setWindowTitle(self.gameType.title)
        self.winMain.setWindowIcon(QtGui.QIcon(icoFile))
        self.uiMain.actionHideWinMain.setChecked(self.settings.hideWinMain)

        self.configFile = "%s%s" % (
            self.settings.gameDir, self.gameType.configFile)
        self.configFileAlt = "%s%s" % (
            self.settings.gameDir, self.gameType.configFileAlt)
        self.gameDirExists = os.path.exists(self.settings.gameDir)

        if self.gameDirExists:
            if self.osType.usingWindows:
                if os.environ.get('WINEPREFIX') != None and os.environ.get('OLDPWD') != None:
                    self.uiMain.actionCheck_Bottle.setEnabled(True)
                    self.uiMain.actionCheck_Bottle.setVisible(True)
            else:
                self.uiMain.actionCheck_Bottle.setEnabled(True)
                self.uiMain.actionCheck_Bottle.setVisible(True)

            if self.settings.app == "Wine":
                self.uiMain.actionCheck_Bottle.setText("Check Prefix")
            elif self.settings.app == "Native":
                self.uiMain.actionCheck_Bottle.setText("Check Config")
            else:
                self.uiMain.actionCheck_Bottle.setText("Check Bottle")
        else:
            self.AddLog("[E13] Game Directory not found")

        self.langConfig = None

        self.configThread = MainWindowThread()
        self.configThread.SetUp(self.winMain, self.settings, self.configFile, self.configFileAlt,
                                self.valHomeDir, self.osType)
        self.configThread.start()

    def GetLanguageConfig(self, langConfig):
        self.langConfig = langConfig

        setPos = 0

        for lang in self.langConfig.langList:
            self.uiMain.cboLanguage.addItem(lang.name)
            if lang.code == self.settings.language:
                self.uiMain.cboLanguage.setCurrentIndex(setPos)

            setPos += 1

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
        self.uiMain.txtAccount.setEnabled(True)
        self.uiMain.txtPassword.setEnabled(True)

        if self.settings.focusAccount:
            self.uiMain.txtAccount.setFocus()
            self.uiMain.chkSaveSettings.setChecked(False)
        else:
            self.uiMain.txtAccount.setText(self.settings.account)
            self.uiMain.chkSaveSettings.setChecked(True)
            self.uiMain.txtPassword.setFocus()

    def GetNews(self, news):
        if self.webMainExists:
            self.webMain.setHtml(news)
        else:
            newsString = news
            temp = news.split("</head>")
            if len(temp) > 0:
                newsString = temp[1].split("</html>")[0]

            self.webMain.setHtml(newsString)

    def GetHomeDir(self):
        temp = os.environ.get('HOME')

        if temp is None:
            temp = os.environ.get('APPDATA')

        if not temp.endswith(os.sep):
            temp += os.sep

        return temp

    def ClearLog(self):
        self.uiMain.txtStatus.setText("")

    def AddLog(self, message):
        for line in message.splitlines():
            if line.startswith("[E"):
                line = ("<font color=\"red\">" + message + "</font>")
            self.uiMain.txtStatus.append(line)

class MainWindowThread(QtCore.QThread):
    def SetUp(self, winMain, settings, configFile, configFileAlt, baseDir, osType):
        self.winMain = winMain
        self.settings = settings
        self.configFile = configFile
        self.configFileAlt = configFileAlt
        self.osType = osType
        self.baseDir = baseDir

    def run(self):
        self.LoadLanguageList()

    def LoadLanguageList(self):
        self.langConfig = LanguageConfig(self.settings.gameDir)

        if self.langConfig.langFound:
            self.winMain.ReturnLog.emit("Available languages checked.")
            self.winMain.ReturnLangConfig.emit(self.langConfig)

            self.langPos = 0
            setPos = 0

            for lang in self.langConfig.langList:
                if lang.code == self.settings.language:
                    self.langPos = setPos
                setPos += 1

            self.LoadLauncherConfig()
        else:
            self.winMain.ReturnLog.emit("[E02] No language files found.")

    def LoadLauncherConfig(self):
        self.baseConfig = BaseConfig(self.configFile)

        if self.baseConfig.isConfigOK:
            self.winMain.ReturnBaseConfig.emit(self.baseConfig)

            self.AccessGLSDataCentre(
                self.baseConfig.GLSDataCentreService, self.baseConfig.gameName)
        else:
            self.baseConfig = BaseConfig(self.configFileAlt)

            if self.baseConfig.isConfigOK:
                self.winMain.ReturnBaseConfig.emit(self.baseConfig)

                self.AccessGLSDataCentre(
                    self.baseConfig.GLSDataCentreService, self.baseConfig.gameName)
            else:
                self.winMain.ReturnLog.emit("[E03] Error reading launcher configuration file.")

    def AccessGLSDataCentre(self, urlGLS, gameName):
        self.dataCentre = GLSDataCentre(
            urlGLS, gameName, self.baseDir, self.osType)

        if self.dataCentre.loadSuccess:
            self.winMain.ReturnLog.emit("Fetched details from GLS data centre.")
            self.winMain.ReturnGLSDataCentre.emit(self.dataCentre)
            self.winMain.ReturnLog.emit("Realm list obtained.")

            self.GetWorldQueueConfig(self.dataCentre.launchConfigServer)
        else:
            self.winMain.ReturnLog.emit("[E04] Error accessing GLS data centre.")

    def GetWorldQueueConfig(self, urlWorldQueueServer):
        self.worldQueueConfig = WorldQueueConfig(
            urlWorldQueueServer, self.settings.usingDND, self.baseDir, self.osType, self.settings.gameDir,
            self.settings.x86Enabled)

        if self.worldQueueConfig.message:
            self.winMain.ReturnLog.emit(self.worldQueueConfig.message)

        if self.worldQueueConfig.loadSuccess:
            self.winMain.ReturnLog.emit("World queue configuration read")
            self.winMain.ReturnWorldQueueConfig.emit(self.worldQueueConfig)

            self.GetNews()
        else:
            self.winMain.ReturnLog.emit("[E05] Error getting world queue configuration")

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

            urlNewsFeed = self.worldQueueConfig.newsFeedURL.replace("{lang}",
                                                                    self.langConfig.langList[self.langPos].news)

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

            self.winMain.ReturnNews.emit(result)
        except:
            self.winMain.ReturnLog.emit("[E12] Error gettings news")
