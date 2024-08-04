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
from functools import cache
from pathlib import Path

import qtawesome
from PySide6 import QtCore, QtGui, QtWidgets

from onelauncher.ui.style import ApplicationStyle

from .__about__ import __title__, __version__
from .resources import data_dir


@cache
def _setup_qapplication() -> QtWidgets.QApplication:
    application = QtWidgets.QApplication(sys.argv)
    # See https://github.com/zhiyiYo/PyQt-Frameless-Window/issues/50
    application.setAttribute(
        QtCore.Qt.ApplicationAttribute.AA_DontCreateNativeWidgetSiblings
    )
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

    # The Qt "Windows" style doesn't work with dark mode
    if os.name == "nt":
        application.setStyle("Fusion")

    def set_qtawesome_defaults() -> None:
        qtawesome.reset_cache()
        qtawesome.set_defaults(color=application.palette().windowText().color())

    set_qtawesome_defaults()
    application.styleHints().colorSchemeChanged.connect(set_qtawesome_defaults)

    return application


@cache
def get_qapp() -> QtWidgets.QApplication:
    application = _setup_qapplication()
    # Setup ApplicationStyle
    _ = get_app_style()
    return application


@cache
def get_app_style() -> ApplicationStyle:
    return ApplicationStyle(_setup_qapplication())
