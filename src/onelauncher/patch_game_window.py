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
import logging
import os
from pathlib import Path

from PySide6 import QtCore, QtWidgets
from PySide6.QtUiTools import QUiLoader

from onelauncher import settings, logger, game_settings
from onelauncher.ui.patching_window_uic import Ui_patchingWindow
from onelauncher.utilities import QByteArray2str
from onelauncher.patching_progress_monitor import ProgressMonitor
from onelauncher.wine_management import edit_qprocess_to_use_wine


class PatchWindow(QtWidgets.QDialog):
    def __init__(
        self,
        urlPatchServer,
        gameDocumentsDir: Path,
    ):
        super(PatchWindow, self).__init__(
            QtCore.QCoreApplication.instance().activeWindow(), QtCore.Qt.FramelessWindowHint)

        self.ui = Ui_patchingWindow()
        self.ui.setupUi(self)

        if settings.usingWindows:
            self.setWindowTitle("Patching Output")
        else:
            self.setWindowTitle("Patching - Wine output")

        self.ui.btnSave.setText("Save Log")
        self.ui.btnSave.setEnabled(False)
        self.ui.progressBar.reset()
        self.ui.btnStop.setText("Close")
        self.ui.btnStart.setText("Patch")
        self.ui.btnSave.clicked.connect(self.btnSaveClicked)
        self.ui.btnStop.clicked.connect(self.btnStopClicked)
        self.ui.btnStart.clicked.connect(self.btnStartClicked)

        self.aborted = False
        self.finished = True
        self.lastRun = False

        self.process_status_timer = QtCore.QTimer()
        self.process_status_timer.timeout.connect(
            self.activelyShowProcessStatus)

        patch_client = game_settings.current_game.game_directory / \
            game_settings.current_game.patch_client_path
        # Fix for the at least one person who has a title case patchclient.dll
        if patch_client.name == "patchclient.dll" and not patch_client.exists():
            patch_client = patch_client.parent/"PatchClient.dll"

        # Make sure patch_client exists
        if not patch_client.exists():
            self.ui.txtLog.append(
                '<font color="Khaki">Patch client %s not found</font>' % (
                    patch_client)
            )
            logger.error("Patch client %s not found" % (patch_client))
            return

        self.progressMonitor = ProgressMonitor(self.ui)

        self.process = QtCore.QProcess()
        self.process.readyReadStandardOutput.connect(self.readOutput)
        self.process.readyReadStandardError.connect(self.readErrors)
        self.process.finished.connect(self.processFinished)
        self.process.setWorkingDirectory(
            str(game_settings.current_game.game_directory))

        if settings.usingWindows:
            # Get log file to read patching details from, since
            # rundll32 doesn't provide output on Windows
            log_folder_name = gameDocumentsDir

            game_logs_folder = Path(os.environ.get(
                "APPDATA")).parent/"Local"/log_folder_name

            patch_log_path = game_logs_folder/"PatchClient.log"
            patch_log_path.unlink(missing_ok=True)
            patch_log_path.touch()
            self.patch_log_file = patch_log_path.open(mode="r")

        self.process.setProgram("rundll32.exe")
        arguments = [
            str(patch_client),
            "Patch",
            urlPatchServer,
            "--language",
            game_settings.current_game.locale.game_language_name,
        ]

        if game_settings.current_game.high_res_enabled:
            arguments.append("--highres")
        self.process.setArguments(arguments)
        edit_qprocess_to_use_wine(self.process)

        # Arguments have to be gotten from self.process, because
        # they mey have been changed by edit_qprocess_to_use_wine().
        self.file_arguments = self.process.arguments().copy()
        self.file_arguments.append("--filesonly")
        self.data_arguments = self.process.arguments().copy()
        self.data_arguments.append("--dataonly")

    def readOutput(self):
        line = QByteArray2str(self.process.readAllStandardOutput())
        self.ui.txtLog.append(line)
        self.progressMonitor.parseOutput(line)
        logger.debug("Patcher: " + line)

    def readErrors(self):
        line = QByteArray2str(self.process.readAllStandardError())
        self.ui.txtLog.append(line)
        logger.debug("Patcher: " + line)

    def resetButtons(self):
        self.finished = True
        self.ui.btnStop.setText("Close")
        self.ui.btnSave.setEnabled(True)
        self.ui.btnStart.setEnabled(True)
        self.progressMonitor.reset()
        if self.aborted:
            self.ui.txtLog.append("<b>***  Aborted  ***</b>")
        elif self.lastRun:
            self.ui.txtLog.append("<b>***  Finished  ***</b>")

    def btnStopClicked(self):
        if self.finished:
            self.close()
        else:
            self.process.kill()
            self.aborted = True

    def btnSaveClicked(self):
        filename = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save log file", str(
                settings.platform_dirs.user_log_path)
        )[0]

        if filename != "":
            with open(filename, "w") as outfile:
                outfile.write(self.ui.txtLog.toPlainText())

    def processFinished(self, exitCode, exitStatus):
        if self.aborted:
            self.resetButtons()
            return
        # handle remaining patching phases
        if self.phase == 1:
            # run file patching again (to avoid problems when patchclient.dll self-patches)
            self.process.setArguments(self.file_arguments)
            self.process.start()
        elif self.phase == 2:
            # run data patching
            self.process.setArguments(self.data_arguments)
            self.process.start()
        else:
            # finished
            self.lastRun = True
            self.resetButtons()
            if settings.usingWindows:
                self.patch_log_file.close()
        self.phase += 1

    def btnStartClicked(self):
        self.lastRun = False
        self.aborted = False
        self.finished = False
        self.phase = 1
        self.ui.btnStart.setEnabled(False)
        self.ui.btnStop.setText("Abort")
        self.ui.btnSave.setEnabled(False)

        self.process.start()
        self.ui.txtLog.append("<b>***  Started  ***</b>")

        if settings.usingWindows:
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

                self.ui.txtLog.append(line)
                self.progressMonitor.parseOutput(line)
                logger.debug("Patcher: " + line)
        else:
            # Add "..." if log is not giving indicator of patching progress
            self.ui.txtLog.append("...")

        self.process_status_timer.start(100)

    def Run(self):
        self.__app = QtCore.QCoreApplication.instance()

        self.exec()
