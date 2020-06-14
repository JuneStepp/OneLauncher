#!/usr/bin/env python3
# coding=utf-8
###########################################################################
# Patching window for OneLauncher.
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
from PySide2 import QtCore, QtWidgets
from PySide2.QtUiTools import QUiLoader
from .OneLauncherUtils import QByteArray2str
from .ProgressMonitor import ProgressMonitor
import os.path
from pkg_resources import resource_filename


class PatchWindow:
    def __init__(
        self,
        urlPatchServer,
        prodCode,
        language,
        runDir,
        patchClient,
        wineProgram,
        hiResEnabled,
        iconFileIn,
        homeDir,
        winePrefix,
        osType,
        rootDir,
        parent,
    ):

        self.homeDir = homeDir
        self.osType = osType

        ui_file = QtCore.QFile(resource_filename(__name__, "ui" + os.sep + "winPatch.ui"))
        ui_file.open(QtCore.QFile.ReadOnly)
        loader = QUiLoader()
        self.winLog = loader.load(ui_file, parentWidget=parent)
        ui_file.close()

        self.winLog.setWindowFlags(QtCore.Qt.Dialog | QtCore.Qt.FramelessWindowHint)

        if self.osType.usingWindows:
            self.winLog.setWindowTitle("Output")
        else:
            self.winLog.setWindowTitle("Patch - Wine output")

        self.winLog.btnSave.setText("Save Log")
        self.winLog.btnSave.setEnabled(False)
        self.winLog.progressBar.reset()
        self.winLog.btnStop.setText("Close")
        self.winLog.btnStart.setText("Patch")
        self.winLog.btnSave.clicked.connect(self.btnSaveClicked)
        self.winLog.btnStop.clicked.connect(self.btnStopClicked)
        self.winLog.btnStart.clicked.connect(self.btnStartClicked)

        self.aborted = False
        self.finished = True
        self.lastRun = False
        self.command = ""
        self.arguments = []

        self.progressMonitor = ProgressMonitor(self.winLog)

        self.process = QtCore.QProcess()
        self.process.readyReadStandardOutput.connect(self.readOutput)
        self.process.readyReadStandardError.connect(self.readErrors)
        self.process.finished.connect(self.processFinished)

        processEnvironment = QtCore.QProcessEnvironment.systemEnvironment()

        if winePrefix != "":
            processEnvironment.insert("WINEPREFIX", winePrefix)

        self.process.setProcessEnvironment(processEnvironment)

        if self.osType.usingWindows:
            patchParams = "%s,Patch %s --language %s --productcode %s" % (
                patchClient,
                urlPatchServer,
                language,
                prodCode,
            )

            if hiResEnabled:
                patchParams = patchParams + " --highres"

            self.command = "rundll32.exe"
            self.process.setWorkingDirectory(runDir)

            for arg in patchParams.split(" "):
                self.arguments.append(arg)

        else:
            patchParams = "rundll32.exe %s,Patch %s --language %s --productcode %s" % (
                patchClient,
                urlPatchServer,
                language,
                prodCode,
            )

            if hiResEnabled:
                patchParams = patchParams + " --highres"

            self.command = wineProgram
            self.process.setWorkingDirectory(runDir)

            for arg in patchParams.split(" "):
                self.arguments.append(arg)

        self.file_arguments = self.arguments.copy()
        self.file_arguments.append("--filesonly")

    def readOutput(self):
        line = QByteArray2str(self.process.readAllStandardOutput())
        self.winLog.txtLog.append(line)
        self.progressMonitor.parseOutput(line)

    def readErrors(self):
        self.winLog.txtLog.append(QByteArray2str(self.process.readAllStandardError()))

    def resetButtons(self):
        self.finished = True
        self.winLog.btnStop.setText("Close")
        self.winLog.btnSave.setEnabled(True)
        self.winLog.btnStart.setEnabled(True)
        self.progressMonitor.reset()
        if self.aborted:
            self.winLog.txtLog.append("<b>***  Aborted  ***</b>")
        else:
            if self.lastRun:
                self.winLog.txtLog.append("<b>***  Finished  ***</b>")

    def btnStopClicked(self):
        if self.finished:
            self.winLog.close()
        else:
            self.process.kill()
            self.aborted = True

    def btnSaveClicked(self):
        filename = QtWidgets.QFileDialog.getSaveFileName(
            self.winLog, "Save log file", self.homeDir
        )[0]

        if filename != "":
            with open(filename, "w") as outfile:
                outfile.write(self.winLog.txtLog.toPlainText())

    def processFinished(self, exitCode, exitStatus):
        if self.aborted:
            self.resetButtons()
            return
        # handle remaining patching phases
        if self.phase == 1:
            # run file patching again (to avoid problems when patchclient.dll self-patches)
            self.process.start(self.command, self.file_arguments)
        elif self.phase == 2:
            # run data patching
            data_arguments = self.arguments.copy()
            data_arguments.append("--dataonly")
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
        self.winLog.btnStart.setEnabled(False)
        self.winLog.btnStop.setText("Abort")
        self.winLog.btnSave.setEnabled(False)
        self.process.start(self.command, self.file_arguments)

    def Run(self, app):
        self.__app = app

        self.winLog.exec_()
