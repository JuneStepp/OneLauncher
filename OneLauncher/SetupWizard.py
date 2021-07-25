# coding=utf-8
###########################################################################
# Settings wizard for OneLauncher.
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
from OneLauncher import Settings
from PySide6 import QtCore, QtWidgets
from PySide6.QtUiTools import QUiLoader
import os
from pathlib import Path
import glob

import OneLauncher


def toString(val):
    if isinstance(val, str):
        return val
    else:
        return val.toString()


class SetupWizard:
    def __init__(self, data_folder: Path, QGuiApplication):
        self.winSetupWizard = QUiLoader().load(str(data_folder/"ui/winSetupWizard.ui"))
        self.winSetupWizard.setWindowFlags(QtCore.Qt.Dialog)
        self.winSetupWizard.setWindowTitle(f"{OneLauncher.__title__} Setup Wizard")
        qr = self.winSetupWizard.frameGeometry()
        cp = QGuiApplication.primaryScreen().availableGeometry().center()
        qr.moveCenter(cp)
        self.winSetupWizard.move(qr.topLeft())

        self.winSetupWizard.btnFindMenu = QtWidgets.QMenu()
        self.winSetupWizard.btnFindMenu.addAction(
            self.winSetupWizard.actionShowTest
        )
        self.winSetupWizard.btnFindMenu.addAction(
            self.winSetupWizard.actionShowNormal
        )
        self.winSetupWizard.actionShowTest.triggered.connect(
            self.actionShowTestSelected
        )
        self.winSetupWizard.actionShowNormal.triggered.connect(
            self.actionShowNormalSelected
        )
        self.winSetupWizard.btnFind.setMenu(self.winSetupWizard.btnFindMenu)
        self.winSetupWizard.btnFind_2.setMenu(self.winSetupWizard.btnFindMenu)

        self.winSetupWizard.btnFind.clicked.connect(self.btnFindClicked)
        self.winSetupWizard.btnFind_2.clicked.connect(self.btnFindClicked)

        self.winSetupWizard.btnGameDirLOTRO.clicked.connect(
            self.btnGameDirLOTROClicked
        )
        self.winSetupWizard.btnGameDirDDO.clicked.connect(
            self.btnGameDirDDOClicked
        )
        self.winSetupWizard.btnGameDirLOTROTest.clicked.connect(
            self.btnGameDirLOTROTestClicked
        )
        self.winSetupWizard.btnGameDirDDOTest.clicked.connect(
            self.btnGameDirDDOTestClicked
        )

        self.winSetupWizard.btnBoxIntro.rejected.connect(self.btnBoxRejected)
        self.winSetupWizard.btnBoxOptions.rejected.connect(self.btnBoxRejected)
        self.winSetupWizard.btnBoxOptions_2.rejected.connect(
            self.btnBoxRejected
        )

        self.winSetupWizard.btnBoxIntro.accepted.connect(
            self.btnBoxIntroAccepted
        )

        self.winSetupWizard.btnBoxOptions.button(
            QtWidgets.QDialogButtonBox.Apply
        ).clicked.connect(self.btnBoxOptionsApplied)
        self.winSetupWizard.btnBoxOptions_2.button(
            QtWidgets.QDialogButtonBox.Apply
        ).clicked.connect(self.btnBoxOptionsApplied)

    def btnBoxIntroAccepted(self):
        self.winSetupWizard.actionShowNormal.setVisible(False)
        self.winSetupWizard.stackedWidget.setCurrentWidget(
            self.winSetupWizard.GameFinder
        )

    def btnBoxOptionsApplied(self, button):
        if self.checkIfAnyGameFolderIsSelected():
            self.winSetupWizard.accept()

    def btnBoxRejected(self):
        self.winSetupWizard.reject()

    def actionShowTestSelected(self):
        self.winSetupWizard.stackedWidget.setCurrentWidget(
            self.winSetupWizard.GameFinder2
        )
        self.winSetupWizard.actionShowNormal.setVisible(True)
        self.winSetupWizard.actionShowTest.setVisible(False)

    def actionShowNormalSelected(self):
        self.winSetupWizard.stackedWidget.setCurrentWidget(
            self.winSetupWizard.GameFinder
        )
        self.winSetupWizard.actionShowTest.setVisible(True)
        self.winSetupWizard.actionShowNormal.setVisible(False)

    def btnFindClicked(self):
        self.winSetupWizard.lstLOTRO.clear()
        self.winSetupWizard.lstDDO.clear()
        self.winSetupWizard.lstLOTROTest.clear()
        self.winSetupWizard.lstDDOTest.clear()

        if Settings.usingWindows:
            startDir = Path("C:/")
            for client in ["lotroclient.exe", "dndclient.exe"]:
                self.client = client

                self.find_game_dirs(startDir/"Program Files")
                if (startDir/"Program Files (x86)").exists():
                    self.find_game_dirs(startDir/"Program Files (x86)")
        else:
            for dir, pattern in [
                (Path("~").expanduser(), "*wine*"),
                (Path("~").expanduser()/Settings.settingsCXG, "*"),
                (Path("~").expanduser()/Settings.settingsCXO, "*"),
                (Path("~").expanduser()/".steam/steam/steamapps/compatdata", "*"),
                (Path("~").expanduser()/".steam/steam/SteamApps/compatdata", "*"),
                (Path("~").expanduser()/".steam/steamapps/compatdata", "*"),
                (Path("~").expanduser()/".local/share/Steam/steamapps/compatdata", "*"),
            ]:
                for path in dir.glob(pattern):
                    # Handle Steam Proton paths
                    if path.is_dir() and (path/"pfx").exists():
                        path = path/"pfx"

                    if path.is_dir() and (path/"drive_c").exists():
                        for client in ["lotroclient.exe", "dndclient.exe"]:
                            self.client = client

                            self.find_game_dirs(path/"drive_c/Program Files")
                            self.find_game_dirs(
                                path/"drive_c/Program Files (x86)")

    def find_game_dirs(self, search_dir: Path, search_depth=5):
        if search_depth <= 0:
            return

        for path in search_dir.glob("*"):
            if self.client == path.name:
                client_dir = path.parent

                if self.client == "dndclient.exe":
                    if "(Preview)" in client_dir.name:
                        self.winSetupWizard.lstDDOTest.addItem(
                            str(client_dir)
                        )
                        self.winSetupWizard.lstDDOTest.setCurrentRow(0)
                    else:
                        self.winSetupWizard.lstDDO.addItem(
                            str(client_dir)
                        )
                        self.winSetupWizard.lstDDO.setCurrentRow(0)

                elif self.client == "lotroclient.exe":
                    if "Bullroarer" in client_dir.name:
                        self.winSetupWizard.lstLOTROTest.addItem(
                            str(client_dir)
                        )
                        self.winSetupWizard.lstLOTROTest.setCurrentRow(0)
                    else:
                        self.winSetupWizard.lstLOTRO.addItem(
                            str(client_dir)
                        )
                        self.winSetupWizard.lstLOTRO.setCurrentRow(0)
            elif path.is_dir() and path.name.upper() != "BACKUP":
                self.find_game_dirs(path, search_depth=search_depth-1)

    def getGame(self):
        if self.winSetupWizard.lstLOTRO.currentItem():
            return "LOTRO"
        elif self.winSetupWizard.lstDDO.currentItem():
            return "DDO"
        elif self.winSetupWizard.lstLOTROTest.currentItem():
            return "LOTRO.Test"
        elif self.winSetupWizard.lstDDOTest.currentItem():
            return "DDO.Test"
        else:
            return None

    def getGameDir(self, game):
        if game == "LOTRO" and self.winSetupWizard.lstLOTRO.currentItem():
            return Path(self.winSetupWizard.lstLOTRO.currentItem().text())
        elif game == "DDO" and self.winSetupWizard.lstDDO.currentItem():
            return Path(self.winSetupWizard.lstDDO.currentItem().text())
        elif (
            game == "LOTRO.Test"
            and self.winSetupWizard.lstLOTROTest.currentItem()
        ):
            return Path(self.winSetupWizard.lstLOTROTest.currentItem().text())
        elif (
            game == "DDO.Test" and self.winSetupWizard.lstDDOTest.currentItem()
        ):
            return Path(self.winSetupWizard.lstDDOTest.currentItem().text())
        else:
            return None

    def btnGameDirLOTROClicked(self):
        self.browseForGameDir(self.winSetupWizard.lstLOTRO)

    def btnGameDirDDOClicked(self):
        self.browseForGameDir(self.winSetupWizard.lstDDO)

    def btnGameDirLOTROTestClicked(self):
        self.browseForGameDir(self.winSetupWizard.lstLOTROTest)

    def btnGameDirDDOTestClicked(self):
        self.browseForGameDir(self.winSetupWizard.lstDDOTest)

    def browseForGameDir(self, output_list):
        if Settings.usingWindows:
            starting_dir = Path(os.environ.get("ProgramFiles"))
        else:
            starting_dir = Path("~").expanduser()

        folder_str = QtWidgets.QFileDialog.getExistingDirectory(
            self.winSetupWizard,
            "Game Directory",
            str(starting_dir),
            options=QtWidgets.QFileDialog.ShowDirsOnly,
        )

        if folder_str != "":
            # Detect if folder is already in list
            if not output_list.findItems(folder_str, QtCore.Qt.MatchExactly):

                if self.checkGameDirForClientExecutable(Path(folder_str)):
                    output_list.addItem(folder_str)

                    # Select the added item
                    item = output_list.findItems(
                        folder_str, QtCore.Qt.MatchExactly)[0]
                    output_list.setCurrentItem(item)
                else:
                    self.raiseWarningMessage(
                        "The folder selected doesn't conain a game client "
                        "executable. Please chose a valid game folder"
                    )

    def checkGameDirForClientExecutable(self, folder: Path):
        """
        Checks for the game's client .exe to validate that the
        folder is a valid game folder.
        """
        folder_contents = [path.name for path in folder.iterdir()]
        return (
            "dndclient.exe" in folder_contents
            or "lotroclient.exe" in folder_contents
        )

    def checkIfAnyGameFolderIsSelected(self):
        """
        Check if any game folders have been added and selected.
        Brings up a warning message if not.
        """
        if not self.getGame():
            self.raiseWarningMessage(
                "There are no game folders selected. "
                "Please select at least one game folder to continue."
            )
            return False
        else:
            return True

    def raiseWarningMessage(self, message):
        messageBox = QtWidgets.QMessageBox(self.winSetupWizard)
        messageBox.setWindowFlag(QtCore.Qt.FramelessWindowHint)
        messageBox.setIcon(QtWidgets.QMessageBox.Warning)
        messageBox.setStandardButtons(messageBox.Ok)
        messageBox.setInformativeText(message)

        messageBox.exec()

    def getHiRes(self, gameDir):
        return bool((gameDir/"client_highres.dat").exists())

    def Run(self):
        return self.winSetupWizard.exec_()
