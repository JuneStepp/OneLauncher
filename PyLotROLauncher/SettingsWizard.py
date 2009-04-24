# coding=utf-8
###########################################################################
# Name:   SettingsWizard
# Author: Alan Jackson
# Date:   4th April 2009
#
# Settings wizard for the Linux/OS X based launcher
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
from PyQt4 import QtCore, QtGui, uic
from .PyLotROUtils import DetermineOS
import os.path
import glob

class SettingsWizard:
	def __init__(self, parent, homeDir, osType, rootDir):

		self.homeDir = homeDir
		self.osType = osType
		self.prefix = ""
		self.gameDir = ""

		self.winSettings = QtGui.QDialog(parent)

		uifile = None

		try:
			from pkg_resources import resource_filename
			uifile = resource_filename(__name__, 'ui/winGameWizard.ui')
		except:
			uifile = os.path.join(rootDir, "ui", "winGameWizard.ui")

		Ui_winGameWizard, base_class = uic.loadUiType(uifile)
		self.uiWizard = Ui_winGameWizard()
		self.uiWizard.setupUi(self.winSettings)
		screen = QtGui.QDesktopWidget().screenGeometry()
		size =  self.winSettings.geometry()
		self.winSettings.move((screen.width()-size.width())/2, (screen.height()-size.height())/2)
		self.winSettings.setWindowTitle("Game Settings")

		self.model = QtGui.QStandardItemModel(0, 3, self.winSettings)
		self.model.setHeaderData(0, QtCore.Qt.Horizontal, QtCore.QVariant("Prefix"))
		self.model.setHeaderData(1, QtCore.Qt.Horizontal, QtCore.QVariant("Game Directory"))
		self.model.setHeaderData(2, QtCore.Qt.Horizontal, QtCore.QVariant("Full Path"))
		self.uiWizard.tblGame.setModel(self.model)
		self.uiWizard.tblGame.setColumnWidth(0, 240)
		self.uiWizard.tblGame.setColumnWidth(1, 410)
		self.uiWizard.tblGame.setColumnWidth(2, 0)
		self.uiWizard.cboApplication.addItem("Wine")
		self.uiWizard.cboApplication.addItem("Crossover Games")
		self.uiWizard.cboApplication.addItem("Crossover Office")
		self.uiWizard.cboGame.addItem("Lord of the Rings Online")
		self.uiWizard.cboGame.addItem("Lord of the Rings Online (Test)")
		self.uiWizard.cboGame.addItem("Dungeons & Dragons Online")
		self.uiWizard.cboGame.addItem("Dungeons & Dragons Online (Test)")

		self.ClearGameTable()

		QtCore.QObject.connect(self.uiWizard.btnFind, QtCore.SIGNAL("clicked()"), self.btnFindClicked)
		QtCore.QObject.connect(self.uiWizard.cboApplication, QtCore.SIGNAL("currentIndexChanged(int)"), self.ClearGameTable)
		QtCore.QObject.connect(self.uiWizard.cboGame, QtCore.SIGNAL("currentIndexChanged(int)"), self.ClearGameTable)
		QtCore.QObject.connect(self.uiWizard.tblGame, QtCore.SIGNAL("clicked(QModelIndex)"), self.GameSelected)

	def GameSelected(self):
		self.uiWizard.btnBoxOptions.setStandardButtons(QtGui.QDialogButtonBox.Apply|QtGui.QDialogButtonBox.Cancel)

		currIndex = self.uiWizard.tblGame.currentIndex()

		self.prefix = self.model.data(currIndex.sibling(self.uiWizard.tblGame.currentIndex().row(), 0)).toString()

		gameDir1 = self.model.data(currIndex.sibling(self.uiWizard.tblGame.currentIndex().row(), 1)).toString()
		gameDir2 = self.model.data(currIndex.sibling(self.uiWizard.tblGame.currentIndex().row(), 2)).toString()
		self.gameDir = gameDir2 + os.sep + gameDir1

	def ClearGameTable(self):
		self.uiWizard.btnBoxOptions.setStandardButtons(QtGui.QDialogButtonBox.Cancel)
		self.model.removeRows(0, self.model.rowCount(QtCore.QModelIndex()), QtCore.QModelIndex())
		
	def btnFindClicked(self):
		self.ClearGameTable()

		if self.uiWizard.cboGame.currentIndex() == 0 or self.uiWizard.cboGame.currentIndex() == 1:
			self.client = "lotroclient.exe"
		else:
			self.client = "dndclient.exe"

		if self.uiWizard.cboApplication.currentIndex() == 0:
			startDir = self.homeDir + ".*"
		elif self.uiWizard.cboApplication.currentIndex() == 1:
			startDir = self.homeDir + self.osType.settingsCXG + "/*"
		else:
			startDir = self.homeDir + self.osType.settingsCXO + "/*"

		for name in glob.glob(startDir):
			if os.path.isdir(name):
				if os.path.exists(os.path.join(name, "drive_c")):
					prefix = ""
					path = os.path.join(name, "drive_c", "Program Files")

					if self.uiWizard.cboApplication.currentIndex() == 0:
						prefix = name
					elif self.uiWizard.cboApplication.currentIndex() == 1:
						prefix = name.replace(self.homeDir + self.osType.settingsCXG + "/", "")
					else:
						prefix = name.replace(self.homeDir + self.osType.settingsCXO + "/", "")

					self.trawl(path, prefix, os.path.join(name, "drive_c", "Program Files"))

	def trawl(self, path, prefix, directory):
		for name in glob.glob(directory + "/*"):
			if name.lower().find(self.client) >= 0:
				row = self.model.rowCount(QtCore.QModelIndex())
				self.model.insertRows(row, 1, QtCore.QModelIndex())
				self.model.setData(self.model.index(row, 0, QtCore.QModelIndex()), QtCore.QVariant(prefix))

				dirName = os.path.dirname(name.replace(path + "/", ""))

				self.model.setData(self.model.index(row, 1, QtCore.QModelIndex()), QtCore.QVariant(dirName))
				self.model.setData(self.model.index(row, 2, QtCore.QModelIndex()), QtCore.QVariant(path))

			if os.path.isdir(name):
				if not name.upper().endswith("/BACKUP"):
					self.trawl(path, prefix, name)

	def getApp(self):
		if self.uiWizard.cboApplication.currentIndex() == 0:
			return "Wine"
		elif self.uiWizard.cboApplication.currentIndex() == 1:
			return "CXGames"
		else:
			return "CXOffice"

	def getUsingDND(self):
		if self.uiWizard.cboGame.currentIndex() == 0 or self.uiWizard.cboGame.currentIndex() == 1:
			return False
		else:
			return True

	def getUsingTest(self):
		if self.uiWizard.cboGame.currentIndex() == 0 or self.uiWizard.cboGame.currentIndex() == 2:
			return False
		else:
			return True

	def getPrefix(self):
		return self.prefix

	def getProg(self):
		return "wine"

	def getDebug(self):
		return "fixme-all"

	def getPatchClient(self):
		return "patchclient.dll"

	def getGameDir(self):
		return self.gameDir

	def getHiRes(self):
		if os.path.exists(self.gameDir + os.sep + "client_highres.dat"):
			return True
		else:
			return False

	def Run(self):
		return self.winSettings.exec_()

