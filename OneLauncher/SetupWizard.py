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
from PySide2 import QtCore, QtWidgets
from PySide2.QtUiTools import QUiLoader
import os
import glob


def toString(val):
    if isinstance(val, str):
        return val
    else:
        return val.toString()


class SetupWizard:
    def __init__(self, homeDir, osType, data_folder):

        self.homeDir = homeDir
        self.osType = osType

        ui_file = QtCore.QFile(
            os.path.join(data_folder, "ui", "winSetupWizard.ui")
        )

        ui_file.open(QtCore.QFile.ReadOnly)
        loader = QUiLoader()
        self.winSetupWizard = loader.load(ui_file)
        ui_file.close()

        self.winSetupWizard.setWindowFlags(QtCore.Qt.Dialog)
        self.winSetupWizard.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.winSetupWizard.setWindowTitle("Setup Wizard")

        qr = self.winSetupWizard.frameGeometry()
        cp = QtWidgets.QDesktopWidget().availableGeometry().center()
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

        if self.osType.usingWindows:
            startDir = "C:\\"
            for client in ["lotroclient.exe", "dndclient.exe"]:
                self.client = client

                self.trawl(
                    os.path.join(startDir, "Program Files"),
                    os.path.join(startDir, "Program Files"),
                )
                if os.path.exists(
                    os.path.join(startDir, "Program Files (x86)")
                ):
                    self.trawl(
                        os.path.join(startDir, "Program Files (x86)"),
                        os.path.join(startDir, "Program Files (x86)"),
                    )
        else:
            for dir in [
                self.homeDir + ".*",
                self.homeDir + self.osType.settingsCXG + "/*",
                self.homeDir + self.osType.settingsCXO + "/*",
            ]:
                startDir = dir

                for name in glob.glob(startDir):
                    if os.path.isdir(name) and os.path.exists(
                        os.path.join(name, "drive_c")
                    ):
                        for client in ["lotroclient.exe", "dndclient.exe"]:
                            self.client = client

                            self.trawl(
                                os.path.join(
                                    name, "drive_c", "Program Files"
                                ),
                                os.path.join(
                                    name, "drive_c", "Program Files"
                                ),
                            )

                            if os.path.exists(
                                os.path.join(
                                    name, "drive_c", "Program Files (x86)"
                                )
                            ):
                                self.trawl(
                                    os.path.join(
                                        name,
                                        "drive_c",
                                        "Program Files (x86)",
                                    ),
                                    os.path.join(
                                        name,
                                        "drive_c",
                                        "Program Files (x86)",
                                    ),
                                )

    def trawl(self, path, directory):
        for name in glob.glob(directory + os.sep + "*"):
            if name.lower().find(self.client) >= 0:
                dirName = os.path.dirname(name.replace(path + os.sep, ""))

                if self.client == "dndclient.exe":
                    if "(Preview)" in dirName:
                        self.winSetupWizard.lstDDOTest.addItem(
                            path + os.sep + dirName
                        )
                        self.winSetupWizard.lstDDOTest.setCurrentRow(0)
                    else:
                        self.winSetupWizard.lstDDO.addItem(
                            path + os.sep + dirName
                        )
                        self.winSetupWizard.lstDDO.setCurrentRow(0)

                elif self.client == "lotroclient.exe":
                    if "Bullroarer" in dirName:
                        self.winSetupWizard.lstLOTROTest.addItem(
                            path + os.sep + dirName
                        )
                        self.winSetupWizard.lstLOTROTest.setCurrentRow(0)
                    else:
                        self.winSetupWizard.lstLOTRO.addItem(
                            path + os.sep + dirName
                        )
                        self.winSetupWizard.lstLOTRO.setCurrentRow(0)
            if os.path.isdir(name) and not name.upper().endswith(
                os.sep + "BACKUP"
            ):
                self.trawl(path, name)

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
            return self.winSetupWizard.lstLOTRO.currentItem().text()
        elif game == "DDO" and self.winSetupWizard.lstDDO.currentItem():
            return self.winSetupWizard.lstDDO.currentItem().text()
        elif (
            game == "LOTRO.Test"
            and self.winSetupWizard.lstLOTROTest.currentItem()
        ):
            return self.winSetupWizard.lstLOTROTest.currentItem().text()
        elif (
            game == "DDO.Test" and self.winSetupWizard.lstDDOTest.currentItem()
        ):
            return self.winSetupWizard.lstDDOTest.currentItem().text()
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
        if self.osType.usingWindows:
            starting_dir = os.environ.get("ProgramFiles")
        else:
            starting_dir = self.homeDir

        folder = QtWidgets.QFileDialog.getExistingDirectory(
            self.winSetupWizard,
            "Game Directory",
            starting_dir,
            options=QtWidgets.QFileDialog.ShowDirsOnly,
        )

        if folder != "":
            # Detect if folder is already in list
            if not output_list.findItems(folder, QtCore.Qt.MatchExactly):

                if self.checkGameDirForClientExecutable(folder):
                    output_list.addItem(folder)

                    # Select the added item
                    item = output_list.findItems(folder, QtCore.Qt.MatchExactly)[0]
                    output_list.setCurrentItem(item)
                else:
                    self.raiseWarningMessage(
                        "The folder selected doesn't conain a game client "
                        "executable. Please chose a valid game folder"
                    )

    def checkGameDirForClientExecutable(self, folder):
        """
        Checks for the game's client .exe to validate that the
        folder is a valid game folder.
        """
        folder_contents = os.listdir(folder)
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
        return bool(os.path.exists(gameDir + os.sep + "client_highres.dat"))

    def Run(self):
        return self.winSetupWizard.exec_()
