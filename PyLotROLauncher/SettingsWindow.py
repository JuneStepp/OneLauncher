# coding=utf-8
###########################################################################
# Name:   SettingsWindow
# Author: Alan Jackson
# Date:   26th March 2009
#
# Settings window for the Linux/OS X based launcher
# for the game Lord of the Rings Online
#
# Based on a script by SNy <SNy@bmx-chemnitz.de>
# Python port of LotROLinux by AJackson <ajackson@bcs.org.uk>
#
# (C) 2009 AJackson <ajackson@bcs.org.uk>
#
# This file is part of PyLotRO
#
# PyLotRO is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# PyLotRO is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with PyLotRO.  If not, see <http://www.gnu.org/licenses/>.
###########################################################################
from PyQt4 import QtCore, QtGui, uic
from .PyLotROUtils import DetermineOS
import os.path
import glob


class SettingsWindow:
    def __init__(self, parent, hiRes, app, wineProg, wineDebug, patchClient, winePrefix,
                 gameDir, homeDir, osType, rootDir):

        self.homeDir = homeDir
        self.osType = osType

        self.winSettings = QtGui.QDialog(parent)
        self.winSettings.setPalette(parent.palette())

        uifile = None

        if self.osType.usingWindows:
            try:
                from pkg_resources import resource_filename
                uifile = resource_filename(__name__, 'ui/winSettingsNative.ui')
            except:
                uifile = os.path.join(rootDir, "ui", "winSettingsNative.ui")
        else:
            try:
                from pkg_resources import resource_filename
                uifile = resource_filename(__name__, 'ui/winSettings.ui')
            except:
                uifile = os.path.join(rootDir, "ui", "winSettings.ui")

        Ui_dlgSettings, base_class = uic.loadUiType(uifile)
        self.uiSettings = Ui_dlgSettings()
        self.uiSettings.setupUi(self.winSettings)
        screen = QtGui.QDesktopWidget().screenGeometry()
        size = self.winSettings.geometry()
        self.winSettings.move(
            (screen.width() - size.width()) / 2, (screen.height() - size.height()) / 2)
        self.winSettings.setWindowTitle("Game Settings")

        if not self.osType.usingWindows:
            self.uiSettings.cboApplication.addItem("Wine")
            self.uiSettings.cboApplication.addItem("Crossover Games")
            self.uiSettings.cboApplication.addItem("Crossover Office")
            self.uiSettings.txtPrefix.setText(winePrefix)
            self.uiSettings.txtDebug.setText(wineDebug)
            self.uiSettings.txtProgram.setText(wineProg)
            self.uiSettings.txtProgram.setEnabled(False)

        self.uiSettings.txtGameDir.setText(gameDir)
        self.uiSettings.cboGraphics.addItem("Enabled")
        self.uiSettings.cboGraphics.addItem("Disabled")
        self.uiSettings.chkAdvanced.setChecked(False)
        self.uiSettings.txtPatchClient.setText(patchClient)
        self.uiSettings.txtPatchClient.setEnabled(False)

        if not self.osType.usingWindows:
            if app == "Wine":
                self.uiSettings.lblPrefix.setText("WINEPREFIX")
                self.uiSettings.txtPrefix.setVisible(True)
                self.uiSettings.cboBottle.setVisible(False)
                self.uiSettings.cboApplication.setCurrentIndex(0)
            else:
                self.uiSettings.lblPrefix.setText("Bottle")
                if app == "CXGames":
                    self.uiSettings.cboApplication.setCurrentIndex(1)
                else:
                    self.uiSettings.cboApplication.setCurrentIndex(2)
                self.uiSettings.txtPrefix.setVisible(False)
                self.uiSettings.cboBottle.setVisible(True)
                self.ShowBottles(winePrefix)

        if hiRes:
            self.uiSettings.cboGraphics.setCurrentIndex(0)
        else:
            self.uiSettings.cboGraphics.setCurrentIndex(1)

        QtCore.QObject.connect(self.uiSettings.btnGameDir, QtCore.SIGNAL(
            "clicked()"), self.btnGameDirClicked)
        QtCore.QObject.connect(self.uiSettings.chkAdvanced, QtCore.SIGNAL(
            "clicked()"), self.chkAdvancedClicked)

        if not self.osType.usingWindows:
            QtCore.QObject.connect(self.uiSettings.cboApplication, QtCore.SIGNAL("currentIndexChanged(int)"),
                                   self.cboApplicationChanged)

    def ShowBottles(self, defaultBottle=None):
        self.uiSettings.cboBottle.clear()

        tempdir = self.homeDir

        if self.uiSettings.cboApplication.currentIndex() == 1:
            tempdir += self.osType.settingsCXG
        else:
            tempdir += self.osType.settingsCXO

        currPos = 0

        for name in glob.glob("%s/*" % (tempdir)):
            if os.path.exists(name + "/drive_c"):
                tempBottle = name.replace(tempdir + "/", "")
                self.uiSettings.cboBottle.addItem(tempBottle)
                if tempBottle == defaultBottle:
                    self.uiSettings.cboBottle.setCurrentIndex(currPos)
                currPos += 1

    def cboApplicationChanged(self):
        if self.uiSettings.cboApplication.currentIndex() == 0:
            self.uiSettings.lblPrefix.setText("WINEPREFIX")
            self.uiSettings.txtPrefix.setVisible(True)
            self.uiSettings.cboBottle.setVisible(False)
        else:
            self.uiSettings.lblPrefix.setText("Bottle")
            self.uiSettings.txtPrefix.setVisible(False)
            self.uiSettings.cboBottle.setVisible(True)
            self.ShowBottles()

    def chkAdvancedClicked(self):
        if self.osType.usingWindows:
            if self.uiSettings.chkAdvanced.isChecked():
                self.uiSettings.txtPatchClient.setEnabled(True)
            else:
                self.uiSettings.txtPatchClient.setEnabled(False)
        else:
            if self.uiSettings.chkAdvanced.isChecked():
                self.uiSettings.txtProgram.setEnabled(True)
                self.uiSettings.txtPatchClient.setEnabled(True)
            else:
                self.uiSettings.txtProgram.setEnabled(False)
                self.uiSettings.txtPatchClient.setEnabled(False)

    def btnGameDirClicked(self):
        tempdir = self.uiSettings.txtGameDir.text()

        if tempdir == "":
            if self.osType.usingWindows:
                tempdir = os.environ.get('ProgramFiles')
            else:
                tempdir = self.homeDir

        filename = QtGui.QFileDialog.getExistingDirectory(
            self.winSettings, "Game Directory", tempdir)

        if filename != "":
            self.uiSettings.txtGameDir.setText(filename)

    def getApp(self):
        if self.osType.usingWindows:
            return "Native"
        else:
            if self.uiSettings.cboApplication.currentIndex() == 0:
                return "Wine"
            elif self.uiSettings.cboApplication.currentIndex() == 1:
                return "CXGames"
            else:
                return "CXOffice"

    def getPrefix(self):
        if self.uiSettings.cboApplication.currentIndex() == 0:
            return self.uiSettings.txtPrefix.text()
        else:
            return self.uiSettings.cboBottle.currentText()

    def getProg(self):
        return self.uiSettings.txtProgram.text()

    def getDebug(self):
        return self.uiSettings.txtDebug.text()

    def getPatchClient(self):
        return self.uiSettings.txtPatchClient.text()

    def getGameDir(self):
        return self.uiSettings.txtGameDir.text()

    def getHiRes(self):
        if self.uiSettings.cboGraphics.currentIndex() == 0:
            return True
        else:
            return False

    def Run(self):
        return self.winSettings.exec_()
