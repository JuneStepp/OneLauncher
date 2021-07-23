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
# (C) 2019-2021 June Stepp <contact@JuneStepp.me>
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
from PySide6 import QtCore, QtWidgets
from PySide6.QtUiTools import QUiLoader
from OneLauncher.OneLauncherUtils import QByteArray2str
from OneLauncher.ProgressMonitor import ProgressMonitor
from OneLauncher import Settings
from pathlib import Path
import os
import logging


class PatchWindow:
    def __init__(
        self,
        urlPatchServer,
        prodCode,
        language,
        runDir: Path,
        patchClient: Path,
        wineProgram: Path,
        highResEnabled,
        winePrefix: Path,
        wineDebug,
        parent,
        data_folder: Path,
        current_game,
        gameDocumentsDir: Path,
    ):

        self.logger = logging.getLogger("main")

        self.winLog = QUiLoader().load(str(data_folder/"ui/winPatch.ui"), parentWidget=parent)

        self.winLog.setWindowFlags(
            QtCore.Qt.Dialog | QtCore.Qt.FramelessWindowHint)

        if Settings.usingWindows:
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

        self.process_status_timer = QtCore.QTimer()
        self.process_status_timer.timeout.connect(
            self.activelyShowProcessStatus)

        patchClient = runDir/patchClient
        # Fix for the at least one person who has a title case patchclient.dll
        if patchClient.name == "patchclient.dll" and not patchClient.exists():
            patchClient = runDir/"PatchClient.dll"

        # Make sure patchClient exists
        if not patchClient.exists():
            self.winLog.txtLog.append(
                '<font color="Khaki">Patch client %s not found</font>' % (
                    patchClient)
            )
            self.logger.error("Patch client %s not found" % (patchClient))
            return

        self.progressMonitor = ProgressMonitor(self.winLog)

        self.process = QtCore.QProcess()
        self.process.readyReadStandardOutput.connect(self.readOutput)
        self.process.readyReadStandardError.connect(self.readErrors)
        self.process.finished.connect(self.processFinished)

        processEnvironment = QtCore.QProcessEnvironment.systemEnvironment()

        if Settings.usingWindows:
            self.arguments = [
                patchClient,
                "Patch",
                urlPatchServer,
                "--language",
                language,
                "--productcode",
                prodCode,
            ]

            self.command = "rundll32.exe"

            # Get log file to read patching details from, since
            # rundll32 doesn't provide output on Windows
            log_folder_name = gameDocumentsDir

            game_logs_folder = Path(os.environ.get(
                "APPDATA")).parent/"Local"/log_folder_name

            self.patch_log_file = game_logs_folder/"PatchClient.log"
            self.patch_log_file.unlink(missing_ok=True)
            self.patch_log_file.touch()
            self.patch_log_file = self.patch_log_file.open(mode="r")
        else:
            if winePrefix != "":
                processEnvironment.insert("WINEPREFIX", str(winePrefix))

            if wineDebug != "":
                processEnvironment.insert("WINEDEBUG", wineDebug)

            self.arguments = [
                "rundll32.exe",
                str(patchClient),
                "Patch",
                urlPatchServer,
                "--language",
                language,
                "--productcode",
                prodCode,
            ]

            self.command = str(wineProgram)

        self.process.setProcessEnvironment(processEnvironment)
        self.process.setWorkingDirectory(str(runDir))

        if highResEnabled:
            self.arguments.append("--highres")

        self.file_arguments = self.arguments.copy()
        self.file_arguments.append("--filesonly")

    def readOutput(self):
        line = QByteArray2str(self.process.readAllStandardOutput())
        self.winLog.txtLog.append(line)
        self.progressMonitor.parseOutput(line)
        self.logger.debug("Patcher: " + line)

    def readErrors(self):
        line = QByteArray2str(self.process.readAllStandardError())
        self.winLog.txtLog.append(line)
        self.logger.debug("Patcher: " + line)

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
            self.winLog, "Save log file", str(
                Settings.platform_dirs.user_log_dir)
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
            if Settings.usingWindows:
                self.patch_log_file.close()
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
        self.winLog.txtLog.append("<b>***  Started  ***</b>")

        if Settings.usingWindows:
            self.process_status_timer.start(100)

    def activelyShowProcessStatus(self):
        """
        Gives patching progress on Windows where rundll32
        doesn't provide output.
        """
        if self.process.state() != QtCore.QProcess.Running:
            return

        line = self.patch_log_file.readline()
        if line:
            # Ignore information only relevent to log
            if not line.startswith("//"):
                line = line.split(": ")[1]

                self.winLog.txtLog.append(line)
                self.progressMonitor.parseOutput(line)
                self.logger.debug("Patcher: " + line)
        else:
            # Add "..." if log is not giving indicator of patching progress
            self.winLog.txtLog.append("...")

        self.process_status_timer.start(100)

    def Run(self, app):
        self.__app = app

        self.winLog.exec_()
