#!/usr/bin/env python3
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
from .PyLotROUtils import DetermineOS, QByteArray2str
from .ProgressMonitor import ProgressMonitor
import os.path


class PatchWindow:
    def __init__(self, parent, urlPatchServer, prodCode, language, runDir, patchClient,
                 wineProgram, hiResEnabled, icoFileIn, homeDir, winePrefix, wineApp, osType, rootDir):

        self.winMain = parent
        self.homeDir = homeDir
        self.winLog = QtGui.QDialog(parent)
        self.winLog.setPalette(parent.palette())
        self.osType = osType

        uifile = None
        icofile = None

        try:
            from pkg_resources import resource_filename
            uifile = resource_filename(__name__, 'ui/winPatch.ui')
            icofile = resource_filename(__name__, icoFileIn)
        except:
            uifile = os.path.join(rootDir, "ui", "winPatch.ui")
            icofile = os.path.join(rootDir, icoFileIn)

        Ui_winLog, base_class = uic.loadUiType(uifile)
        self.uiLog = Ui_winLog()
        self.uiLog.setupUi(self.winLog)
        self.winLog.setWindowFlags(QtCore.Qt.Dialog)
        self.winLog.setWindowIcon(QtGui.QIcon(icofile))
        screen = QtGui.QDesktopWidget().screenGeometry()
        size = self.winLog.geometry()
        self.winLog.move((screen.width() - size.width()) / 2,
                         (screen.height() - size.height()) / 2)

        if self.osType.usingWindows:
            self.winLog.setWindowTitle("Output")
        else:
            if wineApp == "Wine":
                self.winLog.setWindowTitle("Patch - Wine output")
            else:
                self.winLog.setWindowTitle("Patch - Crossover output")

        self.uiLog.btnSave.setText("Save")
        self.uiLog.btnSave.setEnabled(False)
        self.uiLog.progressBar.reset()
        self.uiLog.btnStop.setText("Exit")
        self.uiLog.btnStart.setText("Start")
        QtCore.QObject.connect(self.uiLog.btnSave, QtCore.SIGNAL(
            "clicked()"), self.btnSaveClicked)
        QtCore.QObject.connect(self.uiLog.btnStop, QtCore.SIGNAL(
            "clicked()"), self.btnStopClicked)
        QtCore.QObject.connect(self.uiLog.btnStart, QtCore.SIGNAL(
            "clicked()"), self.btnStartClicked)

        self.aborted = False
        self.finished = True
        self.lastRun = False
        self.command = ""
        self.arguments = []

        self.progressMonitor = ProgressMonitor(self.uiLog)

        if winePrefix != "" and wineApp == "Wine":
            os.environ["WINEPREFIX"] = winePrefix

        self.process = QtCore.QProcess()
        QtCore.QObject.connect(self.process, QtCore.SIGNAL(
            "readyReadStandardOutput()"), self.readOutput)
        QtCore.QObject.connect(self.process, QtCore.SIGNAL(
            "readyReadStandardError()"), self.readErrors)
        QtCore.QObject.connect(self.process, QtCore.SIGNAL("finished(int, QProcess::ExitStatus)"),
                               self.processFinished)

        if wineApp == "Native":
            patchParams = "%s,Patch %s --language %s --productcode %s" % (patchClient, urlPatchServer, language, prodCode)

            if hiResEnabled:
                patchParams = patchParams + " --highres"

            self.command = "rundll32.exe"
            self.process.setWorkingDirectory(runDir)

            for arg in patchParams.split(" "):
                self.arguments.append(arg)

        elif wineApp == "Wine":
            patchParams = "rundll32.exe %s,Patch %s --language %s --productcode %s" % (patchClient, urlPatchServer, language, prodCode)

            if hiResEnabled:
                patchParams = patchParams + " --highres"

            self.command = wineProgram
            self.process.setWorkingDirectory(runDir)
            self.uiLog.txtLog.append(patchParams)

            for arg in patchParams.split(" "):
                self.arguments.append(arg)

        else:
            tempArg = ("--bottle %s --cx-app rundll32.exe --verbose " +
                       "%s,Patch %s --language %s --productcode %s") % (winePrefix, patchClient, urlPatchServer, language, prodCode)

            if hiResEnabled:
                tempArg = tempArg + " --highres"

            for arg in tempArg.split(" "):
                self.arguments.append(arg)

            self.process.setWorkingDirectory(runDir)

            if wineApp == "CXGames":
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
                    self.command = "%s%s" % (
                        self.osType.macPathCX, wineProgram)
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
                    self.command = "%s%s" % (
                        self.osType.macPathCX, wineProgram)

    def readOutput(self):
        line = QByteArray2str(self.process.readAllStandardOutput())
        self.uiLog.txtLog.append(line)
        self.progressMonitor.parseOutput(line)

    def readErrors(self):
        self.uiLog.txtLog.append(QByteArray2str(
            self.process.readAllStandardError()))

    def resetButtons(self):
        self.finished = True
        self.uiLog.btnStop.setText("Exit")
        self.uiLog.btnSave.setEnabled(True)
        self.uiLog.btnStart.setEnabled(True)
        self.progressMonitor.reset()
        if self.aborted:
            self.uiLog.txtLog.append("<b>***  Aborted  ***</b>")
        else:
            if self.lastRun:
                self.uiLog.txtLog.append("<b>***  Finished  ***</b>")

    def btnStopClicked(self):
        if self.finished:
            self.winLog.close()
        else:
            self.process.kill()
            self.aborted = True

    def btnSaveClicked(self):
        filename = QtGui.QFileDialog.getSaveFileName(
            self.winLog, "Save log file", self.homeDir)

        if filename != "":
            outfile = open(filename, "w")
            outfile.write(self.uiLog.txtLog.toPlainText())
            outfile.close()

    def processFinished(self, exitCode, exitStatus):
        if self.aborted:
            self.resetButtons()
            return
        # handle remaining patching phases
        if self.phase == 1:
            # run file patching again (to avoid problems when patchclient.dll self-patches)
            self.process.start(self.command, self.arguments)
        elif self.phase == 2:
            # run data patching
            data_arguments = []
            for arg in self.arguments:
                    data_arguments.append(arg)
            self.process.start(self.command, data_arguments)
        else:
            # finished
            self.lastRun = True
            self.resetButtons()
        self.phase += 1

    def btnStartClicked(self):
        self.lastRun = False
        self.aborted = False
        self.finished = False
        self.phase = 1
        self.uiLog.btnStart.setEnabled(False)
        self.uiLog.btnStop.setText("Abort")
        self.uiLog.btnSave.setEnabled(False)
        self.process.start(self.command, self.arguments)

    def Run(self, app):
        self.__app = app

        self.winLog.exec_()
