# coding=utf-8
###########################################################################
# Main window for OneLauncher.
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
import os
from pkg_resources import resource_filename


class AddonManager:
    def __init__(self, parent):

        self.winAddonManager = QtWidgets.QDialog(parent, QtCore.Qt.FramelessWindowHint)

        uifile = resource_filename(__name__, 'ui' + os.sep + 'winAddonManager.ui')

        Ui_dlgAddonManager, base_class = uic.loadUiType(uifile)
        self.uiAddonManager = Ui_dlgAddonManager()
        self.uiAddonManager.setupUi(self.winAddonManager)

        self.uiAddonManager.btnBox.rejected.connect(self.btnBoxActivated)

    def btnBoxActivated(self):
        self.winAddonManager.accept()

    def Run(self):
        self.winAddonManager.exec_()
