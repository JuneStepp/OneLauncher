# coding=utf-8
###########################################################################
# Class to handle checking bottle/prefix configuration
# for OneLauncher.
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
from pkg_resources import resource_filename
import os
import sys
from .Settings import Settings


class CheckConfig:
    def __init__(self, app, winePrefix, homeDir, osType, rootDir, parent):
        self.app = app
        self.winePrefix = winePrefix
        self.homeDir = homeDir
        self.osType = osType

        self.winCheckConfig = QtWidgets.QDialog(parent, QtCore.Qt.FramelessWindowHint)

        uifile = resource_filename(__name__, 'ui' + os.sep + 'winCheckConfig.ui')

        Ui_dlgCheckConfig, base_class = uic.loadUiType(uifile)
        self.uiSettings = Ui_dlgCheckConfig()
        self.uiSettings.setupUi(self.winCheckConfig)

        if self.app == "Wine":
            self.winCheckConfig.setWindowTitle("Prefix Checker")
        else:
            self.winCheckConfig.setWindowTitle("Bottle Checker")

        self.uiSettings.lblWinVersion.setText(self.findWinVer())
        self.uiSettings.lblMemory.setText(self.findGraphicsMemory())

        if self.findVC2005():
            self.uiSettings.lblVCRun.setText("Installed")
        else:
            self.uiSettings.lblVCRun.setText("Not found")

    def findVC2005(self):
        vc2005 = False

        try:
            infile = None

            if self.app == "Wine":
                if self.winePrefix == "":
                    infile = open(self.homeDir + os.sep +
                                  ".wine" + os.sep + "system.reg", "r")
                else:
                    infile = open(self.winePrefix +
                                  os.sep + "system.reg", "r")
            elif self.app == "CXGames":
                infile = open(self.homeDir + os.sep + self.osType.settingsCXG + os.sep +
                              self.winePrefix + os.sep + "system.reg", "r")
            elif self.app == "CXOffice":
                infile = open(self.homeDir + os.sep + self.osType.settingsCXO + os.sep +
                              self.winePrefix + os.sep + "system.reg", "r")
            else:
                temp = os.environ.get('WINEPREFIX')

                if temp == None:
                    temp = os.environ.get('OLDPWD') + os.sep + ".wine"

                infile = open(temp + os.sep + "system.reg", "r")

            systemReg = infile.readlines()
            infile.close()

            index = 0

            while index < len(systemReg):
                if systemReg[index].find("Microsoft Visual C++ 2005 Redistributable") >= 0:
                    vc2005 = True
                    index = len(systemReg)

                index += 1
        except:
            vc2005 = False

        return vc2005

    def findWinVer(self):
        version = "Unknown"

        try:
            infile = None

            if self.app == "Wine":
                if self.winePrefix == "":
                    infile = open(self.homeDir + os.sep +
                                  ".wine" + os.sep + "user.reg", "r")
                else:
                    infile = open(self.winePrefix +
                                  os.sep + "user.reg", "r")
            elif self.app == "CXGames":
                infile = open(self.homeDir + os.sep + self.osType.settingsCXG + os.sep +
                              self.winePrefix + os.sep + "user.reg", "r")
            elif self.app == "CXOffice":
                infile = open(self.homeDir + os.sep + self.osType.settingsCXO + os.sep +
                              self.winePrefix + os.sep + "user.reg", "r")
            else:
                temp = os.environ.get('WINEPREFIX')

                if temp == None:
                    temp = os.environ.get('OLDPWD') + os.sep + ".wine"

                infile = open(temp + os.sep + "user.reg", "r")

            userReg = infile.readlines()
            infile.close()

            printing = False
            index = 0

            while index < len(userReg):
                if userReg[index].startswith("[") and printing:
                    printing = False
                    index = len(userReg)
                else:
                    if printing:
                        if userReg[index].startswith("\"Version\""):
                            version = userReg[index].strip().replace(
                                "\"", "").replace("Version=", "")

                    if userReg[index].startswith("[Software\\\\Wine]"):
                        printing = True

                    index += 1

            if version == "Unknown":
                if self.app == "Wine":
                    if self.winePrefix == "":
                        infile = open(self.homeDir + os.sep +
                                      ".wine" + os.sep + "system.reg", "r")
                    else:
                        infile = open(self.winePrefix +
                                      os.sep + "system.reg", "r")
                elif self.app == "CXGames":
                    infile = open(self.homeDir + os.sep + self.osType.settingsCXG + os.sep +
                                  self.winePrefix + os.sep + "system.reg", "r")
                elif self.app == "CXOffice":
                    infile = open(self.homeDir + os.sep + self.osType.settingsCXO + os.sep +
                                  self.winePrefix + os.sep + "system.reg", "r")
                else:
                    temp = os.environ.get('WINEPREFIX')

                    if temp == None:
                        temp = os.environ.get('OLDPWD') + os.sep + ".wine"

                    infile = open(temp + os.sep + "system.reg", "r")

                systemReg = infile.readlines()
                infile.close()

                printing = False
                index = 0

                while index < len(systemReg):
                    if systemReg[index].startswith("[") and printing:
                        printing = False
                        index = len(systemReg)
                    else:
                        if printing:
                            if systemReg[index].startswith("\"CurrentBuildNumber\""):
                                tempStr = systemReg[index].strip().replace(
                                    "\"", "")
                                tempStr = tempStr.replace(
                                    "CurrentBuildNumber=", "")
                                if tempStr == "2195":
                                    version = "win2k"
                                else:
                                    version = "not win2k"

                        if systemReg[index].startswith("[Software\\\\Microsoft\\\\Windows NT\\\\CurrentVersion]"):
                            printing = True

                        index += 1
        except:
            version = "Unknown"

        return version

    def findGraphicsMemory(self):
        memory = "auto detect"

        try:
            infile = None

            if self.app == "Wine":
                if self.winePrefix == "":
                    infile = open(self.homeDir + os.sep +
                                  ".wine" + os.sep + "user.reg", "r")
                else:
                    infile = open(self.winePrefix +
                                  os.sep + "user.reg", "r")
            elif self.app == "CXGames":
                infile = open(self.homeDir + os.sep + self.osType.settingsCXG + os.sep +
                              self.winePrefix + os.sep + "user.reg", "r")
            elif self.app == "CXOffice":
                infile = open(self.homeDir + os.sep + self.osType.settingsCXO + os.sep +
                              self.winePrefix + os.sep + "user.reg", "r")
            else:
                temp = os.environ.get('WINEPREFIX')

                if temp == None:
                    temp = os.environ.get('OLDPWD') + os.sep + ".wine"

                infile = open(temp + os.sep + "user.reg", "r")

            userReg = infile.readlines()
            infile.close()

            printing = False
            index = 0

            while index < len(userReg):
                if userReg[index].startswith("[") and printing:
                    printing = False
                    index = len(userReg)
                else:
                    if printing:
                        if userReg[index].startswith("\"VideoMemorySize\""):
                            memory = userReg[index].strip().replace(
                                "\"", "").replace("VideoMemorySize=", "")

                    if userReg[index].startswith("[Software\\\\Wine\\\\Direct3D]"):
                        printing = True

                    index += 1
        except:
            memory = "auto detect"

        return memory

    def Run(self):
        return self.winCheckConfig.exec_()
