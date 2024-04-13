###########################################################################
# Runner for OneLauncher.
#
# Based on PyLotRO
# (C) 2009 AJackson <ajackson@bcs.org.uk>
#
# Based on LotROLinux
# (C) 2007-2008 AJackson <ajackson@bcs.org.uk>
#
#
# (C) 2019-2024 June Stepp <contact@JuneStepp.me>
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
import os
import sys
from pathlib import Path

from PySide6 import QtCore, QtGui, QtWidgets

from .__about__ import __title__, __version__
from .config_old.program_config import program_config
from .resources import get_resource


def setup_qtapplication() -> QtWidgets.QApplication:
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_ShareOpenGLContexts)
    application = QtWidgets.QApplication(sys.argv)
    # Will be quit after Trio event loop finishes
    application.setQuitOnLastWindowClosed(False)
    application.setApplicationName(__title__)
    application.setApplicationDisplayName(__title__)
    application.setApplicationVersion(__version__)
    application.setWindowIcon(
        QtGui.QIcon(
            str(
                get_resource(
                    Path("images/OneLauncherIcon.png"),
                    program_config.get_ui_locale(None),
                )
            )
        )
    )

    # Set font size explicitly to stop OS text size options from
    # breaking the UI.
    font = QtGui.QFont()
    font.setPointSize(10)
    application.setFont(font)

    handle_windows_dark_theme()
    return application


def handle_windows_dark_theme():
    if os.name != "nt":
        return

    qsettings = QtCore.QSettings(
        "HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize",
        QtCore.QSettings.Format.NativeFormat,
    )
    # If user has dark theme activated
    if not qsettings.value("AppsUseLightTheme"):
        # Use QPalette to set custom dark theme for Windows.
        # The builtin Windows dark theme for Windows is not ready
        # as of 7-5-2021
        QtCore.QCoreApplication.instance().setStyle(
            QtWidgets.QStyleFactory.create("Fusion")
        )
        dark_palette = QtGui.QPalette()
        dark_color = QtGui.QColor(45, 45, 45)
        disabled_color = QtGui.QColor(127, 127, 127)

        dark_palette.setColor(QtGui.QPalette.Window, dark_color)
        dark_palette.setColor(QtGui.QPalette.WindowText, QtCore.Qt.white)
        dark_palette.setColor(QtGui.QPalette.Base, QtGui.QColor(18, 18, 18))
        dark_palette.setColor(QtGui.QPalette.AlternateBase, dark_color)
        dark_palette.setColor(QtGui.QPalette.ToolTipBase, QtCore.Qt.white)
        dark_palette.setColor(QtGui.QPalette.ToolTipText, QtCore.Qt.white)
        dark_palette.setColor(QtGui.QPalette.Text, QtCore.Qt.white)
        dark_palette.setColor(
            QtGui.QPalette.Disabled, QtGui.QPalette.Text, disabled_color
        )
        dark_palette.setColor(QtGui.QPalette.Button, dark_color)
        dark_palette.setColor(QtGui.QPalette.ButtonText, QtCore.Qt.white)
        dark_palette.setColor(
            QtGui.QPalette.Disabled, QtGui.QPalette.ButtonText, disabled_color
        )
        dark_palette.setColor(QtGui.QPalette.BrightText, QtCore.Qt.red)
        dark_palette.setColor(QtGui.QPalette.Link, QtGui.QColor(42, 130, 218))

        dark_palette.setColor(QtGui.QPalette.Highlight, QtGui.QColor(42, 130, 218))
        dark_palette.setColor(QtGui.QPalette.HighlightedText, QtCore.Qt.black)
        dark_palette.setColor(
            QtGui.QPalette.Disabled, QtGui.QPalette.HighlightedText, disabled_color
        )

        QtCore.QCoreApplication.instance().setPalette(dark_palette)
        QtCore.QCoreApplication.instance().setStyleSheet(
            "QToolTip { color: #ffffff; background-color: #2a82da; border: 1px solid white; }"
        )
