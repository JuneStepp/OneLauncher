# coding=utf-8
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
import contextlib
import logging
from pathlib import Path
from typing import List, Optional

import httpx
import trio
from pkg_resources import parse_version
from PySide6 import QtCore, QtGui, QtWidgets
from xmlschema import XMLSchemaValidationError

from . import __about__, games_sorted
from .addon_manager import AddonManagerWindow
from .config.games.game import save_game
from .config.program_config import program_config
from .game import Game, GameType
from .game_account import GameAccount
from .game_launcher_local_config import GameLauncherLocalConfig
from .game_utilities import find_game_dir_game_type, get_launcher_config_paths
from .network import login_account
from .network.game_launcher_config import (GameLauncherConfig,
                                           GameLauncherConfigParseError)
from .network.game_newsfeed import newsfeed_url_to_html
from .network.game_services_info import GameServicesInfo
from .network.httpx_client import get_httpx_client
from .network.soap import GLSServiceError
from .network.world import World, WorldUnavailableError
from .network.world_login_queue import (JoinWorldQueueFailedError,
                                        WorldLoginQueue,
                                        WorldQueueResultXMLParseError)
from .patch_game_window import PatchWindow
from .resources import get_resource
from .settings_window import SettingsWindow
from .ui.about_uic import Ui_dlgAbout
from .ui.main_uic import Ui_winMain
from .ui.select_subscription_uic import Ui_dlgSelectSubscription
from .ui.start_game_window import StartGame
from .ui_resources import icon_font
from .ui_utilities import show_message_box_details_as_markdown


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, game: Game):
        super(
            MainWindow,
            self).__init__(
            None,
            QtCore.Qt.WindowType.FramelessWindowHint)
        self.game: Game = game
        self.checked_for_program_update = False

        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose, on=True)

    def init_ui(self):
        self.ui = Ui_winMain()
        self.ui.setupUi(self)

        self.setFixedSize(790, 470)

        # Setup buttons
        self.setupBtnAbout()
        self.setupBtnMinimize()
        self.setupBtnExit()
        self.setupBtnOptions()
        self.setupBtnAddonManager()
        self.setupBtnLoginMenu()
        self.ui.btnSwitchGame.clicked.connect(
            lambda: self.nursery.start_soon(self.btnSwitchGameClicked))

        self.ui.cboAccount.lineEdit().setClearButtonEnabled(True)
        # Accounts combo box item selection signal
        self.ui.cboAccount.currentIndexChanged.connect(
            self.accounts_index_changed)
        self.ui.cboAccount.lineEdit().textEdited.connect(self.user_edited_account_name)

        # Pressing enter in password box acts like pressing login button
        self.ui.txtPassword.returnPressed.connect(
            lambda: self.nursery.start_soon(self.btnLoginClicked))

        self.setupMousePropagation()

    async def run(self):
        async with trio.open_nursery() as self.nursery:
            self.init_ui()
            self.show()
            await self.InitialSetup()
            # Will be canceled when the winddow is closed
            self.nursery.start_soon(trio.sleep_forever)

    def resetFocus(self):
        if self.ui.cboAccount.currentText() == "":
            self.ui.cboAccount.setFocus()
        elif (self.ui.txtPassword.text() == "" and
              self.ui.txtPassword.placeholderText() == ""):
            self.ui.txtPassword.setFocus()

    def mousePressEvent(self, event):
        """Lets the user drag the window when left-click holding it"""
        if event.button() == QtCore.Qt.LeftButton:
            self.windowHandle().startSystemMove()
            event.accept()

    def setupMousePropagation(self):
        """Sets some widgets to WA_NoMousePropagation to avoid window dragging issues"""
        mouse_ignore_list = [
            self.ui.btnAbout,
            self.ui.btnExit,
            self.ui.btnLogin,
            self.ui.btnMinimize,
            self.ui.btnOptions,
            self.ui.btnAddonManager,
            self.ui.btnSwitchGame,
            self.ui.cboWorld,
            self.ui.chkSaveSettings,
        ]
        for widget in mouse_ignore_list:
            widget.setAttribute(QtCore.Qt.WA_NoMousePropagation)

    def closeEvent(self, event):
        self.nursery.cancel_scope.cancel()
        event.accept()

    def setupBtnExit(self):
        self.ui.btnExit.clicked.connect(self.close)

        self.ui.btnExit.setFont(icon_font)
        self.ui.btnExit.setText("\uf00d")

    def setupBtnMinimize(self):
        self.ui.btnMinimize.clicked.connect(self.showMinimized)

        self.ui.btnMinimize.setFont(icon_font)
        self.ui.btnMinimize.setText("\uf2d1")

    def setupBtnAbout(self):
        self.ui.btnAbout.clicked.connect(self.btnAboutSelected)

        self.ui.btnAbout.setFont(icon_font)
        self.ui.btnAbout.setText("\uf05a")

    def setupBtnOptions(self):
        self.ui.btnOptions.clicked.connect(
            lambda: self.nursery.start_soon(self.btnOptionsSelected))

        self.ui.btnOptions.setFont(icon_font)
        self.ui.btnOptions.setText("\uf013")

    def setupBtnAddonManager(self):
        self.ui.btnAddonManager.clicked.connect(
            self.btnAddonManagerSelected)

        self.ui.btnAddonManager.setFont(icon_font)
        self.ui.btnAddonManager.setText("\uf055")

    def setupBtnLoginMenu(self):
        """Sets up signals and context menu for btnLoginMenu"""
        self.ui.btnLogin.clicked.connect(
            lambda: self.nursery.start_soon(self.btnLoginClicked))

        # Setup context menu
        self.ui.btnLoginMenu = QtWidgets.QMenu()
        self.ui.btnLoginMenu.addAction(self.ui.actionPatch)
        self.ui.actionPatch.triggered.connect(self.actionPatchSelected)
        self.ui.btnLogin.setMenu(self.ui.btnLoginMenu)

    def setup_switch_game_button(self):
        """Set icon and dropdown options of switch game button according to current game"""
        if self.game.game_type == GameType.DDO:
            self.ui.btnSwitchGame.setIcon(
                QtGui.QIcon(
                    str(
                        get_resource(
                            Path("images/LOTROSwitchIcon.png"),
                            program_config.get_ui_locale(
                                self.game)))))
        else:
            self.ui.btnSwitchGame.setIcon(
                QtGui.QIcon(
                    str(
                        get_resource(
                            Path("images/DDOSwitchIcon.png"),
                            program_config.get_ui_locale(
                                self.game)))))

        games = games_sorted.get_sorted_games_list(
            program_config.games_sorting_mode,
            self.game.game_type)
        # There is no need to show an action for the currently active game
        games.remove(self.game)

        menu = QtWidgets.QMenu()
        menu.triggered.connect(
            lambda action: self.nursery.start_soon(
                self.game_switch_action_triggered, action))
        for game in games:
            action = QtGui.QAction(game.name, self)
            action.setData(game)
            menu.addAction(action)
        self.ui.btnSwitchGame.setMenu(menu)
        # Needed for menu to show up for some reason
        self.ui.btnSwitchGame.menu()

    def btnAboutSelected(self):
        dlgAbout = QtWidgets.QDialog(self, QtCore.Qt.WindowType.Popup)

        ui = Ui_dlgAbout()
        ui.setupUi(dlgAbout)

        ui.lblDescription.setText(__about__.__description__)
        ui.lblRepoWebsite.setText(f"<a href='{__about__.__project_url__}'>"
                                  f"{__about__.__project_url__}</a>")
        ui.lblCopyright.setText(__about__.__copyright__)
        ui.lblVersion.setText(f"<b>Version:</b> {__about__.__version__}")
        ui.lblCopyrightHistory.setText(__about__.__copyright_history__)

        dlgAbout.exec()
        self.resetFocus()

    def actionPatchSelected(self):
        winPatch = PatchWindow(
            self.game,
            self.game_services_info.patch_server)
        winPatch.Run()
        self.resetFocus()

    async def btnOptionsSelected(self):
        winSettings = SettingsWindow(self.game)
        await winSettings.run()
        if winSettings.result() == QtWidgets.QDialog.DialogCode.Accepted:
            await self.InitialSetup()

    def btnAddonManagerSelected(self):
        winAddonManager = AddonManagerWindow(self.game)
        winAddonManager.Run()
        save_game(self.game)

        self.resetFocus()

    async def btnSwitchGameClicked(self):
        new_game_type = (
            GameType.LOTRO if
            self.game.game_type == GameType.DDO
            else GameType.DDO)
        self.game = games_sorted.get_sorted_games_list(
            program_config.games_sorting_mode, new_game_type)[0]
        await self.InitialSetup()

    async def game_switch_action_triggered(self, action: QtGui.QAction):
        self.game = action.data()
        await self.InitialSetup()

    async def btnLoginClicked(self):
        if (
            self.ui.cboAccount.currentText() == ""
            or (self.ui.txtPassword.text() == "" and
                self.ui.txtPassword.placeholderText() == "")
        ):
            self.AddLog(
                '<font color="Khaki">Please enter account name and password</font>'
            )
            return

        await self.AuthAccount()

    def save_settings(self):
        program_config.save_accounts = self.ui.chkSaveSettings.isChecked()
        program_config.save_accounts_passwords = self.ui.chkSavePassword.isChecked()

        program_config.save()
        save_game(self.game)

    def accounts_index_changed(self, new_index):
        """Sets saved information for selected account."""
        # No selection
        if new_index == -1:
            return

        self.ui.txtPassword.clear()
        self.setCurrentAccountWorld()
        self.set_current_account_placeholder_password()
        self.resetFocus()

    def user_edited_account_name(self, new_text: str):
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

    def loadAllSavedAccounts(self) -> None:
        self.ui.cboAccount.clear()
        self.ui.cboAccount.setCurrentText("")

        if (program_config.save_accounts is False or
                self.game.accounts is None):
            self.game.accounts = None
            return

        accounts = list(self.game.accounts.values())
        if not accounts:
            return

        # Accounts are read backwards, so they
        # are in order of most recentally played
        for account in accounts[::-1]:
            self.ui.cboAccount.addItem(account.display_name, userData=account)
        self.ui.cboAccount.setCurrentIndex(0)

    def get_current_game_account(self) -> GameAccount | None:
        if type(self.ui.cboAccount.currentData()) == GameAccount:
            return self.ui.cboAccount.currentData()
        else:
            return None

    def setCurrentAccountWorld(self):
        account = self.get_current_game_account()
        if account is None:
            return
        self.ui.cboWorld.setCurrentText(account.last_used_world_name)

    def set_current_account_placeholder_password(self):
        if not program_config.save_accounts_passwords:
            self.ui.txtPassword.setFocus()
            return

        account = self.get_current_game_account()
        if account is None:
            return
        password = account.password
        password_length = 0 if password is None else len(password)
        del password

        self.ui.txtPassword.setPlaceholderText("*" * password_length)

    def get_game_subscription_selection(
            self,
            subscriptions: List[login_account.GameSubscription],
            account: GameAccount) -> Optional[login_account.GameSubscription]:
        if last_used_subscription_name := account.last_used_subscription_name:
            for subscription in subscriptions:
                if subscription.name == last_used_subscription_name:
                    del last_used_subscription_name
                    return subscription

            del last_used_subscription_name
            logger.warning(
                "last_used_subscription_name does not match any subscriptions.")

        select_subscription_dialog = QtWidgets.QDialog(
            self, QtCore.Qt.WindowType.FramelessWindowHint)
        ui = Ui_dlgSelectSubscription()
        ui.setupUi(select_subscription_dialog)

        for subscription in subscriptions:
            ui.subscriptionsComboBox.addItem(
                subscription.description, subscription.name)

        if select_subscription_dialog.exec() == QtWidgets.QDialog.Accepted:
            selected_subscription_name: str = ui.subscriptionsComboBox.currentData()
            self.resetFocus()
            return selected_subscription_name
        else:
            self.resetFocus()
            self.AddLog("No sub-account selected - aborting")
            return None

    async def AuthAccount(self) -> None:
        self.AddLog("Checking account details...")

        # Force a small display to ensure message above is displayed
        # as program can look like it is not responding while validating
        for _ in range(4):
            QtCore.QCoreApplication.instance().processEvents()  # type: ignore

        current_account = self.get_current_game_account()
        current_world: World = self.ui.cboWorld.currentData()
        if current_account is None:
            current_account = GameAccount(
                self.ui.cboAccount.currentText(),
                self.game.uuid,
                current_world.name)
            self.ui.cboAccount.setItemData(
                self.ui.cboAccount.currentIndex(), current_account)

        try:
            self.login_response = await login_account.login_account(
                self.game_services_info.auth_server,
                current_account.username,
                self.ui.txtPassword.text() or current_account.password or "")
        except login_account.WrongUsernameOrPasswordError:
            self.AddLog("Username or password is incorrect", True)
            return
        except httpx.HTTPError:
            logger.exception("")
            self.AddLog("Network error while authenticating account", True)
            return
        except GLSServiceError:
            logger.exception("")
            self.AddLog("Non-network error with login service. Please report "
                        "this issue, if it continues.", True)
            return

        # don't keep password longer in memory than required
        if not self.ui.chkSavePassword.isChecked():
            self.ui.txtPassword.clear()

        self.AddLog("Account authenticated")

        if self.ui.chkSaveSettings.isChecked():
            if self.game.accounts is None:
                self.game.accounts = {}

            # Account is deleted first, because accounts are in order of
            # the most recently played at the end.
            with contextlib.suppress(KeyError):
                del self.game.accounts[current_account.username]

            self.game.accounts[current_account.username] = current_account

            current_account.last_used_world_name = current_world.name

            if self.ui.chkSavePassword.isChecked():
                if self.ui.txtPassword.text():
                    current_account.password = self.ui.txtPassword.text()
            else:
                current_account.delete_password()

            self.loadAllSavedAccounts()

        game_subscriptions = self.login_response.get_game_subscriptions(
            self.game.datacenter_game_name)
        if len(game_subscriptions) > 1:
            subscription = self.get_game_subscription_selection(
                game_subscriptions, current_account)
            if subscription is None:
                return
        else:
            subscription = game_subscriptions[0]
            account_number = subscription.name
        current_account.last_used_subscription_name = subscription.name

        self.save_settings()

        selected_world: World = self.ui.cboWorld.currentData()

        try:
            selected_world_status = await selected_world.get_status()
        except httpx.HTTPError:
            logger.exception(
                "Network error while downloading world status xml")
            self.AddLog(
                "Network error while fetching world status",
                is_error=True)
            return
        except WorldUnavailableError:
            logger.exception("Login world unavailable")
            self.AddLog(
                "Error fetching world status. You may want to check "
                "the news feed for a scheduled down time.",
                is_error=True
            )
            return
        except XMLSchemaValidationError:
            logger.exception("World status XML doesn't match schema")
            self.AddLog(
                "World status info has incompatible format. Please report "
                "this issue if using a supported game server",
                is_error=True)  # TODO: Easy report
            return

        if selected_world_status.queue_url == "":
            await self.start_game(account_number)
        else:
            await self.EnterWorldQueue(
                selected_world_status.queue_url, account_number)

    async def start_game(self, account_number: str):
        world: World = self.ui.cboWorld.currentData()
        game = StartGame(
            self.game,
            self.game_launcher_config,
            world,
            account_number,
            self.login_response.session_ticket,
        )
        await game.start_game()

    async def EnterWorldQueue(self, queueURL, account_number):
        world_login_queue = WorldLoginQueue(
            self.game_launcher_config.login_queue_url,
            self.game_launcher_config.login_queue_params_template,
            account_number,
            self.login_response.session_ticket,
            queueURL)
        while True:
            try:
                world_queue_result = await world_login_queue.join_queue()
            except httpx.HTTPError:
                self.AddLog(
                    "Network error while joining world queue",
                    is_error=True)
                logger.exception("")
                return
            except (JoinWorldQueueFailedError, WorldQueueResultXMLParseError):
                self.AddLog(
                    "Non-network error joining world queue. "
                    "Please report this error if it continues")  # TODO Easy report
                logger.exception("")
                return
            if (world_queue_result.queue_number <=
                    world_queue_result.now_serving_number):
                break
            people_ahead_in_queue = world_queue_result.queue_number - \
                world_queue_result.now_serving_number
            self.AddLog(f"Position in queue: {people_ahead_in_queue}")

        await self.start_game(account_number)

    def set_banner_image(self):
        ui_locale = program_config.get_ui_locale(self.game)
        game_dir_banner_override_path = self.game.game_directory / \
            ui_locale.lang_tag.split("-")[0] / "banner.png"
        if game_dir_banner_override_path.exists():
            banner_pixmap = QtGui.QPixmap(str(game_dir_banner_override_path))
        else:
            banner_pixmap = QtGui.QPixmap(str(get_resource(Path(
                f"images/{self.game.game_type}_banner.png"), ui_locale)))

        banner_pixmap = banner_pixmap.scaledToHeight(self.ui.imgMain.height())
        self.ui.imgMain.setPixmap(banner_pixmap)

    def check_game_dir(self) -> bool:
        if not self.game.game_directory.exists():
            self.AddLog("[E13] Game directory not found", is_error=True)
            return False

        if (find_game_dir_game_type(self.game.game_directory)
                != self.game.game_type):
            self.AddLog("Game directory is not valid", is_error=True)
            return False

        return True

    def setup_game(self) -> bool:
        launcher_config_paths = get_launcher_config_paths(
            self.game.game_directory, self.game.game_type)
        if not launcher_config_paths:
            # Should give error associated with there being no launcher configs
            # found
            self.check_game_dir()
            return False
        try:
            launcher_config = GameLauncherLocalConfig.from_config_xml(
                launcher_config_paths[0].read_text())
        except GameLauncherConfigParseError:
            self.AddLog("Error parsing local launcher config", is_error=True)
            logger.exception("")
            return False
        self.game.launcher_local_config = launcher_config

        if not (
                self.game.game_directory /
                f"client_local_{self.game.locale.game_language_name}.dat").exists():
            self.AddLog(
                "[E20] There is no game language data for "
                f"{self.game.locale.display_name} installed "
                f"You may have to select {self.game.locale.display_name}"
                " in the standard game launcher and wait for the data to download."
                " The standard game launcher can be opened from the settings menu.",
                is_error=True)
            return False

        return True

    async def InitialSetup(self):
        self.ui.cboAccount.setEnabled(False)
        self.ui.cboAccount.setFocus()
        self.ui.txtPassword.setEnabled(False)
        self.ui.btnLogin.setEnabled(False)
        self.ui.chkSaveSettings.setEnabled(False)
        self.ui.chkSavePassword.setEnabled(False)
        self.ui.btnOptions.setEnabled(False)
        self.ui.btnSwitchGame.setEnabled(False)

        self.ui.chkSaveSettings.setChecked(program_config.save_accounts)
        self.ui.chkSavePassword.setChecked(
            program_config.save_accounts_passwords)

        self.ui.txtPassword.setText("")
        self.ui.txtPassword.setPlaceholderText("")
        self.ui.cboWorld.clear()
        self.ClearLog()
        self.ClearNews()

        # Set news feed to say "Loading ..." until it is replaced by the news.
        self.ui.txtFeed.setHtml(
            '<html><body><p style="text-align:center;">Loading ...</p></body></html>'
        )

        self.AddLog("Initializing, please wait...")

        # Handle when current game has been removed.
        if self.game not in games_sorted.get_games_sorted_by_priority():
            self.game = games_sorted.get_sorted_games_list(
                program_config.games_sorting_mode)[0]
            await self.InitialSetup()
            return

        self.loadAllSavedAccounts()
        self.set_current_account_placeholder_password()

        self.set_banner_image()
        self.setWindowTitle(
            f"{__about__.__title__} - {self.game.name}")

        # Setup btnSwitchGame for current game
        self.setup_switch_game_button()

        if not self.setup_game():
            return

        self.resetFocus()

        async with trio.open_nursery() as nursery:
            nursery.start_soon(self.game_initial_network_setup)

            if not self.checked_for_program_update:
                nursery.start_soon(check_for_update)
        self.checked_for_program_update = True      

    async def game_initial_network_setup(self):
        await self.get_game_services_info(self.game)
        if not self.game_services_info:
            return
        self.load_worlds_list(self.game_services_info)
        await self.get_game_launcher_config(
            self.game_services_info.launcher_config_url)
        # Enable UI elements that rely on what's been loaded.
        self.ui.actionPatch.setEnabled(True)
        self.ui.actionPatch.setVisible(True)
        self.ui.btnLogin.setEnabled(True)
        self.ui.chkSaveSettings.setEnabled(True)
        self.ui.chkSavePassword.setEnabled(True)
        self.ui.cboAccount.setEnabled(True)
        self.ui.txtPassword.setEnabled(True)

        await self.load_newsfeed()

        self.ui.btnOptions.setEnabled(True)
        self.ui.btnSwitchGame.setEnabled(True)

    async def get_game_services_info(self, game: Game) -> GameServicesInfo | None:
        try:
            self.game_services_info = await GameServicesInfo.from_url(
                game.gls_datacenter_service, game.datacenter_game_name)
        except httpx.HTTPError:
            logger.exception("")
            # TODO: load anything else that can be, provide option to retry, and
            # don't lock up the whole UI
            self.AddLog(
                "Network error while fetching game services info.", True)
            return
        except GLSServiceError:
            logger.exception("")
            # TODO Specify how they they can report or even have the report
            # text be something they can click to report the issue.
            self.AddLog(
                "Non-network error with GLS datacenter service. Please report "
                "this issue, if it continues.", True)
            return

        self.AddLog("Fetched game services info.", False)

    def load_worlds_list(self, game_services_info: GameServicesInfo):
        for world in self.game_services_info.worlds:
            self.ui.cboWorld.addItem(world.name, userData=world)

        self.setCurrentAccountWorld()
        self.AddLog("World list obtained.", False)

    async def get_game_launcher_config(self, game_launcher_config_url: str):
        try:
            self.game_launcher_config = await GameLauncherConfig.from_url(
                game_launcher_config_url)
            self.AddLog("Game launcher configuration read", False)
            return
        except httpx.HTTPError:
            logger.exception("")
            self.AddLog(
                "Network error while retrieving game launcher config.", True)
            return
        except GameLauncherConfigParseError:
            logger.exception("")
            self.AddLog(
                "Game launcher config has incompatible format. Please report "
                "this issue if using a supported game server", True
            )  # TODO: Easy report
            return

    async def load_newsfeed(self):
        ui_locale = program_config.get_ui_locale(self.game)
        newsfeed_url = (self.game.newsfeed or
                        self.game_launcher_config.get_newfeed_url(
                            ui_locale))
        try:
            self.ui.txtFeed.setHtml(await newsfeed_url_to_html(
                    newsfeed_url,
                    ui_locale.babel_locale))
        except httpx.HTTPError:
            self.AddLog(
                "Network error while downloading newsfeed", True)
            logger.exception("Network error while downloading newsfeed.")

    def ClearLog(self):
        self.ui.txtStatus.setText("")

    def ClearNews(self):
        self.ui.txtFeed.setText("")

    def AddLog(self, message: str, is_error: bool = False) -> None:
        for line in message.splitlines():
            # Make line red if it is an error
            if line.startswith("[E") or is_error:
                logger.error(line)

                line = '<font color="red">' + message + "</font>"

                # Enable buttons that won't normally get re-enabled if
                # MainWindowThread gets frozen.
                self.ui.btnOptions.setEnabled(True)
                self.ui.btnSwitchGame.setEnabled(True)
            else:
                logger.info(line)

            self.ui.txtStatus.append(line)


async def check_for_update():
    """Notifies user if their copy of OneLauncher is out of date"""
    current_version = parse_version(__about__.__version__)
    repository_url = __about__.__project_url__
    if "github.com" not in repository_url.lower():
        logger.warning(
            "Repository URL set in Information.py is not "
            "at github.com. The system for update notifications"
            " only supports this site."
        )
        return

    latest_release_template = (
        "https://api.github.com/repos/{user_and_repo}/releases/latest"
    )
    latest_release_url = latest_release_template.format(
        user_and_repo=repository_url.lower().split("github.com")[
            1].strip("/")
    )

    try:
        response = await get_httpx_client(latest_release_url).get(
            latest_release_url)
        response.raise_for_status()
    except (httpx.HTTPError):
        logger.exception(f"Network error while checking for "
                         f"{__about__.__title__} updates")
        return
    release_dictionary = response.json()

    release_version = parse_version(release_dictionary["tag_name"])

    if release_version > current_version:
        url = release_dictionary["html_url"]
        name = release_dictionary["name"]
        description = release_dictionary["body"]

        messageBox = QtWidgets.QMessageBox()
        messageBox.setWindowFlag(QtCore.Qt.WindowType.FramelessWindowHint)
        messageBox.setIcon(QtWidgets.QMessageBox.Icon.Information)
        messageBox.setStandardButtons(messageBox.StandardButton.Ok)

        centered_href = (
            f'<html><head/><body><p align="center"><a href="{url}">'
            f'<span>{name}</span></a></p></body></html>'
        )
        messageBox.setInformativeText(
            f"There is a new version of {__about__.__title__} available! {centered_href}"
        )
        messageBox.setDetailedText(description)
        show_message_box_details_as_markdown(messageBox)
        messageBox.exec()
    else:
        logger.info(f"{__about__.__title__} is up to date.")

logger = logging.getLogger("main")
