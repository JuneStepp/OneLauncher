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
from contextlib import suppress
from pathlib import Path
from uuid import UUID, uuid4

import attrs
from PySide6 import QtCore, QtGui, QtWidgets

from .__about__ import __title__
from .config_manager import ConfigFileParseError, ConfigManager
from .game_config import GameConfig
from .game_launcher_local_config import (
    GameLauncherLocalConfig,
    GameLauncherLocalConfigParseError,
)
from .game_utilities import (
    GamesSortingMode,
    InvalidGameDirError,
    find_game_dir_game_type,
    get_games_sorted_by_priority,
    get_launcher_config_paths,
)
from .official_clients import is_gls_url_for_preview_client
from .program_config import ProgramConfig
from .resources import available_locales, get_default_locale
from .ui.setup_wizard_uic import Ui_Wizard
from .ui_utilities import show_warning_message
from .utilities import CaseInsensitiveAbsolutePath
from .wine.config import WineConfigSection


class SetupWizard(QtWidgets.QWizard):
    def __init__(
        self,
        config_manager: ConfigManager,
        game_selection_only: bool = False,
        show_existing_games: bool = False,
        select_existing_games: bool = True,
    ):
        super().__init__()
        self.config_manager = config_manager
        self.game_selection_only = game_selection_only
        self.show_existing_games = show_existing_games
        self.select_existing_games = select_existing_games

        self.ui = Ui_Wizard()
        self.ui.setupUi(self)  # type: ignore
        self.setWindowTitle(f"{__title__} Setup Wizard")

        self.load_current_configs()

        self.add_available_languages_to_ui()

        self.ui.gamesSelectionWizardPage.validatePage = self.validateGamesSelectionPage  # type: ignore[method-assign]
        self.ui.addGameButton.clicked.connect(self.browse_for_game_dir)
        self.ui.upPriorityButton.clicked.connect(self.raise_selected_game_priority)
        self.ui.downPriorityButton.clicked.connect(self.lower_selected_game_priority)
        self.games_found = False
        self.currentIdChanged.connect(self.current_id_changed)
        self.button(QtWidgets.QWizard.WizardButton.FinishButton).clicked.connect(
            self.save_settings
        )
        self.accepted.connect(self.save_settings)

        if self.game_selection_only:
            for page_id in self.pageIds():
                self.removePage(page_id)

            self.addPage(self.ui.gamesSelectionWizardPage)
            self.setOption(QtWidgets.QWizard.WizardOption.NoBackButtonOnLastPage, True)
            self.find_games()

    def load_current_configs(self) -> None:
        self.program_config: ProgramConfig | None
        try:
            self.program_config = self.config_manager.read_program_config_file()
        except (FileNotFoundError, ConfigFileParseError):
            self.program_config = None

        self.existing_games: dict[GameConfig, UUID] = {}
        existing_unloadable_game_uuids = []
        for game_uuid in self.config_manager.get_game_uuids():
            try:
                self.existing_games[
                    self.config_manager.read_game_config_file(game_uuid)
                ] = game_uuid
            except (FileNotFoundError, ConfigFileParseError):
                existing_unloadable_game_uuids.append(game_uuid)
        self.existing_unloadable_game_uuids: tuple[UUID, ...] = tuple(
            existing_unloadable_game_uuids
        )

    def add_available_languages_to_ui(self) -> None:
        default_locale = get_default_locale()
        for locale in available_locales.values():
            item = QtWidgets.QListWidgetItem(
                QtGui.QPixmap(str(locale.flag_icon)), locale.display_name
            )
            self.ui.languagesListWidget.addItem(item)

            # Default locale should be selected in the list by default.
            if (
                self.program_config
                and locale == self.program_config.default_locale
                or not self.program_config
                and locale == default_locale
            ):
                self.ui.languagesListWidget.setCurrentItem(item)

    def raise_selected_game_priority(self) -> None:
        item = self.ui.gamesListWidget.currentItem()
        row = self.ui.gamesListWidget.row(item)
        if row == 0:
            return
        self.ui.gamesListWidget.takeItem(row)
        self.ui.gamesListWidget.insertItem(row - 1, item)
        self.ui.gamesListWidget.setCurrentItem(item)

    def lower_selected_game_priority(self) -> None:
        item = self.ui.gamesListWidget.currentItem()
        row = self.ui.gamesListWidget.row(item)
        # Item is already at end of list
        if row == self.ui.gamesListWidget.count() - 1:
            return
        self.ui.gamesListWidget.takeItem(row)
        self.ui.gamesListWidget.insertItem(row + 1, item)
        self.ui.gamesListWidget.setCurrentItem(item)

    def validateGamesSelectionPage(self) -> bool:
        # Go back to the games selection page
        # if no games have been selected.
        if not self.get_selected_game_items():
            show_warning_message(
                "Please select at least one game folder.",
                self,
            )
            return False

        return True

    def current_id_changed(self, new_id: int) -> None:
        if new_id == -1:
            return

        if (
            self.currentPage() == self.ui.gamesSelectionWizardPage
            and not self.games_found
        ):
            self.find_games()

    def find_games(self) -> None:
        if self.show_existing_games:
            self.add_existing_games()

        if os.name == "nt":
            start_dir = CaseInsensitiveAbsolutePath("C:/")
            self.find_game_dirs(start_dir / "Program Files")
            if (start_dir / "Program Files (x86)").exists():
                self.find_game_dirs(start_dir / "Program Files (x86)")
        else:
            home_dir = CaseInsensitiveAbsolutePath.home()
            for prefix_search_start_dir, glob_pattern in [
                (home_dir, "*wine*/"),
                # Can't just check steamapps/common because of non-steam games managed
                # with Steam.
                (home_dir / ".steam/steam/steamapps/compatdata", "*/"),
                (home_dir / ".steam/steamapps/compatdata", "*/"),
                (
                    home_dir / ".local/share/Steam/steamapps/compatdata/",
                    "*",
                ),
                (home_dir / "games", "*/"),
            ]:
                for path in prefix_search_start_dir.glob(glob_pattern):
                    # Handle both default WINE and Valve Proton paths
                    prefix_drive_c_path = (
                        "pfx/drive_c" if (path / "pfx").exists() else "drive_c"
                    )
                    if (path / prefix_drive_c_path).exists():
                        self.find_game_dirs(
                            CaseInsensitiveAbsolutePath(path)
                            / prefix_drive_c_path
                            / "Program Files"
                        )
                        self.find_game_dirs(
                            CaseInsensitiveAbsolutePath(path)
                            / prefix_drive_c_path
                            / "Program Files (x86)"
                        )
            for search_dir in [
                home_dir / "games",
                home_dir / ".steam/steam/steamapps/common",
                home_dir / ".steam/steamapps/common",
                home_dir / ".local/share/Steam/steamapps/common",
            ]:
                if search_dir.exists():
                    self.find_game_dirs(search_dir)

        self.games_found = True

    def add_existing_games(self) -> None:
        sorted_game_configs = get_games_sorted_by_priority(self.existing_games.keys())
        for game_config in sorted_game_configs[::-1]:
            self.add_game(game_config, checked=self.select_existing_games)

    def get_game_dir_list_item(
        self, game_dir: CaseInsensitiveAbsolutePath
    ) -> QtWidgets.QListWidgetItem | None:
        for i in range(self.ui.gamesListWidget.count()):
            item = self.ui.gamesListWidget.item(i)
            resolved_path = Path(item.text()).resolve()
            if resolved_path == game_dir.resolve():
                return item
        return None

    def add_game(
        self,
        game_config: GameConfig,
        checked: bool = False,
        selected: bool = False,
    ) -> None:
        if item := self.get_game_dir_list_item(game_config.game_directory):
            if selected:
                self.ui.gamesListWidget.setCurrentItem(item)
            return

        item = QtWidgets.QListWidgetItem(str(game_config.game_directory))
        item.setData(QtCore.Qt.ItemDataRole.UserRole, game_config)
        item.setIcon(QtGui.QIcon(str(game_config.game_directory / "icon.ico")))
        item.setCheckState(
            QtCore.Qt.CheckState.Checked if checked else QtCore.Qt.CheckState.Unchecked
        )
        self.ui.gamesListWidget.insertItem(0, item)
        if selected:
            self.ui.gamesListWidget.setCurrentItem(item)

    def get_game_config_from_game_dir(
        self, game_dir: CaseInsensitiveAbsolutePath
    ) -> GameConfig:
        """
        Raises:
            InvalidGameDirError: `game_dir` is not a valid game directory
        """
        game_type = find_game_dir_game_type(game_dir)
        if not game_type:
            raise InvalidGameDirError("")

        launcher_config_paths = get_launcher_config_paths(
            search_dir=game_dir, game_type=game_type
        )
        if not launcher_config_paths:
            raise InvalidGameDirError("")
        try:
            launcher_config = GameLauncherLocalConfig.from_config_xml(
                config_xml=launcher_config_paths[0].read_text()
            )
        except GameLauncherLocalConfigParseError as e:
            raise InvalidGameDirError("") from e

        return GameConfig(
            game_directory=game_dir,
            game_type=game_type,
            is_preview_client=is_gls_url_for_preview_client(
                launcher_config.gls_datacenter_service
            ),
            wine=WineConfigSection(),
        )

    def find_game_dirs(
        self, search_dir: CaseInsensitiveAbsolutePath, search_depth: int = 5
    ) -> None:
        if (
            search_depth <= 0
            or search_dir.name.startswith(".")
            or search_dir.name == "dosdevices"
        ):
            return

        with suppress(InvalidGameDirError):
            game_config = self.get_game_config_from_game_dir(search_dir)
            self.add_game(game_config)

        for path in search_dir.glob("*/"):
            if path.name.upper() != "BACKUP":
                self.find_game_dirs(path, search_depth=search_depth - 1)

    def browse_for_game_dir(self) -> None:
        if os.name == "nt":
            starting_dir = Path(os.environ.get("PROGRAMFILES") or "C:/Program Files")
        else:
            starting_dir = Path("~").expanduser()

        game_dir_string = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            "Game Directory",
            str(starting_dir),
            options=QtWidgets.QFileDialog.Option.ShowDirsOnly,
        )
        if not game_dir_string:
            return
        game_dir = CaseInsensitiveAbsolutePath(game_dir_string)
        # Warn user if they try to add a game that's already in the list
        if item := self.get_game_dir_list_item(game_dir):
            messageBox = QtWidgets.QMessageBox(self)
            messageBox.setWindowFlag(QtCore.Qt.WindowType.FramelessWindowHint)
            messageBox.setIcon(QtWidgets.QMessageBox.Icon.Information)
            messageBox.setStandardButtons(messageBox.StandardButton.Ok)
            messageBox.setInformativeText("Directory already added")
            messageBox.exec()
            self.ui.gamesListWidget.setCurrentItem(item)
            return
        try:
            game_config = self.get_game_config_from_game_dir(game_dir)
            self.add_game(game_config, selected=True)
        except InvalidGameDirError:
            show_warning_message("Not a valid game installation folder.", self)

    def get_selected_game_items(self) -> list[QtWidgets.QListWidgetItem]:
        items = []
        for i in range(self.ui.gamesListWidget.count()):
            item = self.ui.gamesListWidget.item(i)
            if item.checkState() == QtCore.Qt.CheckState.Checked:
                items.append(item)
        return items

    def sort_list_widget_items(
        self, items: list[QtWidgets.QListWidgetItem]
    ) -> list[QtWidgets.QListWidgetItem]:
        """Sort list widget items by their row number."""
        items_dict = {item.listWidget().row(item): item for item in items}
        return [items_dict[key] for key in sorted(items_dict)]

    def reset_config(self) -> None:
        for game_uuid in self.existing_games.values():
            self.config_manager.delete_game_config(game_uuid=game_uuid)
        self.config_manager.delete_program_config()
        self.load_current_configs()

    def get_games_config_reset_confirmation(self) -> bool:
        """
        Ask user if they want to reset existing games config/data.
        Will do nothing and return True if there is no existing data.

        Returns:
            bool: If the user wants settings to be reset.
        """
        # Return True if there is no existing games data.
        if not self.existing_games:
            return True

        message_box = QtWidgets.QMessageBox(self)
        message_box.setWindowFlag(QtCore.Qt.WindowType.FramelessWindowHint)
        message_box.setIcon(QtWidgets.QMessageBox.Icon.Warning)
        message_box.setStandardButtons(
            message_box.StandardButton.Cancel | message_box.StandardButton.Yes
        )
        message_box.setDefaultButton(message_box.StandardButton.Cancel)
        message_box.setInformativeText(
            "Existing game data will be deleted. (settings, saved "
            "accounts, ect). Do you wish to continue?"
        )

        return message_box.exec() == message_box.StandardButton.Yes

    def save_settings(self) -> None:
        if not self.game_selection_only:
            if self.get_games_config_reset_confirmation() is False:
                return
            self.reset_config()

            selected_locale_display_name = (
                self.ui.languagesListWidget.currentItem().text()
            )
            program_config = ProgramConfig(
                default_locale=next(
                    locale
                    for locale in available_locales.values()
                    if locale.display_name == selected_locale_display_name
                ),
                always_use_default_locale_for_ui=self.ui.alwaysUseDefaultLangForUICheckBox.isChecked(),
                games_sorting_mode=GamesSortingMode.PRIORITY,
            )
        self.add_games_to_settings()
        self.config_manager.update_program_config_file(program_config)

    def add_games_to_settings(self) -> None:
        """
        Add games to settings. This has to be done after language settings
        are set.
        """
        selected_items = self.sort_list_widget_items(self.get_selected_game_items())
        selected_games: list[GameConfig] = []
        for i, game_item in enumerate(selected_items):
            item_data: GameConfig = game_item.data(QtCore.Qt.ItemDataRole.UserRole)
            selected_games.append(attrs.evolve(item_data, sorting_priority=i))

        # Remove any games that were not selected by the user.
        not_selected_games: list[GameConfig] = [
            game_config
            for game_config in self.existing_games
            if game_config not in selected_games
        ]
        # Warn user that the games they didn't select will have their data
        # deleted.
        if (
            self.game_selection_only
            and not_selected_games
            and not self.get_games_config_reset_confirmation()
        ):
            return
        for game_config in not_selected_games:
            self.config_manager.delete_game_config(
                game_uuid=self.existing_games[game_config]
            )

        # Save games
        for game_config in selected_games:
            game_uuid = self.existing_games.get(game_config, uuid4())
            self.config_manager.update_game_config_file(
                game_uuid=game_uuid, config=game_config
            )
