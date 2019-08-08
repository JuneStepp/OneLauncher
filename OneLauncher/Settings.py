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
# (C) 2019 Jeremy Stepp <jeremy@bluetecno.com>
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
from .OneLauncherUtils import DetermineOS, GetText
from xml.dom import EMPTY_NAMESPACE
import xml.dom.minidom


class Settings:
    def __init__(self, baseDir, osType):
        self.currentGame = "LOTRO"
        self.settingsDir = "%s%s" % (baseDir, osType.appDir)
        self.settingsFile = "%sOneLauncher.config" % (self.settingsDir)

    def LoadSettings(self, useGame=None):
        self.hiResEnabled = True
        self.realm = ""
        self.language = "EN"
        self.account = ""
        self.wineProg = "wine"
        self.wineDebug = "fixme-all"
        self.patchClient = "patchclient.dll"
        self.focusAccount = True
        self.winePrefix = self.settingsDir + "wine/prefix"
        self.builtInPrefixEnabled = True
        self.gameDir = ""
        self.x86Enabled = False
        self.savePassword = False
        success = False

        if self.winePrefix is None:
            self.winePrefix = ""

        try:
            if os.path.exists(self.settingsFile):
                doc = xml.dom.minidom.parse(self.settingsFile)

                if useGame == None:
                    defaultGame = GetText(doc.getElementsByTagName(
                        "Default.Game")[0].childNodes)
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
                        #Checks if prefix is set to built in wine prefix
                        if winePrefix != self.winePrefix:
                            self.winePrefix = winePrefix
                            self.builtInPrefixEnabled = False
                    elif node.nodeName == "HiRes":
                        if GetText(node.childNodes) == "True":
                            self.hiResEnabled = True
                        else:
                            self.hiResEnabled = False
                    elif node.nodeName == "x86":
                        if GetText(node.childNodes) == "True":
                            self.x86Enabled = True
                        else:
                            self.x86Enabled = False
                    elif node.nodeName == "Save.Password":
                        if GetText(node.childNodes) == "True":
                            self.savePassword = True
                        else:
                            self.savePassword = False
                    elif node.nodeName == "Game.Directory":
                        self.gameDir = GetText(node.childNodes)
                    elif node.nodeName == "Realm":
                        self.realm = GetText(node.childNodes)
                    elif node.nodeName == "Language":
                        self.language = GetText(node.childNodes)
                    elif node.nodeName == "Account":
                        self.account = GetText(node.childNodes)
                        self.focusAccount = False
                    elif node.nodeName == "PatchClient":
                        self.patchClient = GetText(node.childNodes)

                # Disables 64-bit client if it is unavailable for LOTRO
                if not os.path.exists(self.gameDir + os.sep + "x64" + os.sep +
                    "lotroclient64.exe") and self.currentGame.startswith("LOTRO"):
                    self.x86Enabled = False

                # Disables 64-bit client if it is unavailable for DDO
                if not os.path.exists(self.gameDir + os.sep + "x64" + os.sep +
                    "dndclient64.exe") and self.currentGame.startswith("DDO"):
                    self.x86Enabled = False

                success = True

                if (not os.path.exists(self.wineProg) and self.wineProg != "wine" and
                        not self.builtInPrefixEnabled):
                    success = "[E16] Wine executable set does not exist"
        except:
            success = False

        return success

    def SaveSettings(self, saveAccountDetails=None, savePassword=None, game=None):
        doc = None

        # Check if settings directory exists if not create
        if not os.path.exists(self.settingsDir):
            os.mkdir(self.settingsDir)
        os.makedirs(self.settingsDir + "wine/prefix", exist_ok=True)


        # Check if settings file exists if not create new settings XML
        if os.path.exists(self.settingsFile):
            doc = xml.dom.minidom.parse(self.settingsFile)
        else:
            doc = xml.dom.minidom.Document()
            settingsNode = doc.createElementNS(EMPTY_NAMESPACE, "Settings")
            doc.appendChild(settingsNode)

        if game:
            currGame = game
        else:
            currGame = self.currentGame

        # Set default game to current game
        defaultGameNode = doc.getElementsByTagName("Default.Game")
        if len(defaultGameNode) > 0:
            defaultGameNode[0].firstChild.nodeValue = currGame
        else:
            defaultGameNode = doc.createElementNS(
                EMPTY_NAMESPACE, "Default.Game")
            defaultGameNode.appendChild(doc.createTextNode(currGame))
            settingsNode.appendChild(defaultGameNode)

        # Remove old game block
        tempNode = doc.getElementsByTagName(currGame)
        if len(tempNode) > 0:
            doc.documentElement.removeChild(tempNode[0])

        # Create new game block
        settingsNode = doc.getElementsByTagName("Settings")[0]
        gameConfigNode = doc.createElementNS(EMPTY_NAMESPACE, currGame)
        settingsNode.appendChild(gameConfigNode)

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

        tempNode = doc.createElementNS(EMPTY_NAMESPACE, "x86")
        if self.x86Enabled:
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
            tempNode = doc.createElementNS(EMPTY_NAMESPACE, "Realm")
            tempNode.appendChild(doc.createTextNode("%s" % (self.realm)))
            gameConfigNode.appendChild(tempNode)

            tempNode = doc.createElementNS(EMPTY_NAMESPACE, "Account")
            tempNode.appendChild(doc.createTextNode("%s" % (self.account)))
            gameConfigNode.appendChild(tempNode)

            if savePassword:
                tempNode = doc.createElementNS(EMPTY_NAMESPACE, "Save.Password")
                tempNode.appendChild(doc.createTextNode("True"))
                gameConfigNode.appendChild(tempNode)

        # write new settings file
        f = open(self.settingsFile, 'w')
        f.write(doc.toxml())
        f.close()
