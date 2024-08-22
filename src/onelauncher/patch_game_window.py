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
from typing import Literal, TypeAlias, assert_never

from PySide6 import QtCore, QtWidgets

from onelauncher.game_config import GameConfigID
from onelauncher.logs import ExternalProcessLogsFilter, ForwardLogsHandler
from onelauncher.qtapp import get_qapp
from onelauncher.ui_utilities import log_record_to_rich_text

from .config_manager import ConfigManager
from .game_launcher_local_config import GameLauncherLocalConfig
from .game_utilities import get_default_game_settings_dir
from .patching_progress_monitor import PatchingProgressMonitor
from .ui.patching_window_uic import Ui_patchingDialog
from .utilities import CaseInsensitiveAbsolutePath
from .wine_environment import edit_qprocess_to_use_wine

logger = logging.getLogger(__name__)


class PatchWindow(QtWidgets.QDialog):
    PatchPhase: TypeAlias = Literal["FullPatch", "FilesOnly", "DataOnly"]

    def __init__(
        self,
        game_id: GameConfigID,
        config_manager: ConfigManager,
        launcher_local_config: GameLauncherLocalConfig,
        urlPatchServer: str,
    ):
        super().__init__(
            get_qapp().activeWindow(),
            QtCore.Qt.WindowType.FramelessWindowHint,
        )
        self.launcher_local_config = launcher_local_config

        self.ui = Ui_patchingDialog()
        self.ui.setupUi(self)

        if os.name == "nt":
            self.setWindowTitle("Patching Output")
        else:
            self.setWindowTitle("Patching WINE Output")

        self.process_logging_adapter = logging.LoggerAdapter(logger)
        logger.addFilter(ExternalProcessLogsFilter())
        ui_logging_handler = ForwardLogsHandler(
            new_log_callback=lambda record: self.ui.txtLog.append(
                log_record_to_rich_text(record)
            ),
            level=logging.INFO,
        )
        logger.addHandler(ui_logging_handler)

        self.ui.progressBar.reset()
        self.ui.btnStop.setText("Close")
        self.ui.btnStart.setText("Patch")
        self.ui.btnStop.clicked.connect(self.btnStopClicked)
        self.ui.btnStart.clicked.connect(self.btnStartClicked)

        self.aborted = False
        self.patching_finished = True

        if os.name == "nt":
            self.process_status_timer = QtCore.QTimer()
            self.process_status_timer.timeout.connect(self.activelyShowProcessStatus)

        game_config = config_manager.get_game_config(game_id=game_id)
        patch_client = game_config.game_directory / game_config.patch_client_filename

        # Make sure patch_client exists
        if not patch_client.exists():
            logger.error(f"Patch client {patch_client} not found")
            return

        self.progress_monitor = PatchingProgressMonitor()

        self.process = QtCore.QProcess()
        self.process.readyReadStandardOutput.connect(self.readOutput)
        self.process.readyReadStandardError.connect(self.readErrors)
        self.process.finished.connect(self.processFinished)
        self.process.setWorkingDirectory(str(game_config.game_directory))
        if os.name == "nt":
            # The directory with TTEPatchClient.dll has to be in the PATH for
            # patchclient.dll to find it when OneLauncher is compilled with Nuitka.
            environment = self.process.processEnvironment()
            existing_path_var = environment.value("PATH", "")
            environment.insert(
                "PATH",
                f"{f'{existing_path_var};' if existing_path_var else ''}{game_config.game_directory}",
            )
            self.process.setProcessEnvironment(environment)

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
        self.base_patching_arguments = tuple(self.process.arguments())
        # Run file patching twiceto avoid problems when patchclient.dll
        # self-patches
        self.patch_phases: tuple[PatchWindow.PatchPhase, ...] = (
            "FilesOnly",
            "FilesOnly",
            "DataOnly",
        )
        self.phase_index: int = 0
        if process_arguments := self.get_process_arguments():
            self.process.setArguments(process_arguments)

    def get_process_arguments(self) -> tuple[str, ...] | None:
        if self.phase_index > len(self.patch_phases) - 1 or self.phase_index < 0:
            # Finished
            return None
        current_phase = self.patch_phases[self.phase_index]
        if current_phase == "FilesOnly":
            return (*self.base_patching_arguments, "--filesonly")
        elif current_phase == "DataOnly":
            return (*self.base_patching_arguments, "--dataonly")
        elif current_phase == "FullPatch":
            return self.base_patching_arguments
        else:
            assert_never(current_phase)

    def readOutput(self) -> None:
        line = self.process.readAllStandardOutput().toStdString()
        if line.strip():
            self.process_logging_adapter.debug(line)

        progress = self.progress_monitor.feed_line(line)
        self.ui.progressBar.setMaximum(progress.total_iterations)
        self.ui.progressBar.setValue(progress.current_iterations)

    def readErrors(self) -> None:
        line = self.process.readAllStandardError().toStdString()
        if line.strip():
            self.process_logging_adapter.warn(line)

    def resetButtons(self) -> None:
        self.patching_finished = True
        self.ui.btnStop.setText("Close")
        self.ui.btnStart.setEnabled(True)
        self.progress_monitor.reset()
        # Make sure it's not showing a busy indicator
        self.ui.progressBar.setMinimum(1)
        self.ui.progressBar.setMaximum(1)
        self.ui.progressBar.reset()
        if self.aborted:
            logger.info("***  Aborted  ***<")
        elif self.get_process_arguments() is None:
            logger.info("***  Finished  ***")
            # Let user know that patching is finished if the window isn't currently
            # focussed.
            self.activateWindow()

    def btnStopClicked(self) -> None:
        if self.patching_finished:
            self.close()
        else:
            self.process.kill()
            self.aborted = True

            if self.process.state() != self.process.ProcessState.Running:
                self.resetButtons()

    def processFinished(
        self, exitCode: int, exitStatus: QtCore.QProcess.ExitStatus
    ) -> None:
        if self.aborted:
            self.resetButtons()
            return

        self.phase_index += 1
        # Handle remaining patching phases
        new_arguments = self.get_process_arguments()
        if new_arguments is None:
            # finished
            self.resetButtons()
            if os.name == "nt":
                self.patch_log_file.close()
            return
        self.process.setArguments(new_arguments)
        self.process.start()

    def get_windows_patching_log_path(self) -> CaseInsensitiveAbsolutePath:
        # The name of the log folder is the same as the default name of the
        # game settings folder.
        log_folder_name = get_default_game_settings_dir(
            launcher_local_config=self.launcher_local_config
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
        return patch_log_path

    def btnStartClicked(self) -> None:
        self.aborted = False
        self.patching_finished = False
        self.phase_index = 0
        self.ui.btnStart.setEnabled(False)
        self.ui.btnStop.setText("Abort")

        # Get log file to read patching details from, since
        # rundll32 doesn't provide output on Windows
        if os.name == "nt":
            self.patch_log_file = self.get_windows_patching_log_path().open(mode="r")

        self.process.start()
        self.process_logging_adapter.extra = {
            ExternalProcessLogsFilter.EXTERNAL_PROCESS_ID_KEY: self.process.processId()
        }
        logger.info("***  Started  ***")

        if os.name == "nt":
            self.process_status_timer.start(100)

    def activelyShowProcessStatus(self) -> None:
        """
        Gives patching progress on Windows where rundll32
        doesn't provide output.
        """
        if self.process.state() != QtCore.QProcess.ProcessState.Running:
            return

        if line := self.patch_log_file.readline().strip():
            # Ignore information only relevent to log
            if not line.startswith("//"):
                if ":" in line:
                    line = line.split(": ", maxsplit=1)[1]

                self.process_logging_adapter.info(line)
        else:
            # Add "..." if log is not giving indicator of patching progress
            self.ui.txtLog.append("...")

        self.process_status_timer.start(100)

    def Run(self) -> None:
        self.exec()
