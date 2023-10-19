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
# (C) 2019-2023 June Stepp <contact@JuneStepp.me>
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

from PySide6 import QtCore, QtGui, QtWidgets

from . import games_sorted
from .config.games import games_config
from .config.games.game import save_game
from .config.games.wine import (get_wine_environment_from_game,
                                save_wine_environment)
from .config.program_config import program_config
from .game import ClientType, Game
from .game_utilities import GamesSortingMode, find_game_dir_game_type
from .network.game_launcher_config import GameLauncherConfig
from .resources import available_locales
from .standard_game_launcher import get_standard_game_launcher_path
from .setup_wizard import SetupWizard
from .ui.settings_uic import Ui_dlgSettings
from .ui_utilities import show_warning_message
from .utilities import CaseInsensitiveAbsolutePath
from .wine_environment import edit_qprocess_to_use_wine


class SettingsWindow(QtWidgets.QDialog):
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

        self.ui.showAdvancedSettingsCheckbox.toggled.connect(
            self.toggle_advanced_settings)
        self.ui.showAdvancedSettingsCheckbox.setChecked(False)

        self.ui.gameNameLineEdit.setText(self.game.name)
        escaped_other_game_names = [
            re.escape(
                game.name) for game in games_sorted.games.values() if game != self.game]
        self.ui.gameNameLineEdit.setValidator(QtGui.QRegularExpressionValidator(
            QtCore.QRegularExpression(f"^(?!^({'|'.join(escaped_other_game_names)})$).+$")))
        self.ui.gameUUIDLineEdit.setText(str(self.game.uuid))
        self.ui.gameDescriptionLineEdit.setText(
            self.game.description)
        self.setup_newsfeed_option()
        self.ui.gameDirLineEdit.setText(
            str(self.game.game_directory))
        self.ui.browseGameConfigDirButton.clicked.connect(
            lambda: QtGui.QDesktopServices.openUrl(
                QtCore.QUrl.fromLocalFile(
                    games_config.get_game_config_dir(self.game.uuid))))

        if os.name != "nt":
            self.wine_env = get_wine_environment_from_game(self.game)
            self.ui.autoManageWineCheckBox.toggled.connect(
                self.auto_manage_wine_checkbox_toggled)
            self.ui.autoManageWineCheckBox.setChecked(
                self.wine_env.builtin_prefix_enabled)
            self.ui.winePrefixLineEdit.setText(
                str(self.wine_env.user_prefix_path or ""))
            self.ui.wineExecutableLineEdit.setText(
                str(self.wine_env.user_wine_executable_path or ""))
            self.ui.wineDebugLineEdit.setText(
                self.wine_env.debug_level or "")
        else:
            # WINE isn't used on Windows
            self.ui.tabWidget.setTabVisible(
                self.ui.tabWidget.indexOf(
                    self.ui.winePage), False)

        self.setup_client_type_combo_box()
        self.ui.standardLauncherLineEdit.setText(
            self.game.standard_game_launcher_filename or "")
        self.ui.patchClientLineEdit.setText(
            self.game.patch_client_filename)
        self.ui.standardGameLauncherButton.clicked.connect(
            self.run_standard_game_launcher)
        self.ui.actionRunStandardGameLauncherWithPatchingDisabled.triggered.connect(
            lambda: self.run_standard_game_launcher(disable_patching=True))
        self.ui.standardGameLauncherButton.addAction(
            self.ui.actionRunStandardGameLauncherWithPatchingDisabled)

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

        self.ui.gamesSortingModeComboBox.addItem(
            "Priority", userData=GamesSortingMode.PRIORITY)
        self.ui.gamesSortingModeComboBox.addItem(
            "Last Used", userData=GamesSortingMode.LAST_USED)
        self.ui.gamesSortingModeComboBox.addItem(
            "Alphabetical", userData=GamesSortingMode.ALPHABETICAL)
        self.ui.gamesSortingModeComboBox.setCurrentIndex(
            self.ui.gamesSortingModeComboBox.findData(
                program_config.games_sorting_mode))

        self.ui.setupWizardButton.clicked.connect(
            self.start_setup_wizard)
        self.ui.gamesManagementButton.clicked.connect(
            self.manage_games)
        self.ui.gameDirButton.clicked.connect(self.choose_game_dir)
        self.ui.showAdvancedSettingsCheckbox.clicked.connect(
            self.toggle_advanced_settings)
        self.ui.settingsButtonBox.accepted.connect(self.save_config)

    def setup_newsfeed_option(self):
        # Attempt to set placeholder text to default newsfeed URL
        if self.game.newsfeed is None:
            game_launcher_config = GameLauncherConfig.from_game(self.game)
            if game_launcher_config is not None:
                self.ui.gameNewsfeedLineEdit.setPlaceholderText(
                    game_launcher_config.get_newfeed_url(
                        program_config.get_ui_locale(
                            self.game)))

        self.ui.gameNewsfeedLineEdit.setText(
            self.game.newsfeed)

    def auto_manage_wine_checkbox_toggled(self, is_checked: bool) -> None:
        self.ui.winePrefixLabel.setEnabled(not is_checked)
        self.ui.winePrefixLineEdit.setEnabled(not is_checked)
        self.ui.wineExecutableLabel.setEnabled(not is_checked)
        self.ui.wineExecutableLineEdit.setEnabled(not is_checked)

    def toggle_advanced_settings(self, is_checked: bool):
        advanced_widgets = [self.ui.gameUUIDLabel,
                            self.ui.gameUUIDLineEdit,
                            self.ui.gameNewsfeedLabel,
                            self.ui.gameNewsfeedLineEdit,
                            self.ui.browseGameConfigDirButton,
                            self.ui.standardLauncherLabel,
                            self.ui.standardLauncherLineEdit,
                            self.ui.patchClientLabel,
                            self.ui.patchClientLineEdit]
        for widget in advanced_widgets:
            widget.setVisible(is_checked)

        if os.name != "nt":
            self.ui.tabWidget.setTabVisible(
                self.ui.tabWidget.indexOf(
                    self.ui.winePage),
                is_checked)

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

    def run_standard_game_launcher(self, disable_patching=False):
        launcher_path = get_standard_game_launcher_path(self.game)

        if launcher_path is None:
            show_warning_message("No valid launcher executable found", self)
            return

        process = QtCore.QProcess()
        process.setWorkingDirectory(str(self.game.game_directory))
        process.setProgram(str(launcher_path))
        if disable_patching:
            process.setArguments(["-skiprawdownload", "-disablepatch"])
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
            if find_game_dir_game_type(
                    folder) == self.game.game_type:
                self.ui.gameDirLineEdit.setText(str(folder))
            else:
                show_warning_message(
                    f"The folder selected isn't a valid installation folder for "
                    f"{self.game.game_type}.", self)

    def manage_games(self):
        self.start_setup_wizard(games_managing=True)

    def start_setup_wizard(self, games_managing=False):
        self.hide()
        if games_managing:
            setup_wizard = SetupWizard(
                game_selection_only=True,
                show_existing_games=True,
                select_existing_games=True)
        else:
            setup_wizard = SetupWizard(show_existing_games=True,
                                       select_existing_games=False)
        setup_wizard.exec()
        self.accept()

    def add_languages_to_combobox(self, combobox: QtWidgets.QComboBox):
        for locale in available_locales.values():
            combobox.addItem(QtGui.QPixmap(
                str(locale.flag_icon)), locale.display_name)
            combobox.model().sort(0)

    def save_wine_config(self) -> None:
        self.wine_env.builtin_prefix_enabled = (
            self.ui.autoManageWineCheckBox.isChecked())
        self.wine_env.user_prefix_path = (Path(self.ui.winePrefixLineEdit.text())
                                          if self.ui.winePrefixLineEdit.text()
                                          else None)
        self.wine_env.user_wine_executable_path = (Path(
            self.ui.wineExecutableLineEdit.text())
            if self.ui.wineExecutableLineEdit.text() else None)
        self.wine_env.debug_level = self.ui.wineDebugLineEdit.text() or None
        save_wine_environment(self.game, self.wine_env)

    def save_config(self):
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
            self.save_wine_config()

        program_config.default_locale = available_locales_display_names_mapping[self.ui.defaultLanguageComboBox.currentText(
        )]
        program_config.always_use_default_language_for_ui = self.ui.defaultLanguageForUICheckBox.isChecked()
        program_config.games_sorting_mode = self.ui.gamesSortingModeComboBox.currentData()

        save_game(self.game)
        program_config.save()

        self.accept()
