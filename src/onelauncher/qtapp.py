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
from .resources import OneLauncherLocale, data_dir


def setup_qtapplication() -> QtWidgets.QApplication:
    QtCore.QCoreApplication.setAttribute(
        QtCore.Qt.ApplicationAttribute.AA_ShareOpenGLContexts
    )
    application = QtWidgets.QApplication(sys.argv)
    # Will be quit after Trio event loop finishes
    application.setQuitOnLastWindowClosed(False)
    application.setApplicationName(__title__)
    application.setApplicationDisplayName(__title__)
    application.setApplicationVersion(__version__)
    application.setWindowIcon(
        QtGui.QIcon(
            str(
                data_dir / Path("images/OneLauncherIcon.png"),
            )
        )
    )

    # Set font size explicitly to stop OS text size options from
    # breaking the UI.
    font = QtGui.QFont()
    font.setPointSize(10)
    application.setFont(font)

    handle_windows_dark_theme(application)
    return application


def handle_windows_dark_theme(qapp: QtWidgets.QApplication) -> None:
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
        qapp.setStyle(QtWidgets.QStyleFactory.create("Fusion"))
        dark_palette = QtGui.QPalette()
        dark_color = QtGui.QColor(45, 45, 45)
        disabled_color = QtGui.QColor(127, 127, 127)

        dark_palette.setColor(QtGui.QPalette.ColorRole.Window, dark_color)
        dark_palette.setColor(
            QtGui.QPalette.ColorRole.WindowText, QtCore.Qt.GlobalColor.white
        )
        dark_palette.setColor(QtGui.QPalette.ColorRole.Base, QtGui.QColor(18, 18, 18))
        dark_palette.setColor(QtGui.QPalette.ColorRole.AlternateBase, dark_color)
        dark_palette.setColor(
            QtGui.QPalette.ColorRole.ToolTipBase, QtCore.Qt.GlobalColor.white
        )
        dark_palette.setColor(
            QtGui.QPalette.ColorRole.ToolTipText, QtCore.Qt.GlobalColor.white
        )
        dark_palette.setColor(
            QtGui.QPalette.ColorRole.Text, QtCore.Qt.GlobalColor.white
        )
        dark_palette.setColor(
            QtGui.QPalette.ColorGroup.Disabled,
            QtGui.QPalette.ColorRole.Text,
            disabled_color,
        )
        dark_palette.setColor(QtGui.QPalette.ColorRole.Button, dark_color)
        dark_palette.setColor(
            QtGui.QPalette.ColorRole.ButtonText, QtCore.Qt.GlobalColor.white
        )
        dark_palette.setColor(
            QtGui.QPalette.ColorGroup.Disabled,
            QtGui.QPalette.ColorRole.ButtonText,
            disabled_color,
        )
        dark_palette.setColor(
            QtGui.QPalette.ColorRole.BrightText, QtCore.Qt.GlobalColor.red
        )
        dark_palette.setColor(QtGui.QPalette.ColorRole.Link, QtGui.QColor(42, 130, 218))

        dark_palette.setColor(
            QtGui.QPalette.ColorRole.Highlight, QtGui.QColor(42, 130, 218)
        )
        dark_palette.setColor(
            QtGui.QPalette.ColorRole.HighlightedText, QtCore.Qt.GlobalColor.black
        )
        dark_palette.setColor(
            QtGui.QPalette.ColorGroup.Disabled,
            QtGui.QPalette.ColorRole.HighlightedText,
            disabled_color,
        )

        qapp.setPalette(dark_palette)
        qapp.setStyleSheet(
            "QToolTip { color: #ffffff; background-color: #2a82da; border: 1px solid white; }"
        )
