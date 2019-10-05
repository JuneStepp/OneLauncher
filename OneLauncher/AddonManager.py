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
# (C) 2019 June Stepp <git@junestepp.me>
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
from qtpy import QtCore, QtGui, QtWidgets, uic
import os
from pkg_resources import resource_filename
from glob import glob
from xml.dom import EMPTY_NAMESPACE
import xml.dom.minidom
from .OneLauncherUtils import GetText
import sqlite3
from shutil import rmtree, copy
from zipfile import ZipFile
from urllib import request
from time import strftime, localtime


class AddonManager:
    # ID is from the order plugins are found on the filesystem. InterfaceID is the unique ID for plugins on lotrointerface.com
    COLUMN_LIST = [
        "ID",
        "Name",
        "Category",
        "Version",
        "Author",
        "LatestRelease",
        "File",
        "InterfaceID",
        "Dependencies",
    ]
    TABLE_LIST = [
        "tablePluginsInstalled",
        "tableThemesInstalled",
        "tableMusicInstalled",
        "tablePlugins",
        "tableThemes",
        "tableMusic",
        "tableThemesDDO",
        "tableThemesDDOInstalled",
    ]

    PLUGINS_URL = "https://api.lotrointerface.com/fav/OneLauncher-Plugins.xml"
    THEMES_URL = "https://api.lotrointerface.com/fav/OneLauncher-Themes.xml"
    MUSIC_URL = "https://api.lotrointerface.com/fav/OneLauncher-Music.xml"
    THEMES_DDO_URL = "https://api.lotrointerface.com/fav/OneLauncher-Themes-DDO.xml"

    def __init__(self, currentGame, osType, settingsDir, parent):
        self.settingsDir = settingsDir
        self.currentGame = currentGame
        self.parent = parent

        self.winAddonManager = QtWidgets.QDialog(parent, QtCore.Qt.FramelessWindowHint)

        uifile = resource_filename(__name__, "ui" + os.sep + "winAddonManager.ui")

        Ui_dlgAddonManager, base_class = uic.loadUiType(uifile)
        self.uiAddonManager = Ui_dlgAddonManager()
        self.uiAddonManager.setupUi(self.winAddonManager)

        self.uiAddonManager.btnBox.rejected.connect(self.btnBoxActivated)

        self.uiAddonManager.btnAddonsMenu = QtWidgets.QMenu()
        self.uiAddonManager.btnAddonsMenu.addAction(
            self.uiAddonManager.actionAddonImport
        )
        self.uiAddonManager.actionAddonImport.triggered.connect(
            self.actionAddonImportSelected
        )
        self.uiAddonManager.btnAddons.setMenu(self.uiAddonManager.btnAddonsMenu)
        self.uiAddonManager.btnAddons.clicked.connect(self.btnAddonsClicked)
        self.uiAddonManager.tabWidget.currentChanged.connect(self.tabWidgetIndexChanged)
        self.uiAddonManager.tabWidgetInstalled.currentChanged.connect(
            self.tabWidgetInstalledIndexChanged
        )

        self.uiAddonManager.txtLog.hide()
        self.uiAddonManager.btnLog.clicked.connect(self.btnLogClicked)

        self.uiAddonManager.txtSearchBar.setFocus()
        self.uiAddonManager.txtSearchBar.textChanged.connect(
            self.txtSearchBarTextChanged
        )

        for table in self.TABLE_LIST[:-2]:
            # Gets callable form from the string
            table = getattr(self.uiAddonManager, table)

            # Hides ID column
            table.hideColumn(0)

            # Sort tables by addon name
            table.sortItems(1)

        self.openDB()

        if osType.usingWindows:
            documents_folder = "My Documents"
        else:
            documents_folder = "Documents"

        if currentGame.startswith("DDO"):
            # Removes plugin and music tabs when using DDO
            self.uiAddonManager.tabWidgetFindMore.removeTab(0)
            self.uiAddonManager.tabWidgetFindMore.removeTab(1)
            self.uiAddonManager.tabWidgetInstalled.removeTab(0)
            self.uiAddonManager.tabWidgetInstalled.removeTab(1)

            self.data_folder = os.path.join(
                os.path.expanduser("~"), documents_folder, "Dungeons and Dragons Online"
            )

            self.uiAddonManager.tableThemesInstalled.setObjectName(
                "tableThemesDDOInstalled"
            )
            self.getInstalledThemes()
        else:
            self.data_folder = os.path.join(
                os.path.expanduser("~"),
                documents_folder,
                "The Lord of the Rings Online",
            )

            # Loads in installed plugins
            self.getInstalledPlugins()

    def tabWidgetInstalledIndexChanged(self, index):
        # Load in installed themes on first switch to tab
        if index == 1 and not self.uiAddonManager.tableThemesInstalled.item(0, 0):
            self.getInstalledThemes()

        # Load in installed music on first switch to tab
        if index == 2 and not self.uiAddonManager.tableMusicInstalled.item(0, 0):
            self.getInstalledMusic()

    def getInstalledThemes(self):
        self.uiAddonManager.txtSearchBar.clear()

        data_folder = os.path.join(self.data_folder, "ui", "skins")
        os.makedirs(data_folder, exist_ok=True)

        themes_list = []
        themes_list_compendium = []
        for folder in glob(os.path.join(data_folder, "*", "")):
            themes_list.append(folder[:-1])
            for file in os.listdir(folder):
                if file.endswith(".skincompendium"):
                    themes_list_compendium.append(os.path.join(folder, file))
                    themes_list.remove(folder[:-1])
                    break

        self.addInstalledThemestoDB(
            themes_list,
            themes_list_compendium,
            self.uiAddonManager.tableThemesInstalled,
        )

    def addInstalledThemestoDB(self, themes_list, themes_list_compendium, table):
        # Clears rows from db table
        self.c.execute("DELETE FROM {table}".format(table=table.objectName()))

        for theme in themes_list_compendium:
            items_row = self.parseCompediumFile(theme, "SkinConfig")
            items_row = self.getOnlineAddonInfo(items_row, "tableThemes")
            self.addRowToDB(table.objectName(), items_row)

        for theme in themes_list:
            items_row = [""] * (len(self.COLUMN_LIST) - 1)

            items_row[0] = os.path.split(theme)[1]
            items_row[5] = theme
            items_row[1] = "Unmanaged"

            self.addRowToDB(table.objectName(), items_row)

        # Populate user visible table
        self.searchDB(table, "")

    def getInstalledMusic(self):
        self.uiAddonManager.txtSearchBar.clear()

        data_folder = os.path.join(self.data_folder, "Music")
        os.makedirs(data_folder, exist_ok=True)

        music_list = []
        music_list_compendium = []
        for folder in glob(os.path.join(data_folder, "*", "")):
            music_list.append(folder[:-1])
            for file in os.listdir(folder):
                if file.endswith(".musiccompendium"):
                    music_list_compendium.append(
                        os.path.join(data_folder, folder, file)
                    )
                    music_list.remove(folder[:-1])
                    break

        for file in os.listdir(data_folder):
            if file.endswith(".abc"):
                music_list.append(os.path.join(data_folder, file))

        self.addInstalledMusictoDB(music_list, music_list_compendium)

    def addInstalledMusictoDB(self, music_list, music_list_compendium):
        # Clears rows from db table
        self.c.execute("DELETE FROM tableMusicInstalled")

        for music in music_list_compendium:
            items_row = self.parseCompediumFile(music, "MusicConfig")
            items_row = self.getOnlineAddonInfo(items_row, "tableMusic")
            self.addRowToDB("tableMusicInstalled", items_row)

        for music in music_list:
            items_row = [""] * (len(self.COLUMN_LIST) - 1)

            items_row[0] = os.path.split(music)[1]
            if music.endswith(".abc"):
                items_row[0] = os.path.splitext(items_row[0])[0]

                with open(music, "r") as file:
                    for i in range(3):
                        line = file.readline().strip()
                        if line.startswith("T: "):
                            items_row[0] = line[3:]
                        if line.startswith("Z: "):
                            if line.startswith("Z: Transcribed by "):
                                items_row[3] = line[18:]
                            else:
                                items_row[3] = line[3:]

            items_row[5] = music
            items_row[1] = "Unmanaged"

            self.addRowToDB("tableMusicInstalled", items_row)

        # Populate user visible table
        self.searchDB(self.uiAddonManager.tableMusicInstalled, "")

    def getInstalledPlugins(self):
        self.uiAddonManager.txtSearchBar.clear()

        data_folder = os.path.join(self.data_folder, "Plugins")
        os.makedirs(data_folder, exist_ok=True)

        # Finds all plugins and adds their .plugincompendium files to a list
        plugins_list_compendium = []
        plugins_list = []
        for folder in glob(os.path.join(data_folder, "*", "")):
            for file in os.listdir(folder):
                if file.endswith(".plugincompendium"):
                    plugins_list_compendium.append(os.path.join(folder, file))
                elif file.endswith(".plugin"):
                    plugins_list.append(os.path.join(folder, file))

        # Remove managed plugins from plugins list
        for plugin in plugins_list_compendium:
            doc = xml.dom.minidom.parse(plugin)
            nodes = doc.getElementsByTagName("Descriptors")[0].childNodes

            for node in nodes:
                if node.nodeName == "descriptor":
                    try:
                        plugins_list.remove(
                            os.path.join(
                                data_folder,
                                (GetText(node.childNodes).replace("\\", os.sep)),
                            )
                        )
                    except ValueError:
                        self.addLog(plugin + " has misconfigured descriptors")

        self.addInstalledPluginstoDB(plugins_list, plugins_list_compendium)

    def addInstalledPluginstoDB(self, plugins_list, plugins_list_compendium):
        # Clears rows from db table
        self.c.execute("DELETE FROM tablePluginsInstalled")

        for plugin in plugins_list_compendium + plugins_list:
            # Sets tag for plugin file xml search and category for unmanaged plugins
            if plugin.endswith(".plugincompendium"):
                items_row = self.parseCompediumFile(plugin, "PluginConfig")
                items_row = self.getOnlineAddonInfo(items_row, "tablePlugins")

                dependencies = ""
                doc = xml.dom.minidom.parse(plugin)
                if doc.getElementsByTagName("Dependencies"):
                    nodes = doc.getElementsByTagName("Dependencies")[0].childNodes
                    for node in nodes:
                        if node.nodeName == "dependency":
                            dependencies = (
                                dependencies + "," + (GetText(node.childNodes))
                            )
                items_row[7] = dependencies[1:]
            else:
                items_row = self.parseCompediumFile(plugin, "Information")
                items_row[1] = "Unmanaged"

            self.addRowToDB("tablePluginsInstalled", items_row)

        # Populate user visible table
        self.searchDB(self.uiAddonManager.tablePluginsInstalled, "")

    # Returns list of common values for compendium or .plugin files
    def parseCompediumFile(self, file, tag):
        items_row = [""] * (len(self.COLUMN_LIST) - 1)

        doc = xml.dom.minidom.parse(file)
        nodes = doc.getElementsByTagName(tag)[0].childNodes
        for node in nodes:
            if node.nodeName == "Name":
                items_row[0] = GetText(node.childNodes)
            elif node.nodeName == "Author":
                items_row[3] = GetText(node.childNodes)
            elif node.nodeName == "Version":
                items_row[2] = GetText(node.childNodes)
            elif node.nodeName == "Id":
                items_row[6] = GetText(node.childNodes)
            items_row[5] = file

        return items_row

    def getOnlineAddonInfo(self, items_row, remote_addons_table):
        for info in self.c.execute(
            "SELECT Category, LatestRelease FROM {table} WHERE InterfaceID == '{ID}'".format(
                table=remote_addons_table, ID=items_row[6]
            )
        ):
            items_row[1] = info[0]
            items_row[4] = info[1]

        # Unmanaged if not in online cache
        if not items_row[1]:
            items_row[1] = "Unmanaged"

        return items_row

    def openDB(self):
        # Connects to addons_cache database and creates it if it does not exist
        if not os.path.exists(os.path.join(self.settingsDir, "addons_cache.sqlite")):
            self.conn = sqlite3.connect(
                os.path.join(self.settingsDir, "addons_cache.sqlite")
            )
            self.c = self.conn.cursor()

            for table in self.TABLE_LIST:
                self.c.execute(
                    "CREATE VIRTUAL TABLE {tbl_nm} USING FTS5({clmA}, {clmB}, {clmC}, {clmD}, {clmE}, {clmF}, {clmG}, {clmH})".format(
                        tbl_nm=table,
                        clmA=self.COLUMN_LIST[1],
                        clmB=self.COLUMN_LIST[2],
                        clmC=self.COLUMN_LIST[3],
                        clmD=self.COLUMN_LIST[4],
                        clmE=self.COLUMN_LIST[5],
                        clmF=self.COLUMN_LIST[6],
                        clmG=self.COLUMN_LIST[7],
                        clmH=self.COLUMN_LIST[8],
                    )
                )
        else:
            self.conn = sqlite3.connect(
                os.path.join(self.settingsDir, "addons_cache.sqlite")
            )
            self.c = self.conn.cursor()

    def closeDB(self):
        self.conn.commit()
        self.conn.close()

    def actionAddonImportSelected(self):
        if self.currentGame.startswith("DDO"):
            addon_formats = "*.zip *.rar"
        else:
            addon_formats = "*.zip *.rar *.abc"

        filenames = QtWidgets.QFileDialog.getOpenFileNames(
            self.winAddonManager,
            "Addon Files/Archives",
            os.path.expanduser("~"),
            addon_formats,
        )

        if filenames[0]:
            for file in filenames[0]:
                self.installAddon(file)

    def installAddon(self, addon):
        # Install .abc files
        if addon.endswith(".abc"):
            if self.currentGame.startswith("DDO"):
                self.addLog("DDO does not support .abc/music files")
                return

            copy(addon, os.path.join(self.data_folder, "Music"))

            self.getInstalledMusic()
        elif addon.endswith(".rar"):
            self.addLog(
                "OneLauncher does not support .rar archives, because it is a proprietary format that would require and external program to extract"
            )
        elif addon.endswith(".zip"):
            with ZipFile(addon, "r") as file:
                for entry in file.namelist():
                    if entry.endswith(".plugin"):
                        if self.currentGame.startswith("DDO"):
                            self.addLog("DDO does not support plugins")
                            return

                        file.extractall(path=os.path.join(self.data_folder, "Plugins"))
                        self.getInstalledPlugins()
                        return
                    elif entry.endswith(".abc"):
                        if self.currentGame.startswith("DDO"):
                            self.addLog("DDO does not support .abc/music files")
                            return

                        file.extractall(path=os.path.join(self.data_folder, "Music"))
                        self.getInstalledMusic()
                        return

                file.extractall(path=os.path.join(self.data_folder, "ui", "skins"))
                self.getInstalledThemes()

    def txtSearchBarTextChanged(self, text):
        if self.currentGame.startswith("LOTRO"):
            # If in Installed tab
            if self.uiAddonManager.tabWidget.currentIndex() == 0:
                # If in PluginsInstalled tab
                if self.uiAddonManager.tabWidgetInstalled.currentIndex() == 0:
                    self.searchDB(self.uiAddonManager.tablePluginsInstalled, text)
                # If in ThemesInstalled tab
                elif self.uiAddonManager.tabWidgetInstalled.currentIndex() == 1:
                    self.searchDB(self.uiAddonManager.tableThemesInstalled, text)
                # If in MusicInstalled tab
                elif self.uiAddonManager.tabWidgetInstalled.currentIndex() == 2:
                    self.searchDB(self.uiAddonManager.tableMusicInstalled, text)
            # If in Find More tab
            elif self.uiAddonManager.tabWidget.currentIndex() == 1:
                # If in Plugins tab
                if self.uiAddonManager.tabWidgetFindMore.currentIndex() == 0:
                    self.searchDB(self.uiAddonManager.tablePlugins, text)
                # If in Themes tab
                elif self.uiAddonManager.tabWidgetFindMore.currentIndex() == 1:
                    self.searchDB(self.uiAddonManager.tableThemes, text)
                # If in Music tab
                elif self.uiAddonManager.tabWidgetFindMore.currentIndex() == 2:
                    self.searchDB(self.uiAddonManager.tableMusic, text)
        else:
            self.searchDB(self.uiAddonManager.tableThemesInstalled, text)

    def searchDB(self, table, text):
        table.clearContents()
        table.setRowCount(0)

        if text:
            for word in text.split():
                search_word = "%" + word + "%"

                for row in self.c.execute(
                    "SELECT rowid, * FROM {table} WHERE Author LIKE ? OR Category LIKE ? OR Name LIKE ?".format(
                        table=table.objectName()
                    ),
                    (search_word, search_word, search_word),
                ):
                    # Detects duplicates from multi-word search
                    duplicate = False
                    for item in table.findItems(row[1], QtCore.Qt.MatchExactly):
                        if int((table.item(item.row(), 0)).text()) == row[0]:
                            duplicate = True
                            break
                    if not duplicate:
                        self.addRowToTable(table, row)
        else:
            # Shows all plugins if the search bar is empty
            for row in self.c.execute(
                "SELECT rowid, * FROM {table}".format(table=table.objectName())
            ):
                self.addRowToTable(table, row)

    # Adds row to a visible table. First value in list is row name
    def addRowToTable(self, table, list):
        table.setSortingEnabled(False)

        rows = table.rowCount()
        table.setRowCount(rows + 1)

        # Sets row name
        tbl_item = QtWidgets.QTableWidgetItem()
        tbl_item.setText(str(list[0]))

        # Adds items to row
        for i, item in enumerate(list):
            tbl_item = QtWidgets.QTableWidgetItem()

            tbl_item.setText(str(item))
            # Sets color to red if plugin is unmanaged
            if item == "Unmanaged" and i == 2:
                tbl_item.setForeground(QtGui.QColor("darkred"))
            table.setItem(rows, i, tbl_item)

        table.setSortingEnabled(True)

    def addRowToDB(self, table, list):
        items = ""
        for item in list:
            if item:
                item = item.replace("'", "''")
                items = items + ", '" + item + "'"
            else:
                items = items + ", ''"

        self.c.execute(
            "INSERT INTO {table} values({values})".format(table=table, values=items[1:])
        )

    def btnBoxActivated(self):
        self.winAddonManager.accept()

    def btnLogClicked(self):
        if self.uiAddonManager.txtLog.isHidden():
            self.uiAddonManager.txtLog.show()
        else:
            self.uiAddonManager.txtLog.hide()

    def addLog(self, message):
        self.uiAddonManager.lblErrors.setText(
            "Errors: " + str(int(self.uiAddonManager.lblErrors.text()[-1]) + 1)
        )
        self.uiAddonManager.txtLog.append(message + "\n")

    def btnAddonsClicked(self):
        # If on installed tab which means remove addons
        if self.uiAddonManager.tabWidget.currentIndex() == 0:
            if self.currentGame.startswith("LOTRO"):
                if self.uiAddonManager.tabWidgetInstalled.currentIndex() == 0:
                    table = self.uiAddonManager.tablePluginsInstalled
                    uninstall_class = self.uninstallPlugins
                elif self.uiAddonManager.tabWidgetInstalled.currentIndex() == 1:
                    table = self.uiAddonManager.tableThemesInstalled
                    uninstall_class = self.uninstallThemes
                elif self.uiAddonManager.tabWidgetInstalled.currentIndex() == 2:
                    table = self.uiAddonManager.tableMusicInstalled
                    uninstall_class = self.uninstallMusic
            else:
                table = self.uiAddonManager.tableThemesInstalled
                uninstall_class = self.uninstallThemes

            uninstallConfirm, addons = self.getUninstallConfirm(table)
            if uninstallConfirm:
                uninstall_class(addons, table)

        elif self.uiAddonManager.tabWidget.currentIndex() == 1:
            self.installRemoteAddons()

    def installRemoteAddons(self):
        if self.uiAddonManager.tabWidgetFindMore.currentIndex() == 0:
            table = self.uiAddonManager.tablePlugins
        elif self.uiAddonManager.tabWidgetFindMore.currentIndex() == 1:
            table = self.uiAddonManager.tableThemes
        elif self.uiAddonManager.tabWidgetFindMore.currentIndex() == 2:
            table = self.uiAddonManager.tableMusic

        addons, details = self.getSelectedAddons(table)
        for addon in addons:
            path = os.path.join(self.data_folder, "Downoads", addon[0] + ".zip")
            os.makedirs(os.path.split(path)[0], exist_ok=True)
            self.downloader(addon[1], path)
            self.installAddon(path)
            os.remove(path)
            # self.checkAddonForDependencies()
            self.searchDB(table, "")

    def getUninstallConfirm(self, table):
        addons, details = self.getSelectedAddons(table)

        num_depends = len(details.split("\n")) - 1
        if num_depends == 1:
            plural, plural1 = "this ", " addon?"
        else:
            plural, plural1 = "these ", " addons?"
        text = "Are you sure you want to remove " + plural + str(len(addons)) + plural1
        if self.confirmationPrompt(text, details):
            return True, addons
        else:
            return False, addons

    def getSelectedAddons(self, table):
        if table.selectedItems():
            selected_addons = []
            details = ""
            for item in table.selectedItems()[0 :: (len(self.COLUMN_LIST) - 4)]:
                # Gets db row id for selected row
                selected_row = int((table.item(item.row(), 0)).text())

                selected_name = table.item(item.row(), 1).text()

                for selected_addon in self.c.execute(
                    "SELECT InterfaceID, File, Name FROM {table} WHERE rowid = ?".format(
                        table=table.objectName()
                    ),
                    (selected_row,),
                ):
                    selected_addons.append(selected_addon)
                    details = details + selected_name + "\n"

            return selected_addons, details

    def uninstallPlugins(self, plugins, table):
        data_folder = os.path.join(self.data_folder, "Plugins")
        for plugin in plugins:
            if plugin[1].endswith(".plugin"):
                plugin_files = [plugin[1]]
            else:
                plugin_files = []
                if self.checkAddonForDependencies(plugin, table):
                    doc = xml.dom.minidom.parse(plugin[1])
                    nodes = doc.getElementsByTagName("Descriptors")[0].childNodes
                    for node in nodes:
                        if node.nodeName == "descriptor":
                            plugin_files.append(
                                os.path.join(
                                    data_folder,
                                    (GetText(node.childNodes).replace("\\", os.sep)),
                                )
                            )
                else:
                    continue

            for plugin_file in plugin_files:
                doc = xml.dom.minidom.parse(plugin_file)
                nodes = doc.getElementsByTagName("Plugin")[0].childNodes
                for node in nodes:
                    if node.nodeName == "Package":
                        plugin_folder = os.path.split(
                            GetText(node.childNodes).replace(".", os.sep)
                        )[0]

                        # Removes plugin and all related files
                        if os.path.exists(data_folder + os.sep + plugin_folder):
                            rmtree(data_folder + os.sep + plugin_folder)
                if os.path.exists(plugin_file):
                    os.remove(plugin_file)
            if os.path.exists(plugin[1]):
                os.remove(plugin[1])

        # Reloads plugins
        self.getInstalledPlugins()

    def uninstallThemes(self, themes, talbe):
        for theme in themes:
            if theme[1].endswith(".skincompendium"):
                theme = os.path.split(theme[1])[0]
            else:
                theme = theme[1]
            rmtree(theme)

            # Reloads themes
            self.getInstalledThemes()

    def uninstallMusic(self, musics, table):
        for music in musics:
            if music[1].endswith(".musiccompendium"):
                music = os.path.split(music[1])[0]
            else:
                music = music[1]

            if music.endswith(".abc"):
                os.remove(music)
            else:
                rmtree(music)

            # Reloads themes
            self.getInstalledMusic()

    def checkAddonForDependencies(self, addon, table):
        details = ""

        for dependent in self.c.execute(
            'SELECT Name, Dependencies FROM {table} WHERE Dependencies != ""'.format(
                table=table.objectName()
            )
        ):
            for dependency in dependent[1].split(","):
                if dependency == addon[0]:
                    details = details + dependent[0] + "\n"

        if details:
            num_depends = len(details.split("\n")) - 1
            if num_depends == 1:
                plural = " addon depends"
            else:
                plural = " addons deppend"
            text = (
                str(num_depends)
                + plural
                + " on "
                + addon[2]
                + ". Are you sure you want to remove it?"
            )
            return self.confirmationPrompt(text, details)
        else:
            return True

    def confirmationPrompt(self, text, details):
        messageBox = QtWidgets.QMessageBox(self.parent)
        messageBox.setWindowFlag(QtCore.Qt.FramelessWindowHint)
        messageBox.setIcon(4)
        messageBox.setStandardButtons(messageBox.Apply | messageBox.Cancel)

        messageBox.setInformativeText(text)
        messageBox.setDetailedText(details)

        # Checks if user accepts dialouge
        if messageBox.exec() == 33554432:
            return True
        else:
            return False

    def tabWidgetIndexChanged(self, index):
        if index == 0:
            self.uiAddonManager.btnAddons.setText("-")
            self.uiAddonManager.btnAddons.setToolTip("Remove addons")
        else:
            self.uiAddonManager.btnAddons.setText("+")
            self.uiAddonManager.btnAddons.setToolTip("Install addons")

            # Populates remote addons tables if not done already
            if not self.uiAddonManager.tableThemes.item(0, 0):
                self.loadRemoteAddons()

    def loadRemoteAddons(self):
        if self.currentGame.startswith("LOTRO"):
            self.getRemoteAddons(self.PLUGINS_URL, self.uiAddonManager.tablePlugins)
            self.getRemoteAddons(self.THEMES_URL, self.uiAddonManager.tableThemes)
            self.getRemoteAddons(self.MUSIC_URL, self.uiAddonManager.tableMusic)
        else:
            self.getRemoteAddons(self.THEMES_DDO_URL, self.uiAddonManager.tableThemes)

    def getRemoteAddons(self, favorites_url, table):
        # Clears rows from db table
        self.c.execute("DELETE FROM {table}".format(table=table.objectName()))

        addons_file = request.urlopen(favorites_url).read().decode()
        doc = xml.dom.minidom.parseString(addons_file)
        tags = doc.getElementsByTagName("Ui")
        for tag in tags:
            items_row = [""] * (len(self.COLUMN_LIST) - 1)
            nodes = tag.childNodes
            for node in nodes:
                if node.nodeName == "UIName":
                    items_row[0] = GetText(node.childNodes)
                elif node.nodeName == "UIAuthorName":
                    items_row[3] = GetText(node.childNodes)
                elif node.nodeName == "UICategory":
                    items_row[1] = GetText(node.childNodes)
                elif node.nodeName == "UID":
                    items_row[6] = GetText(node.childNodes)
                elif node.nodeName == "UIVersion":
                    items_row[2] = GetText(node.childNodes)
                elif node.nodeName == "UIUpdated":
                    items_row[4] = strftime(
                        "%m-%d-%Y", localtime(int(GetText(node.childNodes)))
                    )
                elif node.nodeName == "UIFileURL":
                    items_row[5] = GetText(node.childNodes)
            self.addRowToDB(table.objectName(), items_row)

        # Populate user visible table
        self.searchDB(table, "")

    # Downloads file from url to path and shows progress with self.handleDownloadProgress
    def downloader(self, url, path):
        request.urlretrieve(url, path, self.handleDownloadProgress)

        self.uiAddonManager.progressBar.setValue(0)

    def handleDownloadProgress(self, index, frame, size):
        # Updates progress bar with download progress
        percent = 100 * index * frame // size
        self.uiAddonManager.progressBar.setValue(percent)

    def Run(self):
        self.winAddonManager.exec()
        self.closeDB()
