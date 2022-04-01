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
# For setting global timeout used by urllib
import socket
import urllib
from pathlib import Path
import logging
from typing import Optional

import defusedxml.minidom
import xml
import keyring
from PySide6 import QtCore, QtGui, QtWidgets

import onelauncher
from onelauncher import settings
from onelauncher.settings import game_settings, program_settings
from onelauncher.addon_manager import AddonManager
from onelauncher.utilities import (AuthenticateUser, BaseConfig,
                                   GetText,
                                   GLSDataCenter, JoinWorldQueue,
                                   World, WorldQueueConfig,
                                   checkForCertificates, check_if_valid_game_folder)
from onelauncher.patch_game_window import PatchWindow
from onelauncher.settings_window import SettingsWindow
from onelauncher.start_game_window import StartGame
from onelauncher.resources import get_resource
from onelauncher.ui_resources import icon_font
from onelauncher.ui.main_uic import Ui_winMain
from onelauncher.ui.about_uic import Ui_dlgAbout
from onelauncher.ui.select_account_uic import Ui_dlgChooseAccount


class MainWindow(QtWidgets.QMainWindow):
    # Make signals for communicating with MainWindowThread
    ReturnLog = QtCore.Signal(str)
    ReturnBaseConfig = QtCore.Signal(BaseConfig)
    ReturnGLSDataCenter = QtCore.Signal(GLSDataCenter)
    ReturnWorldQueueConfig = QtCore.Signal(WorldQueueConfig)
    ReturnNews = QtCore.Signal(str)

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
        self.setup_save_accounts_dropdown()
        self.ui.btnSwitchGame.clicked.connect(self.btnSwitchGameClicked)

        # Accounts combo box item selection signal
        self.ui.cboAccount.textActivated.connect(self.cboAccountChanged)

        # Pressing enter in password box acts like pressing login button
        self.ui.txtPassword.returnPressed.connect(self.btnLoginClicked)

        self.connectMainWindowThreadSignals()

        self.setupMousePropagation()

        # Set default timeout used by urllib
        socket.setdefaulttimeout(6)

        self.InitialSetup()

    def run(self):
        self.show()

    def resetFocus(self):
        if self.ui.cboAccount.currentText() == "":
            self.ui.cboAccount.setFocus()
        elif self.ui.txtPassword.text() == "":
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

    def setup_save_accounts_dropdown(self):
        self.ui.saveSettingsMenu = QtWidgets.QMenu()
        self.ui.saveSettingsMenu.addAction(self.ui.actionForgetSubaccountSelection)
        self.ui.actionForgetSubaccountSelection.triggered.connect(self.forget_subaccount_selection)
        self.ui.saveSettingsToolButton.setMenu(self.ui.saveSettingsMenu)

    def forget_subaccount_selection(self):
        self.ui.saveSettingsToolButton.setVisible(False)
        self.ui.cboAccount.currentData().save_subaccount_selection = False

        try:
            keyring.delete_password(
                onelauncher.__title__,
                self.get_current_keyring_subaccount_username(),
            )
        except keyring.errors.PasswordDeleteError:
            pass


    def setup_switch_game_button(self):
        """Set icon and dropdown options of switch game button according to current game"""
        if game_settings.current_game.game_type == "DDO":
            self.ui.btnSwitchGame.setIcon(
                QtGui.QIcon(
                    str(get_resource(
                        Path("images/LOTROSwitchIcon.png"), program_settings.ui_locale))
                )
            )

            games = game_settings.ddo_sorting_modes[program_settings.games_sorting_mode].copy(
            )
        else:
            self.ui.btnSwitchGame.setIcon(
                QtGui.QIcon(
                    str(get_resource(
                        Path("images/DDOSwitchIcon.png"), program_settings.ui_locale))
                )
            )

            games = game_settings.lotro_sorting_modes[program_settings.games_sorting_mode].copy(
            )
        # There is no need to show an action for the currently active game
        games.remove(game_settings.current_game)

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
        self.ReturnBaseConfig.connect(self.GetBaseConfig)
        self.ReturnGLSDataCenter.connect(self.GetGLSDataCenter)
        self.ReturnWorldQueueConfig.connect(self.GetWorldQueueConfig)
        self.ReturnNews.connect(self.GetNews)


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
        winPatch = PatchWindow(
            self.dataCenter.patchServer,
            self.baseConfig.gameDocumentsDir,
        )

        winPatch.Run()
        self.resetFocus()

    def btnOptionsSelected(self):
        try:
            winSettings = SettingsWindow(game_settings.current_game,
                                         self.worldQueueConfig.gameClientFilename)
        except AttributeError:
            winSettings = SettingsWindow(game_settings.current_game, None)
        winSettings.accepted.connect(self.InitialSetup)
        winSettings.open()

    def btnAddonManagerSelected(self):
        winAddonManager = AddonManager(
            self.baseConfig.gameDocumentsDir,
        )
        winAddonManager.Run()
        game_settings.save()

        self.resetFocus()

    def btnSwitchGameClicked(self):
        if game_settings.current_game.game_type == "DDO":
            game_settings.current_game = game_settings.lotro_sorting_modes[
                program_settings.games_sorting_mode][0]
        else:
            game_settings.current_game = game_settings.ddo_sorting_modes[
                program_settings.games_sorting_mode][0]
        self.InitialSetup()

    def game_switch_action_triggered(self, action: QtGui.QAction):
        game_settings.current_game = action.data()
        self.InitialSetup()

    def btnLoginClicked(self):
        if (
            self.ui.cboAccount.currentText() == ""
            or self.ui.txtPassword.text() == ""
        ):
            self.AddLog(
                '<font color="Khaki">Please enter account name and password</font>'
            )
        else:
            self.AuthAccount()

    def save_settings(self):
        program_settings.save_accounts = self.ui.chkSaveSettings.isChecked()
        program_settings.save_accounts_passwords = self.ui.chkSavePassword.isChecked()

        program_settings.save()
        game_settings.save()

    def cboAccountChanged(self):
        """Sets saved information for selected account."""
        self.setCurrentAccountWorld()
        self.setCurrentAccountPassword()
        self.ui.txtPassword.setFocus()

    def loadAllSavedAccounts(self):
        self.ui.saveSettingsToolButton.setVisible(False)

        if program_settings.save_accounts is False:
            game_settings.current_game.accounts = {}
            return

        accounts = list(game_settings.current_game.accounts.values())
        if not accounts:
            return

        # Accounts are read backwards, so they
        # are in order of most recentally played
        for account in accounts[::-1]:
            self.ui.cboAccount.addItem(account.name, userData=account)

        self.ui.cboAccount.setCurrentText(accounts[-1].name)
        if self.ui.cboAccount.currentData().save_subaccount_selection:
            self.ui.saveSettingsToolButton.setVisible(True)

    def setCurrentAccountWorld(self):
        account: settings.Account = self.ui.cboAccount.currentData()
        if type(account) != settings.Account:
            return

        self.ui.cboWorld.setCurrentText(account.last_used_world_name)

    def get_current_keyring_username(self) -> str:
        return str(game_settings.current_game.uuid) + \
            self.ui.cboAccount.currentText()

    def get_current_keyring_subaccount_username(self) -> str:
        return "SubaccountSelection" + self.get_current_keyring_username()

    def setCurrentAccountPassword(self):
        keyring_username = self.get_current_keyring_username()

        if not program_settings.save_accounts_passwords:
            self.ui.txtPassword.setFocus()
            return

        self.ui.txtPassword.setText(keyring.get_password(
            onelauncher.__title__, keyring_username) or "")

    def get_subaccount_number(self, account: settings.Account) -> Optional[str]:
        if account.save_subaccount_selection:
            account_number = keyring.get_password(
                onelauncher.__title__,
                self.get_current_keyring_subaccount_username(),
            )
            if account_number:
                return account_number

        choose_account_dialog = QtWidgets.QDialog(self, QtCore.Qt.FramelessWindowHint)
        ui = Ui_dlgChooseAccount()
        ui.setupUi(choose_account_dialog)

        for game in self.account.gameList:
            ui.accountsComboBox.addItem(game.description, game.name)

        ui.saveSelectionCheckBox.setChecked(account.save_subaccount_selection)

        if choose_account_dialog.exec() == QtWidgets.QDialog.Accepted:
            account_number = ui.accountsComboBox.currentData()
            account.save_subaccount_selection = ui.saveSelectionCheckBox.isChecked()
            self.ui.saveSettingsToolButton.setVisible(account.save_subaccount_selection)
            # The subaccount selection can only be saved if the account is saved
            if account.save_subaccount_selection:
                self.ui.chkSaveSettings.setChecked(True)

            keyring.set_password(
                onelauncher.__title__,
                self.get_current_keyring_subaccount_username(),
                account_number,
            )
            self.resetFocus()
            return account_number
        else:
            self.resetFocus()
            self.AddLog("No game selected - aborting")
            return None

    def AuthAccount(self):
        self.AddLog("Checking account details...")

        # Force a small display to ensure message above is displayed
        # as program can look like it is not responding while validating
        for _ in range(4):
            QtCore.QCoreApplication.instance().processEvents()

        self.account = AuthenticateUser(
            self.dataCenter.authServer,
            self.ui.cboAccount.currentText(),
            self.ui.txtPassword.text(),
            self.baseConfig.gameName,
        )

        # don't keep password longer in memory than required
        if not self.ui.chkSavePassword.isChecked():
            self.ui.txtPassword.clear()

        if self.account.authSuccess:
            self.AddLog("Account authenticated")

            if type(self.ui.cboAccount.currentData()) == settings.Account:
                    current_account = self.ui.cboAccount.currentData()
            else:
                current_account = settings.Account(
                    self.ui.cboAccount.currentText(), self.ui.cboWorld.currentText())
                self.ui.cboAccount.setItemData(
                    self.ui.cboAccount.currentIndex(), current_account)

            if self.ui.chkSaveSettings.isChecked():
                # Account is deleted first, because accounts are in order of
                # the most recently played at the end.
                try:
                    del game_settings.current_game.accounts[current_account.name]
                except KeyError:
                    pass
                game_settings.current_game.accounts[current_account.name] = current_account

                current_account.last_used_world_name = self.ui.cboWorld.currentText()

                keyring_username = self.get_current_keyring_username()
                if self.ui.chkSavePassword.isChecked():
                    keyring.set_password(
                        onelauncher.__title__,
                        keyring_username,
                        self.ui.txtPassword.text(),
                    )
                else:
                    try:
                        keyring.delete_password(
                            onelauncher.__title__,
                            keyring_username,
                        )
                    except keyring.errors.PasswordDeleteError:
                        pass

            # Handle merged accounts. Some people have multiple accounts attached to one login.
            if len(self.account.gameList) > 1:
                self.accNumber = self.get_subaccount_number(current_account)
                if not self.accNumber:
                    return
            else:
                self.accNumber = self.account.gameList[0].name

            self.save_settings()

            tempWorld: World = self.ui.cboWorld.currentData()
            tempWorld.CheckWorld()

            if tempWorld.worldAvailable:
                self.urlChatServer = tempWorld.urlChatServer
                self.urlLoginServer = tempWorld.loginServer

                if tempWorld.queueURL == "":
                    self.LaunchGame()
                else:
                    self.EnterWorldQueue(tempWorld.queueURL)
            else:
                self.AddLog(
                    "[E10] Error getting world status. You may want to check "
                    "the news feed for a scheduled down time."
                )
        else:
            self.AddLog(self.account.messError)

    def LaunchGame(self):
        game = StartGame(
            self.worldQueueConfig.gameClientFilename,
            game_settings.current_game,
            self.worldQueueConfig.gameClientArgTemplate,
            self.accNumber,
            self.urlLoginServer,
            self.account.ticket,
            self.urlChatServer,
            self.worldQueueConfig.crashreceiver,
            self.worldQueueConfig.DefaultUploadThrottleMbps,
            self.worldQueueConfig.bugurl,
            self.worldQueueConfig.authserverurl,
            self.worldQueueConfig.supporturl,
            self.worldQueueConfig.supportserviceurl,
            self.worldQueueConfig.glsticketlifetime,
            self.ui.cboWorld.currentText(),
            self.ui.cboAccount.currentText(),
            self.baseConfig.gameDocumentsDir,
        )
        game.Run()

    def EnterWorldQueue(self, queueURL):
        self.worldQueue = JoinWorldQueue(
            self.worldQueueConfig.worldQueueParam,
            self.accNumber,
            self.account.ticket,
            queueURL,
            self.worldQueueConfig.worldQueueURL,
        )

        if self.worldQueue.joinSuccess:
            self.AddLog("Joined world queue")

            displayQueueing = True

            while (
                self.worldQueue.number > self.worldQueue.serving
                and self.worldQueue.joinSuccess
            ):
                if displayQueueing:
                    self.AddLog("Currently queueing, please wait...")
                    displayQueueing = False

                self.worldQueue = JoinWorldQueue(
                    self.worldQueueConfig.worldQueueParam,
                    self.accNumber,
                    self.account.ticket,
                    queueURL,
                    self.worldQueueConfig.worldQueueURL,
                )

                if not self.worldQueue.joinSuccess:
                    self.AddLog("[E10] Error getting world status.")

        if self.worldQueue.joinSuccess:
            self.LaunchGame()
        else:
            self.AddLog("[E11] Error joining world queue.")

    def set_banner_image(self):
        game_dir_banner_override_path = game_settings.current_game.game_directory / \
            program_settings.ui_locale.lang_tag.split("-")[0]/"banner.png"
        if game_dir_banner_override_path.exists():
            banner_pixmap = QtGui.QPixmap(str(game_dir_banner_override_path))
        else:
            banner_pixmap = QtGui.QPixmap(str(get_resource(
                Path(f"images/{game_settings.current_game.game_type}_banner.png"), program_settings.ui_locale)))

        banner_pixmap = banner_pixmap.scaledToHeight(self.ui.imgMain.height())
        self.ui.imgMain.setPixmap(banner_pixmap)

    def check_game_dir(self) -> bool:
        if not game_settings.current_game.game_directory.exists():
            self.AddLog("[E13] Game directory not found")
            return False

        if not check_if_valid_game_folder(game_settings.current_game.game_directory, game_settings.current_game.game_type):
            self.AddLog("The game directory is not valid.", is_error=True)
            return False

        if not (game_settings.current_game.game_directory /
                f"client_local_{game_settings.current_game.locale.game_language_name}.dat").exists():
            self.AddLog("[E20] There is no game language data for "
                        f"{game_settings.current_game.locale.display_name} installed "
                        f"You may have to select {game_settings.current_game.locale.display_name}"
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

        self.ui.chkSaveSettings.setChecked(program_settings.save_accounts)
        self.ui.chkSavePassword.setChecked(
            program_settings.save_accounts_passwords)

        self.ui.cboAccount.clear()
        self.ui.cboAccount.setCurrentText("")
        self.ui.txtPassword.setText("")
        self.ui.cboWorld.clear()
        self.ClearLog()
        self.ClearNews()

        sslContext = checkForCertificates()

        # Set news feed to say "Loading ..." until it is replaced by the news.
        self.ui.txtFeed.setHtml(
            '<html><body><p style="text-align:center;">Loading ...</p></body></html>'
        )

        self.AddLog("Initializing, please wait...")

        self.loadAllSavedAccounts()
        self.setCurrentAccountPassword()

        self.set_banner_image()
        self.setWindowTitle(
            f"{onelauncher.__title__} - {game_settings.current_game.name}")

        # Setup btnSwitchGame for current game
        self.setup_switch_game_button()

        if not self.check_game_dir():
            return

        self.resetFocus()

        self.configThread = MainWindowThread()
        self.configThread.SetUp(
            self.ReturnLog,
            self.ReturnBaseConfig,
            self.ReturnGLSDataCenter,
            self.ReturnWorldQueueConfig,
            self.ReturnNews,
            sslContext,
        )
        self.configThread.start()

    def GetBaseConfig(self, baseConfig: BaseConfig):
        self.baseConfig = baseConfig

    def GetGLSDataCenter(self, dataCenter: GLSDataCenter):
        self.dataCenter = dataCenter

        for world in self.dataCenter.worldList:
            self.ui.cboWorld.addItem(world.name, userData=world)

        self.setCurrentAccountWorld()

    def GetWorldQueueConfig(self, worldQueueConfig: WorldQueueConfig):
        self.worldQueueConfig = worldQueueConfig

        self.ui.actionPatch.setEnabled(True)
        self.ui.actionPatch.setVisible(True)
        self.ui.btnLogin.setEnabled(True)
        self.ui.chkSaveSettings.setEnabled(True)
        self.ui.chkSavePassword.setEnabled(True)
        self.ui.cboAccount.setEnabled(True)
        self.ui.txtPassword.setEnabled(True)

    def GetNews(self, news: str):
        self.ui.txtFeed.setHtml(news)

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

                # Enable buttons that won't normally get re-enabled if MainWindowThread gets frozen.
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
        ReturnLog,
        ReturnBaseConfig,
        ReturnGLSDataCenter,
        ReturnWorldQueueConfig,
        ReturnNews,
        sslContext,
    ):
        self.ReturnLog = ReturnLog
        self.ReturnBaseConfig = ReturnBaseConfig
        self.ReturnGLSDataCenter = ReturnGLSDataCenter
        self.ReturnWorldQueueConfig = ReturnWorldQueueConfig
        self.ReturnNews = ReturnNews
        self.sslContext = sslContext

    def run(self):
        self.LoadLauncherConfig()

    def LoadLauncherConfig(self):
        self.baseConfig = BaseConfig(game_settings.current_game)

        self.ReturnBaseConfig.emit(self.baseConfig)

        self.AccessGLSDataCenter(
            self.baseConfig.GLSDataCenterService, self.baseConfig.gameName
        )

    def AccessGLSDataCenter(self, urlGLS, gameName):
        self.dataCenter = GLSDataCenter(
            urlGLS, gameName)

        if self.dataCenter.loadSuccess:
            self.ReturnLog.emit("Fetched details from GLS data center.")
            self.ReturnGLSDataCenter.emit(self.dataCenter)
            self.ReturnLog.emit("World list obtained.")

            self.GetWorldQueueConfig(self.dataCenter.launchConfigServer)
        else:
            self.ReturnLog.emit("[E04] Error accessing GLS data center.")

    def GetWorldQueueConfig(self, urlWorldQueueServer: str):
        self.worldQueueConfig = WorldQueueConfig(
            urlWorldQueueServer, game_settings.current_game
        )
        if self.worldQueueConfig.loadSuccess:
            self.ReturnLog.emit("World queue configuration read.")
            self.ReturnWorldQueueConfig.emit(self.worldQueueConfig)

            self.GetNews()
        else:
            self.ReturnLog.emit(
                "[E05] Error getting world queue configuration.")

    def GetNews(self):
        with urllib.request.urlopen(self.worldQueueConfig.newsStyleSheetURL, context=self.sslContext) as xml_feed:
            doc = defusedxml.minidom.parseString(
                xml_feed.read(), forbid_entities=False)

        nodes = doc.getElementsByTagName("div")
        for node in nodes:
            if node.nodeType == node.ELEMENT_NODE and (
                node.attributes.item(0).firstChild.nodeValue
                == "launcherNewsItemDate"
            ):
                timeCode = GetText(node.childNodes).strip()
                timeCode = (
                    timeCode.replace("\t", "").replace(
                        ",", "").replace("-", "")
                )
                if len(timeCode) > 0:
                    timeCode = " %s" % (timeCode)

        links = doc.getElementsByTagName("link")
        for link in links:
            if link.nodeType == link.ELEMENT_NODE:
                href = link.attributes["href"]

        # Ignore broken href (as of 3/30/16) in the style sheet and use Launcher.
        # NewsFeedCSSUrl defined in launcher.config
        href.value = self.worldQueueConfig.newsFeedCSSURL

        HTMLTEMPLATE = '<html><head><link rel="stylesheet" type="text/css" href="'
        HTMLTEMPLATE += href.value
        HTMLTEMPLATE += (
            '"/><base target="_blank"/></head><body><div '
            'class="launcherNewsItemsContainer" style="width:auto">'
        )

        if game_settings.current_game.newsfeed:
            urlNewsFeed = game_settings.current_game.newsfeed
        else:
            urlNewsFeed = self.worldQueueConfig.newsFeedURL.replace(
                "{lang}", program_settings.ui_locale.lang_tag.split("-")[0]
            )

        result = HTMLTEMPLATE

        try:
            with urllib.request.urlopen(urlNewsFeed, context=self.sslContext) as xml_feed:
                try:
                    doc = defusedxml.minidom.parseString(xml_feed.read())
                except xml.parsers.expat.ExpatError:
                    message = "The news feed is invalid. This is normal for the DDO preview client."
                    logger.warning(message)
                    self.ReturnNews.emit(
                        f"<html><body><center>{message}</center></body></html>")
                    return
        except (urllib.error.URLError, urllib.error.HTTPError):
            message = "There was an error downloading the news feed. You may want to check your network connection."
            logger.warning(message)
            self.ReturnNews.emit(
                f"<html><body><center>{message}</center></body></html>")
            return

        items = doc.getElementsByTagName("item")
        for item in items:
            title = ""
            description = ""
            date = ""

            for node in item.childNodes:
                if node.nodeType == node.ELEMENT_NODE:
                    if node.nodeName == "title":
                        title = (
                            '<font color="gold"><div class="launcherNewsItemTitle">%s</div></font>'
                            % (GetText(node.childNodes))
                        )
                    elif node.nodeName == "description":
                        description = (
                            '<div class="launcherNewsItemDescription">%s</div>'
                            % (GetText(node.childNodes))
                        )
                    elif node.nodeName == "pubDate":
                        tempDate = GetText(node.childNodes)
                        displayDate = "%s %s %s %s%s" % (
                            tempDate[8:11],
                            tempDate[5:7],
                            tempDate[12:16],
                            tempDate[17:22],
                            timeCode,
                        )
                        date = (
                            '<small><i><div align="right"class="launcherNewsItemDate">%s</div></i></small>'
                            % (displayDate)
                        )

            result += '<div class="launcherNewsItemContainer">%s%s%s%s</div>' % (
                title,
                date,
                description,
                "<hr>",
            )

        result += "</div></body></html>"

        self.ReturnNews.emit(result)


logger = logging.getLogger("main")
