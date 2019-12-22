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
# (C) 2019 June Stepp <git@junestepp.me>
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
from qtpy import QtCore, QtWidgets, uic
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

        self.winLog = QtWidgets.QDialog(parent, QtCore.Qt.FramelessWindowHint)

        uifile = resource_filename(__name__, "ui" + os.sep + "winPatch.ui")
        Ui_winLog, base_class = uic.loadUiType(uifile)
        self.uiLog = Ui_winLog()
        self.uiLog.setupUi(self.winLog)

        if self.osType.usingWindows:
            self.winLog.setWindowTitle("Output")
        else:
            self.winLog.setWindowTitle("Patch - Wine output")

        self.uiLog.btnSave.setText("Save Log")
        self.uiLog.btnSave.setEnabled(False)
        self.uiLog.progressBar.reset()
        self.uiLog.btnStop.setText("Launcher")
        self.uiLog.btnStart.setText("Patch")
        self.uiLog.btnSave.clicked.connect(self.btnSaveClicked)
        self.uiLog.btnStop.clicked.connect(self.btnStopClicked)
        self.uiLog.btnStart.clicked.connect(self.btnStartClicked)

        self.aborted = False
        self.finished = True
        self.lastRun = False
        self.command = ""
        self.arguments = []

        self.progressMonitor = ProgressMonitor(self.uiLog)

        self.process = QtCore.QProcess()
        self.process.readyReadStandardOutput.connect(self.readOutput)
        self.process.readyReadStandardError.connect(self.readErrors)
        self.process.finished.connect(self.processFinished)

        processEnviroment = QtCore.QProcessEnvironment.systemEnvironment()

        if winePrefix != "":
            processEnviroment.insert("WINEPREFIX", winePrefix)

        self.process.setProcessEnvironment(processEnviroment)

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
            patchParams = (
                "rundll32.exe %s,Patch %s --language %s --productcode %s"
                % (patchClient, urlPatchServer, language, prodCode)
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
        self.uiLog.txtLog.append(line)
        self.progressMonitor.parseOutput(line)

    def readErrors(self):
        self.uiLog.txtLog.append(
            QByteArray2str(self.process.readAllStandardError())
        )

    def resetButtons(self):
        self.finished = True
        self.uiLog.btnStop.setText("Launcher")
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
        filename = QtWidgets.QFileDialog.getSaveFileName(
            self.winLog, "Save log file", self.homeDir
        )[0]

        if filename != "":
            with open(filename, "w") as outfile:
                outfile.write(self.uiLog.txtLog.toPlainText())

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
        self.uiLog.btnStart.setEnabled(False)
        self.uiLog.btnStop.setText("Abort")
        self.uiLog.btnSave.setEnabled(False)
        self.process.start(self.command, self.file_arguments)

    def Run(self, app):
        self.__app = app

        self.winLog.exec_()
