import logging
import os
from functools import partial
from pathlib import Path
from typing import Final

import attrs
import qtawesome
import trio
from PySide6 import QtCore, QtGui, QtWidgets
from typing_extensions import override

from onelauncher.config_manager import ConfigManager
from onelauncher.install_game import (
    GAME_INSTALLERS,
    GameInstaller,
    InstallDirValidationError,
    InstallGameError,
    get_default_game_config,
    get_innoextract_path,
    install_game,
    validate_user_provided_install_dir,
)
from onelauncher.utilities import Progress

from .custom_widgets import FramelessQDialogWithStylePreview
from .install_game_window_uic import Ui_installGameWindow
from .qtapp import get_qapp
from .utilities import show_warning_message

logger = logging.getLogger(__name__)

GameInstallerRole: Final[int] = QtCore.Qt.ItemDataRole.UserRole + 1001


class InstallGameWindow(FramelessQDialogWithStylePreview):
    def __init__(self, config_manager: ConfigManager) -> None:
        super().__init__(get_qapp().activeWindow())
        self.config_manager = config_manager
        self.progress: Progress | None = None

    def setup_ui(self) -> None:
        self.titleBar.hide()

        self.ui = Ui_installGameWindow()
        self.ui.setupUi(self)
        color_scheme_changed = get_qapp().styleHints().colorSchemeChanged

        self.ui.progressBar.hide()

        for installer in GAME_INSTALLERS:
            item = QtWidgets.QListWidgetItem(installer.name)
            item.setData(GameInstallerRole, installer)
            item.setIcon(QtGui.QIcon(str(installer.icon_path)))
            self.ui.gameTypeListWidget.addItem(item)
        self.ui.gameTypeListWidget.currentItemChanged.connect(
            self.current_installer_item_changed
        )
        self.game_id, self.game_config = get_default_game_config(
            installer=self.ui.gameTypeListWidget.item(0).data(GameInstallerRole),
            config_manager=self.config_manager,
        )
        self.ui.gameTypeListWidget.setCurrentRow(0)
        self.ui.gameTypeListWidget.setFocus()

        get_select_folder_icon = partial(qtawesome.icon, "mdi6.folder-open-outline")
        self.ui.selectInstallDirButton.setIcon(get_select_folder_icon())
        color_scheme_changed.connect(
            lambda: self.ui.selectInstallDirButton.setIcon(get_select_folder_icon())
        )
        self.ui.selectInstallDirButton.clicked.connect(self.browse_for_install_dir)

        self.install_button = self.ui.buttonBox.addButton(
            "Install Game", QtWidgets.QDialogButtonBox.ButtonRole.AcceptRole
        )
        self.install_button.clicked.connect(
            lambda: self.nursery.start_soon(self.install_game)
        )

        self.adjustSize()
        self.open()

    async def run(self) -> None:
        try:
            get_innoextract_path()
        except FileNotFoundError:
            logger.exception("")
            show_warning_message(
                "innoextract not found. Cannot make a new game install.", None
            )
            self.reject()
            return

        self.setup_ui()
        async with trio.open_nursery() as self.nursery:
            self.finished.connect(self.cleanup)

            self.nursery.start_soon(self.keep_progress_bar_updated)
            # Will be canceled when the winddow is closed.
            self.nursery.start_soon(trio.sleep_forever)

    def cleanup(self) -> None:
        self.nursery.cancel_scope.cancel()

    @override
    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        self.cleanup()
        event.accept()

    @override
    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        # Let the user drag the window when left-click holding it.
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self.windowHandle().startSystemMove()
            event.accept()

    def current_installer_item_changed(
        self, current: QtWidgets.QListWidgetItem, _previous: QtWidgets.QListWidgetItem
    ) -> None:
        installer: GameInstaller = current.data(GameInstallerRole)
        new_game_id, new_game_config = get_default_game_config(
            installer=installer, config_manager=self.config_manager
        )

        # Don't overwrite custom user install directories.
        if not self.ui.installDirLineEdit.text().strip() or (
            self.ui.installDirLineEdit.text() == str(self.game_config.game_directory)
        ):
            self.ui.installDirLineEdit.setText(str(new_game_config.game_directory))
            self.ui.installDirLineEdit.setCursorPosition(0)

        self.game_id, self.game_config = new_game_id, new_game_config

    def browse_for_install_dir(self) -> None:
        if os.name == "nt":
            starting_dir = Path(os.environ.get("PROGRAMFILES", "C:/Program Files"))
        else:
            starting_dir = Path.home()
        install_dir_string = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            "Select Game Install Directory",
            str(starting_dir),
            options=QtWidgets.QFileDialog.Option.ShowDirsOnly
            | QtWidgets.QFileDialog.Option.DontResolveSymlinks,
        )
        if not install_dir_string:
            return

        try:
            install_dir = validate_user_provided_install_dir(
                install_dir_string=install_dir_string,
                config_manager=self.config_manager,
                default_install_dir=self.game_config.game_directory,
            )
        except InstallDirValidationError as e:
            logger.warning(e.msg, exc_info=True)
            show_warning_message(e.msg, self)
            return

        self.ui.installDirLineEdit.setText(str(install_dir))

    async def keep_progress_bar_updated(self) -> None:
        # Will be canceled once the window is closed.
        while True:
            if self.progress:
                current_progress = self.progress.get_current_progress()
                self.ui.progressBar.setFormat(current_progress.progress_text)
                self.ui.progressBar.setMaximum(current_progress.total)
                self.ui.progressBar.setValue(current_progress.completed)
            await trio.sleep(0.05)

    async def install_game(self) -> None:
        try:
            install_dir = validate_user_provided_install_dir(
                install_dir_string=self.ui.installDirLineEdit.text(),
                config_manager=self.config_manager,
                default_install_dir=self.game_config.game_directory,
            )
        except InstallDirValidationError as e:
            logger.warning(e.msg, exc_info=True)
            show_warning_message(e.msg, self)
            return
        self.game_config = attrs.evolve(self.game_config, game_directory=install_dir)

        self.ui.widgetInstallOptions.setEnabled(False)
        self.install_button.setEnabled(False)
        self.progress = Progress()
        self.ui.progressBar.show()

        try:
            await install_game(
                installer=self.ui.gameTypeListWidget.currentItem().data(
                    GameInstallerRole
                ),
                install_dir=install_dir,
                progress=self.progress,
            )
        except InstallGameError as e:
            logger.exception("")
            show_warning_message(e.msg, self)
            self.reject()
            return

        self.accept()
