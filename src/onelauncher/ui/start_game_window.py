# coding=utf-8
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
from typing import Optional

from PySide6 import QtCore, QtWidgets

from onelauncher.config import platform_dirs
from onelauncher.game import Game
from onelauncher.network.game_launcher_config import GameLauncherConfig
from onelauncher.network.world import World
from onelauncher.start_game import MissingLaunchArgumentError, get_qprocess
from onelauncher.ui.start_game_uic import Ui_startGameDialog
from onelauncher.utilities import QByteArray2str


class StartGame(QtWidgets.QDialog):
    def __init__(
        self,
        game: Game,
        game_launcher_config: GameLauncherConfig,
        world: World,
        account_number: str,
        ticket,
    ):
        self.game = game
        self.game_launcher_config = game_launcher_config
        self.world = world
        self.account_number = account_number
        self.ticket = ticket

        super(
            StartGame,
            self).__init__(
            QtCore.QCoreApplication.instance().activeWindow(),
            QtCore.Qt.FramelessWindowHint)

        self.ui = Ui_startGameDialog()
        self.ui.setupUi(self)

        self.ui.btnStart.setText("Back")
        self.ui.btnStart.setEnabled(False)
        self.ui.btnSave.setText("Save")
        self.ui.btnSave.setEnabled(False)
        self.ui.btnStop.setText("Exit")
        self.ui.btnStart.clicked.connect(self.btnStartClicked)
        self.ui.btnSave.clicked.connect(self.btnSaveClicked)
        self.ui.btnStop.clicked.connect(self.btnStopClicked)

        self.aborted = False
        self.finished = False

        self.show()

    def get_qprocess(self) -> Optional[QtCore.QProcess]:
        """Return setup qprocess with connected signals"""
        try:
            process = get_qprocess(
                self.game_launcher_config,
                self.game,
                self.world,
                self.account_number,
                self.ticket)
        except MissingLaunchArgumentError:
            # TODO: Easy bug report
            self.ui.txtLog.append(
                "<font color=\"red\">Game launch argument missing. "
                "Please report this error if using a supported server.< /font >")
            logger.exception("Launch argument missing.")
            self.reset_buttons()
            return None

        process.readyReadStandardOutput.connect(self.readOutput)
        process.readyReadStandardError.connect(self.readErrors)
        process.finished.connect(self.process_finished)
        return process

    def readOutput(self):
        text = QByteArray2str(self.process.readAllStandardOutput())
        self.ui.txtLog.append(text)
        logger.debug(f"Game: {text}")

    def readErrors(self):
        text = QByteArray2str(self.process.readAllStandardError())
        self.ui.txtLog.append(text)
        logger.debug(f"Game: {text}")

    def process_finished(self, exit_code, exit_status):
        self.reset_buttons()
        if self.aborted:
            self.ui.txtLog.append("<b>***  Aborted  ***</b>")
        else:
            self.ui.txtLog.append("<b>***  Finished  ***</b>")

    def reset_buttons(self):
        self.finished = True
        self.ui.btnStop.setText("Exit")
        self.ui.btnSave.setEnabled(True)
        self.ui.btnStart.setEnabled(True)

    def btnStartClicked(self):
        if self.finished:
            self.close()

    def btnStopClicked(self):
        if self.finished:
            QtCore.QCoreApplication.instance().quit()
        else:
            self.aborted = True
            self.process.kill()

    # Saves a file with the debug log generated by running the game
    def btnSaveClicked(self):
        filename = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save log file", str(
                platform_dirs.user_log_path)
        )[0]

        if filename != "":
            with open(filename, "w") as outfile:
                outfile.write(self.ui.txtLog.toPlainText())

    def runStatupScripts(self):
        """Runs Python scripts from add-ons with one that is approved by user"""
        for script in self.game.startup_scripts:
            file_path = self.game.documents_config_dir / script
            if file_path.exists():
                self.ui.txtLog.append(
                    f"Running '{script}' startup script...")

                with file_path.open() as file:
                    code = file.read()

                try:
                    exec(
                        code, {
                            "__file__": str(file_path), "__game_dir__": str(
                                self.game.game_directory), "__game_config_dir__": str(
                                self.game.documents_config_dir)})
                except SyntaxError as e:
                    self.ui.txtLog.append(
                        f"'{script}' ran into syntax error: {e}")
            else:
                self.ui.txtLog.append(
                    f"'{script}' startup script does not exist")

    def start_game(self):
        self.process = self.get_qprocess()
        if self.process is None:
            return

        self.finished = False
        self.ui.btnStop.setText("Abort")
        self.runStatupScripts()
        self.process.start()
        logger.info(
            f"Game started with: {self.process.program(), self.process.arguments()}")
        self.ui.txtLog.append(f"Connecting to world: {self.world.name}")
        

        self.exec()


logger = logging.getLogger("main")
