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
from PyQt5 import QtCore, QtGui, QtWidgets, uic
from .PyLotROUtils import DetermineOS, QByteArray2str
import sys
import os.path


class StartGame:
    def __init__(self, parent, appName, x86, argTemplate, account, server, ticket,
                 chatServer, language, runDir, wineProgram, wineDebug, winePrefix,
                 hiResEnabled, wineApp, osType, homeDir, icoFileIn, rootDir,
                 crashreceiver, DefaultUploadThrottleMbps, bugurl, authserverurl,
                 supporturl, supportserviceurl, glsticketlifetime, realmName, accountText):

        #Fixes binary path for 64-bit client
        if x86:
            appName = ("x64" + os.sep + appName)

        self.winMain = parent
        self.homeDir = homeDir
        self.winLog = QtWidgets.QDialog(parent)
        self.winLog.setPalette(parent.palette())
        self.osType = osType
        self.realmName = realmName
        self.accountText = accountText

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
        self.winLog.setWindowIcon(QtGui.QIcon(icofile))
        screen = QtWidgets.QDesktopWidget().screenGeometry()
        size = self.winLog.geometry()
        self.winLog.move((screen.width() - size.width()) / 2,
                         (screen.height() - size.height()) / 2)

        if self.osType.usingWindows:
            self.winLog.setWindowTitle("Output")
        else:
            if wineApp == "Wine":
                self.winLog.setWindowTitle("Launch Game - Wine output")
            else:
                self.winLog.setWindowTitle("Launch Game - Crossover output")

        # self.uiLog.btnStart.setVisible(False)
        self.uiLog.btnStart.setText("Launcher")
        self.uiLog.btnStart.setEnabled(False)
        self.uiLog.btnSave.setText("Save")
        self.uiLog.btnSave.setEnabled(False)
        self.uiLog.btnStop.setText("Exit")
        self.uiLog.btnStart.clicked.connect(self.btnStartClicked)
        self.uiLog.btnSave.clicked.connect(self.btnSaveClicked)
        self.uiLog.btnStop.clicked.connect(self.btnStopClicked)

        self.aborted = False
        self.finished = False
        self.command = ""
        self.arguments = []

        gameParams = argTemplate.replace("{SUBSCRIPTION}", account).replace("{LOGIN}", server)\
            .replace("{GLS}", ticket).replace("{CHAT}", chatServer).replace("{LANG}", language)\
            .replace("{CRASHRECEIVER}", crashreceiver).replace("{UPLOADTHROTTLE}", DefaultUploadThrottleMbps)\
            .replace("{BUGURL}", bugurl).replace("{AUTHSERVERURL}", authserverurl)\
            .replace("{GLSTICKETLIFETIME}", glsticketlifetime).replace("{SUPPORTURL}", supporturl)\
            .replace("{SUPPORTSERVICEURL}", supportserviceurl)

        if not hiResEnabled:
            gameParams = gameParams + " --HighResOutOfDate"

        if wineDebug != "":
            os.environ["WINEDEBUG"] = wineDebug

        if winePrefix != "" and wineApp == "Wine":
            os.environ["WINEPREFIX"] = winePrefix

        self.process = QtCore.QProcess()
        self.process.readyReadStandardOutput.connect(self.readOutput)
        self.process.readyReadStandardError.connect(self.readErrors)
        self.process.finished.connect(self.resetButtons)

        if wineApp == "Native":
            self.command = appName
            self.process.setWorkingDirectory(runDir)

            os.chdir(runDir)

            for arg in gameParams.split(" "):
                self.arguments.append(arg)

        elif wineApp == "Wine":
            self.command = wineProgram
            self.process.setWorkingDirectory(runDir)

            self.arguments.append(appName)

            for arg in gameParams.split(" "):
                self.arguments.append(arg)

        elif wineApp == "CXGames":
            if not self.osType.startCXG():
                self.uiLog.txtLog.append(
                    "<b>Error: Couldn't start Crossover Games</b>")
                self.uiLog.btnSave.setEnabled(False)
                self.uiLog.btnStart.setEnabled(False)

            if self.osType.macPathCX == "":
                tempFile = "%s%s%s" % (
                    self.osType.globalDir, self.osType.directoryCXG, wineProgram)

                if os.path.isfile(tempFile):
                    self.command = tempFile
                else:
                    tempFile = "%s%s%s" % (
                        homeDir, self.osType.directoryCXG, wineProgram)

                    if os.path.isfile(tempFile):
                        self.command = tempFile
                    else:
                        self.command = wineProgram
            else:
                self.command = "%s%s" % (self.osType.macPathCX, wineProgram)

            self.process.setWorkingDirectory(runDir)

            tempArg = "--bottle %s --verbose -- %s %s" % (
                winePrefix, appName, gameParams)
            for arg in tempArg.split(" "):
                self.arguments.append(arg)
        elif wineApp == "CXOffice":
            if not self.osType.startCXO():
                self.uiLog.txtLog.append(
                    "<b>Error: Couldn't start Crossover</b>")
                self.uiLog.btnSave.setEnabled(False)
                self.uiLog.btnStart.setEnabled(False)

            if self.osType.macPathCX == "":
                tempFile = "%s%s%s" % (
                    self.osType.globalDir, self.osType.directoryCXO, wineProgram)

                if os.path.isfile(tempFile):
                    self.command = tempFile
                else:
                    tempFile = "%s%s%s" % (
                        homeDir, self.osType.directoryCXO, wineProgram)

                    if os.path.isfile(tempFile):
                        self.command = tempFile
                    else:
                        self.command = wineProgram
            else:
                self.command = "%s%s" % (self.osType.macPathCX, wineProgram)

            self.process.setWorkingDirectory(runDir)

            tempArg = "--bottle %s --verbose -- %s %s" % (
                winePrefix, appName, gameParams)
            for arg in tempArg.split(" "):
                self.arguments.append(arg)

        self.uiLog.txtLog.append("Connecting to server: " + realmName)
        self.uiLog.txtLog.append("Account: " + accountText)
        self.uiLog.txtLog.append("Game Directory: " + runDir)
        self.uiLog.txtLog.append("Game Client: " + appName)

    def readOutput(self):
        self.uiLog.txtLog.append(QByteArray2str(
            self.process.readAllStandardOutput()))

    def readErrors(self):
        self.uiLog.txtLog.append(QByteArray2str(
            self.process.readAllStandardError()))

    def resetButtons(self, exitCode, exitStatus):
        self.finished = True
        self.uiLog.btnStop.setText("Exit")
        self.uiLog.btnSave.setEnabled(True)
        self.uiLog.btnStart.setEnabled(True)
        if self.aborted:
            self.uiLog.txtLog.append("<b>***  Aborted  ***</b>")
        else:
            self.uiLog.txtLog.append("<b>***  Finished  ***</b>")

    def btnStartClicked(self):
        if self.finished:
            self.winMain.show()
            self.winLog.close()

    def btnStopClicked(self):
        if self.finished:
            self.winLog.close()
        else:
            self.aborted = True
            self.process.kill()

    def btnSaveClicked(self):
        filename = QtWidgets.QFileDialog.getSaveFileName(
            self.winLog, "Save log file", self.homeDir)[0]

        if filename != "":
            outfile = open(filename, "w")
            outfile.write(self.uiLog.txtLog.toPlainText())
            outfile.close()

    def Run(self):
        self.finished = False

        self.uiLog.btnStop.setText("Abort")
        self.process.start(self.command, self.arguments)

        self.winMain.hide()
        return self.winLog.exec_()
