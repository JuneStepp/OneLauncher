# coding=utf-8
###########################################################################
# Class to handle loading and saving game settings
# for OneLauncher.
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
from pathlib import Path
from sys import platform
from typing import Dict, List, Optional
from uuid import UUID, uuid4
from xml.dom import EMPTY_NAMESPACE
from xml.dom.minidom import Document  # nosec

import defusedxml.minidom
import rtoml
from platformdirs import PlatformDirs
from vkbeautify import xml as prettify_xml

import OneLauncher
from OneLauncher import resources
from OneLauncher.OneLauncherUtils import GetText


def set_os_specific_variables():
    global platform_dirs
    global usingMac
    global usingWindows
    global config_dir
    global documentsDir
    global globalDir
    global settingsCXG
    global settingsCXO
    global directoryCXG
    global directoryCXO
    global macPathCX
    global builtin_prefix_dir

    platform_dirs = PlatformDirs(OneLauncher.__title__, False)
    if os.name == "mac":
        usingMac = True
        usingWindows = False
        documentsDir = Path("~").expanduser()/"Documents"
        globalDir = Path("Application")
        settingsCXG = Path(
            "Library/Application Support/CrossOver Games/Bottles")
        settingsCXO = Path("Library/Application Support/CrossOver/Bottles")
        directoryCXG = Path(
            "CrossOver Games.app/Contents/SharedSupport/CrossOverGames/bin/"
        )
        directoryCXO = Path(
            "CrossOver.app/Contents/SharedSupport/CrossOver/bin/")
        macPathCX = "" if os.environ.get(
            "CX_ROOT") is None else Path(os.environ.get("CX_ROOT"))
        builtin_prefix_dir = platform_dirs.user_cache_path/"wine/prefix"
    elif os.name == "nt":
        import ctypes.wintypes

        # Get documents folder dynamically since it can be changed on Windows
        CSIDL_PERSONAL = 5       # Value for My Documents
        SHGFP_TYPE_CURRENT = 0   # Get current, not default value

        buffer = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
        ctypes.windll.shell32.SHGetFolderPathW(
            None, CSIDL_PERSONAL, None, SHGFP_TYPE_CURRENT, buffer)

        documentsDir = Path(buffer.value)

        usingMac = False
        usingWindows = True
        globalDir = ""
        settingsCXG = ""
        settingsCXO = ""
        directoryCXG = ""
        directoryCXO = ""
        macPathCX = ""
    else:
        usingMac = False
        usingWindows = False
        documentsDir = Path("~").expanduser()/"Documents"
        globalDir = Path("opt")
        settingsCXG = Path(".cxgames")
        settingsCXO = Path(".cxoffice")
        directoryCXG = Path("cxgames/bin/")
        directoryCXO = Path("cxoffice/bin/")
        macPathCX = ""
        builtin_prefix_dir = platform_dirs.user_cache_path/"wine/prefix"


def make_settings_dirs():
    platform_dirs.user_config_path.mkdir(exist_ok=True, parents=True)
    builtin_prefix_dir.mkdir(exist_ok=True, parents=True)
    (platform_dirs.user_cache_path/"game").mkdir(exist_ok=True, parents=True)
    (platform_dirs.user_data_path/"wine").mkdir(exist_ok=True, parents=True)


class ProgramSettings():
    def __init__(self, config_path: Path = None) -> None:
        if not config_path:
            config_path = platform_dirs.user_config_path / \
                f"{OneLauncher.__title__}.toml"
        self.config_path = config_path

        self.load()

    def load(self):
        # Defaults will be used if the settings file doesn't exist
        if self.config_path.exists():
            settings_dict = rtoml.load(self.config_path)
        else:
            settings_dict = {}

        self.default_locale = resources.Locale(
            settings_dict.get("default_language", "en-US"))
        self.always_use_default_language_for_ui: bool = settings_dict.get(
            "always_use_default_language_for_ui", False)
        self.save_password = settings_dict.get("save_password", False)
        last_used_game = settings_dict.get("last_used_game", None)
        self.last_used_game = UUID(settings_dict.get(
            "last_used_game", None)) if last_used_game else None

    def save(self):
        settings_dict = {"onelauncher_version": OneLauncher.__version__,
                         "default_language": self.default_locale,
                         "always_use_default_language_for_ui": self.always_use_default_language_for_ui,
                         "save_password": self.save_password,
                         "last_used_game": OneLauncher.game_settings.current_game.uuid}

        rtoml.dump(settings_dict, self.config_path, pretty=True)


class Account():
    def __init__(self, name: str, last_used_world: str) -> None:
        self._name = name
        self.last_used_world = last_used_world

    @property
    def name(self):
        """Account name. This is immutable."""
        return self._name


class Game():
    def __init__(self,
                 uuid: UUID,
                 game_type: str,
                 game_directory: Path,
                 locale: resources.Locale,
                 client_type: str,
                 high_res_enabled: bool,
                 patch_client_path: Path,
                 startup_scripts: List[Path],
                 name: str,
                 description: str,
                 newsfeed: str = None,
                 wine_path: Path = None,
                 builtin_wine_prefix_enabled: bool = None,
                 wine_prefix_path: Path = None,
                 wine_debug_level: str = None,
                 accounts: Dict[str, Account] = None,
                 share_accounts_with: UUID = None,
                 ) -> None:
        self.uuid = uuid
        self.game_type = game_type
        self.game_directory = game_directory
        self.locale = locale
        self.client_type = client_type
        self.high_res_enabled = high_res_enabled
        self.patch_client_path = patch_client_path
        self.startup_scripts = startup_scripts
        self.name = name
        self.description = description
        self.newsfeed = newsfeed
        self.wine_path = wine_path
        self.builtin_wine_prefix_enabled = builtin_wine_prefix_enabled
        self.wine_prefix_path = wine_prefix_path
        self.wine_debug_level = wine_debug_level
        self.accounts = accounts
        self.share_accounts_with = share_accounts_with

    @property
    def game_type(self) -> str:
        return self._game_type

    @game_type.setter
    def game_type(self, new_value: str) -> None:
        """LOTRO or DDO"""
        valid_game_types = ["LOTRO", "DDO"]
        if new_value not in valid_game_types:
            raise ValueError(
                f"{new_value} is not a valid game type. Valid types are {valid_game_types}.")

        self._game_type = new_value

    @property
    def client_type(self) -> str:
        return self._client_type

    @client_type.setter
    def client_type(self, new_value: str) -> None:
        """WIN32, WIN32Legacy, or WIN64"""
        valid_client_types = ["WIN32", "WIN32Legacy", "WIN64"]
        if new_value not in valid_client_types:
            raise ValueError(
                f"{new_value} is not a valid client type. Valid types are {valid_client_types}.")

        self._client_type = new_value


class GamesSettings():
    def __init__(self, config_path: Path = None) -> None:
        if not config_path:
            config_path = platform_dirs.user_config_path / \
                "games.toml"
        self.config_path = config_path

        self.games: Dict[UUID, Game] = {}
        self.current_game: Optional[Game] = None

        self.load()

    def get_game_name(self, game_directory: Path) -> str:
        return game_directory.name

    def load(self):
        if not self.config_path.exists():
            return

        settings_dict = rtoml.load(self.config_path)
        if "games" not in settings_dict:
            return
        games_dicts = settings_dict["games"]
        for game_dict in games_dicts:
            uuid = UUID(game_dict["uuid"])
            game_directory = Path(game_dict["game_directory"])
            self.games[uuid] == Game(
                uuid,
                game_dict["game_type"],
                game_directory,
                resources.Locale(game_dict.get("language", str(
                    OneLauncher.program_settings.default_locale))),
                game_dict.get("client_type", "WIN64"),
                game_dict.get("high_res_enabled", True),
                Path(game_dict.get("patch_client_path", "patchclient.dll")),
                [Path(script)
                 for script in game_dict.get("startup_scripts", [])],
                game_dict["info"].get(
                    "name", self.get_game_name(game_directory)),
                game_dict["info"].get("description", ""),
                game_dict["info"].get("newsfeed", None),
                Path(game_dict["wine"].get("wine_path", None)),
                game_dict["wine"].get("builtin_prefix_enabled", True),
                Path(game_dict["wine"].get("prefix_path", None)),
                game_dict["wine"].get("debug_level", None),
                {account["account_name"]: Account(
                    account["account_name"], account["last_used_world"]) for account in game_dict["accounts"]},
                UUID(game_dict.get("share_accounts_with", None)) if game_dict.get(
                    "share_accounts_with", None) else None,
            )

        for game in self.games.values():
            # Replace accounts with ones from game that this one is sharing with
            if game.share_accounts_with:
                game.accounts = self.games[game.share_accounts_with].accounts

    def save(self):
        settings_dict = {}
        for game in self.games.values():
            if usingWindows:
                wine_settings_dict = {}
            else:
                wine_settings_dict = {
                    "wine_path": game.wine_path,
                    "builtin_prefix_enabled": game.builtin_wine_prefix_enabled,
                    "prefix_path": game.wine_prefix_path,
                    "debug_level": game.wine_debug_level,
                }

            games_info_settings_dict = {
                "name": game.name,
                "description": game.description,
                "newsfeed": game.newsfeed,
            }

            if not game.share_accounts_with and game.accounts:
                accounts_settings_list = [
                    {"account_name": account.name,
                        "last_used_world": account.last_used_world}
                    for account in game.accounts.values()]
            else:
                accounts_settings_list = []

            settings_dict["games"].append({
                "uuid": game.uuid,
                "game_type": game.game_type,
                "game_directory": game.game_directory,
                "language": game.locale,
                "client_type": game.client_type,
                "high_res_enabled": game.high_res_enabled,
                "patch_client_path": game.patch_client_path,
                "startup_scripts": game.startup_scripts,
                "share_accounts_with": game.share_accounts_with,
                "wine": wine_settings_dict,
                "games_info": games_info_settings_dict,
                "accounts": accounts_settings_list,
            })

        rtoml.dump(settings_dict, self.config_path, pretty=True)


class Settings:
    def __init__(self):
        self.currentGame = "LOTRO"
        self.settingsFile = platform_dirs.user_config_path / \
            f"{OneLauncher.__title__}.config"
        self.logger = logging.getLogger("main")

    def load_game_settings(self, useGame=None):
        self.highResEnabled = True
        # If None isn't overwritten than it will automatically
        # get set to the first installed language detected.
        self.language = None
        # Key is account name and content is list of details
        # relating to account.
        self.accountsDictionary = {}
        self.wineProg = Path("wine")
        self.wineDebug = "fixme-all"
        self.patchClient = Path("patchclient.dll")
        self.focusAccount = True
        self.builtinPrefixEnabled = True
        self.gameDir = None
        self.client = "WIN64"
        self.winePrefix = None
        self.savePassword = False
        self.startupScripts = []
        success = False

        try:
            if self.settingsFile.exists():
                doc = defusedxml.minidom.parse(str(self.settingsFile))

                if useGame is None:
                    defaultGame = GetText(
                        doc.getElementsByTagName("Default.Game")[0].childNodes
                    )
                else:
                    defaultGame = useGame

                self.currentGame = defaultGame

                nodes = doc.getElementsByTagName(defaultGame)[0].childNodes
                for node in nodes:
                    if node.nodeName == "Wine.Program":
                        self.wineProg = Path(GetText(node.childNodes))
                    elif node.nodeName == "Wine.Debug":
                        self.wineDebug = GetText(node.childNodes)
                    elif node.nodeName == "Wine.Prefix":
                        self.winePrefix = Path(GetText(node.childNodes))
                    elif node.nodeName == "Wine.BuiltinPrefix":
                        self.builtinPrefixEnabled = GetText(
                            node.childNodes) == "True"
                    elif node.nodeName == "HiRes":
                        self.highResEnabled = GetText(
                            node.childNodes) == "True"
                    elif node.nodeName == "Client":
                        self.client = GetText(node.childNodes)
                    elif node.nodeName == "x64Client":
                        self.client = "WIN64" if GetText(
                            node.childNodes) == "True" else "WIN32"
                    elif node.nodeName == "Save.Password":
                        self.savePassword = GetText(node.childNodes) == "True"
                    elif node.nodeName == "Game.Directory":
                        self.gameDir = Path(GetText(node.childNodes))
                    elif node.nodeName == "Language":
                        self.language = GetText(node.childNodes)
                    elif node.nodeName == "PatchClient":
                        self.patchClient = Path(GetText(node.childNodes))
                    elif node.nodeName == "Accounts" and not self.currentGame.endswith(
                        ".Test"
                    ):
                        account_nodes = node.childNodes
                        self.setAccountsSettings(account_nodes)
                    elif (
                        node.nodeName == "StartupScripts"
                        and not self.currentGame.endswith(".Test")
                    ):
                        startup_script_nodes = node.childNodes
                        self.setStartupScriptSettings(startup_script_nodes)

                # Test/preview clients use accounts, save password settings,
                # and startups scripts from normal clients
                if self.currentGame.endswith(".Test"):
                    normalClientNode = self.getNormalClientNode(
                        self.currentGame, doc)
                    if normalClientNode:
                        # Load in accounts and their settings from normal client node
                        accountsNode = normalClientNode.getElementsByTagName(
                            "Accounts")
                        if accountsNode:
                            account_nodes = accountsNode[0].childNodes
                            self.setAccountsSettings(account_nodes)

                        # Load in startup scripts from normal client node
                        startupScriptsNode = normalClientNode.getElementsByTagName(
                            "StartupScripts"
                        )
                        if startupScriptsNode:
                            startup_script_nodes = startupScriptsNode[0].childNodes
                            self.setStartupScriptSettings(startup_script_nodes)

                        # Load in save password setting from normal client node
                        savePasswordNode = normalClientNode.getElementsByTagName(
                            "Save.Password"
                        )
                        if savePasswordNode:
                            self.savePassword = GetText(
                                savePasswordNode[0].childNodes)

                # Disable 64-bit client if it is unavailable
                if (self.client == "WIN64" and not self.checkGameClient64()):
                    self.client = "WIN32"

                # Set wine prefix to built in one if it is enabled
                if self.builtinPrefixEnabled:
                    self.winePrefix = builtin_prefix_dir

                success = True

                if (
                    not self.wineProg.exists()
                    and self.wineProg != Path("wine")
                    and not self.builtinPrefixEnabled
                ):
                    success = "[E16] Wine executable set does not exist"
        except Exception as error:
            self.logger.error(error, exc_info=True)
            success = False

        return success

    def checkGameClient64(self, path=None):
        if path is None:
            path = self.gameDir

        exe = "lotroclient64.exe" if self.currentGame.startswith(
            "LOTRO") else "dndclient64.exe"

        return (path/"x64"/exe).exists()

    def setAccountsSettings(self, account_nodes):
        for account_node in account_nodes:
            account_name = account_node.nodeName
            if account_name != "#text":
                # Create account settings list. The amount of
                # empty strings in the list represent the
                # amount of account settings.
                self.accountsDictionary[account_name] = [""]

                for node in account_node.childNodes:
                    if node.nodeName == "World":
                        self.accountsDictionary[account_name][0] = GetText(
                            node.childNodes
                        )

                self.focusAccount = False

    def setStartupScriptSettings(self, startup_script_nodes):
        for node in startup_script_nodes:
            if node.nodeName == "script":
                self.startupScripts.append(GetText(node.childNodes))

    def getNormalClientNode(self, game, doc, make_if_not_found=False):
        """
        Get normal client node. Will make it if
        make_if_not_found=True and it doesn't exist.
        Normal client as in not the test/preview client
        """
        if not game.endswith(".Test"):
            return
        normalClient = game.split(".")[0]
        normalClientNode = doc.getElementsByTagName(normalClient)
        if normalClientNode:
            normalClientNode = normalClientNode[0]
        else:
            if not make_if_not_found:
                return None

            normalClientNode = doc.createElementNS(
                EMPTY_NAMESPACE, normalClient
            )
            settingsNode = doc.getElementsByTagName("Settings")[0]
            settingsNode.appendChild(normalClientNode)
        return normalClientNode

    def save_game_settings(self, saveAccountDetails=None, savePassword=None, game=None):
        doc = None

        # Check if settings file exists if not create new settings XML
        if self.settingsFile.exists():
            doc = defusedxml.minidom.parse(str(self.settingsFile))
            settingsNode = doc.getElementsByTagName("Settings")
        else:
            doc = Document()
            settingsNode = doc.createElementNS(EMPTY_NAMESPACE, "Settings")
            doc.appendChild(settingsNode)

        current_game = game or self.currentGame
        # Set default game to current game
        defaultGameNode = doc.getElementsByTagName("Default.Game")
        if len(defaultGameNode) > 0:
            defaultGameNode[0].firstChild.nodeValue = current_game
        else:
            defaultGameNode = doc.createElementNS(
                EMPTY_NAMESPACE, "Default.Game")
            defaultGameNode.appendChild(doc.createTextNode(current_game))
            settingsNode.appendChild(defaultGameNode)

        # Remove old game block
        tempNode = doc.getElementsByTagName(current_game)
        if len(tempNode) > 0:
            doc.documentElement.removeChild(tempNode[0])

        # Create new game block
        settingsNode = doc.getElementsByTagName("Settings")[0]
        gameConfigNode = doc.createElementNS(EMPTY_NAMESPACE, current_game)
        settingsNode.appendChild(gameConfigNode)

        # Some settings for test/preview clients are saved in normal client settings
        if current_game.endswith(".Test"):
            normalClientNode = self.getNormalClientNode(
                current_game, doc, make_if_not_found=True)

        if not usingWindows:
            tempNode = doc.createElementNS(EMPTY_NAMESPACE, "Wine.Program")
            tempNode.appendChild(doc.createTextNode("%s" %
                                 (str(self.wineProg))))
            gameConfigNode.appendChild(tempNode)

            tempNode = doc.createElementNS(EMPTY_NAMESPACE, "Wine.Debug")
            tempNode.appendChild(doc.createTextNode("%s" % (self.wineDebug)))
            gameConfigNode.appendChild(tempNode)

            tempNode = doc.createElementNS(
                EMPTY_NAMESPACE, "Wine.BuiltinPrefix")
            tempNode.appendChild(doc.createTextNode(
                "%s" % (self.builtinPrefixEnabled)))
            gameConfigNode.appendChild(tempNode)

            if self.winePrefix != "":
                tempNode = doc.createElementNS(EMPTY_NAMESPACE, "Wine.Prefix")
                tempNode.appendChild(
                    doc.createTextNode("%s" % (str(self.winePrefix))))
                gameConfigNode.appendChild(tempNode)

        tempNode = doc.createElementNS(EMPTY_NAMESPACE, "HiRes")
        if self.highResEnabled:
            tempNode.appendChild(doc.createTextNode("True"))
        else:
            tempNode.appendChild(doc.createTextNode("False"))
        gameConfigNode.appendChild(tempNode)

        tempNode = doc.createElementNS(EMPTY_NAMESPACE, "Client")
        tempNode.appendChild(doc.createTextNode("%s" % (self.client)))
        gameConfigNode.appendChild(tempNode)

        if self.client in ["WIN32", "WIN64"]:
            tempNode = doc.createElementNS(EMPTY_NAMESPACE, "x64Client")
            value = "True" if self.client == "WIN64" else "False"
            tempNode.appendChild(doc.createTextNode(value))
            gameConfigNode.appendChild(tempNode)

        tempNode = doc.createElementNS(EMPTY_NAMESPACE, "Game.Directory")
        tempNode.appendChild(doc.createTextNode("%s" % (str(self.gameDir))))
        gameConfigNode.appendChild(tempNode)

        tempNode = doc.createElementNS(EMPTY_NAMESPACE, "PatchClient")
        tempNode.appendChild(doc.createTextNode("%s" %
                             (str(self.patchClient))))
        gameConfigNode.appendChild(tempNode)

        if self.language:
            tempNode = doc.createElementNS(EMPTY_NAMESPACE, "Language")
            tempNode.appendChild(doc.createTextNode("%s" % (self.language)))
            gameConfigNode.appendChild(tempNode)

        if saveAccountDetails:
            accountsNode = doc.createElementNS(EMPTY_NAMESPACE, "Accounts")

            # Adds all saved accounts with their account specific settings.
            for account in self.accountsDictionary:
                accountNode = doc.createElementNS(EMPTY_NAMESPACE, account)

                tempNode = doc.createElementNS(EMPTY_NAMESPACE, "World")
                tempNode.appendChild(
                    doc.createTextNode(
                        "%s" % (self.accountsDictionary[account][0]))
                )
                accountNode.appendChild(tempNode)

                accountsNode.appendChild(accountNode)

            # Test/preview clients use normal client accounts. I.e they are
            # saved and loaded to and from the normal client node rather than the test node
            if current_game.endswith(".Test"):
                # Delete current accounts node if present. All accounts that were originally
                # there were loaded as if they were the test client's, so they are not lost.
                originalAccountsNode = normalClientNode.getElementsByTagName(
                    "Accounts")
                if originalAccountsNode:
                    normalClientNode.removeChild(originalAccountsNode[0])

                normalClientNode.appendChild(accountsNode)
            else:
                gameConfigNode.appendChild(accountsNode)

            if savePassword:
                savePasswordNode = doc.createElementNS(
                    EMPTY_NAMESPACE, "Save.Password")
                savePasswordNode.appendChild(doc.createTextNode("True"))

            # Test/Preview clients store if password is enabled in normal client settings,
            # because the accounts are shared.
            if current_game.endswith(".Test"):
                # Delete current password enabled node if present.
                originalSavePasswordNode = normalClientNode.getElementsByTagName(
                    "Save.Password"
                )
                if originalSavePasswordNode:
                    normalClientNode.removeChild(originalSavePasswordNode[0])

                normalClientNode.appendChild(savePasswordNode)
            else:
                gameConfigNode.appendChild(savePasswordNode)

        startupScriptsNode = doc.createElementNS(
            EMPTY_NAMESPACE, "StartupScripts")
        for script in self.startupScripts:
            scriptNode = doc.createElementNS(EMPTY_NAMESPACE, "script")
            scriptNode.appendChild(doc.createTextNode("%s" % (script)))
            startupScriptsNode.appendChild(scriptNode)
        # Test/Preview clients store startup scripts in normal client settings,
        # because the add-ons folders are generally shared as well.
        if current_game.endswith(".Test"):
            # Delete current startup scripts node if present. All startup scripts
            # that were originally there were loaded as if they were the test client's,
            # so they are not lost.
            originalStartupScriptsNode = normalClientNode.getElementsByTagName(
                "StartupScripts"
            )
            if originalStartupScriptsNode:
                normalClientNode.removeChild(originalStartupScriptsNode[0])

            normalClientNode.appendChild(startupScriptsNode)
        else:
            gameConfigNode.appendChild(startupScriptsNode)

        # write new settings file
        with self.settingsFile.open(mode="w") as file:
            pretty_xml = prettify_xml(doc.toxml())
            file.write(pretty_xml)


set_os_specific_variables()
make_settings_dirs()
