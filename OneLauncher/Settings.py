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
# (C) 2019-2020 Jeremy Stepp <mail@JeremyStepp.me>
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
from OneLauncher.OneLauncherUtils import GetText
from xml.dom import EMPTY_NAMESPACE
from xml.dom.minidom import Document  # nosec
import defusedxml.minidom
from vkbeautify import xml as prettify_xml
from collections import OrderedDict
import logging


class Settings:
    def __init__(self, baseDir, osType):
        self.currentGame = "LOTRO"
        self.settingsDir = "%s%s" % (baseDir, osType.appDir)
        self.settingsFile = "%sOneLauncher.config" % (self.settingsDir)
        self.osType = osType
        self.logger = logging.getLogger("OneLauncher")

    def LoadSettings(self, useGame=None):
        self.hiResEnabled = True
        self.language = "EN"
        # Key is account name and content is list of details relating to account.
        self.accountsDictionary = OrderedDict()
        self.wineProg = "wine"
        self.wineDebug = "fixme-all"
        self.patchClient = "patchclient.dll"
        self.focusAccount = True
        self.winePrefix = self.settingsDir + "wine/prefix"
        self.builtInPrefixEnabled = True
        self.gameDir = ""
        self.x64ClientEnabled = True
        self.savePassword = False
        self.startupScripts = []
        success = False

        if self.winePrefix is None:
            self.winePrefix = ""

        try:
            if os.path.exists(self.settingsFile):
                doc = defusedxml.minidom.parse(self.settingsFile)

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
                        self.wineProg = GetText(node.childNodes)
                    elif node.nodeName == "Wine.Debug":
                        self.wineDebug = GetText(node.childNodes)
                    elif node.nodeName == "Wine.Prefix":
                        winePrefix = GetText(node.childNodes)
                        # Checks if prefix is set to built in wine prefix
                        if winePrefix != self.winePrefix:
                            self.winePrefix = winePrefix
                            self.builtInPrefixEnabled = False
                    elif node.nodeName == "HiRes":
                        self.hiResEnabled = True if GetText(node.childNodes) == "True" else False
                    elif node.nodeName == "x64Client":
                        self.x64ClientEnabled = True if GetText(node.childNodes) == "True" else False
                    elif node.nodeName == "Save.Password":
                        self.savePassword = True if GetText(node.childNodes) == "True" else False
                    elif node.nodeName == "Game.Directory":
                        self.gameDir = GetText(node.childNodes)
                    elif node.nodeName == "Language":
                        self.language = GetText(node.childNodes)
                    elif node.nodeName == "PatchClient":
                        self.patchClient = GetText(node.childNodes)
                    elif node.nodeName == "Accounts" and not self.currentGame.endswith(
                        ".Test"
                    ):
                        account_nodes = node.childNodes
                        self.setAccountsSettings(account_nodes)
                    elif node.nodeName == "StartupScripts" and not self.currentGame.endswith(
                        ".Test"
                    ):
                        startup_script_nodes = node.childNodes
                        self.setStartupScriptSettings(startup_script_nodes)

                # Test/preview clients use accounts and startups scripts from normal clients
                if self.currentGame.endswith(".Test"):
                    normalClientNode = self.getNormalClientNode(self.currentGame, doc)
                    if normalClientNode:
                        # Load in accounts and their settings from normal client node
                        accountsNode = normalClientNode.getElementsByTagName("Accounts")
                        if accountsNode:
                            account_nodes = accountsNode[0].childNodes
                            self.setAccountsSettings(account_nodes)

                        # Load in startup scripts from normal client node
                        startupScriptsNode = normalClientNode.getElementsByTagName("StartupScripts")
                        if startupScriptsNode:
                            startup_script_nodes = startupScriptsNode[0].childNodes
                            self.setStartupScriptSettings(startup_script_nodes)


                # Disables 64-bit client if it is unavailable for LOTRO
                if not os.path.exists(
                    self.gameDir + os.sep + "x64" + os.sep + "lotroclient64.exe"
                ) and self.currentGame.startswith("LOTRO"):
                    self.x64ClientEnabled = False

                # Disables 64-bit client if it is unavailable for DDO
                if not os.path.exists(
                    self.gameDir + os.sep + "x64" + os.sep + "dndclient64.exe"
                ) and self.currentGame.startswith("DDO"):
                    self.x64ClientEnabled = False

                success = True

                if (
                    not os.path.exists(self.wineProg)
                    and self.wineProg != "wine"
                    and not self.builtInPrefixEnabled
                ):
                    success = "[E16] Wine executable set does not exist"
        except Exception as error:
            self.logger.error(error, exc_info=True)
            success = False

        return success

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
                        self.accountsDictionary[account_name][
                            0
                        ] = GetText(node.childNodes)

                self.focusAccount = False
    
    def setStartupScriptSettings(self, startup_script_nodes):
        for node in startup_script_nodes:
            if node.nodeName == "script":
                self.startupScripts.append(GetText(node.childNodes))

    def getNormalClientNode(self, game, doc):
        """
        Get normal client node/make it if it doesn't exist.
        Normal client as in not the test/preview client
        """
        if game.endswith(".Test"):
            normalClient = game.split(".")[0]
            normalClientNode = doc.getElementsByTagName(normalClient)
            if normalClientNode:
                normalClientNode = normalClientNode[0]
                return normalClientNode
            else:
                return None

    def SaveSettings(self, saveAccountDetails=None, savePassword=None, game=None):
        doc = None

        # Check if settings directory exists if not create
        if not os.path.exists(self.settingsDir):
            os.mkdir(self.settingsDir)
        if not self.osType.usingWindows:
            os.makedirs(self.settingsDir + "wine/prefix", exist_ok=True)

        # Check if settings file exists if not create new settings XML
        if os.path.exists(self.settingsFile):
            doc = defusedxml.minidom.parse(self.settingsFile)
            settingsNode = doc.getElementsByTagName("Settings")
        else:
            doc = Document()
            settingsNode = doc.createElementNS(EMPTY_NAMESPACE, "Settings")
            doc.appendChild(settingsNode)

        current_game = game if game else self.currentGame
        # Set default game to current game
        defaultGameNode = doc.getElementsByTagName("Default.Game")
        if len(defaultGameNode) > 0:
            defaultGameNode[0].firstChild.nodeValue = current_game
        else:
            defaultGameNode = doc.createElementNS(EMPTY_NAMESPACE, "Default.Game")
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
            normalClientNode = self.getNormalClientNode(current_game, doc)
            if not normalClientNode:
                normalClientNode = doc.createElementNS(EMPTY_NAMESPACE, current_game)
                settingsNode.appendChild(normalClientNode)

        if not self.osType.usingWindows:
            tempNode = doc.createElementNS(EMPTY_NAMESPACE, "Wine.Program")
            tempNode.appendChild(doc.createTextNode("%s" % (self.wineProg)))
            gameConfigNode.appendChild(tempNode)

            tempNode = doc.createElementNS(EMPTY_NAMESPACE, "Wine.Debug")
            tempNode.appendChild(doc.createTextNode("%s" % (self.wineDebug)))
            gameConfigNode.appendChild(tempNode)

            if self.winePrefix != "":
                tempNode = doc.createElementNS(EMPTY_NAMESPACE, "Wine.Prefix")
                tempNode.appendChild(doc.createTextNode("%s" % (self.winePrefix)))
                gameConfigNode.appendChild(tempNode)

        tempNode = doc.createElementNS(EMPTY_NAMESPACE, "HiRes")
        if self.hiResEnabled:
            tempNode.appendChild(doc.createTextNode("True"))
        else:
            tempNode.appendChild(doc.createTextNode("False"))
        gameConfigNode.appendChild(tempNode)

        tempNode = doc.createElementNS(EMPTY_NAMESPACE, "x64Client")
        if self.x64ClientEnabled:
            tempNode.appendChild(doc.createTextNode("True"))
        else:
            tempNode.appendChild(doc.createTextNode("False"))
        gameConfigNode.appendChild(tempNode)

        tempNode = doc.createElementNS(EMPTY_NAMESPACE, "Game.Directory")
        tempNode.appendChild(doc.createTextNode("%s" % (self.gameDir)))
        gameConfigNode.appendChild(tempNode)

        tempNode = doc.createElementNS(EMPTY_NAMESPACE, "PatchClient")
        tempNode.appendChild(doc.createTextNode("%s" % (self.patchClient)))
        gameConfigNode.appendChild(tempNode)

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
                    doc.createTextNode("%s" % (self.accountsDictionary[account][0]))
                )
                accountNode.appendChild(tempNode)

                accountsNode.appendChild(accountNode)

            # Test/preview clients use normal client accounts. I.e they are
            # saved and loaded to and from the normal client node rather than the test node
            if current_game.endswith(".Test"):
                # Delete current accounts node if present. All accounts that were originally
                # there were loaded as if they were the test client's, so they are not lost.
                originalAccountsNode = normalClientNode.getElementsByTagName("Accounts")
                if originalAccountsNode:
                    normalClientNode.removeChild(originalAccountsNode[0])

                normalClientNode.appendChild(accountsNode)
            else:
                gameConfigNode.appendChild(accountsNode)

            if savePassword:
                tempNode = doc.createElementNS(EMPTY_NAMESPACE, "Save.Password")
                tempNode.appendChild(doc.createTextNode("True"))
                gameConfigNode.appendChild(tempNode)

        startupScriptsNode = doc.createElementNS(EMPTY_NAMESPACE, "StartupScripts")
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
            originalStartupScriptsNode = normalClientNode.getElementsByTagName("StartupScripts")
            if originalStartupScriptsNode:
                normalClientNode.removeChild(originalStartupScriptsNode[0])

            normalClientNode.appendChild(startupScriptsNode)
        else:
            gameConfigNode.appendChild(startupScriptsNode)


        # write new settings file
        with open(self.settingsFile, "w") as file:
            pretty_xml = prettify_xml(doc.toxml())
            file.write(pretty_xml)
