# coding=utf-8
###########################################################################
# Name:   MainWindow
# Author: Alan Jackson
# Date:   11th March 2009
#
# Main window for the Linux/OS X based launcher
# for the game Lord of the Rings Online
#
# Based on a script by SNy <SNy@bmx-chemnitz.de>
# Python port of LotROLinux by AJackson <ajackson@bcs.org.uk>
#
# (C) 2009 AJackson <ajackson@bcs.org.uk>
#
# This file is part of PyLotRO
#
# PyLotRO is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# PyLotRO is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with PyLotRO.  If not, see <http://www.gnu.org/licenses/>.
###########################################################################
import os
import sys
from Ft.Xml.Xslt import Processor
from Ft.Xml.Domlette import NonvalidatingReader
from PyQt4 import QtCore, QtGui, uic
from .SettingsWindow import SettingsWindow
from .SettingsWizard import SettingsWizard
from .PatchWindow import PatchWindow
from .StartGame import StartGame
from .Settings import Settings
from .CheckConfig import CheckConfig
from .PyLotROUtils import DetermineOS, DetermineGame, LanguageConfig, Language
from .PyLotROUtils import BaseConfig, GLSDataCentre, WorldQueueConfig
from .PyLotROUtils import AuthenticateUser, JoinWorldQueue
from . import Information

# If Python 3.0 is in use use http otherwise httplib
try:
	from http.client import HTTPConnection, HTTPSConnection
except:
	from httplib import HTTPConnection, HTTPSConnection

class MainWindow:
	def __init__(self):
		# Determine where module is located (needed for finding ICO & PNG files)
		self.rootDir = __file__
		if os.path.islink(self.rootDir):
			self.rootDir = os.path.realpath(self.rootDir)
		self.rootDir = os.path.dirname(os.path.abspath(self.rootDir))

		uifile = None

		try:
			from pkg_resources import resource_filename
			uifile = resource_filename(__name__, 'ui/winMain.ui')
		except:
			uifile = os.path.join(self.rootDir, "ui", "winMain.ui")

		self.app = QtGui.QApplication(sys.argv)

		# Create the main window and set all text so that translations are handled via gettext
		Ui_winMain, base_class = uic.loadUiType(uifile)
		self.winMain = QtGui.QMainWindow()
		self.winMain.setWindowFlags(QtCore.Qt.Dialog)
		self.uiMain = Ui_winMain()
		self.uiMain.setupUi(self.winMain)

		self.webMainExists = True
		try:
			from PyQt4 import QtWebKit
			self.webMain = QtWebKit.QWebView(self.uiMain.centralwidget)
			self.webMain.setGeometry(QtCore.QRect(5, 130, 390, 280))
			self.webMain.setUrl(QtCore.QUrl("about:blank"))
		except:
			self.webMainExists = False
			self.webMain = QtGui.QTextBrowser(self.uiMain.centralwidget)
			self.webMain.setGeometry(QtCore.QRect(5, 130, 390, 280))
			self.webMain.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
			self.webMain.setOpenLinks(False)

		# Centre window on screen
		screen = QtGui.QDesktopWidget().screenGeometry()
		size =  self.winMain.geometry()
		self.winMain.move((screen.width()-size.width())/2, (screen.height()-size.height())/2)

		# Connect signals to functions
		QtCore.QObject.connect(self.uiMain.btnLogin, QtCore.SIGNAL("clicked()"), self.btnLoginClicked)
		QtCore.QObject.connect(self.uiMain.txtAccount, QtCore.SIGNAL("returnPressed()"), self.txtAccountEnter)
		QtCore.QObject.connect(self.uiMain.txtPassword, QtCore.SIGNAL("returnPressed()"), self.txtPasswordEnter)
		QtCore.QObject.connect(self.uiMain.actionAbout, QtCore.SIGNAL("activated()"), self.actionAboutSelected)
		QtCore.QObject.connect(self.uiMain.actionPatch, QtCore.SIGNAL("activated()"), self.actionPatchSelected)
		QtCore.QObject.connect(self.uiMain.actionOptions, QtCore.SIGNAL("activated()"), self.actionOptionsSelected)
		QtCore.QObject.connect(self.uiMain.actionSettings_Wizard, QtCore.SIGNAL("activated()"), self.actionWizardSelected)
		QtCore.QObject.connect(self.uiMain.actionSwitch_Game, QtCore.SIGNAL("activated()"), self.actionSwitchSelected)
		QtCore.QObject.connect(self.uiMain.actionCheck_Bottle, QtCore.SIGNAL("activated()"), self.actionCheckSelected)
		QtCore.QObject.connect(self.winMain, QtCore.SIGNAL("AddLog(QString)"), self.AddLog)
		QtCore.QObject.connect(self.winMain, QtCore.SIGNAL("ReturnLangConfig(PyQt_PyObject)"), self.GetLanguageConfig)
		QtCore.QObject.connect(self.winMain, QtCore.SIGNAL("ReturnBaseConfig(PyQt_PyObject)"), self.GetBaseConfig)
		QtCore.QObject.connect(self.winMain, QtCore.SIGNAL("ReturnGLSDataCentre(PyQt_PyObject)"), self.GetGLSDataCentre)
		QtCore.QObject.connect(self.winMain, QtCore.SIGNAL("ReturnWorldQueueConfig(PyQt_PyObject)"),
			self.GetWorldQueueConfig)
		QtCore.QObject.connect(self.winMain, QtCore.SIGNAL("ReturnNews(QString)"), self.GetNews)

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

	def actionCheckSelected(self):
		confCheck = CheckConfig(self.winMain, self.settings, self.valHomeDir)
		confCheck.Run()

	def actionAboutSelected(self):
		dlgAbout = QtGui.QDialog(self.winMain)

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
		ui.lblCLIReference.setText(Information.CLIReference)
		ui.lblLotROLinuxReference.setText(Information.LotROLinuxReference)
		dlgAbout.exec_()

	def actionPatchSelected(self):
		winPatch = PatchWindow(self.winMain, self.dataCentre.patchServer, self.worldQueueConfig.patchProductCode,
			self.langConfig.langList[self.uiMain.cboLanguage.currentIndex()].code,
			self.settings.gameDir, self.settings.patchClient, self.settings.wineProg,
			self.settings.hiResEnabled, self.gameType.icoFile, self.valHomeDir, self.settings.winePrefix,
			self.settings.app, self.osType, self.rootDir)
		
		winPatch.Run(self.app)

	def actionOptionsSelected(self):
		winSettings = SettingsWindow(self.winMain, self.settings.hiResEnabled, self.settings.app,
			self.settings.wineProg, self.settings.wineDebug, self.settings.patchClient,
			self.settings.winePrefix, self.settings.gameDir, self.valHomeDir, self.osType, self.rootDir)
		
		if winSettings.Run() == QtGui.QDialog.Accepted:
			self.settings.hiResEnabled = winSettings.getHiRes()
			self.settings.app = winSettings.getApp()
			self.settings.wineProg = winSettings.getProg()
			self.settings.wineDebug = winSettings.getDebug()
			self.settings.patchClient = winSettings.getPatchClient()
			self.settings.winePrefix = winSettings.getPrefix()
			self.settings.gameDir = winSettings.getGameDir()
			self.settings.SaveSettings(self.uiMain.chkSaveSettings.isChecked())
			self.InitialSetup()

	def actionWizardSelected(self):
		winWizard = SettingsWizard(self.winMain, self.valHomeDir, self.osType, self.rootDir)

		if winWizard.Run() == QtGui.QDialog.Accepted:
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

	def actionSwitchSelected(self):
		dlgChooseAccount = QtGui.QDialog(self.winMain)

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

		if dlgChooseAccount.exec_() == QtGui.QDialog.Accepted:
			if ui.comboBox.currentIndex() == 0:
				self.currentGame = "LOTRO"
			elif ui.comboBox.currentIndex() == 1:
				self.currentGame = "LOTRO.Test"
			elif ui.comboBox.currentIndex() == 2:
				self.currentGame = "DDO"
			elif ui.comboBox.currentIndex() == 3:
				self.currentGame = "DDO.Test"

			self.InitialSetup()

	def btnLoginClicked(self):
		if self.uiMain.txtAccount.text() == "" or self.uiMain.txtPassword.text() == "":
			self.AddLog("Please enter account name and password")
		else:
			if self.uiMain.chkSaveSettings.isChecked():
				self.settings.account = self.uiMain.txtAccount.text()
				self.settings.realm = self.uiMain.cboRealm.currentText()
				self.settings.language = self.langConfig.langList[self.uiMain.cboLanguage.currentIndex()].code
				self.settings.SaveSettings(self.uiMain.chkSaveSettings.isChecked())

			self.AuthAccount();

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
			self.uiMain.txtPassword.text(), self.baseConfig.gameName)

		if self.account.authSuccess:
			self.AddLog("Account authenticated")

			tempRealm = ""

			if len(self.account.gameList) > 1:
				dlgChooseAccount = QtGui.QDialog(self.winMain)

				uifile = None

				try:
					from pkg_resources import resource_filename
					uifile = resource_filename(__name__, 'ui/winSelectAccount.ui')
				except:
					uifile = os.path.join(self.rootDir, "ui", "winSelectAccount.ui")

				Ui_dlgChooseAccount, base_class = uic.loadUiType(uifile)
				ui = Ui_dlgChooseAccount()
				ui.setupUi(dlgChooseAccount)
				ui.lblMessage.setText("Multiple game accounts found\n\nPlease select the required game")

				for game in self.account.gameList:
					ui.comboBox.addItem(game.description)

				if dlgChooseAccount.exec_() == QtGui.QDialog.Accepted:
					self.accNumber = self.account.gameList[ui.comboBox.currentIndex()].name
				else:
					self.AddLog("No game selected - aborting")
					return
			else:
				self.accNumber = self.account.gameList[0].name

			tempRealm = self.dataCentre.realmList[self.uiMain.cboRealm.currentIndex()]
			tempRealm.CheckRealm(self.settings.usingDND)

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
		game = StartGame(self.winMain, self.worldQueueConfig.gameClientFilename,
			self.worldQueueConfig.gameClientArgTemplate, self.accNumber, self.urlLoginServer,
			self.account.ticket, self.urlChatServer,
			self.langConfig.langList[self.uiMain.cboLanguage.currentIndex()].code,
			self.settings.gameDir, self.settings.wineProg, self.settings.wineDebug,
			self.settings.winePrefix, self.settings.hiResEnabled, self.settings.app,
			self.osType, self.valHomeDir, self.gameType.icoFile, self.rootDir)

		self.winMain.hide()
		game.Run(self.app)

	def EnterWorldQueue(self, queueURL):
		self.worldQueue = JoinWorldQueue(self.worldQueueConfig.worldQueueParam,
			self.accNumber, self.account.ticket, queueURL, self.worldQueueConfig.worldQueueURL)

		if self.worldQueue.joinSuccess:
			self.AddLog("Joined world queue")

			displayQueueing = True

			while self.worldQueue.number > self.worldQueue.serving and self.worldQueue.joinSuccess:
				if displayQueueing:
					self.AddLog("Currently queueing, please wait...")
					displayQueueing = False

				self.worldQueue = JoinWorldQueue(self.worldQueueConfig.worldQueueParam,
					self.accNumber, self.account.ticket, queueURL, self.worldQueueConfig.worldQueueURL)

				if not self.worldQueue.joinSuccess:
					self.AddLog("[E10] Error getting realm status")

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
			self.webMain.setHtml(QtCore.QString(""))
		else:
			self.webMain.setText(QtCore.QString(""))

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

		self.gameType.GetSettings(self.settings.usingDND, self.settings.usingTest)

		pngFile = None
		icoFile = None

		try:
			from pkg_resources import resource_filename
			pngFile = resource_filename(__name__, self.gameType.pngFile.replace("\\", "/"))
			icoFile = resource_filename(__name__, self.gameType.icoFile.replace("\\", "/"))
		except:
			pngFile = os.path.join(self.rootDir, self.gameType.pngFile)
			icoFile = os.path.join(self.rootDir, self.gameType.icoFile)

		self.uiMain.imgMain.setPixmap(QtGui.QPixmap(pngFile))
		self.winMain.setWindowTitle(self.gameType.title)
		icon = QtGui.QIcon()
		icon.addPixmap(QtGui.QPixmap(icoFile), QtGui.QIcon.Normal, QtGui.QIcon.Off)
		self.winMain.setWindowIcon(icon)

		self.configFile = "%s%s" % (self.settings.gameDir, self.gameType.configFile)
		self.gameDirExists = os.path.exists(self.settings.gameDir)

		if self.gameDirExists:
			self.uiMain.actionCheck_Bottle.setEnabled(True)
			self.uiMain.actionCheck_Bottle.setVisible(True)

			if self.settings.app == "Wine":
				self.uiMain.actionCheck_Bottle.setText("Check Prefix")
			else:
				self.uiMain.actionCheck_Bottle.setText("Check Bottle")
		else:
			self.AddLog("[E13] Game Directory not found")

		self.langConfig = None

		self.configThread = MainWindowThread()
		self.configThread.SetUp(self.winMain, self.settings, self.configFile)
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
			self.webMain.setHtml(QtCore.QString(news))
		else:
			newsString = news
			temp = news.split("</head>")
			if len(temp) > 0:
				newsString = temp[1].split("</html>")[0]

			self.webMain.setHtml(QtCore.QString(newsString))

	def GetHomeDir(self):
		temp = os.environ.get('HOME')

		if not temp.endswith("/"):
			temp += "/"

		return temp

	def ClearLog(self):
		self.uiMain.txtStatus.setText(QtCore.QString(""))

	def AddLog(self, message):
		self.uiMain.txtStatus.append(QtCore.QString(message))

class MainWindowThread(QtCore.QThread):
	def SetUp(self, winMain, settings, configFile):
		self.winMain = winMain
		self.settings = settings
		self.configFile = configFile

	def run(self):
		self.LoadLanguageList()

	def LoadLanguageList(self):
		self.langConfig = LanguageConfig(self.settings.gameDir)

		if self.langConfig.langFound:
			QtCore.QObject.emit(self.winMain, QtCore.SIGNAL("AddLog(QString)"), "Available languages checked.")
			QtCore.QObject.emit(self.winMain, QtCore.SIGNAL("ReturnLangConfig(PyQt_PyObject)"), self.langConfig)

			self.langPos = 0
			setPos = 0

			for lang in self.langConfig.langList:
				if lang.code == self.settings.language:
					self.langPos = setPos
				setPos += 1

			self.LoadLauncherConfig()
		else:
			QtCore.QObject.emit(self.winMain, QtCore.SIGNAL("AddLog(QString)"), "[E02] No language files found.")

	def LoadLauncherConfig(self):
		self.baseConfig = BaseConfig(self.configFile)

		if self.baseConfig.isConfigOK:
			QtCore.QObject.emit(self.winMain, QtCore.SIGNAL("ReturnBaseConfig(PyQt_PyObject)"), self.baseConfig)

			self.AccessGLSDataCentre(self.baseConfig.GLSDataCentreService, self.baseConfig.gameName)
		else:
			self.configFile = "%s%s" % (self.settings.gameDir, self.gameType.configFileAlt)
			self.baseConfig = BaseConfig(self.configFile)

			if self.baseConfig.isConfigOK:
				QtCore.QObject.emit(self.winMain, QtCore.SIGNAL("ReturnBaseConfig(PyQt_PyObject)"), self.baseConfig)

				self.AccessGLSDataCentre(self.baseConfig.GLSDataCentreService, self.baseConfig.gameName)
			else:
				QtCore.QObject.emit(self.winMain, QtCore.SIGNAL("AddLog(QString)"),
					"[E03] Error reading launcher configuration file.")

	def AccessGLSDataCentre(self, urlGLS, gameName):
		self.dataCentre = GLSDataCentre(urlGLS, gameName)

		if self.dataCentre.loadSuccess:
			QtCore.QObject.emit(self.winMain, QtCore.SIGNAL("AddLog(QString)"), "Fetched details from GLS data centre.")
			QtCore.QObject.emit(self.winMain, QtCore.SIGNAL("ReturnGLSDataCentre(PyQt_PyObject)"), self.dataCentre)
			QtCore.QObject.emit(self.winMain, QtCore.SIGNAL("AddLog(QString)"), "Realm list obtained.")

			self.GetWorldQueueConfig(self.dataCentre.launchConfigServer)
		else:
			QtCore.QObject.emit(self.winMain, QtCore.SIGNAL("AddLog(QString)"), "[E04] Error accessing GLS data centre.")

	def GetWorldQueueConfig(self, urlWorldQueueServer):
		self.worldQueueConfig = WorldQueueConfig(urlWorldQueueServer, self.settings.usingDND)

		if self.worldQueueConfig.loadSuccess:
			QtCore.QObject.emit(self.winMain, QtCore.SIGNAL("AddLog(QString)"), "World queue configuration read")
			QtCore.QObject.emit(self.winMain, QtCore.SIGNAL("ReturnWorldQueueConfig(PyQt_PyObject)"), self.worldQueueConfig)

			self.GetNews()
		else:
			QtCore.QObject.emit(self.winMain, QtCore.SIGNAL("AddLog(QString)"),
				"[E05] Error getting world queue configuration")

	def GetNews(self):
		try:
			urlNewsFeed = self.worldQueueConfig.newsFeedURL.replace("{lang}",
				self.langConfig.langList[self.langPos].code.replace("_", "-"))

			if urlNewsFeed.upper().find("HTTP://") >= 0:
				temp = urlNewsFeed[:7]
				url = urlNewsFeed[7:].split("/")[0]
				post = urlNewsFeed[7:].replace(url, "")
				webservice = HTTPConnection(url)
			else:
				temp = urlNewsFeed[:8]
				url = urlNewsFeed[8:].split("/")[0]
				post = urlNewsFeed[8:].replace(url, "")
				webservice = HTTPSConnection(url)

			webservice.putrequest("GET", post)
			webservice.endheaders()

			webresp = webservice.getresponse()

			processor = Processor.Processor()
			transform = NonvalidatingReader.parseUri(self.worldQueueConfig.newsStyleSheetURL)
			source = NonvalidatingReader.parseString(webresp.read(), "http://www.lotrolinux.com/news.xml")
			processor.appendStylesheetNode(transform, "")
			result = processor.runNode(source, "")

			QtCore.QObject.emit(self.winMain, QtCore.SIGNAL("ReturnNews(QString)"), result)
		except:
			QtCore.QObject.emit(self.winMain, QtCore.SIGNAL("AddLog(QString)"), "[E12] Error gettings news")

