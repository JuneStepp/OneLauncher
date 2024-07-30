###########################################################################
# Game launcher for OneLauncher.
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
from datetime import UTC, datetime

import attrs
from onelauncher.game_config import GameConfigID
from onelauncher.qtapp import get_qapp
from PySide6 import QtCore, QtWidgets

from ..addons.startup_script import run_startup_script
from ..async_utils import app_cancel_scope
from ..config import platform_dirs
from ..config_manager import ConfigManager
from ..game_launcher_local_config import GameLauncherLocalConfig
from ..game_utilities import get_game_settings_dir
from ..network.game_launcher_config import GameLauncherConfig
from ..network.world import World
from ..start_game import MissingLaunchArgumentError, get_qprocess
from .start_game_uic import Ui_startGameDialog


class StartGame(QtWidgets.QDialog):
    def __init__(
        self,
        game_id: GameConfigID,
        config_manager: ConfigManager,
        game_launcher_local_config: GameLauncherLocalConfig,
        game_launcher_config: GameLauncherConfig,
        world: World,
        login_server: str,
        account_number: str,
        ticket: str,
    ) -> None:
        self.game_id = game_id
        self.config_manager = config_manager
        self.game_launcher_local_config = game_launcher_local_config
        self.game_launcher_config = game_launcher_config
        self.world = world
        self.login_server = login_server
        self.account_number = account_number
        self.ticket = ticket

        super().__init__(
            get_qapp().activeWindow(),
            QtCore.Qt.WindowType.FramelessWindowHint,
        )

        self.ui = Ui_startGameDialog()
        self.ui.setupUi(self)

        self.ui.btnStart.setText("Close")
        self.ui.btnStart.setEnabled(False)
        self.ui.btnSave.setText("Save Log")
        self.ui.btnSave.setEnabled(False)
        self.ui.btnStop.setText("Exit")
        self.ui.btnStart.clicked.connect(self.btnStartClicked)
        self.ui.btnSave.clicked.connect(self.btnSaveClicked)
        self.ui.btnStop.clicked.connect(self.btnStopClicked)

        self.aborted = False
        self.game_finished = False

        self.show()

    async def get_qprocess(self) -> QtCore.QProcess | None:
        """Return setup qprocess with connected signals"""
        try:
            process = await get_qprocess(
                game_launcher_config=self.game_launcher_config,
                game_launcher_local_config=self.game_launcher_local_config,
                game_config=self.config_manager.get_game_config(self.game_id),
                default_locale=self.config_manager.get_program_config().default_locale,
                world=self.world,
                login_server=self.login_server,
                account_number=self.account_number,
                ticket=self.ticket,
            )
        except MissingLaunchArgumentError:
            self.ui.txtLog.append(
                '<font color="red">Game launch argument missing. '
                "Please report this error if using a supported server.< /font >"
            )
            logger.exception("Launch argument missing")
            self.reset_buttons()
            return None

        def readOutput() -> None:
            text = process.readAllStandardOutput().toStdString()
            self.ui.txtLog.append(text)
            logger.debug(f"Game: {text}")

        def readErrors() -> None:
            text = process.readAllStandardError().toStdString()
            self.ui.txtLog.append(text)
            logger.debug(f"Game: {text}")

        process.readyReadStandardOutput.connect(readOutput)
        process.readyReadStandardError.connect(readErrors)
        process.finished.connect(self.process_finished)
        return process

    def process_finished(
        self, exit_code: int, exit_status: QtCore.QProcess.ExitStatus
    ) -> None:
        self.reset_buttons()
        if self.aborted:
            self.ui.txtLog.append("<b>***  Aborted  ***</b>")
        else:
            self.ui.txtLog.append("<b>***  Finished  ***</b>")

    def reset_buttons(self) -> None:
        self.game_finished = True
        self.ui.btnStop.setText("Exit")
        self.ui.btnSave.setEnabled(True)
        self.ui.btnStart.setEnabled(True)

    def btnStartClicked(self) -> None:
        if self.game_finished:
            self.close()

    def btnStopClicked(self) -> None:
        if self.game_finished:
            self.close()
            # Close entire application
            app_cancel_scope.cancel()
        else:
            self.aborted = True
            if self.process:
                self.process.kill()

    # Saves a file with the debug log generated by running the game
    def btnSaveClicked(self) -> None:
        filename = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save log file", str(platform_dirs.user_log_path)
        )[0]

        if filename != "":
            with open(filename, "w") as outfile:
                outfile.write(self.ui.txtLog.toPlainText())

    def run_startup_scripts(self) -> None:
        """Runs Python scripts from addons with one that is approved by user"""
        game_config = self.config_manager.get_game_config(self.game_id)
        for script in game_config.addons.enabled_startup_scripts:
            try:
                self.ui.txtLog.append(
                    f"Running '{script.relative_path}' startup script..."
                )
                run_startup_script(
                    script=script,
                    game_directory=game_config.game_directory,
                    documents_config_dir=get_game_settings_dir(
                        game_config=game_config,
                        launcher_local_config=self.game_launcher_local_config,
                    ),
                )
            except FileNotFoundError:
                self.ui.txtLog.append(
                    f"'{script.relative_path}' startup script does not exist"
                )
            except SyntaxError as e:
                self.ui.txtLog.append(
                    f"'{script.relative_path}' ran into syntax error: {e}"
                )

    async def start_game(self) -> None:
        self.config_manager.update_game_config_file(
            game_id=self.game_id,
            config=attrs.evolve(
                self.config_manager.read_game_config_file(self.game_id),
                last_played=datetime.now(UTC),
            ),
        )

        self.process = await self.get_qprocess()
        if self.process is None:
            return

        self.game_finished = False
        self.ui.btnStop.setText("Abort")
        self.run_startup_scripts()
        self.process.start()
        logger.info(f"{self.process.program} game executable started")
        self.ui.txtLog.append(f"Connecting to world: {self.world.name}")

        self.exec()


logger = logging.getLogger("main")
