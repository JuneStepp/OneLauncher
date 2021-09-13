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
import logging
import os
# For setting global timeout used by urllib
import socket
import sys
import urllib
from json import loads as jsonLoads
from pathlib import Path
from platform import platform
from typing import List

import defusedxml.minidom
import xml
import keyring
from pkg_resources import parse_version
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtUiTools import QUiLoader

import onelauncher
from onelauncher import settings, resources, logger, game_settings, program_settings
from onelauncher.ui_utilities import show_message_box_details_as_markdown
from onelauncher.addon_manager import AddonManager
from onelauncher.utilities import (AuthenticateUser, BaseConfig,
                                   GetText,
                                   GLSDataCenter, JoinWorldQueue,
                                   World, WorldQueueConfig,
                                   checkForCertificates)
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
        self.ui.btnSwitchGame.clicked.connect(self.btnSwitchGameClicked)

        # Accounts combo box item selection signal
        self.ui.cboAccount.textActivated.connect(self.cboAccountChanged)

        # Pressing enter in password box acts like pressing login button
        self.ui.txtPassword.returnPressed.connect(self.btnLoginClicked)

        self.connectMainWindowThreadSignals()

        self.setupMousePropagation()

        self.configureKeyring()

        # Set default timeout used by urllib
        socket.setdefaulttimeout(6)

        self.InitialSetup(first_setup=True)

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

    def configureKeyring(self):
        """
        Sets the propper keyring backend for the used OS. This isn't
        automatically detected correctly with Nuitka
        """
        if settings.usingWindows:
            from keyring.backends import Windows
            keyring.set_keyring(Windows.WinVaultKeyring())
        elif settings.usingMac:
            from keyring.backends import OS_X
            keyring.set_keyring(OS_X.Keyring())
        else:
            from keyring.backends import SecretService
            keyring.set_keyring(SecretService.Keyring())

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

    def setCurrentAccountWorld(self):
        account: settings.Account = self.ui.cboAccount.currentData()
        if type(account) != settings.Account:
            return

        self.ui.cboWorld.setCurrentText(account.last_used_world_name)

    def get_current_keyring_username(self) -> str:
        return str(game_settings.current_game.uuid) + \
            self.ui.cboAccount.currentText()

    def setCurrentAccountPassword(self):
        keyring_username = self.get_current_keyring_username()

        if not program_settings.save_accounts_passwords:
            self.ui.txtPassword.setFocus()
            return

        self.ui.txtPassword.setText(keyring.get_password(
            onelauncher.__title__, keyring_username) or "")

    def AuthAccount(self):
        self.AddLog("Checking account details...")

        # Force a small display to ensure message above is displayed
        # as program can look like it is not responding while validating
        for _ in range(4):
            qApp.processEvents()

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

            if self.ui.chkSaveSettings.isChecked():
                if type(self.ui.cboAccount.currentData()) == settings.Account:
                    current_account = self.ui.cboAccount.currentData()
                else:
                    current_account = settings.Account(
                        self.ui.cboAccount.currentText(), self.ui.cboWorld.currentText())
                    self.ui.cboAccount.setItemData(
                        self.ui.cboAccount.currentIndex(), current_account)

                # Account is deleted first, because accounts are in order of
                # the most recently played at the end.
                try:
                    del game_settings.current_game.accounts[current_account.name]
                except KeyError:
                    pass
                game_settings.current_game.accounts[current_account.name] = current_account

                self.save_settings()

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

            if len(self.account.gameList) > 1:
                choose_account_dialog = QtWidgets.QDialog(self)
                ui = Ui_dlgChooseAccount()
                ui.setupUi(choose_account_dialog)

                ui.lblMessage.setText(
                    "Multiple game accounts found\n\nPlease select the required game"
                )

                for game in self.account.gameList:
                    ui.comboBox.addItem(game.description)

                if choose_account_dialog.exec() == QtWidgets.QDialog.Accepted:
                    self.accNumber = self.account.gameList[
                        ui.comboBox.currentIndex()
                    ].name
                    self.resetFocus()
                else:
                    self.resetFocus()
                    self.AddLog("No game selected - aborting")
                    return
            else:
                self.accNumber = self.account.gameList[0].name

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

    def checkForUpdate(self):
        """Notifies user if their copy of OneLauncher is out of date"""
        current_version = parse_version(onelauncher.__version__)
        repository_url = onelauncher.__project_url__
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
            with urllib.request.urlopen(latest_release_url, timeout=2) as response:
                release_dictionary = jsonLoads(response.read())
        except (urllib.error.URLError, urllib.error.HTTPError) as error:
            self.AddLog(
                f"[E18] Error checking for {onelauncher.__title__} updates.")
            logger.error(error.reason, exc_info=True)
            return

        release_version = parse_version(release_dictionary["tag_name"])

        if release_version > current_version:
            url = release_dictionary["html_url"]
            name = release_dictionary["name"]
            description = release_dictionary["body"]

            messageBox = QtWidgets.QMessageBox(self)
            messageBox.setWindowFlag(QtCore.Qt.FramelessWindowHint)
            messageBox.setIcon(QtWidgets.QMessageBox.Information)
            messageBox.setStandardButtons(messageBox.Ok)

            centered_href = (
                f'<html><head/><body><p align="center"><a href="{url}">'
                f'<span>{name}</span></a></p></body></html>'
            )
            messageBox.setInformativeText(
                f"There is a new version of {onelauncher.__title__} available! {centered_href}"
            )
            messageBox.setDetailedText(description)
            show_message_box_details_as_markdown(messageBox)
            messageBox.exec()
        else:
            self.AddLog(f"{onelauncher.__title__} is up to date.")

    def getLaunchArgument(self, key: str, accepted_values: List[str]):
        launch_arguments = sys.argv
        try:
            modifier_index = launch_arguments.index(key)
        except ValueError:
            pass
        else:
            try:
                value = launch_arguments[modifier_index + 1]
            except IndexError:
                pass
            else:
                if value in accepted_values:
                    return value

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

    def InitialSetup(self, first_setup=False):
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

        if first_setup:
            self.checkForUpdate()

            # Launch into specific game if specified in launch argument
            game = self.getLaunchArgument("--game",
                                          ["LOTRO", "LOTRO.Test", "DDO", "DDO.Test"])
            if game:
                self.currentGame = game

        sslContext = checkForCertificates()

        # Set news feed to say "Loading ..." until it is replaced by the news.
        self.ui.txtFeed.setHtml(
            '<html><body><p style="text-align:center;">Loading ...</p></body></html>'
        )

        self.AddLog("Initializing, please wait...")

        self.loadAllSavedAccounts()
        self.setCurrentAccountPassword()

        # Set specific client language if specified in launch argument
        # This is an advanced feature, so there are no checks to make
        # sure the specified language is installed. The game will
        # give an error if that is the case anyways.
        language = self.getLaunchArgument("--language", ["EN", "DE", "FR"])
        if language:
            self.settings.language = language

        self.set_banner_image()
        self.setWindowTitle(
            f"{onelauncher.__title__} - {game_settings.current_game.name}")

        # Setup btnSwitchGame for current game
        self.setup_switch_game_button()

        if not game_settings.current_game.game_directory.exists():
            self.AddLog("[E13] Game Directory not found")
            return

        if not (game_settings.current_game.game_directory /
                f"client_local_{game_settings.current_game.locale.game_language_name}.dat").exists():
            self.AddLog("[E20] There is no game language data for "
                        f"{game_settings.current_game.locale.display_name} installed "
                        f"You may have to select {game_settings.current_game.locale.display_name}"
                        " in the normal game launcher and wait for the data to download."
                        " The normal game launcher can be opened from the settings menu.")

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

    def AddLog(self, message: str) -> None:
        for line in message.splitlines():
            # Make line red if it is an error
            if line.startswith("[E"):
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

        if self.worldQueueConfig.message:
            self.ReturnLog.emit(self.worldQueueConfig.message)

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
