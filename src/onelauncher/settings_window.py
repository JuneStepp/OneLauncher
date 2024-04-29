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
import re
from contextlib import suppress
from pathlib import Path
from uuid import UUID

import attrs
import trio
from PySide6 import QtCore, QtGui, QtWidgets

from .config_manager import ConfigManager
from .game_config import ClientType
from .game_utilities import (
    InvalidGameDirError,
    find_game_dir_game_type,
)
from .network.game_launcher_config import GameLauncherConfig
from .program_config import GamesSortingMode
from .resources import available_locales
from .setup_wizard import SetupWizard
from .standard_game_launcher import get_standard_game_launcher_path
from .ui.settings_uic import Ui_dlgSettings
from .ui_utilities import show_warning_message
from .utilities import CaseInsensitiveAbsolutePath
from .wine_environment import edit_qprocess_to_use_wine


class SettingsWindow(QtWidgets.QDialog):
    def __init__(self, config_manager: ConfigManager, game_uuid: UUID):
        super().__init__(
            QtCore.QCoreApplication.instance().activeWindow(),  # type: ignore[union-attr]
            QtCore.Qt.WindowType.FramelessWindowHint,
        )
        self.config_manager = config_manager
        self.game_uuid = game_uuid
        self.ui = Ui_dlgSettings()
        self.ui.setupUi(self)  # type: ignore[no-untyped-call]

    def setup_ui(self) -> None:
        self.finished.connect(self.cleanup)

        self.ui.showAdvancedSettingsCheckbox.toggled.connect(
            self.toggle_advanced_settings
        )
        self.ui.showAdvancedSettingsCheckbox.setChecked(False)

        game_config = self.config_manager.read_game_config_file(self.game_uuid)
        self.ui.gameNameLineEdit.setText(game_config.name)
        escaped_other_game_names = [
            re.escape(self.config_manager.read_game_config_file(game_uuid).name)
            for game_uuid in self.config_manager.get_game_uuids()
            if game_uuid != self.game_uuid
        ]
        self.ui.gameNameLineEdit.setValidator(
            QtGui.QRegularExpressionValidator(
                QtCore.QRegularExpression(
                    f"^(?!^({'|'.join(escaped_other_game_names)})$).+$"
                )
            )
        )
        self.ui.gameUUIDLineEdit.setText(str(self.game_uuid))
        self.ui.gameDescriptionLineEdit.setText(game_config.description)
        self.ui.gameDirLineEdit.setText(str(game_config.game_directory))
        self.ui.browseGameConfigDirButton.clicked.connect(
            lambda: QtGui.QDesktopServices.openUrl(
                QtCore.QUrl.fromLocalFile(
                    self.config_manager.get_game_config_dir(self.game_uuid)
                )
            )
        )

        if os.name != "nt":
            self.ui.autoManageWineCheckBox.toggled.connect(
                self.auto_manage_wine_checkbox_toggled
            )
            self.ui.autoManageWineCheckBox.setChecked(
                game_config.wine.builtin_prefix_enabled
            )
            self.ui.winePrefixLineEdit.setText(
                str(game_config.wine.user_prefix_path or "")
            )
            self.ui.wineExecutableLineEdit.setText(
                str(game_config.wine.user_wine_executable_path or "")
            )
            self.ui.wineDebugLineEdit.setText(game_config.wine.debug_level or "")
        else:
            # WINE isn't used on Windows
            self.ui.tabWidget.setTabVisible(
                self.ui.tabWidget.indexOf(self.ui.winePage), False
            )

        self.setup_client_type_combo_box()
        self.ui.standardLauncherLineEdit.setText(
            game_config.standard_game_launcher_filename or ""
        )
        self.ui.patchClientLineEdit.setText(game_config.patch_client_filename)
        self.ui.standardGameLauncherButton.clicked.connect(
            lambda: self.nursery.start_soon(self.run_standard_game_launcher)
        )
        self.ui.actionRunStandardGameLauncherWithPatchingDisabled.triggered.connect(
            lambda: self.nursery.start_soon(self.run_standard_game_launcher, True)
        )
        self.ui.standardGameLauncherButton.addAction(
            self.ui.actionRunStandardGameLauncherWithPatchingDisabled
        )

        self.ui.highResCheckBox.setChecked(game_config.high_res_enabled)

        program_config = self.config_manager.get_program_config()
        self.add_languages_to_combobox(self.ui.gameLanguageComboBox)
        self.ui.gameLanguageComboBox.setCurrentText(
            game_config.locale.display_name
            if game_config.locale
            else program_config.default_locale.display_name
        )
        self.add_languages_to_combobox(self.ui.defaultLanguageComboBox)
        self.ui.defaultLanguageComboBox.setCurrentText(
            program_config.default_locale.display_name
        )
        self.ui.defaultLanguageForUICheckBox.setChecked(
            program_config.always_use_default_locale_for_ui
        )

        self.ui.gamesSortingModeComboBox.addItem(
            "Priority", userData=GamesSortingMode.PRIORITY
        )
        self.ui.gamesSortingModeComboBox.addItem(
            "Last Used", userData=GamesSortingMode.LAST_USED
        )
        self.ui.gamesSortingModeComboBox.addItem(
            "Alphabetical", userData=GamesSortingMode.ALPHABETICAL
        )
        self.ui.gamesSortingModeComboBox.setCurrentIndex(
            self.ui.gamesSortingModeComboBox.findData(program_config.games_sorting_mode)
        )

        self.ui.setupWizardButton.clicked.connect(self.start_setup_wizard)
        self.ui.gamesManagementButton.clicked.connect(
            lambda: self.start_setup_wizard(games_managing=True)
        )
        self.ui.gameDirButton.clicked.connect(self.choose_game_dir)
        self.ui.showAdvancedSettingsCheckbox.clicked.connect(
            self.toggle_advanced_settings
        )
        self.ui.settingsButtonBox.accepted.connect(self.save_config)

        self.open()

    async def run(self) -> None:
        self.setup_ui()
        async with trio.open_nursery() as self.nursery:
            self.nursery.start_soon(self.indicate_unavailable_client_types)
            self.nursery.start_soon(self.setup_newsfeed_option)
            # Will be canceled when the winddow is closed
            self.nursery.start_soon(trio.sleep_forever)

    def cleanup(self) -> None:
        self.nursery.cancel_scope.cancel()

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        self.cleanup()
        event.accept()

    async def setup_newsfeed_option(self) -> None:
        game_config = self.config_manager.read_game_config_file(self.game_uuid)
        # Attempt to set placeholder text to default newsfeed URL
        if game_config.newsfeed is None:
            game_launcher_config = await GameLauncherConfig.from_game_config(
                game_config=game_config
            )
            if game_launcher_config is not None:
                self.ui.gameNewsfeedLineEdit.setPlaceholderText(
                    game_launcher_config.get_newfeed_url(
                        locale=self.config_manager.get_ui_locale(
                            game_uuid=self.game_uuid
                        )
                    )
                )

        self.ui.gameNewsfeedLineEdit.setText(game_config.newsfeed or "")

    def auto_manage_wine_checkbox_toggled(self, is_checked: bool) -> None:
        self.ui.winePrefixLabel.setEnabled(not is_checked)
        self.ui.winePrefixLineEdit.setEnabled(not is_checked)
        self.ui.wineExecutableLabel.setEnabled(not is_checked)
        self.ui.wineExecutableLineEdit.setEnabled(not is_checked)

    def toggle_advanced_settings(self, is_checked: bool) -> None:
        advanced_widgets = [
            self.ui.gameUUIDLabel,
            self.ui.gameUUIDLineEdit,
            self.ui.gameNewsfeedLabel,
            self.ui.gameNewsfeedLineEdit,
            self.ui.browseGameConfigDirButton,
            self.ui.standardLauncherLabel,
            self.ui.standardLauncherLineEdit,
            self.ui.patchClientLabel,
            self.ui.patchClientLineEdit,
        ]
        for widget in advanced_widgets:
            widget.setVisible(is_checked)

        if os.name != "nt":
            self.ui.tabWidget.setTabVisible(
                self.ui.tabWidget.indexOf(self.ui.winePage), is_checked
            )

    def setup_client_type_combo_box(self) -> None:
        combo_box_item_names = {
            ClientType.WIN64: "64-bit",
            ClientType.WIN32: "32-bit",
            ClientType.WIN32_LEGACY: "32-bit Legacy",
        }
        game_config = self.config_manager.read_game_config_file(self.game_uuid)
        self.ui.clientTypeComboBox.addItem(
            combo_box_item_names[ClientType.WIN64], userData=ClientType.WIN64
        )
        self.ui.clientTypeComboBox.addItem(
            combo_box_item_names[ClientType.WIN32], userData=ClientType.WIN32
        )
        self.ui.clientTypeComboBox.addItem(
            combo_box_item_names[ClientType.WIN32_LEGACY],
            userData=ClientType.WIN32_LEGACY,
        )
        self.ui.clientTypeComboBox.setCurrentIndex(
            self.ui.clientTypeComboBox.findData(game_config.client_type)
        )

    async def indicate_unavailable_client_types(self) -> None:
        """Mark all unavailable client types as not found."""
        game_config = self.config_manager.read_game_config_file(self.game_uuid)
        game_launcher_config = await GameLauncherConfig.from_game_config(game_config)
        if game_launcher_config is not None:
            for (
                client_type,
                client_filename,
            ) in game_launcher_config.client_type_mapping.items():
                if client_filename is None:
                    item_index = self.ui.clientTypeComboBox.findData(
                        client_type,
                        QtCore.Qt.ItemDataRole.UserRole,
                        QtCore.Qt.MatchFlag.MatchExactly,
                    )
                    current_item_text = self.ui.clientTypeComboBox.itemText(item_index)
                    self.ui.clientTypeComboBox.setItemText(
                        item_index, f"{current_item_text} (Not found)"
                    )

    async def run_standard_game_launcher(self, disable_patching: bool = False) -> None:
        game_config = self.config_manager.get_game_config(self.game_uuid)
        launcher_path = await get_standard_game_launcher_path(game_config=game_config)

        if launcher_path is None:
            show_warning_message("No valid launcher executable found", self)
            return

        process = QtCore.QProcess()
        process.setWorkingDirectory(str(game_config.game_directory))
        process.setProgram(str(launcher_path))
        if disable_patching:
            process.setArguments(["-skiprawdownload", "-disablepatch"])
        edit_qprocess_to_use_wine(qprocess=process, wine_config=game_config.wine)
        process.startDetached()

    def choose_game_dir(self) -> None:
        gameDirLineEdit = self.ui.gameDirLineEdit.text()

        if gameDirLineEdit == "":
            if os.name == "nt":
                starting_dir = Path(
                    os.environ.get("PROGRAMFILES") or "C:/Program Files"
                )
            else:
                starting_dir = Path("~").expanduser()
        else:
            starting_dir = Path(gameDirLineEdit)

        filename = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            "Game Directory",
            str(starting_dir),
            options=QtWidgets.QFileDialog.Option.ShowDirsOnly,
        )

        if filename == "":
            return None

        folder = CaseInsensitiveAbsolutePath(filename)
        game_config = self.config_manager.read_game_config_file(self.game_uuid)
        with suppress(InvalidGameDirError):
            if find_game_dir_game_type(folder) == game_config.game_type:
                self.ui.gameDirLineEdit.setText(str(folder))
            else:
                show_warning_message(
                    f"The folder selected isn't a valid installation folder for "
                    f"{game_config.game_type}.",
                    self,
                )

    def start_setup_wizard(self, games_managing: bool = False) -> None:
        self.hide()
        if games_managing:
            setup_wizard = SetupWizard(
                config_manager=self.config_manager,
                game_selection_only=True,
                select_existing_games=True,
            )
        else:
            setup_wizard = SetupWizard(
                config_manager=self.config_manager, select_existing_games=False
            )
        setup_wizard.exec()
        self.accept()

    def add_languages_to_combobox(self, combobox: QtWidgets.QComboBox) -> None:
        for locale in available_locales.values():
            combobox.addItem(QtGui.QPixmap(str(locale.flag_icon)), locale.display_name)
            combobox.model().sort(0)

    def save_wine_config(self) -> None:
        game_config = self.config_manager.read_game_config_file(self.game_uuid)
        updated_wine_config = attrs.evolve(
            game_config.wine,
            builtin_prefix_enabled=self.ui.autoManageWineCheckBox.isChecked(),
            user_prefix_path=(
                Path(self.ui.winePrefixLineEdit.text())
                if self.ui.winePrefixLineEdit.text()
                else None
            ),
            user_wine_executable_path=(
                Path(self.ui.wineExecutableLineEdit.text())
                if self.ui.wineExecutableLineEdit.text()
                else None
            ),
            debug_level=self.ui.wineDebugLineEdit.text() or None,
        )
        self.config_manager.update_game_config_file(
            self.game_uuid,
            attrs.evolve(game_config, wine=updated_wine_config),
        )

    def save_config(self) -> None:
        available_locales_display_names_mapping = {
            locale.display_name: locale for locale in available_locales.values()
        }

        if not self.ui.gameNameLineEdit.hasAcceptableInput():
            show_warning_message(
                "The game name you've chosen is already in use by another game.", self
            )
            return
        self.config_manager.update_game_config_file(
            self.game_uuid,
            attrs.evolve(
                self.config_manager.read_game_config_file(self.game_uuid),
                name=self.ui.gameNameLineEdit.text(),
                description=self.ui.gameDescriptionLineEdit.text(),
                newsfeed=self.ui.gameNewsfeedLineEdit.text() or None,
                locale=available_locales_display_names_mapping[
                    self.ui.gameLanguageComboBox.currentText()
                ],
                game_directory=CaseInsensitiveAbsolutePath(
                    self.ui.gameDirLineEdit.text()
                ),
                high_res_enabled=self.ui.highResCheckBox.isChecked(),
                client_type=self.ui.clientTypeComboBox.currentData(),
                standard_game_launcher_filename=(
                    self.ui.standardLauncherLineEdit.text() or None
                ),
                patch_client_filename=self.ui.patchClientLineEdit.text(),
            ),
        )

        if os.name != "nt":
            self.save_wine_config()

        self.config_manager.update_program_config_file(
            attrs.evolve(
                self.config_manager.read_program_config_file(),
                default_locale=available_locales_display_names_mapping[
                    self.ui.defaultLanguageComboBox.currentText()
                ],
                always_use_default_locale_for_ui=(
                    self.ui.defaultLanguageForUICheckBox.isChecked()
                ),
                games_sorting_mode=(self.ui.gamesSortingModeComboBox.currentData()),
            )
        )

        self.accept()
