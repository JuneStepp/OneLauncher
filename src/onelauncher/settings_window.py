# coding=utf-8
###########################################################################
# Settings window for OneLauncher.
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
import os
from pathlib import Path
from typing import Final, Optional
from uuid import UUID
from bidict import bidict
import re

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtUiTools import QUiLoader

from onelauncher import settings, program_settings, game_settings
from onelauncher.ui.settings_uic import Ui_dlgSettings
from onelauncher.start_ui import run_setup_wizard_with_main_window
from onelauncher.resources import get_game_dir_available_locales, available_locales
from onelauncher.ui_utilities import raise_warning_message
from onelauncher.utilities import check_if_valid_game_folder
from onelauncher.wine_management import edit_qprocess_to_use_wine

import onelauncher


class SettingsWindow(QtWidgets.QDialog):
    CLIENT_TYPE_MAPPING: Final = bidict({
        "64-bit": "WIN64", "32-bit": "WIN32", "32-bit Legacy": "WIN32Legacy"})
    GAMES_SORTING_MODES_MAPPING: Final = bidict({
        "Priority": "priority", "Alphabetical": "alphabetical", "Last Used": "last_used"})

    def __init__(self, game: settings.Game, game_client_filename: Optional[str]):
        super(SettingsWindow, self).__init__(
            qApp.activeWindow(), QtCore.Qt.FramelessWindowHint)
        self.game = game

        self.ui = Ui_dlgSettings()
        self.ui.setupUi(self)

        if game_client_filename:
            self.game_client_filename = game_client_filename
        else:
            self.ui.defaultGameLauncherButton.setDisabled(True)

        self.toggle_advanced_settings()

        self.ui.gameNameLineEdit.setText(self.game.name)
        escaped_other_game_names = [re.escape(
            game.name) for game in game_settings.games.values() if game != self.game]
        self.ui.gameNameLineEdit.setValidator(QtGui.QRegularExpressionValidator(QtCore.QRegularExpression(
            f"^(?!^({'|'.join(escaped_other_game_names)})$).+$")))
        self.ui.gameDescriptionLineEdit.setText(
            self.game.description)
        self.ui.gameNewsfeedLineEdit.setText(
            self.game.newsfeed)
        self.ui.defaultGameLauncherButton.clicked.connect(
            self.run_default_game_launcher)

        if not settings.usingWindows:
            if self.game.builtin_wine_prefix_enabled:
                self.ui.wineFormGroupBox.setChecked(False)
            else:
                self.ui.wineFormGroupBox.setCheckable(True)
                self.ui.prefixLineEdit.setText(
                    str(self.game.wine_prefix_path))
                self.ui.wineExecutableLineEdit.setText(
                    str(self.game.wine_path))

            self.ui.wineDebugLineEdit.setText(
                self.game.wine_debug_level)
        else:
            self.ui.tabWidget.removeTab(1)

        self.ui.gameDirLineEdit.setText(
            str(self.game.game_directory))
        self.ui.clientTypeComboBox.addItems(self.CLIENT_TYPE_MAPPING.keys())
        self.ui.clientTypeComboBox.setCurrentText(
            self.CLIENT_TYPE_MAPPING.inverse[self.game.client_type])

        self.ui.patchClientLineEdit.setText(
            str(self.game.patch_client_path))

        self.ui.highResCheckBox.setChecked(
            self.game.high_res_enabled)

        self.add_languages_to_combobox(self.ui.gameLanguageComboBox)
        self.ui.gameLanguageComboBox.setCurrentText(
            self.game.locale.display_name)
        self.add_languages_to_combobox(self.ui.defaultLanguageComboBox)
        self.ui.defaultLanguageComboBox.setCurrentText(
            program_settings.default_locale.display_name)
        self.ui.defaultLanguageForUICheckBox.setChecked(
            program_settings.always_use_default_language_for_ui)
        self.ui.gamesSortingModeComboBox.addItems(
            self.GAMES_SORTING_MODES_MAPPING.keys())
        self.ui.gamesSortingModeComboBox.setCurrentText(
            self.GAMES_SORTING_MODES_MAPPING.inverse[program_settings.games_sorting_mode])

        self.ui.setupWizardButton.clicked.connect(
            self.start_setup_wizard)
        self.ui.gamesManagementButton.clicked.connect(
            self.manage_games)
        self.ui.gameDirButton.clicked.connect(self.choose_game_dir)
        self.ui.showAdvancedSettingsCheckbox.clicked.connect(
            self.toggle_advanced_settings)
        self.ui.settingsButtonBox.accepted.connect(self.save_settings)

    def toggle_advanced_settings(self):
        if not settings.usingWindows:
            if self.ui.showAdvancedSettingsCheckbox.isChecked():
                self.ui.wineAdvancedFrame.show()
            else:
                self.ui.wineAdvancedFrame.hide()

        if self.ui.showAdvancedSettingsCheckbox.isChecked():
            self.ui.gameNewsfeedLabel.setVisible(True)
            self.ui.gameNewsfeedLineEdit.setVisible(True)

            self.ui.patchClientLineEdit.setVisible(True)
            self.ui.patchClientLabel.setVisible(True)
        else:
            self.ui.gameNewsfeedLabel.setVisible(False)
            self.ui.gameNewsfeedLineEdit.setVisible(False)

            self.ui.patchClientLineEdit.setVisible(False)
            self.ui.patchClientLabel.setVisible(False)

    def run_default_game_launcher(self):
        lowercase_launcher_filename = self.game_client_filename.lower().split('client')[
            0]+"launcher.exe"
        launcher_path = None
        for file in self.game.game_directory.iterdir():
            if file.name.lower() == lowercase_launcher_filename:
                launcher_path = file
                break

        if launcher_path is None:
            raise ValueError(
                f"Could not find a game launcher from {lowercase_launcher_filename}"
                f" in {self.game.game_directory}")

        process = QtCore.QProcess()
        process.setWorkingDirectory(str(self.game.game_directory))
        process.setProgram(str(launcher_path))
        edit_qprocess_to_use_wine(process)
        process.startDetached()

    def choose_game_dir(self):
        gameDirLineEdit = self.ui.gameDirLineEdit.text()

        if gameDirLineEdit == "":
            if settings.usingWindows:
                starting_dir = Path(os.environ.get("ProgramFiles"))
            else:
                starting_dir = Path("~").expanduser()
        else:
            starting_dir = Path(gameDirLineEdit)

        filename = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            "Game Directory",
            str(starting_dir),
            options=QtWidgets.QFileDialog.ShowDirsOnly,
        )

        if filename != "":
            if check_if_valid_game_folder(Path(filename),
                                          game_type=game_settings.current_game.game_type):
                self.ui.gameDirLineEdit.setText(filename)
            else:
                raise_warning_message(
                    f"The folder selected isn't a valid installation folder for "
                    f"{game_settings.current_game.game_type}.", self
                )

    def manage_games(self):
        self.start_setup_wizard(games_managing=True)

    def start_setup_wizard(self, games_managing=False):
        self.close()
        if games_managing:
            run_setup_wizard_with_main_window(
                game_selection_only=True, show_existing_games=True)
        else:
            run_setup_wizard_with_main_window()

    def add_languages_to_combobox(self, combobox: QtWidgets.QComboBox):
        for locale in available_locales.values():
            combobox.addItem(QtGui.QPixmap(
                str(locale.flag_icon)), locale.display_name)
            combobox.model().sort(0)

    def save_settings(self):
        available_locales_display_names_mapping = {
            locale.display_name: locale for locale in available_locales.values()}

        if not self.ui.gameNameLineEdit.hasAcceptableInput():
            raise_warning_message(
                "The game name you've chosen is already in use by another game.", self)
            return
        self.game.name = self.ui.gameNameLineEdit.text()
        self.game.description = self.ui.gameDescriptionLineEdit.text()
        self.game.newsfeed = self.ui.gameNewsfeedLineEdit.text()

        self.game.locale = available_locales_display_names_mapping[self.ui.gameLanguageComboBox.currentText(
        )]
        self.game.game_directory = Path(
            self.ui.gameDirLineEdit.text())
        self.game.high_res_enabled = self.ui.highResCheckBox.isChecked()
        self.game.client_type = self.CLIENT_TYPE_MAPPING[self.ui.clientTypeComboBox.currentText(
        )]
        self.game.patch_client_path = Path(
            self.ui.patchClientLineEdit.text())

        if not settings.usingWindows:
            self.game.builtin_wine_prefix_enabled = not self.ui.wineFormGroupBox.isChecked()
            if self.game.builtin_wine_prefix_enabled:
                self.game.wine_prefix_path = Path(
                    self.ui.prefixLineEdit.text())
                self.game.wine_path = Path(
                    self.ui.wineExecutableLineEdit.text())
            self.game.wine_debug_level = self.ui.wineDebugLineEdit.text()

        program_settings.default_locale = available_locales_display_names_mapping[self.ui.defaultLanguageComboBox.currentText(
        )]
        program_settings.always_use_default_language_for_ui = self.ui.defaultLanguageForUICheckBox.isChecked()
        program_settings.games_sorting_mode = self.GAMES_SORTING_MODES_MAPPING[self.ui.gamesSortingModeComboBox.currentText(
        )]

        game_settings.save()
        program_settings.save()

        self.accept()
