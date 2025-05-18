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
# (C) 2019-2025 June Stepp <contact@JuneStepp.me>
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
from onelauncher.logs import ExternalProcessLogsFilter, ForwardLogsHandler
from onelauncher.qtapp import get_qapp
from onelauncher.ui_utilities import log_record_to_rich_text
from PySide6 import QtCore, QtWidgets

from ..addons.startup_script import run_startup_script
from ..async_utils import app_cancel_scope
from ..config_manager import ConfigManager
from ..game_launcher_local_config import GameLauncherLocalConfig
from ..game_utilities import get_game_settings_dir
from ..network.game_launcher_config import GameLauncherConfig
from ..network.world import World
from ..start_game import MissingLaunchArgumentError, get_qprocess
from .start_game_uic import Ui_startGameDialog

logger = logging.getLogger(__name__)


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

        self.process_logging_adapter = logging.LoggerAdapter(logger)
        logger.addFilter(ExternalProcessLogsFilter())
        logger.addHandler(
            ForwardLogsHandler(
                new_log_callback=lambda record: self.ui.txtLog.append(
                    log_record_to_rich_text(record)
                ),
                level=logging.INFO,
            )
        )

        # Can't quit until program finishes or is aborted
        self.ui.btnQuit.setEnabled(False)

        self.ui.btnAbort.clicked.connect(self.btnAbortClicked)
        self.ui.btnQuit.clicked.connect(self.btnQuitClicked)

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
            logger.exception(
                "Game launch argument missing. Please report this error if using a supported server."
            )
            self.reset_buttons()
            return None

        def readOutput() -> None:
            self.process_logging_adapter.debug(
                process.readAllStandardOutput().toStdString()
            )

        def readErrors() -> None:
            self.process_logging_adapter.warn(
                process.readAllStandardError().toStdString()
            )

        process.readyReadStandardOutput.connect(readOutput)
        process.readyReadStandardError.connect(readErrors)
        process.finished.connect(self.process_finished)
        return process

    def process_finished(
        self, exit_code: int, exit_status: QtCore.QProcess.ExitStatus
    ) -> None:
        self.reset_buttons()
        if self.aborted:
            logger.info("***  Aborted  ***")
        else:
            logger.info("***  Finished  ***")

    def reset_buttons(self) -> None:
        self.game_finished = True
        self.ui.btnAbort.setText("Close")
        self.ui.btnQuit.setEnabled(True)

    def btnAbortClicked(self) -> None:
        if self.game_finished:
            self.close()
        else:
            self.aborted = True
            if self.process:
                self.process.kill()

    def btnQuitClicked(self) -> None:
        if self.game_finished:
            self.close()
            # Close entire application
            app_cancel_scope.cancel()

    def run_startup_scripts(self) -> None:
        """Runs Python scripts from addons with one that is approved by user"""
        game_config = self.config_manager.get_game_config(self.game_id)
        for script in game_config.addons.enabled_startup_scripts:
            try:
                logger.info(f"Running '{script.relative_path}' startup script...")
                run_startup_script(
                    script=script,
                    game_directory=game_config.game_directory,
                    documents_config_dir=get_game_settings_dir(
                        game_config=game_config,
                        launcher_local_config=self.game_launcher_local_config,
                    ),
                )
            except FileNotFoundError:
                logger.exception(
                    f"'{script.relative_path}' startup script does not exist"
                )
            except SyntaxError as e:
                logger.exception(f"'{script.relative_path}' ran into syntax error: {e}")

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
        self.ui.btnAbort.setText("Abort")
        self.run_startup_scripts()
        self.process.start()
        self.process_logging_adapter.extra = {
            ExternalProcessLogsFilter.EXTERNAL_PROCESS_ID_KEY: self.process.processId()
        }
        logger.info("Game started")

        self.exec()
