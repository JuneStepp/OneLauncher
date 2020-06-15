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
# (C) 2019-2020 Jeremy Stepp <mail@JeremyStepp.me>
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
from OneLauncher.OneLauncherUtils import QByteArray2str
import os.path
from pkg_resources import resource_filename


class StartGame:
    def __init__(
        self,
        appName,
        x86,
        argTemplate,
        account,
        server,
        ticket,
        chatServer,
        language,
        runDir,
        wineProgram,
        wineDebug,
        winePrefix,
        hiResEnabled,
        builtInPrefixEnabled,
        osType,
        homeDir,
        iconFileIn,
        rootDir,
        crashreceiver,
        DefaultUploadThrottleMbps,
        bugurl,
        authserverurl,
        supporturl,
        supportserviceurl,
        glsticketlifetime,
        worldName,
        accountText,
        parent,
    ):

        # Fixes binary path for 64-bit client
        if x86:
            appName = "x64" + os.sep + appName

        self.homeDir = homeDir
        self.osType = osType
        self.worldName = worldName
        self.accountText = accountText
        self.parent = parent

        ui_file = QtCore.QFile(resource_filename(__name__, "ui" + os.sep + "winLog.ui"))
        ui_file.open(QtCore.QFile.ReadOnly)
        loader = QUiLoader()
        self.winLog = loader.load(ui_file, parentWidget=parent)
        ui_file.close()

        self.winLog.setWindowFlags(QtCore.Qt.Dialog | QtCore.Qt.FramelessWindowHint)

        if self.osType.usingWindows:
            self.winLog.setWindowTitle("Output")
        else:
            self.winLog.setWindowTitle("Launch Game - Wine output")

        # self.winLog.btnStart.setVisible(False)
        self.winLog.btnStart.setText("Back")
        self.winLog.btnStart.setEnabled(False)
        self.winLog.btnSave.setText("Save")
        self.winLog.btnSave.setEnabled(False)
        self.winLog.btnStop.setText("Exit")
        self.winLog.btnStart.clicked.connect(self.btnStartClicked)
        self.winLog.btnSave.clicked.connect(self.btnSaveClicked)
        self.winLog.btnStop.clicked.connect(self.btnStopClicked)

        self.aborted = False
        self.finished = False
        self.command = ""
        self.arguments = []

        gameParams = (
            argTemplate.replace("{SUBSCRIPTION}", account)
            .replace("{LOGIN}", server)
            .replace("{GLS}", ticket)
            .replace("{CHAT}", chatServer)
            .replace("{LANG}", language)
            .replace("{CRASHRECEIVER}", crashreceiver)
            .replace("{UPLOADTHROTTLE}", DefaultUploadThrottleMbps)
            .replace("{BUGURL}", bugurl)
            .replace("{AUTHSERVERURL}", authserverurl)
            .replace("{GLSTICKETLIFETIME}", glsticketlifetime)
            .replace("{SUPPORTURL}", supporturl)
            .replace("{SUPPORTSERVICEURL}", supportserviceurl)
        )

        if not hiResEnabled:
            gameParams = gameParams + " --HighResOutOfDate"

        self.process = QtCore.QProcess()
        self.process.readyReadStandardOutput.connect(self.readOutput)
        self.process.readyReadStandardError.connect(self.readErrors)
        self.process.finished.connect(self.resetButtons)

        if self.osType.usingWindows:
            self.command = appName
            self.process.setWorkingDirectory(runDir)

            os.chdir(runDir)

            for arg in gameParams.split(" "):
                self.arguments.append(arg)

        else:
            processEnviroment = QtCore.QProcessEnvironment.systemEnvironment()

            if wineDebug != "":
                processEnviroment.insert("WINEDEBUG", wineDebug)

            if winePrefix != "":
                processEnviroment.insert("WINEPREFIX", winePrefix)

            self.command = wineProgram
            self.process.setWorkingDirectory(runDir)

            self.arguments.append(appName)

            for arg in gameParams.split(" "):
                self.arguments.append(arg)

            # Applies needed settings for the buit in wine prefix
            if builtInPrefixEnabled:
                # Enables esync if open file limit is high enough
                if os.path.exists("/proc/sys/fs/file-max"):
                    with open("/proc/sys/fs/file-max") as file:
                        file_data = file.read()
                        if int(file_data) >= 524288:
                            processEnviroment.insert("WINEESYNC", "1")

                # Adds dll overrides for directx, so dxvk is used instead of wine3d
                processEnviroment.insert("WINEDLLOVERRIDES", "d3d11=n;dxgi=n;d3d10=n")

            self.process.setProcessEnvironment(processEnviroment)

        self.winLog.txtLog.append("Connecting to server: " + worldName)
        self.winLog.txtLog.append("Account: " + accountText)
        self.winLog.txtLog.append("Game Directory: " + runDir)
        self.winLog.txtLog.append("Game Client: " + appName)

    def readOutput(self):
        self.winLog.txtLog.append(QByteArray2str(self.process.readAllStandardOutput()))

    def readErrors(self):
        self.winLog.txtLog.append(QByteArray2str(self.process.readAllStandardError()))

    def resetButtons(self, exitCode, exitStatus):
        self.finished = True
        self.winLog.btnStop.setText("Exit")
        self.winLog.btnSave.setEnabled(True)
        self.winLog.btnStart.setEnabled(True)
        if self.aborted:
            self.winLog.txtLog.append("<b>***  Aborted  ***</b>")
        else:
            self.winLog.txtLog.append("<b>***  Finished  ***</b>")

    def btnStartClicked(self):
        if self.finished:
            self.parent.show()
            self.winLog.close()

    def btnStopClicked(self):
        if self.finished:
            self.winLog.close()
        else:
            self.aborted = True
            self.process.kill()

    # Saves a file with the debug log generated by running the game
    def btnSaveClicked(self):
        filename = QtWidgets.QFileDialog.getSaveFileName(
            self.winLog, "Save log file", self.homeDir
        )[0]

        if filename != "":
            with open(filename, "w") as outfile:
                outfile.write(self.winLog.txtLog.toPlainText())

    def Run(self):
        self.finished = False

        self.winLog.btnStop.setText("Abort")
        self.process.start(self.command, self.arguments)

        return self.winLog.exec_()
