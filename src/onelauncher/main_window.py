###########################################################################
# Main window for OneLauncher.
#
# Based on PyLotRO
# (C) 2009 AJackson <ajackson@bcs.org.uk>
#
# Based on LotROLinux
# (C) 2007-2008 AJackson <ajackson@bcs.org.uk>
#
#
# (C) 2019-2025 June Stepp <contact@JuneStepp.me>
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
from __future__ import annotations

import logging
import sys
from functools import partial
from pathlib import Path
from typing import cast

import attrs
import httpx
import keyring
import packaging.version
import qtawesome
import trio
from keyring.errors import KeyringLocked, NoKeyringError
from PySide6 import QtCore, QtGui, QtWidgets
from typing_extensions import override
from xmlschema import XMLSchemaValidationError

from onelauncher.async_utils import app_cancel_scope

from . import __about__, addon_manager_window
from .addons.startup_script import run_startup_script
from .config_manager import ConfigManager, NoValidGamesError
from .game_account_config import GameAccountConfig
from .game_config import GameConfigID, GameType
from .game_launcher_local_config import (
    GameLauncherLocalConfig,
    GameLauncherLocalConfigParseError,
    get_launcher_config_paths,
)
from .game_utilities import (
    InvalidGameDirError,
    find_game_dir_game_type,
    get_game_settings_dir,
)
from .logs import ForwardLogsHandler
from .network import login_account
from .network.game_launcher_config import (
    GameLauncherConfig,
    GameLauncherConfigParseError,
)
from .network.game_newsfeed import get_game_newsfeed_html
from .network.game_services_info import GameServicesInfo
from .network.httpx_client import get_httpx_client
from .network.soap import GLSServiceError
from .network.world import World, WorldUnavailableError
from .network.world_login_queue import (
    JoinWorldQueueFailedError,
    WorldLoginQueue,
    WorldQueueResultXMLParseError,
)
from .resources import get_resource
from .settings_window import SettingsWindow
from .start_game import MissingLaunchArgumentError, start_game
from .ui.about_window_uic import Ui_aboutWindow
from .ui.custom_widgets import FramelessQMainWindowWithStylePreview
from .ui.main_window_uic import Ui_mainWindow
from .ui.patch_game_window import PatchGameWindow
from .ui.qtapp import get_app_style, get_qapp
from .ui.select_subscription_window_uic import Ui_selectSubscriptionWindow
from .ui.utilities import log_record_to_rich_text, show_message_box_details_as_markdown

logger = logging.getLogger(__name__)


class MainWindow(FramelessQMainWindowWithStylePreview):
    def __init__(
        self,
        config_manager: ConfigManager,
        game_id: GameConfigID,
    ) -> None:
        super().__init__(None)
        self.titleBar.hide()
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose, on=True)
        self.config_manager = config_manager
        self.game_id: GameConfigID = game_id

        self.network_setup_nursery: trio.Nursery | None = None
        self.starting_game: bool = False
        self.game_cancel_scope: trio.CancelScope | None = None
        self.addon_manager_window: addon_manager_window.AddonManagerWindow | None = None
        self.game_launcher_config: GameLauncherConfig | None = None

    def addon_manager_error_log(self, record: logging.LogRecord) -> None:
        self.ui.txtStatus.append(log_record_to_rich_text(record))
        self.raise_()
        self.activateWindow()

    def setup_ui(self) -> None:
        self.ui = Ui_mainWindow()
        self.ui.setupUi(self)

        logger.addHandler(
            ForwardLogsHandler(
                new_log_callback=lambda record: self.ui.txtStatus.append(
                    log_record_to_rich_text(record)
                ),
                level=logging.INFO,
            )
        )
        addon_manager_window.logger.addHandler(
            ForwardLogsHandler(
                new_log_callback=self.addon_manager_error_log, level=logging.INFO
            )
        )

        color_scheme_changed = get_qapp().styleHints().colorSchemeChanged
        self.ui.btnExit.clicked.connect(self.close)
        get_exit_icon = partial(qtawesome.icon, "fa5s.times")
        self.ui.btnExit.setIcon(get_exit_icon())
        color_scheme_changed.connect(lambda: self.ui.btnExit.setIcon(get_exit_icon()))
        self.ui.btnMinimize.clicked.connect(self.showMinimized)
        get_minimize_icon = partial(qtawesome.icon, "fa5s.window-minimize")
        self.ui.btnMinimize.setIcon(get_minimize_icon())
        color_scheme_changed.connect(
            lambda: self.ui.btnMinimize.setIcon(get_minimize_icon())
        )
        self.ui.btnAbout.clicked.connect(self.btnAboutSelected)
        get_about_icon = partial(qtawesome.icon, "fa5s.info-circle")
        self.ui.btnAbout.setIcon(get_about_icon())
        color_scheme_changed.connect(lambda: self.ui.btnAbout.setIcon(get_about_icon()))
        self.ui.btnOptions.clicked.connect(
            lambda: self.nursery.start_soon(self.btnOptionsSelected)
        )
        get_options_icon = partial(qtawesome.icon, "fa5s.cog")
        self.ui.btnOptions.setIcon(get_options_icon())
        color_scheme_changed.connect(
            lambda: self.ui.btnOptions.setIcon(get_options_icon())
        )
        self.ui.btnAddonManager.clicked.connect(self.btnAddonManagerSelected)
        get_addons_manager_icon = partial(qtawesome.icon, "fa5s.plus-circle")
        self.ui.btnAddonManager.setIcon(get_addons_manager_icon())
        color_scheme_changed.connect(
            lambda: self.ui.btnAddonManager.setIcon(get_addons_manager_icon())
        )
        self.setup_start_game_button()
        self.ui.btnSwitchGame.clicked.connect(
            lambda: self.nursery.start_soon(self.btnSwitchGameClicked)
        )

        account_line_edit = cast(QtWidgets.QLineEdit, self.ui.cboAccount.lineEdit())
        account_line_edit.setClearButtonEnabled(True)
        # Accounts combo box item selection signal
        self.ui.cboAccount.currentIndexChanged.connect(self.accounts_index_changed)
        account_line_edit.textEdited.connect(self.user_edited_account_name)
        self.ui.chkSaveAccount.toggled.connect(self.chk_save_account_toggled)

        self.setupMousePropagation()

        # Basic MacOS native menu bar support.
        if sys.platform == "darwin":
            global_menu_bar = QtWidgets.QMenuBar(parent=None)
            menu = QtWidgets.QMenu()
            menu.addActions(
                (self.ui.actionAbout, self.ui.actionSettings, self.ui.actionExit)
            )
            global_menu_bar.addMenu(menu)

    async def run(self) -> None:
        async with trio.open_nursery() as self.nursery:
            self.setup_ui()
            self.show()
            self.nursery.start_soon(self.InitialSetup)
            self.nursery.start_soon(check_for_update)
            # Will be canceled when the winddow is closed
            self.nursery.start_soon(trio.sleep_forever)

    def resetFocus(self) -> None:
        if self.ui.cboAccount.currentText() == "":
            self.ui.cboAccount.setFocus()
        elif (
            self.ui.txtPassword.text() == ""
            and self.ui.txtPassword.placeholderText() == ""
        ):
            self.ui.txtPassword.setFocus()

    @override
    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        """Lets the user drag the window when left-click holding it"""
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self.windowHandle().startSystemMove()
            event.accept()

    def setupMousePropagation(self) -> None:
        """Sets some widgets to WA_NoMousePropagation to avoid window dragging issues"""
        mouse_ignore_list = [
            self.ui.btnAbout,
            self.ui.btnExit,
            self.ui.btnStartGame,
            self.ui.btnMinimize,
            self.ui.btnOptions,
            self.ui.btnAddonManager,
            self.ui.btnSwitchGame,
            self.ui.cboWorld,
            self.ui.chkSaveAccount,
            self.ui.chkSavePassword,
        ]
        for widget in mouse_ignore_list:
            widget.setAttribute(QtCore.Qt.WidgetAttribute.WA_NoMousePropagation)

    @override
    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        self.nursery.cancel_scope.cancel()
        event.accept()

    @override
    def changeEvent(self, event: QtCore.QEvent) -> None:
        super().changeEvent(event)
        if event.type() == QtCore.QEvent.Type.ThemeChange:
            get_app_style().update_base_font()

    def reset_start_game_button(self) -> None:
        self.ui.btnStartGame.setText("Play")
        self.ui.btnStartGame.setToolTip("Start your adventure!")

    def setup_start_game_button(self) -> None:
        """Set up signals and context menu for `btnStartGame`"""
        self.reset_start_game_button()

        self.ui.btnStartGame.clicked.connect(
            lambda: self.nursery.start_soon(self.start_game_button_clicked)
        )
        # Pressing enter in password box acts like pressing login button
        self.ui.txtPassword.returnPressed.connect(
            lambda: self.nursery.start_soon(self.start_game_button_clicked)
        )

        # Setup context menu
        self.btnStartGameMenu = QtWidgets.QMenu()
        self.btnStartGameMenu.addAction(self.ui.actionPatch)
        self.ui.actionPatch.triggered.connect(
            lambda: self.nursery.start_soon(self.actionPatchSelected)
        )
        self.ui.btnStartGame.setMenu(self.btnStartGameMenu)

    def setup_switch_game_button(self) -> None:
        """Set icon and dropdown options of switch game button according to current game"""
        game_config = self.config_manager.get_game_config(self.game_id)
        if game_config.game_type == GameType.DDO:
            self.ui.btnSwitchGame.setIcon(
                QtGui.QIcon(
                    str(
                        get_resource(
                            relative_path=Path("images/LOTROSwitchIcon.png"),
                            locale=self.config_manager.get_ui_locale(self.game_id),
                        )
                    )
                )
            )
        else:
            self.ui.btnSwitchGame.setIcon(
                QtGui.QIcon(
                    str(
                        get_resource(
                            relative_path=Path("images/DDOSwitchIcon.png"),
                            locale=self.config_manager.get_ui_locale(self.game_id),
                        )
                    )
                )
            )

        game_ids = list(
            self.config_manager.get_games_sorted(
                sorting_mode=self.config_manager.get_program_config().games_sorting_mode,
                game_type=game_config.game_type,
            )
        )
        # There is no need to show an action for the currently active game
        game_ids.remove(self.game_id)

        menu = QtWidgets.QMenu()
        menu.triggered.connect(
            lambda action: self.nursery.start_soon(
                self.game_switch_action_triggered, action
            )
        )
        for game_id in game_ids:
            action = QtGui.QAction(
                self.config_manager.get_game_config(game_id).name, self
            )
            action.setData(game_id)
            menu.addAction(action)
        self.ui.btnSwitchGame.setMenu(menu)
        # Needed for menu to show up for some reason
        self.ui.btnSwitchGame.menu()
        self.ui.btnSwitchGame.setEnabled(True)

    def btnAboutSelected(self) -> None:
        about_window = QtWidgets.QDialog(self, QtCore.Qt.WindowType.Popup)

        ui = Ui_aboutWindow()
        ui.setupUi(about_window)

        ui.lblDescription.setText(__about__.__description__)
        if __about__.__project_url__:
            ui.lblRepoWebsite.setText(
                f"<a href='{__about__.__project_url__}'>{__about__.__project_url__}</a>"
            )
        else:
            ui.lblRepoWebsite.hide()
        ui.lblCopyright.setText(__about__.__copyright__)
        ui.lblVersion.setText(f"<b>Version:</b> {__about__.__version__}")
        ui.lblCopyrightHistory.setText(__about__.__copyright_history__)

        about_window.exec()
        self.resetFocus()

    async def actionPatchSelected(self) -> None:
        game_config = self.config_manager.get_game_config(game_id=self.game_id)
        game_services_info = await GameServicesInfo.from_game_config(
            game_config=game_config
        )
        if game_services_info is None:
            return

        patch_window = PatchGameWindow(
            game_id=self.game_id,
            config_manager=self.config_manager,
            patch_server_url=game_services_info.patch_server,
        )
        await patch_window.run()
        self.resetFocus()

    async def btnOptionsSelected(self) -> None:
        winSettings = SettingsWindow(
            config_manager=self.config_manager, game_id=self.game_id
        )
        await winSettings.run()
        if winSettings.result() == QtWidgets.QDialog.DialogCode.Accepted:
            await self.InitialSetup()

    def btnAddonManagerSelected(self) -> None:
        if self.addon_manager_window:
            if self.addon_manager_window.isVisible():
                self.addon_manager_window.raise_()
                self.addon_manager_window.activateWindow()
                return
            else:
                self.addon_manager_window.deleteLater()

        self.addon_manager_window = addon_manager_window.AddonManagerWindow(
            config_manager=self.config_manager,
            game_id=self.game_id,
            launcher_local_config=self.game_launcher_local_config,
        )
        self.addon_manager_window.show()

    async def btnSwitchGameClicked(self) -> None:
        new_game_type = (
            GameType.LOTRO
            if self.config_manager.get_game_config(self.game_id).game_type
            == GameType.DDO
            else GameType.DDO
        )
        new_type_game_ids = self.config_manager.get_games_sorted(
            sorting_mode=self.config_manager.get_program_config().games_sorting_mode,
            game_type=new_game_type,
        )
        if not new_type_game_ids:
            logger.error("No %s games found to switch to", new_game_type)
            return
        self.game_id = new_type_game_ids[0]
        await self.InitialSetup()

    async def game_switch_action_triggered(self, action: QtGui.QAction) -> None:
        new_game_id: GameConfigID = action.data()
        self.game_id = new_game_id
        await self.InitialSetup()

    def run_startup_scripts(self) -> None:
        """Run enabled startup scripts"""
        game_config = self.config_manager.get_game_config(self.game_id)
        for script in game_config.addons.enabled_startup_scripts:
            try:
                logger.info("Running '%s' startup script...", script.relative_path)
                run_startup_script(
                    script=script,
                    game_directory=game_config.game_directory,
                    documents_config_dir=get_game_settings_dir(
                        game_config=game_config,
                        launcher_local_config=self.game_launcher_local_config,
                    ),
                )
            except FileNotFoundError:
                logger.exception(
                    "'%s' startup script does not exist", script.relative_path
                )
            except SyntaxError:
                logger.exception("'%s' ran into syntax error", script.relative_path)

    async def start_game_button_clicked(self) -> None:
        if self.game_cancel_scope:
            logger.info("Aborting game")
            self.game_cancel_scope.cancel()
            return

        if self.starting_game:
            return

        try:
            self.starting_game = True

            if not self.game_launcher_config:
                logger.error("Game launcher network config isn't loaded")
                return

            # Mainly re-checking the game dir to prevent people from starting the game
            # when it's known that it needs to be patched.
            try:
                self.validate_game_dir()
            except self.GameDirValidationError as e:
                logger.exception(e.msg)
                return

            if self.ui.cboAccount.currentText() == "" or (
                self.ui.txtPassword.text() == ""
                and self.ui.txtPassword.placeholderText() == ""
            ):
                logger.error("Please enter account name and password")
                return

            await self.start_game(game_launcher_config=self.game_launcher_config)
        finally:
            self.starting_game = False

    def accounts_index_changed(self, new_index: int) -> None:
        """Sets saved information for selected account."""
        # No selection
        if new_index == -1:
            self.ui.chkSaveAccount.setChecked(False)
            # In case it's still in it's initial unchecked state.
            self.chk_save_account_toggled(self.ui.chkSaveAccount.isChecked())
            return

        self.setCurrentAccountWorld()
        # We know these account settings are saved, because they exist
        self.ui.chkSaveAccount.setChecked(True)
        self.ui.txtPassword.clear()
        self.set_current_account_placeholder_password()
        self.resetFocus()

    def user_edited_account_name(self, new_text: str) -> None:
        # No saved account is selected
        if self.ui.cboAccount.currentIndex() == -1:
            return

        # Unselect any saved accounts once user manually edits account name.
        self.ui.cboAccount.setCurrentIndex(-1)
        # Make sure text doesn't get reset when index is changed
        self.ui.cboAccount.setEditText(new_text)
        # Remove any placeholder text for saved password of previously selected
        # account.
        self.ui.txtPassword.setPlaceholderText("")
        self.ui.chkSaveAccount.setChecked(False)

    def chk_save_account_toggled(self, checked: bool) -> None:
        if checked:
            self.ui.chkSavePassword.setEnabled(True)
        else:
            self.ui.chkSavePassword.setChecked(False)
            self.ui.chkSavePassword.setEnabled(False)

    def loadAllSavedAccounts(self) -> None:
        self.ui.cboAccount.clear()
        self.ui.cboAccount.setCurrentText("")

        accounts = self.config_manager.get_game_accounts(self.game_id)
        if not accounts:
            self.accounts_index_changed(-1)
            return
        for account in accounts:
            self.ui.cboAccount.addItem(
                account.display_name or account.username, userData=account
            )
        self.ui.cboAccount.setCurrentIndex(0)
        # Make sure information gets reset, since accounts may be different, but same
        # index.
        self.accounts_index_changed(0)

    def get_current_game_account(self) -> GameAccountConfig | None:
        current_data = self.ui.cboAccount.currentData()
        return current_data if isinstance(current_data, GameAccountConfig) else None

    def setCurrentAccountWorld(self) -> None:
        account = self.get_current_game_account()
        if account is None or account.last_used_world_name is None:
            return
        self.ui.cboWorld.setCurrentText(account.last_used_world_name)

    def set_current_account_placeholder_password(self) -> None:
        if (account := self.get_current_game_account()) and (
            self.config_manager.get_game_account_password(self.game_id, account)
            is not None
        ):
            self.ui.txtPassword.setPlaceholderText("********")
            self.ui.chkSavePassword.setChecked(True)
            return

        self.ui.txtPassword.setPlaceholderText("")
        self.ui.chkSavePassword.setChecked(False)
        # Focus on the password field, so user can easily type password, since none are
        # saved.
        self.ui.txtPassword.setFocus()
        return

    def get_game_subscription_selection(
        self,
        subscriptions: list[login_account.GameSubscription],
        account_config: GameAccountConfig,
    ) -> login_account.GameSubscription | None:
        select_subscription_dialog = QtWidgets.QDialog(
            self, QtCore.Qt.WindowType.FramelessWindowHint
        )
        ui = Ui_selectSubscriptionWindow()
        ui.setupUi(select_subscription_dialog)

        for subscription in subscriptions:
            ui.subscriptionsComboBox.addItem(subscription.description, subscription)

        # Select last used subscription
        if (
            last_used_subscription_name
            := self.config_manager.get_game_account_last_used_subscription_name(
                self.game_id, account_config
            )
        ):
            for i, subscription in enumerate(subscriptions):
                if subscription.name == last_used_subscription_name:
                    ui.subscriptionsComboBox.setCurrentIndex(i)
                    break

        if select_subscription_dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            selected_subscription: login_account.GameSubscription = (
                ui.subscriptionsComboBox.currentData()
            )
            self.resetFocus()
            return selected_subscription
        else:
            self.resetFocus()
            logger.error("No subscription selected")
            return None

    async def authenticate_account(
        self, account: GameAccountConfig
    ) -> login_account.AccountLoginResponse | None:
        logger.info("Checking account details...")

        game_config = self.config_manager.get_game_config(self.game_id)
        game_services_info = await GameServicesInfo.from_game_config(
            game_config=game_config
        )
        if game_services_info is None:
            return None

        try:
            login_response = await login_account.login_account(
                auth_server=game_services_info.auth_server,
                username=account.username,
                password=self.ui.txtPassword.text()
                or self.config_manager.get_game_account_password(
                    game_id=self.game_id, game_account=account
                )
                or "",
            )
        except login_account.WrongUsernameOrPasswordError as e:
            logger.exception(e.msg)
            return None
        except httpx.HTTPError:
            logger.exception("Network error while authenticating account")
            return None
        except GLSServiceError:
            logger.exception(
                "Non-network error with login service. Please report "
                "this issue, if it continues.",
            )
            return None

        # don't keep password longer in memory than required
        if not self.ui.chkSavePassword.isChecked():
            self.ui.txtPassword.clear()

        logger.info("Account authenticated")
        return login_response

    async def start_game(self, game_launcher_config: GameLauncherConfig) -> None:  # noqa: PLR0911
        current_account = self.get_current_game_account()
        current_world: World = self.ui.cboWorld.currentData()
        if current_account is None:
            current_account = GameAccountConfig(
                username=self.ui.cboAccount.currentText(),
                display_name=None,
                last_used_world_name=current_world.name,
            )
        login_response = await self.authenticate_account(current_account)
        if not login_response:
            return

        game_subscriptions = login_response.get_game_subscriptions(
            datacenter_game_name=self.game_launcher_local_config.datacenter_game_name
        )
        if len(game_subscriptions) > 1:
            subscription = self.get_game_subscription_selection(
                subscriptions=game_subscriptions, account_config=current_account
            )
            if subscription is None:
                return
        else:
            subscription = game_subscriptions[0]
        account_number = subscription.name

        if self.ui.chkSaveAccount.isChecked():
            if len(game_subscriptions) > 1:
                self.config_manager.save_game_account_last_used_subscription_name(
                    game_id=self.game_id,
                    game_account=current_account,
                    subscription_name=subscription.name,
                )
            else:
                self.config_manager.delete_game_account_last_used_subscription_name(
                    game_id=self.game_id,
                    game_account=current_account,
                )

            if self.ui.chkSavePassword.isChecked():
                if self.ui.txtPassword.text():
                    self.config_manager.save_game_account_password(
                        self.game_id, current_account, self.ui.txtPassword.text()
                    )
            else:
                self.config_manager.delete_game_account_password(
                    self.game_id, current_account
                )

            current_account = attrs.evolve(
                current_account, last_used_world_name=current_world.name
            )

            # Update order of account in config file
            accounts = list(
                self.config_manager.read_game_accounts_config_file(self.game_id)
            )
            # Account is deleted first, so it can be inserted back at the beginning.
            # Accounts are sorted with the most recently played first.
            for account in accounts:
                if account.username == current_account.username:
                    accounts.remove(account)
            accounts.insert(0, current_account)
            self.config_manager.update_game_accounts_config_file(
                game_id=self.game_id, accounts=tuple(accounts)
            )
        else:
            self.config_manager.update_game_accounts_config_file(self.game_id, ())
        self.loadAllSavedAccounts()

        selected_world: World = self.ui.cboWorld.currentData()

        try:
            selected_world_status = await selected_world.get_status()
        except httpx.HTTPError:
            logger.exception("Network error while fetching world status")
            return
        except WorldUnavailableError:
            logger.exception(
                "Error fetching world status. You may want to check "
                "the news feed for a scheduled down time.",
            )
            return
        except XMLSchemaValidationError:
            logger.exception(
                "World status info has incompatible format. Please report "
                "this issue if using a supported game server",
            )
            return

        # Check if the user is allowed to join this world.
        if subscription.product_tokens is not None and (
            (
                selected_world_status.allowed_billing_roles is not None
                and not selected_world_status.allowed_billing_roles.intersection(
                    subscription.product_tokens
                )
            )
            or (
                selected_world_status.denied_billing_roles
                and selected_world_status.denied_billing_roles.intersection(
                    subscription.product_tokens
                )
            )
        ):
            logger.exception("You are not allowed to join this world")
            return

        if selected_world_status.queue_url:
            try:
                await self.world_queue(
                    queueURL=selected_world_status.queue_url,
                    account_number=account_number,
                    login_response=login_response,
                    game_launcher_config=game_launcher_config,
                )
            except httpx.HTTPError:
                logger.exception("Network error while joining world login queue")
                return
            except WorldQueueResultXMLParseError:
                logger.exception("Error parsing world login queue response")
                return
            except JoinWorldQueueFailedError as e:
                logger.exception(e.msg)
                return

        self.run_startup_scripts()
        logger.info("Starting game")
        self.ui.btnStartGame.setText("Abort")
        self.ui.btnStartGame.setToolTip("Abort running game")
        self.ui.btnSwitchGame.setEnabled(False)
        self.ui.actionPatch.setEnabled(False)
        self.ui.btnOptions.setEnabled(False)
        program_config = self.config_manager.get_program_config()
        windows_visible_before_start = tuple(
            widget for widget in get_qapp().topLevelWidgets() if widget.isVisible()
        )
        try:
            async with trio.open_nursery() as nursery:
                self.game_cancel_scope = nursery.cancel_scope

                process: trio.Process = await nursery.start(
                    partial(
                        start_game,
                        config_manager=self.config_manager,
                        game_id=self.game_id,
                        game_launcher_config=game_launcher_config,
                        game_launcher_local_config=self.game_launcher_local_config,
                        world=selected_world,
                        login_server=selected_world_status.login_server,
                        account_number=account_number,
                        ticket=login_response.session_ticket,
                    )
                )
                if (
                    program_config.on_game_start == "close"
                    and process.returncode is None
                ):
                    # We hide and close after the game finishes rather than literally
                    # closing when the game starts.
                    for widget in windows_visible_before_start:
                        widget.hide()

                if await process.wait() != 0:
                    logger.error("Game closed unexpectedly")
                else:
                    logger.info("Game finished")
                    if program_config.on_game_start == "close":
                        app_cancel_scope.cancel()
                        await trio.lowlevel.checkpoint_if_cancelled()
        except* MissingLaunchArgumentError:
            logger.exception(
                "Game launch argument missing. Please report this error if using a supported server."
            )
        except* OSError:
            logger.exception("Failed to start game")

        # Show windows again, because there was an error.
        if program_config.on_game_start == "close":
            for widget in windows_visible_before_start:
                widget.show()

        self.game_cancel_scope = None
        self.reset_start_game_button()
        self.ui.btnSwitchGame.setEnabled(True)
        self.ui.actionPatch.setEnabled(True)
        self.ui.btnOptions.setEnabled(True)

    async def world_queue(
        self,
        queueURL: str,
        account_number: str,
        login_response: login_account.AccountLoginResponse,
        game_launcher_config: GameLauncherConfig,
    ) -> None:
        """
        Raises:
            HTTPError
            JoinWorldQueueFailedError
            WorldQueueResultXMLParseError
        """
        world_login_queue = WorldLoginQueue(
            game_launcher_config.login_queue_url,
            game_launcher_config.login_queue_params_template,
            account_number,
            login_response.session_ticket,
            queueURL,
        )
        while True:
            world_queue_result = await world_login_queue.join_queue()
            if world_queue_result.queue_number <= world_queue_result.now_serving_number:
                break
            people_ahead_in_queue = (
                world_queue_result.queue_number - world_queue_result.now_serving_number
            )
            logger.info("Position in queue: %s", people_ahead_in_queue)

    def set_banner_image(self) -> None:
        game_config = self.config_manager.get_game_config(self.game_id)
        ui_locale = self.config_manager.get_ui_locale(self.game_id)
        game_dir_banner_override_path = (
            game_config.game_directory / ui_locale.lang_tag.split("-")[0] / "banner.png"
        )
        if game_dir_banner_override_path.exists():
            banner_pixmap = QtGui.QPixmap(str(game_dir_banner_override_path))
        else:
            banner_pixmap = QtGui.QPixmap(
                str(
                    get_resource(
                        Path(f"images/{game_config.game_type}_banner.png"), ui_locale
                    )
                )
            )
        self.ui.imgGameBanner.setPixmap(banner_pixmap)

    @attrs.frozen(kw_only=True)
    class GameDirValidationError(Exception):
        msg: str
        prevents_initialization: bool = True

    def validate_game_dir(self) -> None:
        """
        Raises:
            GameDirValidationError
        """
        game_config = self.config_manager.get_game_config(self.game_id)
        if not game_config.game_directory.exists():
            raise self.GameDirValidationError(msg="Game directory not found")

        try:
            if (
                find_game_dir_game_type(game_config.game_directory)
                != game_config.game_type
            ):
                raise self.GameDirValidationError(
                    msg="Game directory game type does not match config"
                )
        except InvalidGameDirError as e:
            raise self.GameDirValidationError(msg="Game directory is not valid") from e

        locale = (
            game_config.locale
            or self.config_manager.get_program_config().default_locale
        )
        if not (
            game_config.game_directory / f"client_local_{locale.game_language_name}.dat"
        ).exists():
            raise self.GameDirValidationError(
                msg="The game needs to be patched. That can be done from the dropdown "
                "menu on the Play button.",
                prevents_initialization=False,
            )

    def setup_game(self) -> bool:
        try:
            self.validate_game_dir()
        except self.GameDirValidationError as e:
            if e.prevents_initialization:
                logger.exception(e.msg)
                return False
            else:
                logger.warning(e.msg, exc_info=True)

        game_config = self.config_manager.get_game_config(self.game_id)
        launcher_config_paths = get_launcher_config_paths(
            search_dir=game_config.game_directory, game_type=game_config.game_type
        )
        try:
            self.game_launcher_local_config = GameLauncherLocalConfig.from_config_xml(
                launcher_config_paths[0].read_text(encoding="UTF-8")
            )
        except GameLauncherLocalConfigParseError:
            logger.exception("Error parsing local launcher config")
            return False

        return True

    async def InitialSetup(self) -> None:
        if self.network_setup_nursery:
            self.network_setup_nursery.cancel_scope.cancel()

        # Keyring dependent
        self.ui.cboAccount.setEnabled(False)
        self.ui.txtPassword.setEnabled(False)
        self.ui.widgetSaveSettings.setEnabled(False)

        # Network loading dependent
        self.ui.cboWorld.setEnabled(False)
        self.ui.btnStartGame.setEnabled(False)

        self.ui.btnSwitchGame.setEnabled(False)

        self.ui.txtPassword.setText("")
        self.ui.txtPassword.setPlaceholderText("")
        self.ui.cboWorld.clear()
        self.ClearLog()
        self.ClearNews()

        # Set news feed to say "Loading ..." until it is replaced by the news.
        self.ui.txtFeed.setHtml(
            '<html><body><p style="text-align:center;">Loading ...</p></body></html>'
        )

        logger.info("Initializing, please wait...")

        # Handle when current game has been removed.
        if self.game_id not in self.config_manager.get_game_config_ids():
            try:
                self.game_id = self.config_manager.get_initial_game()
            except NoValidGamesError as e:
                logger.exception(e.msg)
                return
            await self.InitialSetup()
            return

        try:
            keyring.get_password(__about__.__title__, "TEST")
        except NoKeyringError:
            logger.warning(
                "No system keyring found. Password and subscription saving will fail.",
                exc_info=True,
            )
        except KeyringLocked:
            logger.exception(
                "Failed to unlock system keyring. Password and subscription saving will fail."
            )

        self.loadAllSavedAccounts()
        self.ui.cboAccount.setEnabled(True)
        self.ui.txtPassword.setEnabled(True)
        self.ui.widgetSaveSettings.setEnabled(True)

        self.set_banner_image()
        self.setWindowTitle(self.config_manager.get_game_config(self.game_id).name)

        # Setup btnSwitchGame for current game
        self.setup_switch_game_button()

        if not self.setup_game():
            return

        self.resetFocus()
        async with trio.open_nursery() as self.network_setup_nursery:
            self.network_setup_nursery.start_soon(self.game_initial_network_setup)

    async def game_initial_network_setup(self) -> None:
        try:
            game_services_info = await GameServicesInfo.from_url(
                gls_datacenter_service=self.game_launcher_local_config.gls_datacenter_service,
                game_datacenter_name=self.game_launcher_local_config.datacenter_game_name,
            )
        except httpx.HTTPError:
            logger.exception("Network error while fetching game services info")
            return
        except GLSServiceError:
            logger.exception(
                "Non-network error with GLS datacenter service. Please report "
                "this issue, if it continues.",
            )
            return

        logger.info("Fetched game services info")

        self.load_worlds_list(game_services_info)
        self.game_launcher_config = await self.get_game_launcher_config(
            game_launcher_config_url=game_services_info.launcher_config_url
        )
        if not self.game_launcher_config:
            return
        # Enable UI elements that rely on what's been loaded.
        self.ui.cboWorld.setEnabled(True)
        self.ui.btnStartGame.setEnabled(True)

        await self.load_newsfeed(self.game_launcher_config)

    def load_worlds_list(self, game_services_info: GameServicesInfo) -> None:
        # Sort alphabetically with old worlds at the bottom.
        sorted_worlds = sorted(
            game_services_info.worlds,
            key=lambda world: f"{2 if world.name.strip().lower().endswith('[old]') else 1}{world.name}",
        )
        for world in sorted_worlds:
            self.ui.cboWorld.addItem(world.name, userData=world)

        self.setCurrentAccountWorld()
        logger.info("World list obtained")

    async def get_game_launcher_config(
        self, game_launcher_config_url: str
    ) -> GameLauncherConfig | None:
        try:
            game_launcher_config = await GameLauncherConfig.from_url(
                game_launcher_config_url
            )
            logger.info("Game launcher configuration read")
            return game_launcher_config
        except httpx.HTTPError:
            logger.exception("Network error while retrieving game launcher config")
            return None
        except GameLauncherConfigParseError:
            logger.exception(
                "Game launcher config has incompatible format. Please report "
                "this issue if using a supported game server",
            )
            return None

    async def load_newsfeed(self, game_launcher_config: GameLauncherConfig) -> None:
        ui_locale = self.config_manager.get_ui_locale(self.game_id)
        game_config = self.config_manager.get_game_config(self.game_id)
        newsfeed_url = game_config.newsfeed or game_launcher_config.get_newfeed_url(
            ui_locale
        )
        try:
            self.ui.txtFeed.setHtml(
                await get_game_newsfeed_html(
                    url=newsfeed_url, locale=ui_locale, game_config=game_config
                )
            )
        except httpx.HTTPError:
            logger.exception("Network error while downloading newsfeed")

    def ClearLog(self) -> None:
        self.ui.txtStatus.setText("")

    def ClearNews(self) -> None:
        self.ui.txtFeed.setText("")


async def check_for_update() -> None:
    """Notifies user if their copy of OneLauncher is out of date"""
    repository_url = __about__.__project_url__
    if not repository_url:
        logger.warning("No updates URL available")
        return
    if "github.com" not in repository_url.lower():
        logger.warning(
            "Repository URL is not at github.com. Update checking is currently only supported for github.com"
        )
        return

    latest_release_template = (
        "https://api.github.com/repos/{user_and_repo}/releases/latest"
    )
    latest_release_url = latest_release_template.format(
        user_and_repo=repository_url.lower().split("github.com")[1].strip("/")
    )

    try:
        response = await get_httpx_client(latest_release_url).get(latest_release_url)
        response.raise_for_status()
    except httpx.HTTPError:
        logger.exception(
            "Network error while checking for %s updates", __about__.__title__
        )
        return
    release_dictionary = response.json()

    release_version = packaging.version.parse(release_dictionary["tag_name"])

    if release_version > __about__.version_parsed:
        url = release_dictionary["html_url"]
        name = release_dictionary["name"]
        description = release_dictionary["body"]

        messageBox = QtWidgets.QMessageBox()
        messageBox.setWindowFlag(QtCore.Qt.WindowType.FramelessWindowHint)
        messageBox.setIcon(QtWidgets.QMessageBox.Icon.Information)
        messageBox.setStandardButtons(messageBox.StandardButton.Ok)

        centered_href = (
            f'<html><head/><body><p align="center"><a href="{url}">'
            f"<span>{name}</span></a></p></body></html>"
        )
        messageBox.setInformativeText(
            f"There is a new version of {__about__.__title__} available! {centered_href}"
        )
        messageBox.setDetailedText(description)
        show_message_box_details_as_markdown(messageBox)
        messageBox.exec()
    else:
        logger.info("%s is up to date", __about__.__title__)
