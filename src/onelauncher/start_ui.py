# coding=utf-8
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
import logging
import os
import sys
import urllib.error
import urllib.request
from json import loads as jsonLoads
from pathlib import Path

from pkg_resources import parse_version
from PySide6 import QtCore, QtGui, QtWidgets

import onelauncher.logs
from onelauncher import (__project_url__, __title__, __version__,
                         launch_arguments)
from onelauncher.config.program_config import program_config
from onelauncher.resources import get_resource
from onelauncher.config.games_config import games_config
from onelauncher.ui_utilities import show_message_box_details_as_markdown


def main():
    onelauncher.logs.setup_application_logging()
    global logger
    logger = logging.getLogger("main")

    launch_arguments.process_launch_arguments()

    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_ShareOpenGLContexts)
    application = QtWidgets.QApplication(sys.argv)
    application.setApplicationName(__title__)
    application.setApplicationDisplayName(__title__)
    application.setApplicationVersion(__version__)
    application.setWindowIcon(QtGui.QIcon(str(get_resource(
        Path("images/OneLauncherIcon.png"), program_config.get_ui_locale(None)))))

    # Set font size explicitly to stop OS text size options from
    # breaking the UI.
    font = QtGui.QFont()
    font.setPointSize(10)
    application.setFont(font)

    handle_windows_dark_theme()

    check_for_update()

    handle_program_start_setup_wizard()

    start_main_window()

    sys.exit(application.exec())


def handle_program_start_setup_wizard():
    """Run setup wizard if there are no settings"""
    # If game settings haven't been generated
    if not games_config.games:
        start_setup_wizard()

    # Close program if the user left the setup wizard
    # without generating the game settings
    if not games_config.games:
        sys.exit()


def start_main_window():
    # Import has to be done here, because some code run by
    # main_window.py imports requires the QApplication to exist.
    from onelauncher.main_window import MainWindow
    global main_window
    main_window = MainWindow()
    main_window.run()


def handle_windows_dark_theme():
    if os.name != "nt":
        return

    qsettings = QtCore.QSettings(
        "HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize",
        QtCore.QSettings.NativeFormat)
    # If user has dark theme activated
    if not qsettings.value("AppsUseLightTheme"):
        # Use QPalette to set custom dark theme for Windows.
        # The builtin Windows dark theme for Windows is not ready
        # as of 7-5-2021
        QtCore.QCoreApplication.instance().setStyle(
            QtWidgets.QStyleFactory.create("Fusion"))
        dark_palette = QtGui.QPalette()
        dark_color = QtGui.QColor(45, 45, 45)
        disabled_color = QtGui.QColor(127, 127, 127)

        dark_palette.setColor(QtGui.QPalette.Window, dark_color)
        dark_palette.setColor(QtGui.QPalette.WindowText, QtCore.Qt.white)
        dark_palette.setColor(QtGui.QPalette.Base,
                              QtGui.QColor(18, 18, 18))
        dark_palette.setColor(QtGui.QPalette.AlternateBase, dark_color)
        dark_palette.setColor(QtGui.QPalette.ToolTipBase, QtCore.Qt.white)
        dark_palette.setColor(QtGui.QPalette.ToolTipText, QtCore.Qt.white)
        dark_palette.setColor(QtGui.QPalette.Text, QtCore.Qt.white)
        dark_palette.setColor(QtGui.QPalette.Disabled,
                              QtGui.QPalette.Text, disabled_color)
        dark_palette.setColor(QtGui.QPalette.Button, dark_color)
        dark_palette.setColor(QtGui.QPalette.ButtonText, QtCore.Qt.white)
        dark_palette.setColor(QtGui.QPalette.Disabled,
                              QtGui.QPalette.ButtonText, disabled_color)
        dark_palette.setColor(QtGui.QPalette.BrightText, QtCore.Qt.red)
        dark_palette.setColor(QtGui.QPalette.Link,
                              QtGui.QColor(42, 130, 218))

        dark_palette.setColor(QtGui.QPalette.Highlight,
                              QtGui.QColor(42, 130, 218))
        dark_palette.setColor(
            QtGui.QPalette.HighlightedText, QtCore.Qt.black)
        dark_palette.setColor(QtGui.QPalette.Disabled,
                              QtGui.QPalette.HighlightedText, disabled_color)

        QtCore.QCoreApplication.instance().setPalette(dark_palette)
        QtCore.QCoreApplication.instance().setStyleSheet(
            "QToolTip { color: #ffffff; background-color: #2a82da; border: 1px solid white; }")


def start_setup_wizard(**kwargs):
    from onelauncher.setup_wizard import SetupWizard
    setup_wizard = SetupWizard(**kwargs)
    setup_wizard.exec()


def run_setup_wizard_with_main_window(**kwargs):
    """Run setup wizard and re-do main window initial setup"""
    start_setup_wizard(**kwargs)
    main_window.InitialSetup()


def check_for_update():
    """Notifies user if their copy of OneLauncher is out of date"""
    current_version = parse_version(__version__)
    repository_url = __project_url__
    if "github.com" not in repository_url.lower():
        logger.warning(
            "Repository URL set in Information.py is not "
            "at github.com. The system for update notifications"
            " only supports this site."
        )
        return

    latest_release_template = (
        "https://api.github.com/repos/{user_and_repo}/releases/latest"
    )
    latest_release_url = latest_release_template.format(
        user_and_repo=repository_url.lower().split("github.com")[
            1].strip("/")
    )

    try:
        with urllib.request.urlopen(latest_release_url, timeout=4) as response:
            release_dictionary = jsonLoads(response.read())
    except (urllib.error.URLError, urllib.error.HTTPError) as error:
        logger.error(error.reason, exc_info=True)
        return

    release_version = parse_version(release_dictionary["tag_name"])

    if release_version > current_version:
        url = release_dictionary["html_url"]
        name = release_dictionary["name"]
        description = release_dictionary["body"]

        messageBox = QtWidgets.QMessageBox()
        messageBox.setWindowFlag(QtCore.Qt.FramelessWindowHint)
        messageBox.setIcon(QtWidgets.QMessageBox.Information)
        messageBox.setStandardButtons(messageBox.Ok)

        centered_href = (
            f'<html><head/><body><p align="center"><a href="{url}">'
            f'<span>{name}</span></a></p></body></html>'
        )
        messageBox.setInformativeText(
            f"There is a new version of {__title__} available! {centered_href}"
        )
        messageBox.setDetailedText(description)
        show_message_box_details_as_markdown(messageBox)
        messageBox.exec()
    else:
        logger.info(f"{__title__} is up to date.")


if __name__ == "__main__":
    main()
