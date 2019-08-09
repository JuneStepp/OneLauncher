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
# (C) 2019 Jeremy Stepp <jeremy@bluetecno.com>
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
from qtpy import QtCore, QtGui, QtWidgets, uic
from .OneLauncherUtils import DetermineOS, QByteArray2str
import sys
import os.path
from pkg_resources import resource_filename


class StartGame:
    def __init__(self, appName, x86, argTemplate, account, server, ticket,
                 chatServer, language, runDir, wineProgram, wineDebug, winePrefix,
                 hiResEnabled, builtInPrefixEnabled, osType, homeDir, iconFileIn, rootDir,
                 crashreceiver, DefaultUploadThrottleMbps, bugurl, authserverurl,
                 supporturl, supportserviceurl, glsticketlifetime, realmName,
                 accountText, parent):

        #Fixes binary path for 64-bit client
        if x86:
            appName = ("x64" + os.sep + appName)

        self.homeDir = homeDir
        self.winLog = QtWidgets.QDialog()
        self.osType = osType
        self.realmName = realmName
        self.accountText = accountText
        self.parent = parent

        uifile = resource_filename(__name__, 'ui' + os.sep + 'winLog.ui')

        self.winLog = QtWidgets.QDialog(parent, QtCore.Qt.FramelessWindowHint)
        Ui_winLog, base_class = uic.loadUiType(uifile)
        self.uiLog = Ui_winLog()
        self.uiLog.setupUi(self.winLog)

        if self.osType.usingWindows:
            self.winLog.setWindowTitle("Output")
        else:
            self.winLog.setWindowTitle("Launch Game - Wine output")

        # self.uiLog.btnStart.setVisible(False)
        self.uiLog.btnStart.setText("Launcher")
        self.uiLog.btnStart.setEnabled(False)
        self.uiLog.btnSave.setText("Save")
        self.uiLog.btnSave.setEnabled(False)
        self.uiLog.btnStop.setText("Exit")
        self.uiLog.btnStart.clicked.connect(self.btnStartClicked)
        self.uiLog.btnSave.clicked.connect(self.btnSaveClicked)
        self.uiLog.btnStop.clicked.connect(self.btnStopClicked)

        self.aborted = False
        self.finished = False
        self.command = ""
        self.arguments = []

        gameParams = argTemplate.replace("{SUBSCRIPTION}", account).replace("{LOGIN}", server)\
            .replace("{GLS}", ticket).replace("{CHAT}", chatServer).replace("{LANG}", language)\
            .replace("{CRASHRECEIVER}", crashreceiver).replace("{UPLOADTHROTTLE}", DefaultUploadThrottleMbps)\
            .replace("{BUGURL}", bugurl).replace("{AUTHSERVERURL}", authserverurl)\
            .replace("{GLSTICKETLIFETIME}", glsticketlifetime).replace("{SUPPORTURL}", supporturl)\
            .replace("{SUPPORTSERVICEURL}", supportserviceurl)

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

            #Applies needed settings for the buit in wine prefix
            if builtInPrefixEnabled:
                #Enables esync if open file limit is high enough
                if os.path.exists("/proc/sys/fs/file-max"):
                    with open("/proc/sys/fs/file-max") as file:
                        file_data = file.read()
                        if int(file_data) >= 524288:
                            processEnviroment.insert("WINEESYNC", "1")

                #Adds dll overrides for directx, so dxvk is used instead of wine3d
                processEnviroment.insert("WINEDLLOVERRIDES", "d3d11=n;dxgi=n;d3d10=n")

            self.process.setProcessEnvironment(processEnviroment)

        self.uiLog.txtLog.append("Connecting to server: " + realmName)
        self.uiLog.txtLog.append("Account: " + accountText)
        self.uiLog.txtLog.append("Game Directory: " + runDir)
        self.uiLog.txtLog.append("Game Client: " + appName)

    def readOutput(self):
        self.uiLog.txtLog.append(QByteArray2str(
            self.process.readAllStandardOutput()))

    def readErrors(self):
        self.uiLog.txtLog.append(QByteArray2str(
            self.process.readAllStandardError()))

    def resetButtons(self, exitCode, exitStatus):
        self.finished = True
        self.uiLog.btnStop.setText("Exit")
        self.uiLog.btnSave.setEnabled(True)
        self.uiLog.btnStart.setEnabled(True)
        if self.aborted:
            self.uiLog.txtLog.append("<b>***  Aborted  ***</b>")
        else:
            self.uiLog.txtLog.append("<b>***  Finished  ***</b>")

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

    #Saves a file with the debug log generated by running the game
    def btnSaveClicked(self):
        filename = QtWidgets.QFileDialog.getSaveFileName(
            self.winLog, "Save log file", self.homeDir)[0]

        if filename != "":
            outfile = open(filename, "w")
            outfile.write(self.uiLog.txtLog.toPlainText())
            outfile.close()

    def Run(self):
        self.finished = False

        self.uiLog.btnStop.setText("Abort")
        self.process.start(self.command, self.arguments)

        return self.winLog.exec_()
