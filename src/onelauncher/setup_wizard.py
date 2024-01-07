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
from pathlib import Path
from shutil import rmtree
from typing import List

from PySide6 import QtCore, QtGui, QtWidgets

from . import games_sorted
from .__about__ import __title__
from .config.games import games_config
from .config.games.game import get_game_from_config, save_game
from .config.program_config import program_config
from .game import Game
from .game_utilities import GamesSortingMode, find_game_dir_game_type
from .resources import available_locales
from .ui.setup_wizard_uic import Ui_Wizard
from .ui_utilities import show_warning_message
from .utilities import CaseInsensitiveAbsolutePath


class SetupWizard(QtWidgets.QWizard):
    def __init__(self,
                 game_selection_only: bool = False,
                 show_existing_games: bool = False,
                 select_existing_games: bool = True):
        super(SetupWizard, self).__init__()

        self.game_selection_only = game_selection_only
        self.show_existing_games = show_existing_games
        self.select_existing_games = select_existing_games

        self.setWindowTitle(f"{__title__} Setup Wizard")

        self.ui = Ui_Wizard()
        self.ui.setupUi(self)

        self.add_available_languages_to_ui()

        self.ui.addGameButton.clicked.connect(self.browse_for_game_dir)
        self.ui.upPriorityButton.clicked.connect(
            self.raise_selected_game_priority)
        self.ui.downPriorityButton.clicked.connect(
            self.lower_selected_game_priority)
        self.games_found = False
        self.currentIdChanged.connect(self.current_id_changed)
        self.accepted.connect(self.save_settings)

        if self.game_selection_only:
            for id in self.pageIds():
                self.removePage(id)

            self.addPage(self.ui.gamesSelectionWizardPage)
            self.setOption(
                QtWidgets.QWizard.WizardOption.NoBackButtonOnLastPage, True)
            self.find_games()

    def add_available_languages_to_ui(self):
        for locale in available_locales.values():
            item = QtWidgets.QListWidgetItem(QtGui.QPixmap(
                str(locale.flag_icon)), locale.display_name)
            self.ui.languagesListWidget.addItem(item)

            # Default locale should be selected in the list by default.
            if locale == program_config.default_locale:
                self.ui.languagesListWidget.setCurrentItem(item)

    def raise_selected_game_priority(self):
        item = self.ui.gamesListWidget.currentItem()
        row = self.ui.gamesListWidget.row(item)
        if row == 0:
            return
        self.ui.gamesListWidget.takeItem(row)
        self.ui.gamesListWidget.insertItem(row - 1, item)
        self.ui.gamesListWidget.setCurrentItem(item)

    def lower_selected_game_priority(self):
        item = self.ui.gamesListWidget.currentItem()
        row = self.ui.gamesListWidget.row(item)
        # Item is already at end of list
        if row == self.ui.gamesListWidget.count() - 1:
            return
        self.ui.gamesListWidget.takeItem(row)
        self.ui.gamesListWidget.insertItem(row + 1, item)
        self.ui.gamesListWidget.setCurrentItem(item)

    def current_id_changed(self, new_id):
        if new_id == -1:
            return

        if (self.currentPage() ==
                self.ui.gamesSelectionWizardPage and not self.games_found):
            self.find_games()
        elif new_id == self.ui.gamesSelectionWizardPage.nextId():
            self.games_selection_page_finished()

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
                (Path("~").expanduser() / ".steam/steam/steamapps/compatdata",
                 "*"),
                (Path("~").expanduser() / ".steam/steam/SteamApps/compatdata",
                 "*"),
                (Path("~").expanduser() / ".steam/steamapps/compatdata", "*"),
                (Path("~").expanduser() /
                    ".local/share/Steam/steamapps/compatdata", "*"),
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
            games_sorted.get_games_sorted_by_priority(),
            select_games=self.select_existing_games)

    def add_games_from_list(
            self,
            games: List[Game],
            select_games: bool = False) -> None:
        """Add games from list to game finding UI."""
        for game in games[::-1]:
            self.add_game(game, checked=select_games)

    def get_game_dir_list_item(
            self,
            game_dir: CaseInsensitiveAbsolutePath
    ) -> QtWidgets.QListWidgetItem | None:
        for i in range(self.ui.gamesListWidget.count()):
            item = self.ui.gamesListWidget.item(i)
            resolved_path = Path(item.text()).resolve()
            if resolved_path == game_dir.resolve():
                return item
        return None

    def add_game(
            self,
            game: Game | CaseInsensitiveAbsolutePath,
            checked: bool = False,
            selected: bool = False) -> None:
        game_dir = game.game_directory if type(game) is Game else game
        assert type(game_dir) is CaseInsensitiveAbsolutePath
        if item := self.get_game_dir_list_item(game_dir):
            messageBox = QtWidgets.QMessageBox(self)
            messageBox.setWindowFlag(QtCore.Qt.WindowType.FramelessWindowHint)
            messageBox.setIcon(QtWidgets.QMessageBox.Icon.Information)
            messageBox.setStandardButtons(messageBox.StandardButton.Ok)
            messageBox.setInformativeText("Directory already added")
            messageBox.exec()
            if selected:
                self.ui.gamesListWidget.setCurrentItem(item)
            return

        item = QtWidgets.QListWidgetItem(str(game_dir))
        item.setData(QtCore.Qt.ItemDataRole.UserRole, game)
        item.setIcon(QtGui.QIcon(str(game_dir / "icon.ico")))
        item.setCheckState(QtCore.Qt.CheckState.Checked if checked
                           else QtCore.Qt.CheckState.Unchecked)
        self.ui.gamesListWidget.insertItem(0, item)
        if selected:
            self.ui.gamesListWidget.setCurrentItem(item)

    def find_game_dirs(
            self,
            search_dir: CaseInsensitiveAbsolutePath,
            search_depth=5):
        if search_depth <= 0:
            return

        if find_game_dir_game_type(search_dir):
            self.add_game(search_dir)
            return

        for path in search_dir.glob("*"):
            if path.is_dir() and path.name.upper() != "BACKUP":
                self.find_game_dirs(path, search_depth=search_depth - 1)

    def browse_for_game_dir(self):
        if os.name == "nt":
            starting_dir = Path(os.environ.get("ProgramFiles"))
        else:
            starting_dir = Path("~").expanduser()

        game_dir_string = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            "Game Directory",
            str(starting_dir),
            options=QtWidgets.QFileDialog.ShowDirsOnly,
        )
        if not game_dir_string:
            return
        game_dir = CaseInsensitiveAbsolutePath(game_dir_string)
        if find_game_dir_game_type(game_dir):
            self.add_game(game_dir, selected=True)
        else:
            show_warning_message(
                "Not a valid game installation folder.", self)

    def get_selected_game_items(self) -> list[QtWidgets.QListWidgetItem]:
        items = []
        for i in range(self.ui.gamesListWidget.count()):
            item = self.ui.gamesListWidget.item(i)
            if item.checkState() == QtCore.Qt.CheckState.Checked:
                items.append(item)
        return items

    def games_selection_page_finished(self):
        if not self.ui.gamesSelectionWizardPage.isComplete():
            return

        # Go back to the games selection page
        # if no games have been selected.
        if not self.get_selected_game_items():
            show_warning_message(
                "There are no game folders selected. "
                "Please select at least one game folder to continue.", self
            )
            self.back()

    def sort_list_widget_items(self, items: List[QtWidgets.QListWidgetItem]
                               ) -> List[QtWidgets.QListWidgetItem]:
        """Sort list widget items by their row number."""
        items_dict = {item.listWidget().row(item): item for item in items}
        return [items_dict[key] for key in sorted(items_dict)]

    def delete_game_config(self, game: Game) -> None:
        if game.accounts:
            for account in game.accounts.values():
                account.delete_account_keyring_info()

        rmtree(games_config.get_game_config_dir(game.uuid))

    def reset_config(self) -> None:
        for game in games_sorted.games.values():
            self.delete_game_config(game)

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

            selected_locale_display_name = (
                self.ui.languagesListWidget.currentItem().text())
            program_config.default_locale = [
                locale for locale in available_locales.values(
                ) if locale.display_name == selected_locale_display_name][0]

            program_config.always_use_default_language_for_ui = (
                self.ui.alwaysUseDefaultLangForUICheckBox.isChecked())

            program_config.games_sorting_mode = GamesSortingMode.PRIORITY

        self.add_games_to_settings()

        program_config.save()
        program_config.__init__(
            program_config.config_path)

    def add_games_to_settings(self) -> None:
        """
        Add games to settings. This has to be done after language settings
        are set.
        """
        selected_items = self.sort_list_widget_items(
            self.get_selected_game_items())
        selected_games: List[Game] = []
        for i, game_item in enumerate(selected_items):
            item_data = game_item.data(QtCore.Qt.ItemDataRole.UserRole)
            # Update only priority if game already exists.
            if self.game_selection_only and type(item_data) is Game:
                item_data.sorting_priority = i
                selected_games.append(item_data)
                continue

            game_dir = item_data.game_directory if type(
                item_data) is Game else item_data
            assert type(game_dir) is CaseInsensitiveAbsolutePath
            uuid = games_sorted.get_new_uuid()
            game = get_game_from_config(
                {
                    "uuid": str(uuid),
                    "sorting_priority": i,
                    "game_type": find_game_dir_game_type(game_dir),
                    "game_directory": str(game_dir)})
            games_sorted.games[game.uuid] = game
            selected_games.append(game)

        # Remove any games that were not selected by the user.
        not_selected_games = [
            game for game in list(
                games_sorted.games.values()) if game not in selected_games]
        # Warn user that the games they didn't select will have their data
        # deleted.
        if (self.game_selection_only and not_selected_games and
                not self.get_games_config_reset_confirmation()):
            return
        for game in not_selected_games:
            del games_sorted.games[game.uuid]
            self.delete_game_config(game)

        # Save games
        for game in selected_games:
            save_game(game)
