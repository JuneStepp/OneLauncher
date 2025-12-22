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

import trio
from PySide6 import QtCore, QtWidgets
from qtpy import QtGui
from typing_extensions import override

from onelauncher.config_manager import ConfigManager
from onelauncher.game_config import GameConfigID
from onelauncher.logs import ForwardLogsHandler
from onelauncher.patch_game import (
    PATCH_CLIENT_RUNNER,
    patch_game,
)
from onelauncher.patch_game import logger as patch_game_logger
from onelauncher.qtapp import get_qapp
from onelauncher.utilities import Progress

from .patch_game_uic import Ui_patchingDialog
from .utilities import log_record_to_rich_text

logger = logging.getLogger(__name__)


class PatchGameWindow(QtWidgets.QDialog):
    def __init__(
        self,
        game_id: GameConfigID,
        config_manager: ConfigManager,
        patch_server_url: str,
    ):
        super().__init__(
            get_qapp().activeWindow(),
            QtCore.Qt.WindowType.FramelessWindowHint,
        )
        self.game_id = game_id
        self.config_manager = config_manager
        self.patch_server_url = patch_server_url

        self.progress: Progress | None = None

        self.ui = Ui_patchingDialog()
        self.ui.setupUi(self)
        self.setWindowTitle("Patching Output")

        self.ui_logs_handler = ForwardLogsHandler(
            new_log_callback=lambda record: self.ui.txtLog.append(
                log_record_to_rich_text(record)
            ),
            level=logging.INFO,
        )
        logger.addHandler(self.ui_logs_handler)
        patch_game_logger.addHandler(self.ui_logs_handler)

        self.patching_finished = True

    def setup_ui(self) -> None:
        self.finished.connect(self.cleanup)

        self.ui.btnStart.setText("Patch")
        self.ui.btnStop.clicked.connect(self.btnStopClicked)
        self.ui.btnStart.clicked.connect(lambda: self.nursery.start_soon(self.start))
        self.reset_buttons()

        if not PATCH_CLIENT_RUNNER.exists():
            logger.error("Cannot patch. run_ptch_client.exe is missing.")
            self.ui.btnStart.setEnabled(False)

    async def run(self) -> None:
        self.setup_ui()
        self.open()
        async with trio.open_nursery() as self.nursery:
            self.nursery.start_soon(self.keep_progress_bar_updated)
            # Will be canceled when the winddow is closed.
            self.nursery.start_soon(trio.sleep_forever)

    def cleanup(self) -> None:
        patch_game_logger.removeHandler(self.ui_logs_handler)
        self.ui_logs_handler.close()

        self.nursery.cancel_scope.cancel()

    @override
    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        self.cleanup()
        event.accept()

    def reset_buttons(self) -> None:
        self.patching_finished = True
        self.ui.btnStop.setText("Close")
        self.ui.btnStart.setEnabled(True)

        self.progress = None
        # Make sure it's not showing a busy indicator
        self.ui.progressBar.setMinimum(1)
        self.ui.progressBar.setMaximum(1)
        self.ui.progressBar.reset()

    def btnStopClicked(self) -> None:
        if self.patching_finished:
            self.close()
        else:
            self.patching_cancel_scope.cancel()
            logger.info("***  Aborted  ***")

    async def keep_progress_bar_updated(self) -> None:
        # Will be canceled once the patching window is closed.
        while True:
            if self.progress:
                current_progress = self.progress.get_current_progress()
                self.ui.progressBar.setFormat(current_progress.progress_text)
                self.ui.progressBar.setMaximum(current_progress.total)
                self.ui.progressBar.setValue(current_progress.completed)
            await trio.sleep(0.05)

    async def start(self) -> None:
        self.patching_finished = False
        self.ui.btnStart.setEnabled(False)
        self.ui.btnStop.setText("Abort")

        self.progress = Progress()

        logger.info("***  Started  ***")
        with trio.CancelScope() as self.patching_cancel_scope:
            await patch_game(
                patch_server_url=self.patch_server_url,
                game_id=self.game_id,
                config_manager=self.config_manager,
                progress=self.progress,
            )
            logger.info("***  Finished  ***")

        self.reset_buttons()
        # Let user know that patching is finished if the window isn't currently
        # focussed.
        self.activateWindow()
