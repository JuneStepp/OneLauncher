# coding=utf-8
###########################################################################
# Name:   Settings
# Author: Alan Jackson
# Date:   30th March 2009
#
# Class to handle loading and saving game settings
# for the Linux/OS X based launcher
# for the game Lord of the Rings Online
#
# Based on a script by SNy <SNy@bmx-chemnitz.de>
# Python port of LotROLinux by AJackson <ajackson@bcs.org.uk>
#
# (C) 2009 AJackson <ajackson@bcs.org.uk>
#
# This file is part of PyLotRO
#
# PyLotRO is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# PyLotRO is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with PyLotRO.  If not, see <http://www.gnu.org/licenses/>.
###########################################################################
import os
from Ft.Xml.Domlette import NonvalidatingReader, Print
from Ft.Xml import EMPTY_NAMESPACE
from Ft.Lib import Uri
from PyLotROUtils import DetermineOS

class Settings:
	def __init__(self, baseDir, osType):
		self.usingDND = False
		self.usingTest = False
		self.settingsDir = "%s%s" % (baseDir, osType.appDir)
		self.settingsFile = "%sLotROLinux.config" % (self.settingsDir)

	def LoadSettings(self, useGame=None):
		self.hiResEnabled = True
		self.app = "Wine"
		self.realm = ""
		self.language = ""
		self.account = ""
		self.wineProg = "wine"
		self.wineDebug = "fixme-all"
		self.patchClient = "patchclient.dll"
		self.focusAccount = True
		self.winePrefix = os.environ.get('WINEPREFIX')
		self.gameDir = ""
		success = False

		if self.winePrefix is None:
			self.winePrefix = ""

		try:
			if os.path.exists(self.settingsFile):
				file_uri = Uri.OsPathToUri(self.settingsFile)
				doc = NonvalidatingReader.parseUri(file_uri)

				if useGame == None:
					defaultGame = doc.xpath(u"//Settings/Default.Game")[0].firstChild.nodeValue
				else:
					defaultGame = useGame

				if defaultGame == "LOTRO":
					self.usingDND = False
					self.usingTest = False
				elif defaultGame == "LOTRO.Test":
					self.usingDND = False
					self.usingTest = True
				elif defaultGame == "DDO":
					self.usingDND = True
					self.usingTest = False
				elif defaultGame == "DDO.Test":
					self.usingDND = True
					self.usingTest = True

				xpathquery = u"//Settings/%s/" % (defaultGame)

				tempNode = doc.xpath(xpathquery + "Wine.Application")
				if len(tempNode) > 0:
					self.app = tempNode[0].firstChild.nodeValue

				tempNode = doc.xpath(xpathquery + "Wine.Program")
				if len(tempNode) > 0:
					self.wineProg = tempNode[0].firstChild.nodeValue

				tempNode = doc.xpath(xpathquery + "Wine.Debug")
				if len(tempNode) > 0:
					if tempNode[0].hasChildNodes():
						self.wineDebug = tempNode[0].firstChild.nodeValue
					else:
						self.wineDebug = ""

				tempNode = doc.xpath(xpathquery + "Wine.Prefix")
				if len(tempNode) > 0:
					if tempNode[0].hasChildNodes():
						self.winePrefix = tempNode[0].firstChild.nodeValue
					else:
						self.winePrefix = ""

				tempNode = doc.xpath(xpathquery + "HiRes")
				if len(tempNode) > 0:
					if tempNode[0].firstChild.nodeValue == "True":
						self.hiResEnabled = True
					else:
						self.hiResEnabled = False

				tempNode = doc.xpath(xpathquery + "Game.Directory")
				if len(tempNode) > 0:
					self.gameDir = tempNode[0].firstChild.nodeValue

				tempNode = doc.xpath(xpathquery + "Realm")
				if len(tempNode) > 0:
					self.realm = tempNode[0].firstChild.nodeValue

				tempNode = doc.xpath(xpathquery + "Language")
				if len(tempNode) > 0:
					self.language = tempNode[0].firstChild.nodeValue

				tempNode = doc.xpath(xpathquery + "Account")
				if len(tempNode) > 0:
					self.account = tempNode[0].firstChild.nodeValue
					self.focusAccount = False

				tempNode = doc.xpath(xpathquery + "PatchClient")
				if len(tempNode) > 0:
					self.patchClient = tempNode[0].firstChild.nodeValue

				success = True
		except:
			success = False

		return success

	def SaveSettings(self, saveAccountDetails):
		doc = None

		# Check if settings directory exists if not create
		if not os.path.exists(self.settingsDir):
			os.mkdir(self.settingsDir)

		# Check if settings file exists if not create new settings XML
		if os.path.exists(self.settingsFile):
			file_uri = Uri.OsPathToUri(self.settingsFile)
			doc = NonvalidatingReader.parseUri(file_uri)
		else:
			from Ft.Xml.Domlette import implementation
			doc = implementation.createDocument(EMPTY_NAMESPACE, None, None)
			settingsNode = doc.createElementNS(EMPTY_NAMESPACE, "Settings")
			doc.appendChild(settingsNode)

		currGame = ""

		if self.usingDND:
			currGame = "DDO"
			if self.usingTest:
				currGame += ".Test"
		else:
			currGame = "LOTRO"
			if self.usingTest:
				currGame += ".Test"

		# Set default game to current game
		defaultGameNode = doc.xpath(u"//Settings/Default.Game")
		if len(defaultGameNode) > 0:
			defaultGameNode[0].firstChild.nodeValue = currGame
		else:
			defaultGameNode = doc.createElementNS(EMPTY_NAMESPACE, "Default.Game")
			defaultGameNode.appendChild(doc.createTextNode(currGame))
			settingsNode.appendChild(defaultGameNode)

		# Remove old game block
		tempNode = doc.xpath(u"//Settings/%s" % (currGame))
		if len(tempNode) > 0:
			doc.documentElement.removeChild(tempNode[0])

		# Create new game block
		settingsNode = doc.xpath(u"//Settings")[0]
		gameConfigNode = doc.createElementNS(EMPTY_NAMESPACE, currGame)
		settingsNode.appendChild(gameConfigNode)

		tempNode = doc.createElementNS(EMPTY_NAMESPACE, "Wine.Application")
		tempNode.appendChild(doc.createTextNode(self.app))
		gameConfigNode.appendChild(tempNode)

		tempNode = doc.createElementNS(EMPTY_NAMESPACE, "Wine.Program")
		tempNode.appendChild(doc.createTextNode(self.wineProg))
		gameConfigNode.appendChild(tempNode)

		tempNode = doc.createElementNS(EMPTY_NAMESPACE, "Wine.Debug")
		tempNode.appendChild(doc.createTextNode(self.wineDebug))
		gameConfigNode.appendChild(tempNode)

		if self.winePrefix != "":
			tempNode = doc.createElementNS(EMPTY_NAMESPACE, "Wine.Prefix")
			tempNode.appendChild(doc.createTextNode(self.winePrefix))
			gameConfigNode.appendChild(tempNode)

		tempNode = doc.createElementNS(EMPTY_NAMESPACE, "HiRes")
		if self.hiResEnabled:
			tempNode.appendChild(doc.createTextNode("True"))
		else:
			tempNode.appendChild(doc.createTextNode("False"))
		gameConfigNode.appendChild(tempNode)

		tempNode = doc.createElementNS(EMPTY_NAMESPACE, "Game.Directory")
		tempNode.appendChild(doc.createTextNode(self.gameDir))
		gameConfigNode.appendChild(tempNode)

		tempNode = doc.createElementNS(EMPTY_NAMESPACE, "PatchClient")
		tempNode.appendChild(doc.createTextNode(self.patchClient))
		gameConfigNode.appendChild(tempNode)

		if saveAccountDetails:
			tempNode = doc.createElementNS(EMPTY_NAMESPACE, "Realm")
			tempNode.appendChild(doc.createTextNode(self.realm))
			gameConfigNode.appendChild(tempNode)

			tempNode = doc.createElementNS(EMPTY_NAMESPACE, "Language")
			tempNode.appendChild(doc.createTextNode(self.language))
			gameConfigNode.appendChild(tempNode)

			tempNode = doc.createElementNS(EMPTY_NAMESPACE, "Account")
			tempNode.appendChild(doc.createTextNode(self.account))
			gameConfigNode.appendChild(tempNode)

		# write new settings file
		f = open(self.settingsFile, 'w')
		Print(doc, stream=f, encoding='utf-8')
		f.close()

