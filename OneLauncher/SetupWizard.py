# coding=utf-8
###########################################################################
# Settings wizard for OneLauncher.
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
import glob
import os
from pathlib import Path
from typing import List, Optional
from uuid import UUID, uuid4
from bidict import bidict

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtUiTools import QUiLoader

import OneLauncher
from OneLauncher import Settings, __title__
from OneLauncher.resources import available_locales
from OneLauncher.ui_utilities import raise_warning_message
from OneLauncher.ui.setup_wizard_uic import Ui_Wizard


# Files that can be used to check if a folder is the installation
# direcotry of a game. These files should be in the root installation
# folder. Not for example, the 64-bit client folder within the root folder.
GAME_FOLDER_VERIFICATION_FILES = bidict({
    "LOTRO": Path("lotroclient.exe"), "DDO": Path("dndclient.exe")})


class SetupWizard(QtWidgets.QWizard):
    def __init__(self):
        super(SetupWizard, self).__init__()

        self.setWindowTitle(f"{__title__} Setup Wizard")

        self.ui = Ui_Wizard()
        self.ui.setupUi(self)

        self.add_available_languages_to_ui()

        self.games_found = False
        self.game_type_to_ui_list = bidict({
            "LOTRO": self.ui.lotroListWidget, "DDO": self.ui.ddoListWidget})
        self.currentIdChanged.connect(self.current_id_changed)
        self.ui.lotroListWidget.itemDoubleClicked.connect(
            self.game_item_double_clicked)
        self.ui.ddoListWidget.itemDoubleClicked.connect(
            self.game_item_double_clicked)

        self.accepted.connect(self.save_settings)

    def add_available_languages_to_ui(self):
        for locale in available_locales.values():
            item = QtWidgets.QListWidgetItem(QtGui.QPixmap(
                str(locale.flag_icon)), locale.display_name)
            self.ui.languagesListWidget.addItem(item)

            # Default locale should be selected in the list by default.
            if locale == OneLauncher.program_settings.default_locale:
                self.ui.languagesListWidget.setCurrentItem(item)

    def current_id_changed(self, new_id):
        if self.currentPage() == self.ui.gamesSelectionWizardPage and not self.games_found:
            self.find_games()
        elif new_id == self.ui.gamesSelectionWizardPage.nextId():
            self.games_selection_page_finished()

    def game_item_double_clicked(self, item: QtWidgets.QListWidgetItem):
        if item.text() == "Manually add game from filesystem...":
            self.browse_for_game_dir(item.listWidget())

    def find_games(self):
        if Settings.usingWindows:
            startDir = Path("C:/")
            self.find_game_dirs(startDir/"Program Files")
            if (startDir/"Program Files (x86)").exists():
                self.find_game_dirs(startDir/"Program Files (x86)")
        else:
            for dir, pattern in [
                (Path("~").expanduser(), "*wine*"),
                (Path("~").expanduser()/Settings.settingsCXG, "*"),
                (Path("~").expanduser()/Settings.settingsCXO, "*"),
                (Path("~").expanduser()/".steam/steam/steamapps/compatdata", "*"),
                (Path("~").expanduser()/".steam/steam/SteamApps/compatdata", "*"),
                (Path("~").expanduser()/".steam/steamapps/compatdata", "*"),
                (Path("~").expanduser()/".local/share/Steam/steamapps/compatdata", "*"),
            ]:
                for path in dir.glob(pattern):
                    # Handle Steam Proton paths
                    if path.is_dir() and (path/"pfx").exists():
                        path = path/"pfx"

                    if path.is_dir() and (path/"drive_c").exists():
                        self.find_game_dirs(path/"drive_c/Program Files")
                        self.find_game_dirs(
                            path/"drive_c/Program Files (x86)")

        self.games_found = True

    def find_game_dirs(self, search_dir: Path, search_depth=5):
        if search_depth <= 0:
            return

        game_type = self.check_if_valid_game_folder(search_dir)
        if game_type:
            list_widget = self.game_type_to_ui_list[game_type]
            # Only add the game folder to the list if it isn't already there
            if list_widget.findItems(str(search_dir), QtCore.Qt.MatchExactly):
                list_widget.insertItem(0, str(search_dir))
            return

        for path in search_dir.glob("*"):
            if path.is_dir() and path.name.upper() != "BACKUP":
                self.find_game_dirs(path, search_depth=search_depth-1)

    def browse_for_game_dir(self, output_list: QtWidgets.QListWidget):
        if Settings.usingWindows:
            starting_dir = Path(os.environ.get("ProgramFiles"))
        else:
            starting_dir = Path("~").expanduser()

        folder_str = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            "Game Directory",
            str(starting_dir),
            options=QtWidgets.QFileDialog.ShowDirsOnly,
        )

        if folder_str == "":
            return

        # Detect if folder is already in list
        if output_list.findItems(folder_str, QtCore.Qt.MatchExactly):
            return

        game_type = self.game_type_to_ui_list.inverse[output_list]
        if self.check_if_valid_game_folder(Path(folder_str),
                                           game_type=game_type):
            output_list.insertItem(0, folder_str)

            # Select the added item
            output_list.setCurrentRow(0)
        else:
            raise_warning_message(
                f"The folder selected isn't a valid installation folder for {game_type}.", self
            )

    def check_if_valid_game_folder(self, folder: Path, game_type: str = None) -> Optional[str]:
        """
        Checks for the game's verification file to validate that the
        folder is a valid game folder.
        """
        if game_type:
            verifying_files = [GAME_FOLDER_VERIFICATION_FILES[game_type]]
        else:
            verifying_files = GAME_FOLDER_VERIFICATION_FILES.values()

        for verifying_file in verifying_files:
            if (folder/verifying_file).exists():
                return GAME_FOLDER_VERIFICATION_FILES.inverse[verifying_file]

    def is_any_game_folder_selected(self) -> bool:
        """
        Check if any game folders have been added and selected.
        Brings up a warning message if not.
        """
        for list in self.game_type_to_ui_list.values():
            if list.selectedItems():
                return True

        raise_warning_message(
            "There are no game folders selected. "
            "Please select at least one game folder to continue.", self
        )
        return False

    def games_selection_page_finished(self):
        if not self.ui.gamesSelectionWizardPage.isComplete():
            return

        # Go back to the games selection page
        # if no games have been selected.
        if not self.is_any_game_folder_selected():
            self.back()

    def sort_list_widget_items(self, items: List[QtWidgets.QListWidgetItem]) -> List[QtWidgets.QListWidgetItem]:
        """Sort list widget items by their row number."""
        items_dict = {item.listWidget().row(item): item for item in items}
        return [items_dict[key] for key in sorted(items_dict)]

    def save_settings(self):
        # Reset settings
        OneLauncher.program_settings.config_path.unlink(missing_ok=True)
        OneLauncher.game_settings.config_path.unlink(missing_ok=True)
        OneLauncher.program_settings.__init__(
            OneLauncher.program_settings.config_path)
        OneLauncher.game_settings.__init__(
            OneLauncher.game_settings.config_path)

        selected_locale_display_name = self.ui.languagesListWidget.currentItem().text()
        OneLauncher.program_settings.default_locale = [locale for locale in available_locales.values(
        ) if locale.display_name == selected_locale_display_name][0]

        OneLauncher.program_settings.always_use_default_language_for_ui = self.ui.alwaysUseDefaultLangForUICheckBox.isChecked()

        OneLauncher.program_settings.games_sorting_mode = "priority"

        # Add games to settings. This has to be done after language settings are set.
        for game_type in self.game_type_to_ui_list:
            games_priority_sorted = []
            selected_items = self.sort_list_widget_items(
                self.game_type_to_ui_list[game_type].selectedItems())
            for game in selected_items:
                uuid = OneLauncher.game_settings.get_new_uuid()
                OneLauncher.game_settings.load_game({"uuid": str(uuid),
                                                     "game_type": game_type,
                                                     "game_directory": game.text()})
                games_priority_sorted.append(
                    OneLauncher.game_settings.games[uuid])

            if game_type == "LOTRO":
                OneLauncher.game_settings.lotro_games_priority_sorted = games_priority_sorted

                # Start off the last used list with the priority order,
                # since there is no use data yet.
                OneLauncher.game_settings.lotro_games_last_used_sorted
            elif game_type == "DDO":
                OneLauncher.game_settings.ddo_games_priority_sorted = games_priority_sorted

                # Start off the last used list with the priority order,
                # since there is no use data yet.
                OneLauncher.game_settings.ddo_games_last_used_sorted

        OneLauncher.program_settings.save()
        OneLauncher.game_settings.save()
        OneLauncher.program_settings.__init__(
            OneLauncher.program_settings.config_path)
        OneLauncher.game_settings.__init__(
            OneLauncher.game_settings.config_path)
