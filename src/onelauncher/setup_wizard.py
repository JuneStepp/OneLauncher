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
# (C) 2019-2026 June Stepp <contact@JuneStepp.me>
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
from collections.abc import Iterable
from contextlib import suppress
from functools import partial
from pathlib import Path
from shutil import rmtree
from typing import Final

import attrs
import qtawesome
import trio
from PySide6 import QtCore, QtGui, QtWidgets
from typing_extensions import override

from .__about__ import __title__
from .addons.config import AddonsConfigSection
from .config_manager import ConfigManager
from .game_config import (
    GameConfig,
    GameConfigID,
    GameType,
    generate_game_config_id,
    generate_game_name,
)
from .game_launcher_local_config import (
    GameLauncherLocalConfig,
    GameLauncherLocalConfigParseError,
    get_launcher_config_paths,
)
from .game_utilities import (
    InvalidGameDirError,
    find_game_dir_game_type,
)
from .official_clients import get_game_icon, is_gls_url_for_preview_client
from .program_config import GamesSortingMode, ProgramConfig
from .resources import available_locales
from .ui.install_game_window import InstallGameWindow
from .ui.qtapp import get_app_style, get_qapp
from .ui.setup_wizard_window_uic import Ui_setupWizardWindow
from .ui.utilities import show_warning_message
from .utilities import CaseInsensitiveAbsolutePath
from .v1x_config_migrator import (
    V1xConfigParseError,
    get_v1x_config_file_path,
    migrate_v1x_config,
)
from .wine.config import WineConfigSection

logger = logging.getLogger(__name__)

GameConfigIDRole: Final[int] = QtCore.Qt.ItemDataRole.UserRole + 1001
GameConfigRole: Final[int] = QtCore.Qt.ItemDataRole.UserRole + 1000


class GamesDeletionStatusItemDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(
        self,
        item_checked_icon: QtGui.QIcon,
        existing_game_ids: Iterable[GameConfigID],
        parent: QtCore.QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self.item_checked_icon = item_checked_icon
        self.existing_game_ids = existing_game_ids

    @override
    def initStyleOption(
        self,
        option: QtWidgets.QStyleOptionViewItem,
        index: QtCore.QModelIndex | QtCore.QPersistentModelIndex,
    ) -> None:
        super().initStyleOption(option, index)
        game_id: GameConfigID = index.data(GameConfigIDRole)
        if option.checkState == QtCore.Qt.CheckState.Checked:  # type: ignore[attr-defined]
            option.icon = (  # type: ignore[attr-defined]
                self.item_checked_icon
                if game_id in self.existing_game_ids
                else qtawesome.icon("mdi6.folder-plus-outline")
            )
        else:
            option.icon = (  # type: ignore[attr-defined]
                qtawesome.icon("mdi6.trash-can-outline")
                if game_id in self.existing_game_ids
                else QtGui.QIcon()
            )


class SetupWizard(QtWidgets.QWizard):
    def __init__(
        self,
        config_manager: ConfigManager,
        game_selection_only: bool = False,
        select_existing_games: bool = True,
    ):
        super().__init__()
        self.config_manager = config_manager
        self.game_selection_only = game_selection_only
        self.select_existing_games = select_existing_games

        self.ui = Ui_setupWizardWindow()
        self.ui.setupUi(self)
        self.setWindowTitle("Setup Wizard")

        self.migrate_old_config_asked: bool = False
        self.new_install_game_ids: list[GameConfigID] = []
        """Game config IDs for installs created in this setup wizard"""

    def setup_ui(self) -> None:
        # As of PySide 6.1, other styles don't have right spacing or work with the dark
        # theme on Windows. Sticking with this known look on all platforms for now.
        self.setWizardStyle(self.WizardStyle.ClassicStyle)

        color_scheme_changed = get_qapp().styleHints().colorSchemeChanged

        # Language selection page
        self.add_available_languages_to_ui()
        self.ui.languageSelectionWizardPage.validatePage = (  # type: ignore[method-assign]
            self.validateLanguageSelectionPage
        )

        # Games discovery page
        self.ui.gamesSelectionWizardPage.validatePage = self.validateGamesSelectionPage  # type: ignore[method-assign]
        self.ui.addExistingGameButton.clicked.connect(self.browse_for_game_dir)
        self.ui.installGameButton.clicked.connect(
            lambda: self.nursery.start_soon(self.install_game)
        )
        if os.name == "nt":
            # Game installation is disabled on Windows for now pending extra testing.
            # See #313 (internal issue tracker).
            self.ui.installGameButton.hide()
            self.ui.addExistingGameButton.setText("Add Game")
        self.ui.upPriorityButton.clicked.connect(self.raise_selected_game_priority)
        self.ui.downPriorityButton.clicked.connect(self.lower_selected_game_priority)

        # Existing game data page
        self.ui.dataDeletionWizardPage.setCommitPage(True)
        self.ui.gamesDeletionStatusListView.setModel(self.ui.gamesListWidget.model())
        self.ui.gamesDeletionStatusListView.setEnabled(False)
        self.ui.gamesDataButtonGroup.buttonToggled.connect(self.gamesDataButtonToggled)
        self.ui.dataDeletionWizardPage.isComplete = self.dataDeletionPageIsComplete  # type: ignore[method-assign]
        get_keep_data_icon = partial(qtawesome.icon, "mdi6.content-save-outline")
        self.ui.keepDataRadioButton.setIcon(get_keep_data_icon())
        color_scheme_changed.connect(
            lambda: self.ui.keepDataRadioButton.setIcon(get_keep_data_icon())
        )
        get_reset_data_icon = partial(qtawesome.icon, "mdi6.backspace-outline")
        self.ui.resetDataRadioButton.setIcon(get_reset_data_icon())
        color_scheme_changed.connect(
            lambda: self.ui.resetDataRadioButton.setIcon(get_reset_data_icon())
        )

        def data_deletion_page_update() -> None:
            checked_button: QtWidgets.QAbstractButton | None = (
                self.ui.gamesDataButtonGroup.checkedButton()
            )
            if checked_button:
                self.gamesDataButtonToggled(
                    button=checked_button,
                    checked=True,
                )

        color_scheme_changed.connect(data_deletion_page_update)
        if self.game_selection_only:
            self.ui.keepDataRadioButton.setChecked(True)

        # Finished page
        self.button(QtWidgets.QWizard.WizardButton.FinishButton).clicked.disconnect()
        self.button(QtWidgets.QWizard.WizardButton.FinishButton).clicked.connect(
            self.finish
        )

        if self.game_selection_only:
            for page_id in self.pageIds():
                self.removePage(page_id)
            self.addPage(self.ui.gamesSelectionWizardPage)
            # Existing data page isn't needed, if there's no existing data.
            if self.config_manager.get_game_config_ids():
                self.addPage(self.ui.dataDeletionWizardPage)
        else:
            # Only show data deletion page if there is existing game data
            self.ui.gamesSelectionWizardPage.nextId = (  # type: ignore[method-assign]
                lambda: self.currentId() + 1
                if self.config_manager.get_game_config_ids()
                else self.currentId() + 2
            )

        self.open()

    async def run(self) -> None:
        self.setup_ui()
        async with trio.open_nursery() as self.nursery:
            self.finished.connect(self.cleanup)

            self.nursery.start_soon(self.initialize_games_selection_page)

            # Will be canceled when the winddow is closed
            self.nursery.start_soon(trio.sleep_forever)

    def cleanup(self) -> None:
        if self.result() == QtWidgets.QDialog.DialogCode.Rejected:
            # Delete new game installs that are in the OneLauncher games
            # directory.
            for new_install_game_id in self.new_install_game_ids:
                with suppress(FileNotFoundError):
                    rmtree(
                        self.config_manager.get_game_config_dir(
                            game_id=new_install_game_id
                        )
                    )
        self.nursery.cancel_scope.cancel()

    @override
    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        self.cleanup()
        event.accept()

    @override
    def changeEvent(self, event: QtCore.QEvent) -> None:
        super().changeEvent(event)
        # Update the app style on theme change, if the main window doesn't exist.
        # Normally the main window does this.
        if (
            event.type() == QtCore.QEvent.Type.ThemeChange
            and len(get_qapp().topLevelWidgets()) == 1
            and get_qapp().topLevelWidgets()[0] == self
        ):
            get_app_style().update_base_font()

    def add_available_languages_to_ui(self) -> None:
        program_config = self.config_manager.read_program_config_file()
        for locale in available_locales.values():
            item = QtWidgets.QListWidgetItem(
                QtGui.QPixmap(str(locale.flag_icon)), locale.display_name
            )
            self.ui.languagesListWidget.addItem(item)

            # Default locale should be selected in the list by default.
            if locale == program_config.default_locale:
                self.ui.languagesListWidget.setCurrentItem(item)

    def validateLanguageSelectionPage(self) -> bool:
        if self.migrate_old_config_asked:
            return True
        # Check for a v1.x config that can be migrated from, if there is no current
        # config data.
        if (
            not self.config_manager.get_game_config_ids()
            and not self.config_manager.program_config_path.exists()
            and get_v1x_config_file_path().exists()
        ):
            messageBox = QtWidgets.QMessageBox(self)
            messageBox.setWindowFlag(QtCore.Qt.WindowType.FramelessWindowHint)
            messageBox.setIcon(QtWidgets.QMessageBox.Icon.Question)
            messageBox.setStandardButtons(
                messageBox.StandardButton.No | messageBox.StandardButton.Yes
            )
            messageBox.setInformativeText(
                f"Found configuration data from a previous {__title__} release. Would you like to migrate the data?"
            )
            migrate_config = messageBox.exec() == messageBox.StandardButton.Yes
            self.migrate_old_config_asked = True
            if not migrate_config:
                return True
            messageBox.setInformativeText(
                "Should the old data be deleted after it's migrated?"
            )
            delete_old_config = messageBox.exec() == messageBox.StandardButton.Yes
            try:
                migrate_v1x_config(
                    config_manager=self.config_manager,
                    delete_old_config=delete_old_config,
                )
            except V1xConfigParseError:
                logger.exception("")
                show_warning_message(
                    message="Error parsing old configuration. No changes were made.",
                    parent=self,
                )
        return True

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

    def dataDeletionPageIsComplete(self) -> bool:
        return bool(self.ui.gamesDataButtonGroup.checkedButton())

    def gamesDataButtonToggled(
        self, button: QtWidgets.QAbstractButton, checked: bool
    ) -> None:
        if self.ui.keepDataRadioButton.isChecked():
            icon = self.ui.keepDataRadioButton.icon()
        else:
            icon = self.ui.resetDataRadioButton.icon()
        self.ui.gamesDeletionStatusListView.setItemDelegate(
            GamesDeletionStatusItemDelegate(
                item_checked_icon=icon,
                existing_game_ids=self.config_manager.get_game_config_ids(),
            )
        )
        self.ui.gamesDeletionStatusListView.setEnabled(True)
        self.ui.dataDeletionWizardPage.completeChanged.emit()

    async def initialize_games_selection_page(self) -> None:
        self.ui.gamesDiscoveryStatusLabel.setText(
            "Searching for existing game directories..."
        )
        self.ui.gamesDiscoveryStatusLabel.show()
        await trio.to_thread.run_sync(self.find_games)
        self.ui.gamesDiscoveryStatusLabel.hide()

    def find_games(self) -> None:
        self.add_existing_games()

        self.found_games: list[GameConfig] = []

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
                    "*/",
                ),
                (
                    home_dir
                    / "Library"
                    / "Application Support"
                    / "Crossover"
                    / "Bottles",
                    "*/",
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

        def sort_games(key: GameConfig) -> str:
            priority = 0
            if key.game_type == GameType.DDO:
                priority += 2
            if key.is_preview_client:
                priority += 1
            return f"{priority}{key.game_directory}"

        for game in sorted(self.found_games, key=sort_games):
            self.add_game(game_id=generate_game_config_id(game), game_config=game)
        self.ui.gamesListWidget.setCurrentRow(0)

    def add_existing_games(self) -> None:
        for game_id in self.config_manager.get_games_sorted_by_priority():
            self.add_game(
                game_id=game_id,
                game_config=self.config_manager.read_game_config_file(game_id),
                checked=self.select_existing_games,
            )

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
        game_id: GameConfigID,
        game_config: GameConfig,
        checked: bool = False,
        selected: bool = False,
    ) -> None:
        if item := self.get_game_dir_list_item(game_config.game_directory):
            if selected:
                self.ui.gamesListWidget.setCurrentItem(item)
            return

        item = QtWidgets.QListWidgetItem(str(game_config.game_directory))
        item.setData(GameConfigIDRole, game_id)
        item.setData(GameConfigRole, game_config)
        game_icon = game_config.game_directory / "icon.ico"
        if game_icon.exists():
            item.setIcon(QtGui.QIcon(str(game_icon)))
        else:
            item.setIcon(QtGui.QIcon(str(get_game_icon(game_config.game_type))))
        item.setCheckState(
            QtCore.Qt.CheckState.Checked if checked else QtCore.Qt.CheckState.Unchecked
        )
        self.ui.gamesListWidget.addItem(item)
        if selected:
            self.ui.gamesListWidget.setCurrentItem(item)

    def get_game_config_from_game_dir(
        self, game_dir: CaseInsensitiveAbsolutePath
    ) -> GameConfig:
        """
        Raises:
            InvalidGameDirError: `game_dir` is not a valid game directory
        """
        game_type = find_game_dir_game_type(game_dir=game_dir)

        launcher_config_paths = get_launcher_config_paths(
            search_dir=game_dir, game_type=game_type
        )
        if not launcher_config_paths:
            raise InvalidGameDirError("")

        try:
            launcher_config = GameLauncherLocalConfig.from_config_xml(
                config_xml=launcher_config_paths[0].read_text(encoding="UTF-8")
            )
        except GameLauncherLocalConfigParseError as e:
            raise InvalidGameDirError("") from e

        return GameConfig(
            game_directory=game_dir,
            game_type=game_type,
            is_preview_client=is_gls_url_for_preview_client(
                launcher_config.gls_datacenter_service
            ),
            addons=AddonsConfigSection(),
            wine=WineConfigSection(),
        )

    def find_game_dirs(
        self, search_dir: CaseInsensitiveAbsolutePath, search_depth: int = 5
    ) -> None:
        if (
            search_depth <= 0
            or search_dir.name.startswith(".")
            or search_dir.name == "dosdevices"
            or search_dir.name.upper() == "BACKUP"
        ):
            return

        with suppress(InvalidGameDirError):
            game_config = self.get_game_config_from_game_dir(search_dir)
            self.found_games.append(game_config)

        for path in search_dir.glob("*/"):
            self.find_game_dirs(path, search_depth=search_depth - 1)

    def browse_for_game_dir(self) -> None:
        if os.name == "nt":
            starting_dir = Path(os.environ.get("PROGRAMFILES") or "C:/Program Files")
        else:
            starting_dir = Path("~").expanduser()

        game_dir_string = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            "Select Game Directory",
            str(starting_dir),
            options=QtWidgets.QFileDialog.Option.ShowDirsOnly
            | QtWidgets.QFileDialog.Option.DontResolveSymlinks,
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
            self.add_game(
                game_id=generate_game_config_id(game_config),
                game_config=game_config,
                checked=True,
                selected=True,
            )
        except InvalidGameDirError:
            show_warning_message("Not a valid game installation folder", self)

    async def install_game(self) -> None:
        install_game_window = InstallGameWindow(config_manager=self.config_manager)
        await install_game_window.run()
        if install_game_window.result() == QtWidgets.QDialog.DialogCode.Accepted:
            self.new_install_game_ids.append(install_game_window.game_id)
            self.add_game(
                game_id=install_game_window.game_id,
                game_config=install_game_window.game_config,
                checked=True,
                selected=True,
            )

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

    def finish(self) -> None:
        self.save_settings()
        self.accept()

    def save_settings(self) -> None:
        if not self.game_selection_only:
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
            self.config_manager.update_program_config_file(program_config)
        self.add_games_to_settings()

    def add_games_to_settings(self) -> None:
        """
        Add games to settings. This has to be done after language settings
        are set.
        """
        selected_items = self.sort_list_widget_items(self.get_selected_game_items())
        selected_games: dict[GameConfigID, GameConfig] = {}
        for i, game_item in enumerate(selected_items):
            game_id: GameConfigID = game_item.data(GameConfigIDRole)
            game_config: GameConfig = game_item.data(GameConfigRole)
            # Update sorting priority
            selected_games[game_id] = attrs.evolve(game_config, sorting_priority=i)

        if existing_game_ids := self.config_manager.get_game_config_ids():
            if self.ui.resetDataRadioButton.isChecked():
                # Reset existing selected games
                for game_id, game_config in selected_games.items():
                    if game_id not in existing_game_ids:
                        continue

                    self.config_manager.delete_game_config(
                        game_id, exclude_install_dir=True
                    )
                    reset_game_config = self.get_game_config_from_game_dir(
                        game_config.game_directory
                    )
                    selected_games[game_id] = attrs.evolve(
                        reset_game_config, sorting_priority=game_config.sorting_priority
                    )

            # Remove any games that were not selected by the user.
            not_selected_existing_game_ids: tuple[GameConfigID, ...] = tuple(
                game_id
                for game_id in existing_game_ids
                if game_id not in selected_games
            )
            for game_id in not_selected_existing_game_ids:
                self.config_manager.delete_game_config(game_id)

        # Delete unselected new game installs that are in the OneLauncher games
        # directory. Users are responsible for any installs they created in a custom
        # directory.
        for new_install_game_id in self.new_install_game_ids:
            if new_install_game_id not in selected_games:
                with suppress(FileNotFoundError):
                    rmtree(
                        self.config_manager.get_game_config_dir(
                            game_id=new_install_game_id
                        )
                    )

        existing_game_names = [
            game_config.name
            for game_id, game_config in selected_games.items()
            if game_id in existing_game_ids
        ]
        # Save games
        for game_id, game_config in selected_games.items():
            if game_id in existing_game_ids:
                name = game_config.name
            else:
                # Make sure that newly added games have unique names
                name = generate_game_name(
                    game_config=game_config, existing_game_names=existing_game_names
                )
                existing_game_names.append(name)
            self.config_manager.update_game_config_file(
                game_id=game_id, config=attrs.evolve(game_config, name=name)
            )
