#!/usr/bin/env python
# coding=utf-8
###########################################################################
# Name:   PatchWindow
# Author: Alan Jackson
# Date:   11th March 2009
#
# Patching window for the Linux/OS X based launcher
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
from .PyLotROUtils import DetermineOS
import os.path

class PatchWindow:
	def __init__(self, parent, urlPatchServer, prodCode, language, runDir, patchClient,
		wineProgram, hiResEnabled, icoFileIn, homeDir, winePrefix, wineApp, osType, rootDir):

		self.homeDir = homeDir
		self.winLog = QtGui.QMainWindow(parent)
		self.osType = osType

		uifile = None
		icofile = None

		try:
			from pkg_resources import resource_filename
			uifile = resource_filename(__name__, 'ui/winLog.ui')
			icofile = resource_filename(__name__, icoFileIn)
		except:
			uifile = os.path.join(rootDir, "ui", "winLog.ui")
			icofile = os.path.join(rootDir, icoFileIn)

		Ui_winLog, base_class = uic.loadUiType(uifile)
		self.uiLog = Ui_winLog()
		self.uiLog.setupUi(self.winLog)
		self.winLog.setWindowFlags(QtCore.Qt.Dialog)
		icon = QtGui.QIcon()
		icon.addPixmap(QtGui.QPixmap(icofile), QtGui.QIcon.Normal, QtGui.QIcon.Off)
		self.winLog.setWindowIcon(icon)
		screen = QtGui.QDesktopWidget().screenGeometry()
		size =  self.winLog.geometry()
		self.winLog.move((screen.width()-size.width())/2, (screen.height()-size.height())/2)

		if wineApp == "Wine":
			self.winLog.setWindowTitle("Wine output")
		else:
			self.winLog.setWindowTitle("Crossover output")

		self.uiLog.btnSave.setText("Save")
		self.uiLog.btnSave.setEnabled(False)
		self.uiLog.btnStop.setText("Exit")
		self.uiLog.btnStart.setText("Start")
		QtCore.QObject.connect(self.uiLog.btnSave, QtCore.SIGNAL("clicked()"), self.btnSaveClicked)
		QtCore.QObject.connect(self.uiLog.btnStop, QtCore.SIGNAL("clicked()"), self.btnStopClicked)
		QtCore.QObject.connect(self.uiLog.btnStart, QtCore.SIGNAL("clicked()"), self.btnStartClicked)

		self.aborted = False
		self.finished = True
		self.lastRun = False
		self.command = ""
		self.arguments = QtCore.QStringList()

		if winePrefix != "" and wineApp == "Wine":
			os.environ["WINEPREFIX"] = winePrefix

		self.process = QtCore.QProcess()
		QtCore.QObject.connect(self.process, QtCore.SIGNAL("readyReadStandardOutput()"), self.readOutput)
		QtCore.QObject.connect(self.process, QtCore.SIGNAL("readyReadStandardError()"), self.readErrors)
		QtCore.QObject.connect(self.process, QtCore.SIGNAL("finished(int, QProcess::ExitStatus)"),
			self.resetButtons)

		if wineApp == "Wine":
			patchParams = "rundll32.exe %s,Patch %s --language %s --productcode %s --filesonly" % (patchClient,
				urlPatchServer, language, prodCode)

			if hiResEnabled:
				patchParams = patchParams + " --highres"

			self.command = QtCore.QString(wineProgram)
			self.process.setWorkingDirectory(runDir)

			for arg in patchParams.split(" "):
				self.arguments.append(QtCore.QString(arg))

		else:
			tempArg = ("--bottle %s --cx-app rundll32.exe --verbose " +
				"%s,Patch %s --language %s --productcode %s --filesonly") % (winePrefix,
					patchClient, urlPatchServer, language, prodCode)

			if hiResEnabled:
				tempArg = tempArg + " --highres"

			for arg in tempArg.split(" "):
				self.arguments.append(QtCore.QString(arg))

			self.process.setWorkingDirectory(runDir)

			if wineApp == "CXGames":
				if not self.osType.startCXG():
					self.uiLog.txtLog.append(QtCore.QString("<b>Error: Couldn't start Crossover Games</b>"))
					self.uiLog.btnSave.setEnabled(False)
					self.uiLog.btnStart.setEnabled(False)

				if self.osType.macPathCX == "":
					tempFile = "%s%s%s" % (self.osType.globalDir, self.osType.directoryCXG, wineProgram)

					if os.path.isfile(tempFile):
						self.command = QtCore.QString(tempFile)
					else:
						tempFile = "%s%s%s" % (homeDir, self.osType.directoryCXG, wineProgram)

						if os.path.isfile(tempFile):
							self.command = QtCore.QString(tempFile)
						else:
							self.command = QtCore.QString(wineProgram)
				else:
					self.command = QtCore.QString("%s%s" % (self.osType.macPathCX, wineProgram))
			elif wineApp == "CXOffice":
				if not self.osType.startCXO():
					self.uiLog.txtLog.append(QtCore.QString("<b>Error: Couldn't start Crossover</b>"))
					self.uiLog.btnSave.setEnabled(False)
					self.uiLog.btnStart.setEnabled(False)

				if self.osType.macPathCX == "":
					tempFile = "%s%s%s" % (self.osType.globalDir, self.osType.directoryCXO, wineProgram)

					if os.path.isfile(tempFile):
						self.command = QtCore.QString(tempFile)
					else:
						tempFile = "%s%s%s" % (homeDir, self.osType.directoryCXO, wineProgram)

						if os.path.isfile(tempFile):
							self.command = QtCore.QString(tempFile)
						else:
							self.command = QtCore.QString(wineProgram)
				else:
					self.command = QtCore.QString("%s%s" % (self.osType.macPathCX, wineProgram))


	def readOutput(self):
		self.uiLog.txtLog.append(QtCore.QString(self.process.readAllStandardOutput()))

	def readErrors(self):
		self.uiLog.txtLog.append(QtCore.QString(self.process.readAllStandardError()))

	def resetButtons(self, exitCode, exitStatus):
		self.finished = True
		self.uiLog.btnStop.setText("Exit")
		self.uiLog.btnSave.setEnabled(True)
		self.uiLog.btnStart.setEnabled(True)
		if self.aborted:
			self.uiLog.txtLog.append(QtCore.QString("<b>***  Aborted  ***</b>"))
		else:
			if self.lastRun:
				self.uiLog.txtLog.append(QtCore.QString("<b>***  Finished  ***</b>"))

	def btnStopClicked(self):
		if self.finished:
			self.winLog.close()
		else:
			self.process.kill()
			self.aborted = True

	def btnSaveClicked(self):
		filename = QtGui.QFileDialog.getSaveFileName(self.winLog, "Save log file", self.homeDir)

		if filename != "":
			outfile = open(filename, "w")
			outfile.write(self.uiLog.txtLog.toPlainText())
			outfile.close()

	def btnStartClicked(self):
		self.lastRun = False
		self.aborted = False
		self.finished = False
		self.uiLog.btnStart.setEnabled(False)
		self.uiLog.btnStop.setText("Abort")
		self.uiLog.btnSave.setEnabled(False)
		self.process.start(self.command, self.arguments)

		while not self.finished:
			self.__app.processEvents()

		if not self.aborted:
			self.finished = False
			self.uiLog.btnStart.setEnabled(False)
			self.uiLog.btnStop.setText("Abort")
			self.uiLog.btnSave.setEnabled(False)
			self.process.start(self.command, self.arguments)

			while not self.finished:
				self.__app.processEvents()

			if not self.aborted:
				self.lastRun = True
				self.finished = False
				self.uiLog.btnStart.setEnabled(False)
				self.uiLog.btnStop.setText("Abort")
				self.uiLog.btnSave.setEnabled(False)

				loop = 0

				while loop < len(self.arguments):
					if self.arguments[loop] == "--filesonly":
						self.arguments[loop] = QtCore.QString("--dataonly")
						loop = len(self.arguments)
					else:
						loop += 1

				self.process.start(self.command, self.arguments)

	def Run(self, app):
		self.winLog.show()

		self.__app = app

		while self.winLog.isVisible():
			self.__app.processEvents()

