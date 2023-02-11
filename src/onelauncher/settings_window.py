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
import re
from pathlib import Path
from typing import Final

from bidict import bidict
from PySide6 import QtCore, QtGui, QtWidgets

from onelauncher import games_sorted
from onelauncher.config.games.game import save_game
from onelauncher.config.games.wine import (get_wine_environment_from_game,
                                           save_wine_environment)
from onelauncher.config.program_config import program_config
from onelauncher.games import ClientType, Game, GamesSortingMode
from onelauncher.network.game_launcher_config import GameLauncherConfig
from onelauncher.resources import available_locales
from onelauncher.standard_game_launcher import get_standard_game_launcher_path
from onelauncher.start_ui import run_setup_wizard_with_main_window
from onelauncher.ui.settings_uic import Ui_dlgSettings
from onelauncher.ui_utilities import show_warning_message
from onelauncher.utilities import (CaseInsensitiveAbsolutePath,
                                   check_if_valid_game_folder)
from onelauncher.wine_environment import edit_qprocess_to_use_wine


class SettingsWindow(QtWidgets.QDialog):
    GAMES_SORTING_MODES_MAPPING: Final = bidict(
        {
            "Priority": GamesSortingMode.PRIORITY,
            "Alphabetical": GamesSortingMode.ALPHABETICAL,
            "Last Used": GamesSortingMode.LAST_USED})

    def __init__(
            self,
            game: Game):
        super(
            SettingsWindow,
            self).__init__(
            QtCore.QCoreApplication.instance().activeWindow(),
            QtCore.Qt.WindowType.FramelessWindowHint)
        self.game = game

        self.ui = Ui_dlgSettings()
        self.ui.setupUi(self)

        self.toggle_advanced_settings()

        self.ui.gameNameLineEdit.setText(self.game.name)
        escaped_other_game_names = [
            re.escape(
                game.name) for game in games_sorted.games.values() if game != self.game]
        self.ui.gameNameLineEdit.setValidator(QtGui.QRegularExpressionValidator(
            QtCore.QRegularExpression(f"^(?!^({'|'.join(escaped_other_game_names)})$).+$")))
        self.ui.gameDescriptionLineEdit.setText(
            self.game.description)
        self.setup_newsfeed_option()
        self.ui.standardGameLauncherButton.clicked.connect(
            self.run_standard_game_launcher)

        if os.name != "nt":
            self.wine_env = get_wine_environment_from_game(self.game)
            if self.wine_env.builtin_prefix_enabled:
                self.ui.wineFormGroupBox.setChecked(False)
            else:
                self.ui.wineFormGroupBox.setCheckable(True)
                self.ui.prefixLineEdit.setText(
                    str(self.wine_env.user_prefix_path))
                self.ui.wineExecutableLineEdit.setText(
                    str(self.wine_env.user_wine_executable_path))

            self.ui.wineDebugLineEdit.setText(
                self.wine_env.debug_level or "")
        else:
            # WINE isn't used on Windows
            self.ui.tabWidget.removeTab(2)

        self.ui.gameDirLineEdit.setText(
            str(self.game.game_directory))
        self.setup_client_type_combo_box()

        self.ui.standardLauncherLineEdit.setText(
            self.game.standard_game_launcher_filename or "")
        self.ui.patchClientLineEdit.setText(
            self.game.patch_client_filename)

        self.ui.highResCheckBox.setChecked(
            self.game.high_res_enabled)

        self.add_languages_to_combobox(self.ui.gameLanguageComboBox)
        self.ui.gameLanguageComboBox.setCurrentText(
            self.game.locale.display_name)
        self.add_languages_to_combobox(self.ui.defaultLanguageComboBox)
        self.ui.defaultLanguageComboBox.setCurrentText(
            program_config.default_locale.display_name)
        self.ui.defaultLanguageForUICheckBox.setChecked(
            program_config.always_use_default_language_for_ui)
        self.ui.gamesSortingModeComboBox.addItems(
            self.GAMES_SORTING_MODES_MAPPING.keys())
        self.ui.gamesSortingModeComboBox.setCurrentText(
            self.GAMES_SORTING_MODES_MAPPING.inverse[program_config.games_sorting_mode])

        self.ui.setupWizardButton.clicked.connect(
            self.start_setup_wizard)
        self.ui.gamesManagementButton.clicked.connect(
            self.manage_games)
        self.ui.gameDirButton.clicked.connect(self.choose_game_dir)
        self.ui.showAdvancedSettingsCheckbox.clicked.connect(
            self.toggle_advanced_settings)
        self.ui.settingsButtonBox.accepted.connect(self.save_settings)

    def setup_newsfeed_option(self):
        # Attempt to set placeholder text to default newsfeed URL
        if self.game.newsfeed is None:
            game_launcher_config = GameLauncherConfig.from_game(self.game)
            if game_launcher_config is not None:
                self.ui.gameNewsfeedLineEdit.setPlaceholderText(
                    game_launcher_config.get_newfeed_url(
                        program_config.get_ui_locale(
                            games_sorted.current_game)))

        self.ui.gameNewsfeedLineEdit.setText(
            self.game.newsfeed)

    def toggle_advanced_settings(self):
        if os.name != "nt":
            if self.ui.showAdvancedSettingsCheckbox.isChecked():
                self.ui.wineAdvancedFrame.show()
            else:
                self.ui.wineAdvancedFrame.hide()

        if self.ui.showAdvancedSettingsCheckbox.isChecked():
            self.ui.gameNewsfeedLabel.setVisible(True)
            self.ui.gameNewsfeedLineEdit.setVisible(True)

            self.ui.standardLauncherLabel.setVisible(True)
            self.ui.standardLauncherLineEdit.setVisible(True)
            self.ui.patchClientLabel.setVisible(True)
            self.ui.patchClientLineEdit.setVisible(True)
        else:
            self.ui.gameNewsfeedLabel.setVisible(False)
            self.ui.gameNewsfeedLineEdit.setVisible(False)

            self.ui.standardLauncherLabel.setVisible(False)
            self.ui.standardLauncherLineEdit.setVisible(False)
            self.ui.patchClientLabel.setVisible(False)
            self.ui.patchClientLineEdit.setVisible(False)

    def setup_client_type_combo_box(self):
        combo_box_item_names = {ClientType.WIN64: "64-bit",
                                ClientType.WIN32: "32-bit",
                                ClientType.WIN32_LEGACY: "32-bit Legacy"}
        game_launcher_config = GameLauncherConfig.from_game(self.game)
        if game_launcher_config is not None:
            # Mark all unavailable client types as not found.
            for client_type, client_filename in (game_launcher_config.
                                                 client_type_mapping.items()):
                if client_filename is None:
                    combo_box_item_names[client_type] += " (Not found)"

        self.ui.clientTypeComboBox.addItem(
            combo_box_item_names[ClientType.WIN64], userData=ClientType.WIN64)
        self.ui.clientTypeComboBox.addItem(
            combo_box_item_names[ClientType.WIN32], userData=ClientType.WIN32)
        self.ui.clientTypeComboBox.addItem(
            combo_box_item_names[ClientType.WIN32_LEGACY], userData=ClientType.WIN32_LEGACY)
        self.ui.clientTypeComboBox.setCurrentIndex(
            self.ui.clientTypeComboBox.findData(
                self.game.client_type))

    def run_standard_game_launcher(self):
        launcher_path = get_standard_game_launcher_path(self.game)

        if launcher_path is None:
            show_warning_message("No valid launcher executable found", self)
            return

        process = QtCore.QProcess()
        process.setWorkingDirectory(str(self.game.game_directory))
        process.setProgram(str(launcher_path))
        edit_qprocess_to_use_wine(
            process, get_wine_environment_from_game(
                self.game))
        process.startDetached()

    def choose_game_dir(self):
        gameDirLineEdit = self.ui.gameDirLineEdit.text()

        if gameDirLineEdit == "":
            if os.name == "nt":
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
            folder = CaseInsensitiveAbsolutePath(filename)
            if check_if_valid_game_folder(
                    folder, game_type=games_sorted.current_game.game_type):
                self.ui.gameDirLineEdit.setText(str(folder))
            else:
                show_warning_message(
                    f"The folder selected isn't a valid installation folder for "
                    f"{games_sorted.current_game.game_type}.", self)

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
            show_warning_message(
                "The game name you've chosen is already in use by another game.", self)
            return
        self.game.name = self.ui.gameNameLineEdit.text()
        self.game.description = self.ui.gameDescriptionLineEdit.text()
        self.game.newsfeed = self.ui.gameNewsfeedLineEdit.text() or None

        self.game.locale = available_locales_display_names_mapping[self.ui.gameLanguageComboBox.currentText(
        )]
        self.game.game_directory = CaseInsensitiveAbsolutePath(
            self.ui.gameDirLineEdit.text())
        self.game.high_res_enabled = self.ui.highResCheckBox.isChecked()
        self.game.client_type = self.ui.clientTypeComboBox.currentData()
        self.game.standard_game_launcher_filename = (
            self.ui.standardLauncherLineEdit.text() or None)
        self.game.patch_client_filename = self.ui.patchClientLineEdit.text()

        if os.name != "nt":
            self.wine_env.builtin_prefix_enabled = not self.ui.wineFormGroupBox.isChecked()
            if not self.wine_env.builtin_prefix_enabled:
                self.wine_env.user_prefix_path = Path(
                    self.ui.prefixLineEdit.text())
                self.wine_env.user_wine_executable_path = Path(
                    self.ui.wineExecutableLineEdit.text())
            self.wine_env.debug_level = self.ui.wineDebugLineEdit.text() or None
            save_wine_environment(self.game, self.wine_env)

        program_config.default_locale = available_locales_display_names_mapping[self.ui.defaultLanguageComboBox.currentText(
        )]
        program_config.always_use_default_language_for_ui = self.ui.defaultLanguageForUICheckBox.isChecked()
        program_config.games_sorting_mode = self.GAMES_SORTING_MODES_MAPPING[self.ui.gamesSortingModeComboBox.currentText(
        )]

        save_game(self.game)
        program_config.save()

        self.accept()
