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
import os
from pathlib import Path
from shutil import rmtree
from typing import List

from bidict import bidict
from PySide6 import QtCore, QtGui, QtWidgets

from . import __title__, games_sorted
from .config.games import games_config
from .config.games.game import get_game_from_config, save_game
from .config.program_config import program_config
from .game import Game, GameType
from .game_utilities import (GamesSortingMode,
                                        find_game_dir_game_type)
from .resources import available_locales
from .ui.setup_wizard_uic import Ui_Wizard
from .ui_utilities import show_warning_message
from .utilities import CaseInsensitiveAbsolutePath


class SetupWizard(QtWidgets.QWizard):
    def __init__(self, game_selection_only: bool = False,
                 show_existing_games: bool = False):
        super(SetupWizard, self).__init__()

        self.game_selection_only = game_selection_only
        self.show_existing_games = show_existing_games

        self.setWindowTitle(f"{__title__} Setup Wizard")

        self.ui = Ui_Wizard()
        self.ui.setupUi(self)

        self.add_available_languages_to_ui()

        self.games_found = False
        self.game_type_to_ui_list = bidict({
            GameType.LOTRO: self.ui.lotroListWidget,
            GameType.DDO: self.ui.ddoListWidget})
        self.currentIdChanged.connect(self.current_id_changed)
        self.ui.lotroListWidget.itemDoubleClicked.connect(
            self.game_item_double_clicked)
        self.ui.ddoListWidget.itemDoubleClicked.connect(
            self.game_item_double_clicked)

        self.accepted.connect(self.save_settings)

        if self.game_selection_only:
            for id in self.pageIds():
                self.removePage(id)

            self.addPage(self.ui.gamesSelectionWizardPage)
            self.find_games()

    def add_available_languages_to_ui(self):
        for locale in available_locales.values():
            item = QtWidgets.QListWidgetItem(QtGui.QPixmap(
                str(locale.flag_icon)), locale.display_name)
            self.ui.languagesListWidget.addItem(item)

            # Default locale should be selected in the list by default.
            if locale == program_config.default_locale:
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
        if self.show_existing_games:
            self.add_existing_games()

        if os.name == "nt":
            startDir = CaseInsensitiveAbsolutePath("C:/")
            self.find_game_dirs(startDir / "Program Files")
            if (startDir / "Program Files (x86)").exists():
                self.find_game_dirs(startDir / "Program Files (x86)")
        else:
            for dir, pattern in [
                (Path("~").expanduser(), "*wine*"),
                (Path("~").expanduser() / ".steam/steam/steamapps/compatdata", "*"),
                (Path("~").expanduser() / ".steam/steam/SteamApps/compatdata", "*"),
                (Path("~").expanduser() / ".steam/steamapps/compatdata", "*"),
                (Path("~").expanduser() / ".local/share/Steam/steamapps/compatdata", "*"),
            ]:
                for path in dir.glob(pattern):
                    # Handle Steam Proton paths
                    if path.is_dir() and (path / "pfx").exists():
                        path = path / "pfx"

                    if path.is_dir() and (path / "drive_c").exists():
                        self.find_game_dirs(path / "drive_c/Program Files")
                        self.find_game_dirs(
                            path / "drive_c/Program Files (x86)")

        self.games_found = True

    def add_existing_games(self):
        self.add_games_from_list(
            games_sorted.get_games_by_game_type("LOTRO"))
        self.add_games_from_list(
            games_sorted.get_games_by_game_type("DDO"))

    def add_games_from_list(self, games: List[Game]) -> None:
        """Add games from list to game finding UI. All games in list
        must be of the same type. Ex. LOTRO"""
        ui_list = self.game_type_to_ui_list[games[0].game_type]

        for game in games[::-1]:
            item = QtWidgets.QListWidgetItem(str(game.game_directory))
            item.setData(QtCore.Qt.UserRole, game)
            ui_list.insertItem(0, item)

            # Select the added item
            ui_list.setCurrentRow(0)

    def find_game_dirs(
            self,
            search_dir: CaseInsensitiveAbsolutePath,
            search_depth=5):
        if search_depth <= 0:
            return

        if game_type := find_game_dir_game_type(search_dir):
            list_widget = self.game_type_to_ui_list[game_type]
            # Only add the game folder to the list if it isn't already there
            if list_widget.findItems(
                    str(search_dir),
                    QtCore.Qt.MatchFlag.MatchExactly):
                list_widget.insertItem(0, str(search_dir))
            return

        for path in search_dir.glob("*"):
            if path.is_dir() and path.name.upper() != "BACKUP":
                self.find_game_dirs(path, search_depth=search_depth - 1)

    def browse_for_game_dir(self, output_list: QtWidgets.QListWidget):
        if os.name == "nt":
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
        if output_list.findItems(folder_str, QtCore.Qt.MatchFlag.MatchExactly):
            return

        game_type = self.game_type_to_ui_list.inverse[output_list]
        if find_game_dir_game_type(
                CaseInsensitiveAbsolutePath(folder_str)) == game_type:
            output_list.insertItem(0, folder_str)

            # Select the added item
            output_list.setCurrentRow(0)
        else:
            show_warning_message(
                f"The folder selected isn't a valid installation folder for {game_type}.", self)

    def is_any_game_folder_selected(self) -> bool:
        """
        Check if any game folders have been added and selected.
        Brings up a warning message if not.
        """
        for list in self.game_type_to_ui_list.values():
            if list.selectedItems():
                return True

        show_warning_message(
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

    def sort_list_widget_items(
            self, items: List[QtWidgets.QListWidgetItem]) -> List[QtWidgets.QListWidgetItem]:
        """Sort list widget items by their row number."""
        items_dict = {item.listWidget().row(item): item for item in items}
        return [items_dict[key] for key in sorted(items_dict)]

    def reset_config(self) -> None:
        # Delete all accounts information stored with keyring
        for game in games_sorted.games.values():
            if game.accounts is None:
                continue
            for account in game.accounts.values():
                account.delete_account_keyring_info()

        program_config.config_path.unlink(missing_ok=True)
        rmtree(games_config.games_dir)
        program_config.__init__(
            program_config.config_path)
        games_config.__init__(games_config.games_dir)
        games_sorted.__init__([])

    def get_games_config_reset_confirmation(self) -> bool:
        """
        Ask user if they want to reset existing games config/data.
        Will do nothing and return True if there is no existing data.

        Returns:
            bool: If the user wants settings to be reset.
        """
        # Return True if there is no existing games data.
        if not (
            games_config.games_dir.exists() and any(
                games_config.games_dir.iterdir())):
            return True

        message_box = QtWidgets.QMessageBox(self)
        message_box.setWindowFlag(QtCore.Qt.WindowType.FramelessWindowHint)
        message_box.setIcon(QtWidgets.QMessageBox.Icon.Warning)
        message_box.setStandardButtons(
            message_box.StandardButton.Cancel | message_box.StandardButton.Yes)
        message_box.setDefaultButton(message_box.StandardButton.Cancel)
        message_box.setInformativeText(
            "Existing game data will be deleted. (settings, saved "
            "accounts, ect). Do you wish to continue?")

        return message_box.exec() == message_box.StandardButton.Yes

    def save_settings(self):
        if not self.game_selection_only:
            if self.get_games_config_reset_confirmation() is False:
                return
            self.reset_config()

            selected_locale_display_name = self.ui.languagesListWidget.currentItem().text()
            program_config.default_locale = [locale for locale in available_locales.values(
            ) if locale.display_name == selected_locale_display_name][0]

            program_config.always_use_default_language_for_ui = self.ui.alwaysUseDefaultLangForUICheckBox.isChecked()

            program_config.games_sorting_mode = GamesSortingMode.PRIORITY

        self.add_games_to_settings()

        program_config.save()
        program_config.__init__(
            program_config.config_path)

    def add_games_to_settings(self) -> None:
        """Add games to settings. This has to be done after language settings are set."""
        for game_type in self.game_type_to_ui_list:
            selected_items = self.sort_list_widget_items(
                self.game_type_to_ui_list[game_type].selectedItems())
            selected_games: List[Game] = []
            for i, game_item in enumerate(selected_items):
                if self.game_selection_only:
                    game = game_item.data(QtCore.Qt.ItemDataRole.UserRole)
                    if isinstance(game, Game):
                        game.sorting_priority = i
                        selected_games.append(game)
                        continue

                uuid = games_sorted.get_new_uuid()
                game = get_game_from_config({"uuid": str(uuid),
                                             "sorting_priority": i,
                                             "game_type": game_type,
                                             "game_directory": game_item.text()})
                games_sorted.games[game.uuid] = game
                selected_games.append(game)

            # Remove any games that were not selected by the user.
            for game in list(games_sorted.games.values()):
                if game.game_type != game_type:
                    continue

                if game not in selected_games:
                    del games_sorted.games[game.uuid]

            # Save games
            for game in selected_games:
                save_game(game)
