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
from pathlib import Path
from sys import path

from PySide6 import QtCore, QtWidgets
from PySide6.QtUiTools import QUiLoader

from onelauncher import settings, logger
from onelauncher.utilities import QByteArray2str
from onelauncher.wine_management import edit_qprocess_to_use_wine
from onelauncher.ui.start_game_uic import Ui_startGameDialog


class StartGame(QtWidgets.QDialog):
    def __init__(
        self,
        client_filename: str,
        game: settings.Game,
        argTemplate,
        account,
        server,
        ticket,
        chatServer,
        crashreceiver,
        DefaultUploadThrottleMbps,
        bugurl,
        authserverurl,
        supporturl,
        supportserviceurl,
        glsticketlifetime,
        worldName,
        accountText,
        gameConfigPath: settings.CaseInsensitiveAbsolutePath,
    ):
        super(StartGame, self).__init__(
            QtCore.QCoreApplication.instance().activeWindow(), QtCore.Qt.FramelessWindowHint)

        self.ui = Ui_startGameDialog()
        self.ui.setupUi(self)

        # Fixes binary path for 64-bit client
        if game.client_type == "WIN64":
            client_relative_path = Path("x64")/client_filename
        else:
            client_relative_path = Path(client_filename)

        self.worldName = worldName
        self.accountText = accountText
        self.game = game
        self.gameConfigPath = gameConfigPath

        if settings.usingWindows:
            self.setWindowTitle("Output")
        else:
            self.setWindowTitle("Launch Game - Wine output")

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

        gameParams = (
            argTemplate.replace("{SUBSCRIPTION}", account)
            .replace("{LOGIN}", server)
            .replace("{GLS}", ticket)
            .replace("{CHAT}", chatServer)
            .replace("{LANG}", game.locale.game_language_name)
            .replace("{CRASHRECEIVER}", crashreceiver)
            .replace("{UPLOADTHROTTLE}", DefaultUploadThrottleMbps)
            .replace("{BUGURL}", bugurl)
            .replace("{AUTHSERVERURL}", authserverurl)
            .replace("{GLSTICKETLIFETIME}", glsticketlifetime)
            .replace("{SUPPORTURL}", supporturl)
            .replace("{SUPPORTSERVICEURL}", supportserviceurl)
        )

        if not game.high_res_enabled:
            gameParams += " --HighResOutOfDate"

        self.process = QtCore.QProcess()
        self.process.readyReadStandardOutput.connect(self.readOutput)
        self.process.readyReadStandardError.connect(self.readErrors)
        self.process.finished.connect(self.resetButtons)

        self.process.setProgram(str(client_relative_path))
        self.process.setArguments([arg for arg in gameParams.split(" ")])
        if not settings.usingWindows:
            edit_qprocess_to_use_wine(self.process)

        self.process.setWorkingDirectory(str(game.game_directory))

        self.ui.txtLog.append("Connecting to server: " + worldName)
        self.ui.txtLog.append("Account: " + accountText)
        self.ui.txtLog.append("Game Directory: " + str(game.game_directory))
        self.ui.txtLog.append("Game Client: " + str(client_relative_path))

        self.show()

        self.runStatupScripts()

    def readOutput(self):
        text = QByteArray2str(self.process.readAllStandardOutput())
        self.ui.txtLog.append(text)
        logger.debug("Game: " + text)

    def readErrors(self):
        text = QByteArray2str(self.process.readAllStandardError())
        self.ui.txtLog.append(text)
        logger.debug("Game: " + text)

    def resetButtons(self, exitCode, exitStatus):
        self.finished = True
        self.ui.btnStop.setText("Exit")
        self.ui.btnSave.setEnabled(True)
        self.ui.btnStart.setEnabled(True)
        if self.aborted:
            self.ui.txtLog.append("<b>***  Aborted  ***</b>")
        else:
            self.ui.txtLog.append("<b>***  Finished  ***</b>")

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
                settings.platform_dirs.user_log_path)
        )[0]

        if filename != "":
            with open(filename, "w") as outfile:
                outfile.write(self.ui.txtLog.toPlainText())

    def runStatupScripts(self):
        """Runs Python scripts from add-ons with one that is approved by user"""
        for script in self.game.startup_scripts:
            file_path = self.gameConfigPath/script
            if file_path.exists():
                self.ui.txtLog.append(
                    f"Running '{script}' startup script...")

                with file_path.open() as file:
                    code = file.read()

                try:
                    exec(code, {"__file__": str(file_path)})
                except SyntaxError as e:
                    self.ui.txtLog.append(
                        f"'{script}' ran into syntax error: {e}")
            else:
                self.ui.txtLog.append(
                    f"'{script}' startup script does not exist")

    def Run(self):
        self.finished = False

        self.ui.btnStop.setText("Abort")
        self.process.start()
        logger.info("Game started with: " +
                    str([self.process.program(), self.process.arguments()]))

        self.exec()
