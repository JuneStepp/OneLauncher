# coding=utf-8
###########################################################################
# Name:   StartGame
# Author: Alan Jackson
# Date:   11th March 2009
#
# Game launcher for the Linux/OS X based launcher
# for the game Lord of the Rings Online
#
# Based on a script by SNy <SNy@bmx-chemnitz.de>
# Python port of PyLotRO by AJackson <ajackson@bcs.org.uk>
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
from PyLotROUtils import DetermineOS
import os.path

class StartGame:
	def __init__(self, parent, appName, argTemplate, account, server, ticket,
		chatServer, language, runDir, wineProgram, wineDebug, winePrefix, 
		hiResEnabled, wineApp, osType, homeDir, icoFile, rootDir):

		self.homeDir = homeDir
		self.winLog = QtGui.QMainWindow(parent)
		Ui_winLog, base_class = uic.loadUiType(os.path.join(rootDir, "ui", "winLog.ui"))
		self.uiLog = Ui_winLog()
		self.uiLog.setupUi(self.winLog)
		self.winLog.setWindowFlags(QtCore.Qt.Dialog)
		icon = QtGui.QIcon()
		icon.addPixmap(QtGui.QPixmap(icoFile), QtGui.QIcon.Normal, QtGui.QIcon.Off)
		self.winLog.setWindowIcon(icon)
		screen = QtGui.QDesktopWidget().screenGeometry()
		size =  self.winLog.geometry()
		self.winLog.move((screen.width()-size.width())/2, (screen.height()-size.height())/2)

		if wineApp == "Wine":
			self.winLog.setWindowTitle("Wine output")
		else:
			self.winLog.setWindowTitle("Crossover output")

		self.uiLog.btnStart.setVisible(False)
		self.uiLog.btnSave.setText("Save")
		self.uiLog.btnSave.setEnabled(False)
		self.uiLog.btnStop.setText("Exit")
		QtCore.QObject.connect(self.uiLog.btnSave, QtCore.SIGNAL("clicked()"), self.btnSaveClicked)
		QtCore.QObject.connect(self.uiLog.btnStop, QtCore.SIGNAL("clicked()"), self.btnStopClicked)

		self.finished = False
		self.command = ""
		self.arguments = QtCore.QStringList()

		gameParams = argTemplate.replace("{0}", account).replace("{1}", server)\
			.replace("{2}", ticket).replace("{3}", chatServer).replace("{4}", language)

		if not hiResEnabled:
			gameParams = gameParams + " --HighResOutOfDate"

		if wineDebug != "":
			os.environ["WINEDEBUG"] = wineDebug

		if winePrefix != "" and wineApp == "Wine":
			os.environ["WINEPREFIX"] = winePrefix

		self.process = QtCore.QProcess()
		QtCore.QObject.connect(self.process, QtCore.SIGNAL("readyReadStandardOutput()"), self.readOutput)
		QtCore.QObject.connect(self.process, QtCore.SIGNAL("readyReadStandardError()"), self.readErrors)
		QtCore.QObject.connect(self.process, QtCore.SIGNAL("finished(int, QProcess::ExitStatus)"), self.resetButtons)

		if wineApp == "Wine":
			self.command = QtCore.QString(wineProgram)
			self.process.setWorkingDirectory(runDir)

			self.arguments.append(QtCore.QString(appName))

			for arg in gameParams.split(" "):
				self.arguments.append(QtCore.QString(arg))

		elif wineApp == "CXGames":
			if osType.macPathCX == "":
				tempFile = "%s%s%s" % (osType.globalDir, osType.directoryCXG, wineProgram)

				if os.path.isfile(tempFile):
					self.command = QtCore.QString(tempFile)
				else:
					tempFile = "%s%s%s" % (homeDir, osType.directoryCXG, wineProgram)

					if os.path.isfile(tempFile):
						self.command = QtCore.QString(tempFile)
					else:
						self.command = QtCore.QString(wineProgram)
			else:
				self.command = QtCore.QString("%s%s" % (osType.macPathCX, wineProgram))

			self.process.setWorkingDirectory(runDir)

			tempArg = "--bottle %s --verbose -- %s %s" % (winePrefix, appName, gameParams)
			for arg in tempArg.split(" "):
				self.arguments.append(QtCore.QString(arg))
		elif wineApp == "CXOffice":
			if osType.macPathCX == "":
				tempFile = "%s%s%s" % (osType.globalDir, osType.directoryCXO, wineProgram)

				if os.path.isfile(tempFile):
					self.command = QtCore.QString(tempFile)
				else:
					tempFile = "%s%s%s" % (homeDir, osType.directoryCXO, wineProgram)

					if os.path.isfile(tempFile):
						self.command = QtCore.QString(tempFile)
					else:
						self.command = QtCore.QString(wineProgram)
			else:
				self.command = QtCore.QString("%s%s" % (osType.macPathCX, wineProgram))

			self.process.setWorkingDirectory(runDir)

			tempArg = "--bottle %s --verbose -- %s %s" % (winePrefix, appName, gameParams)
			for arg in tempArg.split(" "):
				self.arguments.append(QtCore.QString(arg))

	def readOutput(self):
		self.uiLog.txtLog.append(QtCore.QString(self.process.readAllStandardOutput()))

	def readErrors(self):
		self.uiLog.txtLog.append(QtCore.QString(self.process.readAllStandardError()))

	def resetButtons(self, exitCode, exitStatus):
		self.finished = True
		self.uiLog.btnSave.setEnabled(True)

	def btnStopClicked(self):
		if not self.finished:
			self.process.kill()
		self.winLog.close()

	def btnSaveClicked(self):
		filename = QtGui.QFileDialog.getSaveFileName(self.winLog, "Save log file", self.homeDir)

		if filename != "":
			outfile = open(filename, "w")
			outfile.write(self.uiLog.txtLog.toPlainText())
			outfile.close()

	def Run(self, app):
		self.winLog.show()
		self.finished = False

		self.process.start(self.command, self.arguments)

		while self.winLog.isVisible():
			app.processEvents()

