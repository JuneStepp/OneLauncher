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
import contextlib
import logging
from pathlib import Path
from typing import List, Optional

from PySide6 import QtCore, QtGui, QtWidgets
from requests.exceptions import RequestException
from xmlschema import XMLSchemaValidationError

import onelauncher
from onelauncher.addon_manager import AddonManager
from onelauncher.config.program_config import program_config
from onelauncher.game import Game
from onelauncher.game_account import GameAccount
from onelauncher.network import login_account
from onelauncher.network.game_launcher_config import (
    GameLauncherConfig, GameLauncherConfigParseError)
from onelauncher.network.game_newsfeed import newsfeed_url_to_html
from onelauncher.network.game_services_info import GameServicesInfo
from onelauncher.network.soap import GLSServiceError
from onelauncher.network.world import World, WorldUnavailableError
from onelauncher.network.world_login_queue import (
    JoinWorldQueueFailedError, WorldLoginQueue, WorldQueueResultXMLParseError)
from onelauncher.patch_game_window import PatchWindow
from onelauncher.resources import get_resource
from onelauncher.config.games_config import games_config
from onelauncher.settings_window import SettingsWindow
from onelauncher.ui.about_uic import Ui_dlgAbout
from onelauncher.ui.main_uic import Ui_winMain
from onelauncher.ui.select_subscription_uic import Ui_dlgSelectSubscription
from onelauncher.ui.start_game_window import StartGame
from onelauncher.ui_resources import icon_font
from onelauncher.utilities import check_if_valid_game_folder


class MainWindow(QtWidgets.QMainWindow):
    # Make signals for communicating with MainWindowThread
    ReturnLog = QtCore.Signal(str, bool)
    return_game_services_info = QtCore.Signal(GameServicesInfo)
    return_game_launcher_config = QtCore.Signal(GameLauncherConfig)
    return_newsfeed = QtCore.Signal(str)

    def __init__(self):
        super(MainWindow, self).__init__(None, QtCore.Qt.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, on=True)

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
        self.ui.btnSwitchGame.clicked.connect(self.btnSwitchGameClicked)

        self.ui.cboAccount.lineEdit().setClearButtonEnabled(True)
        # Accounts combo box item selection signal
        self.ui.cboAccount.currentIndexChanged.connect(
            self.accounts_index_changed)
        self.ui.cboAccount.lineEdit().textEdited.connect(self.user_edited_account_name)

        # Pressing enter in password box acts like pressing login button
        self.ui.txtPassword.returnPressed.connect(self.btnLoginClicked)

        self.connectMainWindowThreadSignals()

        self.setupMousePropagation()

        self.InitialSetup()

    def run(self):
        self.show()

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
        self.ui.btnOptions.clicked.connect(self.btnOptionsSelected)

        self.ui.btnOptions.setFont(icon_font)
        self.ui.btnOptions.setText("\uf013")

    def setupBtnAddonManager(self):
        self.ui.btnAddonManager.clicked.connect(
            self.btnAddonManagerSelected)

        self.ui.btnAddonManager.setFont(icon_font)
        self.ui.btnAddonManager.setText("\uf055")

    def setupBtnLoginMenu(self):
        """Sets up signals and context menu for btnLoginMenu"""
        self.ui.btnLogin.clicked.connect(self.btnLoginClicked)

        # Setup context menu
        self.ui.btnLoginMenu = QtWidgets.QMenu()
        self.ui.btnLoginMenu.addAction(self.ui.actionPatch)
        self.ui.actionPatch.triggered.connect(self.actionPatchSelected)
        self.ui.btnLogin.setMenu(self.ui.btnLoginMenu)

    def setup_switch_game_button(self):
        """Set icon and dropdown options of switch game button according to current game"""
        if games_config.current_game.game_type == "DDO":
            self.ui.btnSwitchGame.setIcon(
                QtGui.QIcon(
                    str(
                        get_resource(
                            Path("images/LOTROSwitchIcon.png"),
                            program_config.get_ui_locale(
                                games_config.current_game)))))

            games = games_config.ddo_sorting_modes[program_config.games_sorting_mode].copy(
            )
        else:
            self.ui.btnSwitchGame.setIcon(
                QtGui.QIcon(
                    str(
                        get_resource(
                            Path("images/DDOSwitchIcon.png"),
                            program_config.get_ui_locale(
                                games_config.current_game)))))

            games = games_config.lotro_sorting_modes[program_config.games_sorting_mode].copy(
            )
        # There is no need to show an action for the currently active game
        games.remove(games_config.current_game)

        menu = QtWidgets.QMenu()
        menu.triggered.connect(self.game_switch_action_triggered)
        for game in games:
            action = QtGui.QAction(game.name, self)
            action.setData(game)
            menu.addAction(action)
        self.ui.btnSwitchGame.setMenu(menu)
        # Needed for menu to show up for some reason
        self.ui.btnSwitchGame.menu()

    def connectMainWindowThreadSignals(self):
        """Connects function signals for communicating with MainWindowThread."""
        self.ReturnLog.connect(self.AddLog)
        self.return_game_services_info.connect(self.get_game_services_info)
        self.return_game_launcher_config.connect(self.get_game_launcher_config)
        self.return_newsfeed.connect(self.get_newsfeed)

    def btnAboutSelected(self):
        dlgAbout = QtWidgets.QDialog(self, QtCore.Qt.Popup)

        ui = Ui_dlgAbout()
        ui.setupUi(dlgAbout)

        ui.lblDescription.setText(onelauncher.__description__)
        ui.lblRepoWebsite.setText(f"<a href='{onelauncher.__project_url__}'>"
                                  f"{onelauncher.__project_url__}</a>")
        ui.lblCopyright.setText(onelauncher.__copyright__)
        ui.lblVersion.setText(
            "<b>Version:</b> " + onelauncher.__version__)
        ui.lblCopyrightHistory.setText(onelauncher.__copyright_history__)

        dlgAbout.exec()
        self.resetFocus()

    def actionPatchSelected(self):
        winPatch = PatchWindow(self.game_services_info.patch_server)
        winPatch.Run()
        self.resetFocus()

    def btnOptionsSelected(self):
        winSettings = SettingsWindow(games_config.current_game)
        winSettings.accepted.connect(self.InitialSetup)
        winSettings.open()

    def btnAddonManagerSelected(self):
        winAddonManager = AddonManager()
        winAddonManager.Run()
        games_config.save()

        self.resetFocus()

    def btnSwitchGameClicked(self):
        if games_config.current_game.game_type == "DDO":
            games_config.current_game = games_config.lotro_sorting_modes[
                program_config.games_sorting_mode][0]
        else:
            games_config.current_game = games_config.ddo_sorting_modes[
                program_config.games_sorting_mode][0]
        self.InitialSetup()

    def game_switch_action_triggered(self, action: QtGui.QAction):
        games_config.current_game = action.data()
        self.InitialSetup()

    def btnLoginClicked(self):
        if (
            self.ui.cboAccount.currentText() == ""
            or (self.ui.txtPassword.text() == "" and
                self.ui.txtPassword.placeholderText() == "")
        ):
            self.AddLog(
                '<font color="Khaki">Please enter account name and password</font>'
            )
            return

        self.AuthAccount()

    def save_settings(self):
        program_config.save_accounts = self.ui.chkSaveSettings.isChecked()
        program_config.save_accounts_passwords = self.ui.chkSavePassword.isChecked()

        program_config.save()
        games_config.save()

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

    def loadAllSavedAccounts(self):
        self.ui.cboAccount.clear()
        self.ui.cboAccount.setCurrentText("")

        if program_config.save_accounts is False:
            games_config.current_game.accounts = {}
            return

        accounts = list(games_config.current_game.accounts.values())
        if not accounts:
            return

        # Accounts are read backwards, so they
        # are in order of most recentally played
        for account in accounts[::-1]:
            self.ui.cboAccount.addItem(account.username, userData=account)
        self.ui.cboAccount.setCurrentIndex(0)

    def get_current_game_account(self) -> GameAccount:
        if type(self.ui.cboAccount.currentData()) == GameAccount:
            return self.ui.cboAccount.currentData()

        current_world: World = self.ui.cboWorld.currentData()
        current_account = GameAccount(
            self.ui.cboAccount.currentText(),
            games_config.current_game.uuid,
            current_world.name)
        self.ui.cboAccount.setItemData(
            self.ui.cboAccount.currentIndex(), current_account)

        return current_account

    def setCurrentAccountWorld(self):
        account = self.get_current_game_account()
        self.ui.cboWorld.setCurrentText(account.last_used_world_name)

    def set_current_account_placeholder_password(self):
        if not program_config.save_accounts_passwords:
            self.ui.txtPassword.setFocus()
            return

        account = self.get_current_game_account()
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
            self, QtCore.Qt.FramelessWindowHint)
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

    def AuthAccount(self):
        self.AddLog("Checking account details...")

        # Force a small display to ensure message above is displayed
        # as program can look like it is not responding while validating
        for _ in range(4):
            QtCore.QCoreApplication.instance().processEvents()

        current_account = self.get_current_game_account()

        try:
            self.login_response = login_account.login_account(
                self.game_services_info.auth_server,
                self.ui.cboAccount.currentText(),
                self.ui.txtPassword.text() or current_account.password,
            )
        except login_account.WrongUsernameOrPasswordError:
            self.AddLog("Username or password is incorrect", True)
            return
        except RequestException:
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
            # Account is deleted first, because accounts are in order of
            # the most recently played at the end.
            with contextlib.suppress(KeyError):
                del games_config.current_game.accounts[current_account.username]

            games_config.current_game.accounts[current_account.username] = current_account

            current_world: World = self.ui.cboWorld.currentData()
            current_account.last_used_world_name = current_world.name

            if self.ui.chkSavePassword.isChecked():
                if self.ui.txtPassword.text():
                    current_account.password = self.ui.txtPassword.text()
            else:
                current_account.delete_password()

            self.loadAllSavedAccounts()

        game_subscriptions = self.login_response.get_game_subscriptions(
            games_config.current_game.datacenter_game_name)
        if len(game_subscriptions) > 1:
            subscription = self.get_game_subscription_selection(
                current_account)
            if subscription is None:
                return
        else:
            subscription = game_subscriptions[0]
            account_number = subscription.name
        current_account.last_used_subscription_name = subscription.name

        self.save_settings()

        selected_world: World = self.ui.cboWorld.currentData()

        try:
            selected_world_status = selected_world.get_status()
        except RequestException:
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
            self.start_game(account_number)
        else:
            self.EnterWorldQueue(
                selected_world_status.queue_url, account_number)

    def start_game(self, account_number: str):
        world: World = self.ui.cboWorld.currentData()
        game = StartGame(
            games_config.current_game,
            self.game_launcher_config,
            world,
            account_number,
            self.login_response.session_ticket,
        )
        game.start_game()

    def EnterWorldQueue(self, queueURL, account_number):
        world_login_queue = WorldLoginQueue(
            self.game_launcher_config.login_queue_url,
            self.game_launcher_config.login_queue_params_template,
            account_number,
            self.login_response.session_ticket,
            queueURL)
        while True:
            try:
                world_queue_result = world_login_queue.join_queue()
            except RequestException:
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

        self.start_game(account_number)

    def set_banner_image(self):
        ui_locale = program_config.get_ui_locale(games_config.current_game)
        game_dir_banner_override_path = games_config.current_game.game_directory / \
            ui_locale.lang_tag.split("-")[0] / "banner.png"
        if game_dir_banner_override_path.exists():
            banner_pixmap = QtGui.QPixmap(str(game_dir_banner_override_path))
        else:
            banner_pixmap = QtGui.QPixmap(str(get_resource(Path(
                f"images/{games_config.current_game.game_type}_banner.png"), ui_locale)))

        banner_pixmap = banner_pixmap.scaledToHeight(self.ui.imgMain.height())
        self.ui.imgMain.setPixmap(banner_pixmap)

    def check_game_dir(self) -> bool:
        if not games_config.current_game.game_directory.exists():
            self.AddLog("[E13] Game directory not found")
            return False

        if not check_if_valid_game_folder(
                games_config.current_game.game_directory,
                games_config.current_game.game_type):
            self.AddLog("The game directory is not valid.", is_error=True)
            return False

        if not (
                games_config.current_game.game_directory /
                f"client_local_{games_config.current_game.locale.game_language_name}.dat").exists():
            self.AddLog(
                "[E20] There is no game language data for "
                f"{games_config.current_game.locale.display_name} installed "
                f"You may have to select {games_config.current_game.locale.display_name}"
                " in the normal game launcher and wait for the data to download."
                " The normal game launcher can be opened from the settings menu.")
            return False

        return True

    def InitialSetup(self):
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

        self.loadAllSavedAccounts()
        self.set_current_account_placeholder_password()

        self.set_banner_image()
        self.setWindowTitle(
            f"{onelauncher.__title__} - {games_config.current_game.name}")

        # Setup btnSwitchGame for current game
        self.setup_switch_game_button()

        if not self.check_game_dir():
            return

        self.resetFocus()

        self.configThread = MainWindowThread()
        self.configThread.SetUp(
            self.ReturnLog,
            self.return_game_services_info,
            self.return_game_launcher_config,
            self.return_newsfeed
        )
        self.configThread.start()

    def get_game_services_info(self, game_services_info: GameServicesInfo):
        self.game_services_info = game_services_info

        for world in self.game_services_info.worlds:
            self.ui.cboWorld.addItem(world.name, userData=world)

        self.setCurrentAccountWorld()

    def get_game_launcher_config(
            self, game_launcher_config: GameLauncherConfig):
        self.game_launcher_config = game_launcher_config

        self.ui.actionPatch.setEnabled(True)
        self.ui.actionPatch.setVisible(True)
        self.ui.btnLogin.setEnabled(True)
        self.ui.chkSaveSettings.setEnabled(True)
        self.ui.chkSavePassword.setEnabled(True)
        self.ui.cboAccount.setEnabled(True)
        self.ui.txtPassword.setEnabled(True)

    def get_newsfeed(self, newsfeed: str):
        self.ui.txtFeed.setHtml(newsfeed)

        self.configThreadFinished()

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

    def configThreadFinished(self) -> None:
        self.ui.btnOptions.setEnabled(True)
        self.ui.btnSwitchGame.setEnabled(True)


class MainWindowThread(QtCore.QThread):
    def SetUp(
        self,
        ReturnLog: QtCore.Signal,
        return_game_services_info: QtCore.Signal,
        return_game_launcher_config: QtCore.Signal,
        return_newsfeed: QtCore.Signal,
    ):
        # First argument is string. Second is bool representing if message is
        # error or not
        self.ReturnLog = ReturnLog
        self.return_game_services_info = return_game_services_info
        self.return_game_launcher_config = return_game_launcher_config
        self.return_newsfeed = return_newsfeed

    def run(self):
        self.access_game_services_info(games_config.current_game)

    def access_game_services_info(self, game: Game):
        try:
            self.game_services_info = GameServicesInfo.from_url(
                game.gls_datacenter_service, game.datacenter_game_name)
        except RequestException:
            logger.exception("")
            # TODO: load anything else that can be, provide option to retry, and
            # don't lock up the whole UI
            self.ReturnLog.emit(
                "Network error while fetching game services info.", True)
            return
        except GLSServiceError:
            logger.exception("")
            # TODO Specify how they they can report or even have the report
            # text be something they can click to report the issue.
            self.ReturnLog.emit(
                "Non-network error with GLS datacenter service. Please report "
                "this issue, if it continues.", True)
            return

        self.ReturnLog.emit("Fetched game services info.", False)
        self.return_game_services_info.emit(self.game_services_info)
        self.ReturnLog.emit("World list obtained.", False)

        self.get_game_launcher_config(
            self.game_services_info.launcher_config_url)

    def get_game_launcher_config(self, game_launcher_config_url: str):
        try:
            self.game_launcher_config = GameLauncherConfig.from_url(
                game_launcher_config_url)
        except RequestException:
            logger.exception("")
            self.ReturnLog.emit(
                "Network error while retrieving game launcher config.", True)
            return
        except GameLauncherConfigParseError:
            logger.exception("")
            self.ReturnLog.emit(
                "Game launcher config has incompatible format. Please report "
                "this issue if using a supported game server", True
            )  # TODO: Easy report
            return

        self.ReturnLog.emit("Game launcher configuration read", False)
        self.return_game_launcher_config.emit(self.game_launcher_config)

        self.get_newsfeed()

    def get_newsfeed(self):
        ui_locale = program_config.get_ui_locale(games_config.current_game)
        newsfeed_url = (games_config.current_game.newsfeed or
                        self.game_launcher_config.get_newfeed_url(
                            ui_locale))
        try:
            self.return_newsfeed.emit(
                newsfeed_url_to_html(
                    newsfeed_url,
                    ui_locale.babel_locale))
        except RequestException:
            self.ReturnLog.emit(
                "Network error while downloading newsfeed", True)
            logger.exception("Network error while downloading newsfeed.")


logger = logging.getLogger("main")
