#!/usr/bin/env python3
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
# (C) 2019-2024 June Stepp <contact@JuneStepp.me>
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
from typing import Literal, TypeAlias
from uuid import UUID

from PySide6 import QtCore, QtWidgets

from .config import platform_dirs
from .config_manager import ConfigManager
from .game_launcher_local_config import GameLauncherLocalConfig
from .game_utilities import get_documents_config_dir
from .patching_progress_monitor import PatchingProgressMonitor
from .ui.patching_window_uic import Ui_patchingDialog
from .utilities import CaseInsensitiveAbsolutePath
from .wine_environment import edit_qprocess_to_use_wine


class PatchWindow(QtWidgets.QDialog):
    PatchPhase: TypeAlias = Literal["FullPatch", "FilesOnly", "DataOnly", "Done"]
    
    def __init__(
        self,
        game_uuid: UUID,
        config_manager: ConfigManager,
        launcher_local_config: GameLauncherLocalConfig,
        urlPatchServer: str,
    ):
        super().__init__(
            qApp.activeWindow(),  # type: ignore[name-defined]  # noqa: F821
            QtCore.Qt.WindowType.FramelessWindowHint,
        )

        self.ui = Ui_patchingDialog()
        self.ui.setupUi(self)

        if os.name == "nt":
            self.setWindowTitle("Patching Output")
        else:
            self.setWindowTitle("Patching WINE Output")

        self.ui.btnSave.setText("Save Log")
        self.ui.btnSave.setEnabled(False)
        self.ui.progressBar.reset()
        self.ui.btnStop.setText("Close")
        self.ui.btnStart.setText("Patch")
        self.ui.btnSave.clicked.connect(self.btnSaveClicked)
        self.ui.btnStop.clicked.connect(self.btnStopClicked)
        self.ui.btnStart.clicked.connect(self.btnStartClicked)

        self.aborted = False
        self.patching_finished = True
        self.lastRun = False
        self.patch_phases: tuple[PatchWindow.PatchPhase, ...] = ("FilesOnly", "FilesOnly", "DataOnly")
        self.phase_index: int = 0

        if os.name == "nt":
            self.process_status_timer = QtCore.QTimer()
            self.process_status_timer.timeout.connect(self.activelyShowProcessStatus)

        game_config = config_manager.get_game_config(game_uuid=game_uuid)
        patch_client = game_config.game_directory / game_config.patch_client_filename

        # Make sure patch_client exists
        if not patch_client.exists():
            self.ui.txtLog.append(
                f'<font color="Red">Patch client {patch_client} not found</font>'
            )
            logger.error(f"Patch client {patch_client} not found")
            return

        self.progress_monitor = PatchingProgressMonitor()

        self.process = QtCore.QProcess()
        self.process.readyReadStandardOutput.connect(self.readOutput)
        self.process.readyReadStandardError.connect(self.readErrors)
        self.process.finished.connect(self.processFinished)
        self.process.setWorkingDirectory(str(game_config.game_directory))

        if os.name == "nt":
            # Get log file to read patching details from, since
            # rundll32 doesn't provide output on Windows
            log_folder_name = get_documents_config_dir(
                launcher_local_config=launcher_local_config
            ).name

            game_logs_folder = (
                CaseInsensitiveAbsolutePath(
                    os.environ.get("APPDATA")
                    or CaseInsensitiveAbsolutePath.home() / "AppData/Roaming"
                ).parent
                / "Local"
                / log_folder_name
            )

            game_logs_folder.mkdir(parents=True, exist_ok=True)
            patch_log_path = game_logs_folder / "PatchClient.log"
            patch_log_path.unlink(missing_ok=True)
            patch_log_path.touch()
            self.patch_log_file = patch_log_path.open(mode="r")

        self.process.setProgram("rundll32.exe")
        arguments = [
            str(patch_client),
            "Patch",
            urlPatchServer,
            "--language",
            game_config.locale.game_language_name
            if game_config.locale
            else config_manager.get_program_config().default_locale.game_language_name,
        ]

        if game_config.high_res_enabled:
            arguments.append("--highres")
        self.process.setArguments(arguments)
        if os.name != "nt":
            edit_qprocess_to_use_wine(
                qprocess=self.process, wine_config=game_config.wine
            )

        # Arguments have to be gotten from self.process, because
        # they mey have been changed by edit_qprocess_to_use_wine().
        self.arguments = self.process.arguments().copy()
        self.file_arguments = self.process.arguments().copy()
        self.file_arguments.append("--filesonly")
        self.data_arguments = self.process.arguments().copy()
        self.data_arguments.append("--dataonly")

    def readOutput(self) -> None:
        line = self.process.readAllStandardOutput().toStdString()
        self.ui.txtLog.append(line)

        progress = self.progress_monitor.feed_line(line)
        self.ui.progressBar.setMaximum(progress.total_iterations)
        self.ui.progressBar.setValue(progress.current_iterations)
        logger.debug(f"Patcher: {line}")

    def readErrors(self) -> None:
        line = self.process.readAllStandardError().toStdString()
        self.ui.txtLog.append(line)
        logger.debug(f"Patcher: {line}")

    def resetButtons(self) -> None:
        self.patching_finished = True
        self.ui.btnStop.setText("Close")
        self.ui.btnSave.setEnabled(True)
        self.ui.btnStart.setEnabled(True)
        self.progress_monitor.reset()
        # Make sure it's not showing a busy indicator
        self.ui.progressBar.setMinimum(1)
        self.ui.progressBar.setMaximum(1)
        self.ui.progressBar.reset()
        if self.aborted:
            self.ui.txtLog.append("<b>***  Aborted  ***</b>")
        elif self.lastRun:
            self.ui.txtLog.append("<b>***  Finished  ***</b>")

    def btnStopClicked(self) -> None:
        if self.patching_finished:
            self.close()
        else:
            self.process.kill()
            self.aborted = True

    def btnSaveClicked(self) -> None:
        filename = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save log file", str(platform_dirs.user_log_path)
        )[0]

        if filename != "":
            with open(filename, "w") as outfile:
                outfile.write(self.ui.txtLog.toPlainText())

    def processFinished(
        self, exitCode: int, exitStatus: QtCore.QProcess.ExitStatus
    ) -> None:
        if self.aborted:
            self.resetButtons()
            return
        
        if self.phase_index > len(self.patch_phases) - 1:
            # finished
            self.lastRun = True
            self.resetButtons()
            if os.name == "nt":
                self.patch_log_file.close()
            return
        # Handle remaining patching phases
        if self.patch_phases[self.phase_index] == "FilesOnly":
            # run file patching again (to avoid problems when patchclient.dll
            # self-patches)
            self.process.setArguments(self.file_arguments)
            self.process.start()
        elif self.patch_phases[self.phase_index] == "DataOnly":
            self.process.setArguments(self.data_arguments)
            self.process.start()
        elif self.patch_phases[self.phase_index] == "FullPatch":
            self.process.setArguments(self.arguments)
            self.process.start()
        self.phase_index += 1

    def btnStartClicked(self) -> None:
        self.lastRun = False
        self.aborted = False
        self.patching_finished = False
        self.phase_index = 0
        self.ui.btnStart.setEnabled(False)
        self.ui.btnStop.setText("Abort")
        self.ui.btnSave.setEnabled(False)

        self.process.start()
        self.ui.txtLog.append("<b>***  Started  ***</b>")

        if os.name == "nt":
            self.process_status_timer.start(100)

    def activelyShowProcessStatus(self) -> None:
        """
        Gives patching progress on Windows where rundll32
        doesn't provide output.
        """
        if self.process.state() != QtCore.QProcess.ProcessState.Running:
            return

        if line := self.patch_log_file.readline():
            # Ignore information only relevent to log
            if not line.startswith("//"):
                line = line.split(": ")[1]

                self.ui.txtLog.append(line)
                logger.debug(f"Patcher: {line}")
        else:
            # Add "..." if log is not giving indicator of patching progress
            self.ui.txtLog.append("...")

        self.process_status_timer.start(100)

    def Run(self) -> None:
        self.__app = QtCore.QCoreApplication.instance()
        self.exec()


logger = logging.getLogger("main")
