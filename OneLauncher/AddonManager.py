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
from PySide2 import QtCore, QtGui, QtWidgets
from PySide2.QtUiTools import QUiLoader
import os
from glob import glob
from xml.dom import EMPTY_NAMESPACE
from xml.dom.minidom import Document  # nosec
import defusedxml.minidom
from vkbeautify import xml as prettify_xml
from OneLauncher.OneLauncherUtils import GetText
import sqlite3
from shutil import rmtree, copy, move
from zipfile import ZipFile
import urllib
from time import strftime, localtime
import logging


class AddonManager:
    # ID is from the order plugins are found on the filesystem. InterfaceID is
    # the unique ID for plugins on lotrointerface.com
    # Don't change order of list
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
        "StartupScript",
    ]
    # Don't change order of list
    TABLE_LIST = [
        "tablePluginsInstalled",
        "tableSkinsInstalled",
        "tableMusicInstalled",
        "tablePlugins",
        "tableSkins",
        "tableMusic",
        "tableSkinsDDO",
        "tableSkinsDDOInstalled",
    ]

    PLUGINS_URL = "https://api.lotrointerface.com/fav/OneLauncher-Plugins.xml"
    SKINS_URL = "https://api.lotrointerface.com/fav/OneLauncher-Themes.xml"
    MUSIC_URL = "https://api.lotrointerface.com/fav/OneLauncher-Music.xml"
    SKINS_DDO_URL = "https://api.lotrointerface.com/fav/OneLauncher-Themes-DDO.xml"

    def __init__(
        self,
        currentGame,
        osType,
        settingsDir,
        parent,
        data_folder,
        gameDocumentsDir,
        startupScripts,
    ):
        self.settingsDir = settingsDir
        self.currentGame = currentGame
        self.parent = parent
        self.logger = logging.getLogger("OneLauncher")
        self.startupScripts = startupScripts

        ui_file = QtCore.QFile(os.path.join(data_folder, "ui", "winAddonManager.ui"))

        ui_file.open(QtCore.QFile.ReadOnly)
        loader = QUiLoader()
        self.winAddonManager = loader.load(ui_file, parentWidget=parent)
        ui_file.close()

        self.winAddonManager.setWindowFlags(
            QtCore.Qt.Dialog | QtCore.Qt.FramelessWindowHint
        )

        if currentGame.startswith("DDO"):
            # Removes plugin and music tabs when using DDO.
            # This has to be done before the tab switching signals are connected.
            self.winAddonManager.tabWidgetRemote.removeTab(0)
            self.winAddonManager.tabWidgetRemote.removeTab(1)
            self.winAddonManager.tabWidgetInstalled.removeTab(0)
            self.winAddonManager.tabWidgetInstalled.removeTab(1)

        # Creates backround color for addons that are installed already in remote tables
        self.installed_addons_color = QtGui.QColor()
        self.installed_addons_color.setRgb(63, 73, 83)

        self.winAddonManager.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.winAddonManager.customContextMenuRequested.connect(
            self.contextMenuRequested
        )
        self.winAddonManager.actionShowOnLotrointerface.triggered.connect(
            self.actionShowOnLotrointerfaceSelected
        )

        self.winAddonManager.btnBox.rejected.connect(self.btnBoxActivated)

        self.winAddonManager.btnAddonsMenu = QtWidgets.QMenu()
        self.winAddonManager.btnAddonsMenu.addAction(
            self.winAddonManager.actionAddonImport
        )
        self.winAddonManager.btnAddonsMenu.addAction(
            self.winAddonManager.actionShowSelectedOnLotrointerface
        )
        self.winAddonManager.actionAddonImport.triggered.connect(
            self.actionAddonImportSelected
        )
        self.winAddonManager.actionShowSelectedOnLotrointerface.triggered.connect(
            self.showSelectedOnLotrointerface
        )
        self.winAddonManager.actionShowAddonInFileManager.triggered.connect(
            self.actionShowAddonInFileManagerSelected
        )
        self.winAddonManager.btnAddonsMenu.addAction(
            self.winAddonManager.actionShowPluginsFolderInFileManager
        )
        self.winAddonManager.actionShowPluginsFolderInFileManager.triggered.connect(
            self.actionShowPluginsFolderSelected
        )
        self.winAddonManager.btnAddonsMenu.addAction(
            self.winAddonManager.actionShowSkinsFolderInFileManager
        )
        self.winAddonManager.actionShowSkinsFolderInFileManager.triggered.connect(
            self.actionShowSkinsFolderSelected
        )
        self.winAddonManager.btnAddonsMenu.addAction(
            self.winAddonManager.actionShowMusicFolderInFileManager
        )
        self.winAddonManager.actionShowMusicFolderInFileManager.triggered.connect(
            self.actionShowMusicFolderSelected
        )
        self.winAddonManager.btnAddonsMenu.addAction(
            self.winAddonManager.actionUpdateAllSelectedAddons
        )
        self.winAddonManager.actionUpdateAllSelectedAddons.triggered.connect(
            self.updateAllSelectedAddons
        )

        self.updateAddonFolderActions(0)

        self.winAddonManager.actionInstallAddon.triggered.connect(
            self.actionInstallAddonSelected
        )
        self.winAddonManager.actionUninstallAddon.triggered.connect(
            self.actionUninstallAddonSelected
        )
        self.winAddonManager.actionUpdateAddon.triggered.connect(
            self.actionUpdateAddonSelected
        )

        self.winAddonManager.actionEnableStartupScript.triggered.connect(
            self.actionEnableStartupScriptSelected
        )
        self.winAddonManager.actionDisableStartupScript.triggered.connect(
            self.actionDisableStartupScriptSelected
        )

        self.winAddonManager.btnCheckForUpdates.setIcon(
            QtGui.QIcon(os.path.join(data_folder, "images", "refresh.png"))
        )
        self.winAddonManager.btnCheckForUpdates.pressed.connect(self.checkForUpdates)
        self.winAddonManager.btnUpdateAll.pressed.connect(self.updateAll)

        self.winAddonManager.btnAddons.setMenu(self.winAddonManager.btnAddonsMenu)
        self.winAddonManager.btnAddons.clicked.connect(self.btnAddonsClicked)
        self.winAddonManager.tabWidget.currentChanged.connect(
            self.tabWidgetIndexChanged
        )
        self.winAddonManager.tabWidgetInstalled.currentChanged.connect(
            self.tabWidgetInstalledIndexChanged
        )
        self.winAddonManager.tabWidgetRemote.currentChanged.connect(
            self.tabWidgetRemoteIndexChanged
        )

        self.winAddonManager.txtLog.hide()
        self.winAddonManager.btnLog.clicked.connect(self.btnLogClicked)

        self.winAddonManager.txtSearchBar.setFocus()
        self.winAddonManager.txtSearchBar.textChanged.connect(
            self.txtSearchBarTextChanged
        )

        for table in self.TABLE_LIST[:-2]:
            # Gets callable form from the string
            table = getattr(self.winAddonManager, table)

            # Hides ID column
            table.hideColumn(0)

            # Sort tables by addon name
            table.sortItems(1)

        self.openDB()

        self.data_folder = os.path.join(osType.documentsDir, gameDocumentsDir)
        if currentGame.startswith("DDO"):
            self.data_folder_skins = os.path.join(self.data_folder, "ui", "skins")

            self.winAddonManager.tableSkinsInstalled.setObjectName(
                "tableSkinsDDOInstalled"
            )
            self.winAddonManager.tableSkins.setObjectName("tableSkinsDDO")
            self.getInstalledSkins()
        else:
            self.data_folder_plugins = os.path.join(self.data_folder, "Plugins")
            self.data_folder_skins = os.path.join(self.data_folder, "ui", "skins")
            self.data_folder_music = os.path.join(self.data_folder, "Music")

            # Loads in installed plugins
            self.getInstalledPlugins()

    def getInstalledSkins(self, folders_list=None):
        if self.isTableEmpty(self.winAddonManager.tableSkinsInstalled):
            folders_list = None

        os.makedirs(self.data_folder_skins, exist_ok=True)

        if not folders_list:
            folders_list = glob(os.path.join(self.data_folder_skins, "*", ""))
        else:
            folders_list = [
                os.path.join(self.data_folder_skins, folder) for folder in folders_list
            ]

        skins_list = []
        skins_list_compendium = []
        for folder in folders_list:
            folder = folder[:-1] + folder[-1].replace(os.sep, "")
            skins_list.append(folder)
            for file in os.listdir(folder):
                if file.endswith(".skincompendium"):
                    skins_list_compendium.append(os.path.join(folder, file))
                    skins_list.remove(folder)
                    break

        self.addInstalledSkinsToDB(skins_list, skins_list_compendium)

    def addInstalledSkinsToDB(self, skins_list, skins_list_compendium):
        table = self.winAddonManager.tableSkinsInstalled

        # Clears rows from db table if needed (This function is called to add
        # newly installed skins after initial load as well)
        if self.isTableEmpty(table):
            self.c.execute(
                "DELETE FROM {table}".format(table=table.objectName())  # nosec
            )

        for skin in skins_list_compendium:
            items_row = self.parseCompendiumFile(skin, "SkinConfig")
            items_row = self.getOnlineAddonInfo(
                items_row, self.winAddonManager.tableSkins.objectName()
            )
            self.addRowToDB(table, items_row)

        for skin in skins_list:
            items_row = [""] * (len(self.COLUMN_LIST) - 1)

            items_row[0] = os.path.split(skin)[1]
            items_row[5] = skin
            items_row[1] = "Unmanaged"

            self.addRowToDB(table, items_row)

        # Populate user visible table
        self.reloadSearch(self.winAddonManager.tableSkinsInstalled)

    def getInstalledMusic(self, folders_list=None):
        if self.isTableEmpty(self.winAddonManager.tableMusicInstalled):
            folders_list = None

        os.makedirs(self.data_folder_music, exist_ok=True)

        if not folders_list:
            folders_list = glob(os.path.join(self.data_folder_music, "*", ""))
        else:
            folders_list = [
                os.path.join(self.data_folder_music, folder) for folder in folders_list
            ]

        music_list = []
        music_list_compendium = []
        for folder in folders_list:
            folder = folder[:-1] + folder[-1].replace(os.sep, "")
            music_list.append(folder)
            for file in os.listdir(folder):
                if file.endswith(".musiccompendium"):
                    music_list_compendium.append(
                        os.path.join(self.data_folder_music, folder, file)
                    )
                    music_list.remove(folder)
                    break

        for file in os.listdir(self.data_folder_music):
            if file.endswith(".abc"):
                music_list.append(os.path.join(self.data_folder_music, file))

        self.addInstalledMusicToDB(music_list, music_list_compendium)

    def addInstalledMusicToDB(self, music_list, music_list_compendium):
        table = self.winAddonManager.tableMusicInstalled

        # Clears rows from db table if needed (This function is called
        # to add newly installed music after initial load as well)
        if self.isTableEmpty(table):
            self.c.execute("DELETE FROM tableMusicInstalled")

        for music in music_list_compendium:
            items_row = self.parseCompendiumFile(music, "MusicConfig")
            items_row = self.getOnlineAddonInfo(items_row, "tableMusic")
            self.addRowToDB(table, items_row)

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

            self.addRowToDB(table, items_row)

        # Populate user visible table
        self.reloadSearch(table)

    def getInstalledPlugins(self, folders_list=None):
        if self.isTableEmpty(self.winAddonManager.tablePluginsInstalled):
            folders_list = None
        os.makedirs(self.data_folder_plugins, exist_ok=True)

        if not folders_list:
            folders_list = glob(os.path.join(self.data_folder_plugins, "*", ""))
        else:
            folders_list = [
                os.path.join(self.data_folder_plugins, folder)
                for folder in folders_list
            ]

        # Finds all plugins and adds their .plugincompendium files to a list
        plugins_list_compendium = []
        plugins_list = []
        for folder in folders_list:
            for file in glob(folder + "/**/*.plugin*", recursive=True):
                if file.endswith(".plugincompendium"):
                    # .plugincompenmdium file should be in author folder of plugin
                    if os.path.split(file)[0].strip("/\\") == folder.strip("/\\"):
                        plugins_list_compendium.append(file)
                elif file.endswith(".plugin"):
                    plugins_list.append(file)

        (plugins_list, plugins_list_compendium,) = self.removeManagedPluginsFromList(
            plugins_list, plugins_list_compendium
        )

        self.addInstalledPluginsToDB(plugins_list, plugins_list_compendium)

    def removeManagedPluginsFromList(self, plugins_list, plugins_list_compendium):
        for plugin in plugins_list_compendium:
            doc = defusedxml.minidom.parse(plugin)
            nodes = doc.getElementsByTagName("Descriptors")[0].childNodes

            for node in nodes:
                if node.nodeName == "descriptor":
                    descriptor_path = os.path.join(
                        self.data_folder_plugins,
                        (GetText(node.childNodes).replace("\\", os.sep)),
                    )
                    try:
                        plugins_list.remove(descriptor_path)
                    except ValueError:
                        if not os.path.exists(descriptor_path):
                            self.addLog(plugin + " has misconfigured descriptors")

        return plugins_list, plugins_list_compendium

    def addInstalledPluginsToDB(self, plugins_list, plugins_list_compendium):
        table = self.winAddonManager.tablePluginsInstalled

        # Clears rows from db table if needed (This function is called to
        # add newly installed plugins after initial load as well)
        if self.isTableEmpty(table):
            self.c.execute("DELETE FROM tablePluginsInstalled")

        for plugin in plugins_list_compendium + plugins_list:
            # Sets tag for plugin file xml search and category for unmanaged plugins
            if plugin.endswith(".plugincompendium"):
                items_row = self.parseCompendiumFile(plugin, "PluginConfig")
                items_row = self.getOnlineAddonInfo(items_row, "tablePlugins")
            else:
                items_row = self.parseCompendiumFile(plugin, "Information")
                items_row[1] = "Unmanaged"

            self.addRowToDB(table, items_row)

        # Populate user visible table
        self.reloadSearch(self.winAddonManager.tablePluginsInstalled)

    def getAddonDependencies(self, dependencies_node):
        dependencies = ""
        for node in dependencies_node.childNodes:
            if node.nodeName == "dependency":
                dependencies = dependencies + "," + (GetText(node.childNodes))
        return dependencies[1:]

    # Returns list of common values for compendium or .plugin files
    def parseCompendiumFile(self, file, tag):
        items_row = [""] * (len(self.COLUMN_LIST) - 1)

        doc = defusedxml.minidom.parse(file)
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
            elif node.nodeName == "Dependencies":
                items_row[7] = self.getAddonDependencies(node)
            elif node.nodeName == "StartupScript":
                items_row[8] = GetText(node.childNodes)
        items_row[5] = file

        return items_row

    def getOnlineAddonInfo(self, items_row, remote_addons_table):
        for info in self.c.execute(
            "SELECT Category, LatestRelease FROM {table} WHERE InterfaceID == ?".format(  # nosec
                table=remote_addons_table
            ),
            (items_row[6],),
        ):
            items_row[1] = info[0]
            items_row[4] = info[1]

        # Unmanaged if not in online cache
        if not items_row[1]:
            items_row[1] = "Unmanaged"

        return items_row

    def openDB(self):
        """
        Opens addons_cache database and creates new database if 
        one doesn't exist or the current one has an outdated structure
        """
        addons_cache_db_path = os.path.join(self.settingsDir, "addons_cache.sqlite")
        if os.path.exists(addons_cache_db_path):
            # Connects to addons_cache database
            self.conn = sqlite3.connect(addons_cache_db_path)
            self.c = self.conn.cursor()

            # Replace old database if its structure is out of date
            if self.isCurrentDBOutdated():
                self.closeDB()
                os.remove(addons_cache_db_path)
                self.createDB()
        else:
            self.createDB()

    def isCurrentDBOutdated(self):
        """
        Checks if currently loaded database's structure is up to date.
        Returns True if it is outdated and False otherwise.
        """

        tables_dict = {}
        # SQL returns all the columns in all the tables labled with what table they're from
        for column_data in self.c.execute(
            "SELECT m.name as tableName, p.name as columnName FROM sqlite_master"
            " m left outer join pragma_table_info((m.name)) p on m.name <>"
            " p.name ORDER BY tableName, columnName"
        ):
            # Ignore tables without actual information
            if column_data[0].endswith(
                ("_idx", "_docsize", "_data", "_content", "_config")
            ):
                continue

            if column_data[0] in tables_dict:
                tables_dict[column_data[0]].append(column_data[1])
            else:
                tables_dict[column_data[0]] = [column_data[1]]

        for table in self.TABLE_LIST:
            if table in tables_dict:
                for column in self.COLUMN_LIST[1:]:
                    try:
                        tables_dict[table].remove(column)
                    except ValueError:
                        return True

                # Return true if there are extra columns in table
                if tables_dict[table]:
                    return True

                # Delete table from dictionary, so program can
                # check if there are extra tables in tables_dict afterwards
                del tables_dict[table]
            else:
                return True

        # Only return False if there are no extra tables
        if tables_dict:
            return True
        else:
            return False

    def createDB(self):
        """Creates ans sets up addons_cache database"""
        self.conn = sqlite3.connect(
            os.path.join(self.settingsDir, "addons_cache.sqlite")
        )
        self.c = self.conn.cursor()

        for table in self.TABLE_LIST:
            self.c.execute(
                "CREATE VIRTUAL TABLE {tbl_nm} USING FTS5({clmA}, {clmB}, {clmC}, "
                "{clmD}, {clmE}, {clmF}, {clmG}, {clmH}, {clmI})".format(
                    tbl_nm=table,
                    clmA=self.COLUMN_LIST[1],
                    clmB=self.COLUMN_LIST[2],
                    clmC=self.COLUMN_LIST[3],
                    clmD=self.COLUMN_LIST[4],
                    clmE=self.COLUMN_LIST[5],
                    clmF=self.COLUMN_LIST[6],
                    clmG=self.COLUMN_LIST[7],
                    clmH=self.COLUMN_LIST[8],
                    clmI=self.COLUMN_LIST[9],
                )
            )

    def closeDB(self):
        self.conn.commit()
        self.conn.close()

    def actionAddonImportSelected(self):
        # DDO doesn't support playing music from .abc files
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

    def installAddon(self, addon, interface_id=""):
        # Install .abc files
        if addon.endswith(".abc"):
            if self.currentGame.startswith("DDO"):
                self.addLog("DDO does not support .abc/music files")
                return

            copy(addon, self.data_folder_music)
            self.logger.info(addon + " installed")

            self.getInstalledMusic()
        elif addon.endswith(".rar"):
            self.addLog(
                "OneLauncher does not support .rar archives, because it"
                " is a proprietary format that would require and external "
                "program to extract"
            )
            return
        elif addon.endswith(".zip"):
            addon_type = ""
            with ZipFile(addon, "r") as file:
                files_list = file.namelist()
                if not files_list:
                    self.addLog("Add-on Zip is empty. Aborting")
                    return

                for entry in files_list:
                    if entry.endswith(".plugin"):
                        if self.currentGame.startswith("DDO"):
                            self.addLog("DDO does not support plugins")
                            return

                        addon_type = "Plugin"
                        table = self.winAddonManager.tablePlugins
                        folder_original = entry.split("/")[0]
                        path = self.data_folder_plugins
                        file.extractall(path=path)

                        folder = self.moveAddonsFromInvalidFolder(
                            self.data_folder_plugins, folder_original
                        )
                        updated_files_list = []
                        for entry in files_list:
                            try:
                                updated_files_list.append(
                                    os.path.join(folder, entry.split(folder)[1].strip("/"))
                                )
                            except IndexError:
                                # Anything that was in an invalid folder 
                                # should be ignored. This also fixes issues 
                                # with entries for the invalid folders such
                                # as 'Plugins/'
                                continue

                        plugins_list = []
                        for entry in updated_files_list:
                            if len(entry.split("/")) == 2:
                                if entry.endswith(".plugin"):
                                    plugins_list.append(
                                        os.path.join(self.data_folder_plugins, entry)
                                    )

                        plugins_list_compendium = []
                        if interface_id:
                            compendium_file = self.generateCompendiumFile(
                                updated_files_list,
                                folder,
                                interface_id,
                                addon_type,
                                path,
                                table.objectName(),
                            )
                            plugins_list_compendium = [compendium_file]

                        (
                            plugins_list,
                            plugins_list_compendium,
                        ) = self.removeManagedPluginsFromList(
                            plugins_list, plugins_list_compendium
                        )

                        self.addInstalledPluginsToDB(
                            plugins_list, plugins_list_compendium
                        )

                        self.handleStartupScriptActivationPrompt(table, interface_id)
                        self.logger.info(
                            "Installed addon corresponding to "
                            + str(plugins_list)
                            + str(plugins_list_compendium)
                        )

                        self.installAddonRemoteDependencies(
                            table.objectName() + "Installed"
                        )
                        return
                    elif entry.endswith(".abc"):
                        if self.currentGame.startswith("DDO"):
                            self.addLog("DDO does not support .abc/music files")
                            return

                        # Some plugins have .abc files, but music collections
                        # shouldn't have .plugin files.
                        if self.checkForPluginFile(files_list):
                            continue

                        addon_type = "Music"
                        table = self.winAddonManager.tableMusic

                        path, folder = self.getAddonInstallationFolder(
                            entry, addon, files_list, self.data_folder_music
                        )
                        file.extractall(path=path)
                        self.logger.info(addon + " music installed")

                        folder = self.moveAddonsFromInvalidFolder(
                            self.data_folder_music, folder
                        )

                        if interface_id:
                            compendium_file = self.generateCompendiumFile(
                                files_list,
                                folder,
                                interface_id,
                                addon_type,
                                path,
                                table.objectName(),
                            )
                        self.getInstalledMusic(folders_list=[folder])

                        self.handleStartupScriptActivationPrompt(table, interface_id)

                        self.installAddonRemoteDependencies(
                            table.objectName() + "Installed"
                        )
                        return
                if not addon_type:
                    addon_type = "Skin"
                    table = self.winAddonManager.tableSkins
                    path, folder = self.getAddonInstallationFolder(
                        entry, addon, files_list, self.data_folder_skins
                    )
                    file.extractall(path=path)
                    self.logger.info(addon + " skin installed")

                    folder = self.moveAddonsFromInvalidFolder(
                        self.data_folder_skins, folder
                    )

                    if interface_id:
                        compendium_file = self.generateCompendiumFile(
                            files_list,
                            folder,
                            interface_id,
                            addon_type,
                            path,
                            table.objectName(),
                        )
                    self.getInstalledSkins(folders_list=[folder])

                    self.handleStartupScriptActivationPrompt(table, interface_id)

                    self.installAddonRemoteDependencies(
                        table.objectName() + "Installed"
                    )
                    return

    def checkForPluginFile(self, files_list):
        """Returns True if list of files contains a .plugin file"""
        for entry in files_list:
            if entry.endswith(".plugin"):
                return True

    def installAddonRemoteDependencies(self, table):
        """Installs the dependencies for the last installed addon"""
        # Gets dependencies for last column in db
        for item in self.c.execute(
            "SELECT Dependencies FROM {table} ORDER BY rowid DESC LIMIT 1".format(  # nosec
                table=table
            )
        ):
            dependencies = item[0]

        for dependency in dependencies.split(","):
            if dependency:
                # 0 is the arbitrary ID for Turbine Utilities. 1064 is the ID
                # of OneLauncher's upload of the utilities on LotroInterface
                if dependency == "0":
                    dependency = "1064"

                for item in self.c.execute(  # nosec
                    "SELECT File, Name FROM {table} WHERE InterfaceID = ? AND InterfaceID NOT IN "
                    "(SELECT InterfaceID FROM {table_installed})".format(
                        table=table.split("Installed")[0], table_installed=table,
                    ),
                    (dependency,),
                ):
                    self.installRemoteAddon(item[0], item[1], dependency)

    # Gets folder and makes one if there is no root folder
    def getAddonInstallationFolder(self, entry, addon, files_list, data_folder):
        # Gets list of base folders in archive
        folders_list = []
        for file in files_list:
            folder = file.split(os.path.sep)[0]
            if folder not in folders_list:
                folders_list.append(folder)

        # If no root folder or multiple root folders
        if len(entry.split(os.path.sep)) == 1 or len(folders_list) > 1:
            name = os.path.split(os.path.splitext(addon)[0])[1]
            path = os.path.join(data_folder, name)
            os.makedirs(os.path.split(path)[0], exist_ok=True)
            folder = name
        else:
            path = data_folder
            folder = entry.split("/")[0]

        return path, folder

    # Scans data folder for invalid folder names like "ui" or "plugins" and moves stuff out of them
    def moveAddonsFromInvalidFolder(
        self, data_folder, folder, folders_list=[], folders=""
    ):
        invalid_folder_names = [
            "ui",
            "skins",
            "Plugins",
            "Music",
            "My Documents",
            "Documents",
            "The Lord of the Rings Online",
            "Dungeons and Dragons Online",
            "Dungeons & Dragons Online",
        ]

        if not folders_list:
            folders_list = [folder]

        for folder in folders_list:
            folder = folder.strip(os.path.sep)
            folder = os.path.split(folder)[1]
            if folder in invalid_folder_names:
                folders = os.path.join(folders, folder)
                folders_list = glob(os.path.join(data_folder, folders, "*", ""))
                output = self.moveAddonsFromInvalidFolder(
                    data_folder, "", folders_list=folders_list, folders=folders
                )
                return output

        if folders:
            # List of the folders that will be moved to the data folder
            addon_folders_list = []

            for file in os.listdir(os.path.join(data_folder, folders)):
                if os.path.isdir(os.path.join(data_folder, folders, file)):
                    addon_folders_list.append(file)
                move(os.path.join(data_folder, folders, file), data_folder)

            rmtree(os.path.join(data_folder, folders.split(os.path.sep)[0]))

            return addon_folders_list[0]
        else:
            return folder

    # Generates a compendium file for remote addon
    def generateCompendiumFile(
        self, files_list, folder, interface_id, addon_type, path, table
    ):
        dependencies = []
        startup_python_script = ""
        # Return if a compendium file already exists
        for file in files_list:
            if file.endswith(addon_type.lower() + "compendium"):
                # Path includes folder when one has to be generated
                tmp_folder = folder
                if path.endswith(folder):
                    tmp_folder = ""

                compendium_file_path = os.path.join(
                    path, tmp_folder, os.path.split(file)[1]
                )
                if os.path.exists(compendium_file_path):
                    existing_compendium_values = self.parseCompendiumFile(
                        compendium_file_path, addon_type + "Config"
                    )
                    dependencies = existing_compendium_values[7]
                    startup_python_script = existing_compendium_values[8]
                    os.remove(compendium_file_path)

        for row in self.c.execute(
            "SELECT * FROM {table} WHERE InterfaceID = ?".format(table=table),  # nosec
            (interface_id,),
        ):
            if row[0]:
                doc = Document()
                mainNode = doc.createElementNS(EMPTY_NAMESPACE, addon_type + "Config")
                doc.appendChild(mainNode)

                tempNode = doc.createElementNS(EMPTY_NAMESPACE, "Id")
                tempNode.appendChild(doc.createTextNode("%s" % (row[6])))
                mainNode.appendChild(tempNode)

                tempNode = doc.createElementNS(EMPTY_NAMESPACE, "Name")
                tempNode.appendChild(doc.createTextNode("%s" % (row[0])))
                mainNode.appendChild(tempNode)

                tempNode = doc.createElementNS(EMPTY_NAMESPACE, "Version")
                tempNode.appendChild(doc.createTextNode("%s" % (row[2])))
                mainNode.appendChild(tempNode)

                tempNode = doc.createElementNS(EMPTY_NAMESPACE, "Author")
                tempNode.appendChild(doc.createTextNode("%s" % (row[3])))
                mainNode.appendChild(tempNode)

                tempNode = doc.createElementNS(EMPTY_NAMESPACE, "InfoUrl")
                tempNode.appendChild(
                    doc.createTextNode("%s" % (self.getInterfaceInfoUrl(row[5])))
                )
                mainNode.appendChild(tempNode)

                tempNode = doc.createElementNS(EMPTY_NAMESPACE, "DownloadUrl")
                tempNode.appendChild(doc.createTextNode("%s" % (row[5])))
                mainNode.appendChild(tempNode)

                if addon_type == "Plugin":
                    # Add addon's .plugin files
                    descriptorsNode = doc.createElementNS(
                        EMPTY_NAMESPACE, "Descriptors"
                    )
                    mainNode.appendChild(descriptorsNode)
                    for file in files_list:
                        if file.endswith(".plugin"):
                            tempNode = doc.createElementNS(
                                EMPTY_NAMESPACE, "descriptor"
                            )
                            tempNode.appendChild(
                                doc.createTextNode("%s" % (file.replace("/", "\\")))
                            )
                            descriptorsNode.appendChild(tempNode)

                # Can't add dependencies, because they are defined in compendium files
                dependenciesNode = doc.createElementNS(EMPTY_NAMESPACE, "Dependencies")
                mainNode.appendChild(dependenciesNode)

                # If compendium file from add-on already existed with dependencies
                if dependencies:
                    for dependency in dependencies.split(","):
                        tempNode = doc.createElementNS(EMPTY_NAMESPACE, "dependency")
                        tempNode.appendChild(doc.createTextNode("%s" % (dependency)))
                        dependenciesNode.appendChild(tempNode)

                # Can't add startup script, because it is defined in compendium files
                startupScriptNode = doc.createElementNS(
                    EMPTY_NAMESPACE, "StartupScript"
                )
                # If compendium file from add-on already existed with startup script
                if startup_python_script:
                    startupScriptNode.appendChild(
                        doc.createTextNode("%s" % (startup_python_script))
                    )
                mainNode.appendChild(startupScriptNode)

                # Write compendium file

                # Path includes folder when one has to be generated
                if path.endswith(folder):
                    folder = ""

                compendium_file = os.path.join(
                    path, folder, row[0] + "." + addon_type.lower() + "compendium",
                )
                with open(compendium_file, "w+") as file:
                    pretty_xml = prettify_xml(doc.toxml())
                    file.write(pretty_xml)

                return compendium_file

    # Replaces "download" with "info" in download url to make info url
    def getInterfaceInfoUrl(self, download_url):
        download_url_tail = os.path.split(download_url)[1]
        info_url = download_url.replace(
            download_url_tail, download_url_tail.replace("download", "info")
        )
        return info_url

    def txtSearchBarTextChanged(self, text):
        if self.currentGame.startswith("LOTRO"):
            # If in Installed tab
            if self.winAddonManager.tabWidget.currentIndex() == 0:
                index_installed = self.winAddonManager.tabWidgetInstalled.currentIndex()

                # If in PluginsInstalled tab
                if index_installed == 0:
                    self.searchDB(self.winAddonManager.tablePluginsInstalled, text)
                # If in SkinsInstalled tab
                elif index_installed == 1:
                    self.searchDB(self.winAddonManager.tableSkinsInstalled, text)
                # If in MusicInstalled tab
                elif index_installed == 2:
                    self.searchDB(self.winAddonManager.tableMusicInstalled, text)
            # If in Find More tab
            elif self.winAddonManager.tabWidget.currentIndex() == 1:
                index_remote = self.winAddonManager.tabWidgetRemote.currentIndex()
                # If in Plugins tab
                if index_remote == 0:
                    self.searchDB(self.winAddonManager.tablePlugins, text)
                # If in Skins tab
                elif index_remote == 1:
                    self.searchDB(self.winAddonManager.tableSkins, text)
                # If in Music tab
                elif index_remote == 2:
                    self.searchDB(self.winAddonManager.tableMusic, text)
        else:
            # If in Installed tab
            if self.winAddonManager.tabWidget.currentIndex() == 0:
                self.searchDB(self.winAddonManager.tableSkinsInstalled, text)
            # If in Find More tab
            elif self.winAddonManager.tabWidget.currentIndex() == 1:
                self.searchDB(self.winAddonManager.tableSkins, text)

    def searchDB(self, table, text):
        table.clearContents()
        table.setRowCount(0)

        if text:
            for word in text.split():
                search_word = "%" + word + "%"

                for row in self.c.execute(
                    "SELECT rowid, * FROM {table} WHERE Author LIKE ? OR Category"  # nosec
                    " LIKE ? OR Name LIKE ?".format(table=table.objectName()),
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
                "SELECT rowid, * FROM {table}".format(table=table.objectName())  # nosec
            ):
                self.addRowToTable(table, row)

    def isTableEmpty(self, table):
        if table.item(0, 1):
            return False
        else:
            return True

    def reloadSearch(self, table):
        """Re-searches the current search"""
        self.searchDB(table, self.winAddonManager.txtSearchBar.text())

    def resetRemoteAddonsTables(self):
        for i in range(self.winAddonManager.tabWidgetRemote.count()):
            tab = self.winAddonManager.tabWidgetRemote.widget(i)
            table = getattr(
                self.winAddonManager, tab.objectName().replace("tab", "table")
            )
            if not self.isTableEmpty(table):
                self.searchDB(table, "")

    def setRemoteAddonToUninstalled(self, addon, remote_table):
        self.c.execute(
            "UPDATE {table} SET Name = ? WHERE InterfaceID == ?".format(  # nosec
                table=remote_table.objectName()
            ),
            (addon[2], addon[0],),
        )

        # Removes indicator that a new version of an installed addon is out if present.
        # This is important, because addons are uninstalled and then reinstalled
        # during the update process.
        self.c.execute(
            "UPDATE {table} SET Version = REPLACE(Version,'(Updated) ', '') WHERE "  # nosec
            "Version LIKE '(Updated) %'".format(table=remote_table.objectName())
        )

    def setRemoteAddonToInstalled(self, addon, remote_table):
        self.c.execute(
            "UPDATE {table} SET Name = ? WHERE InterfaceID == ?".format(  # nosec
                table=remote_table.objectName()
            ),
            ("(Installed) " + addon[2], addon[0],),
        )

    # Adds row to a visible table. First value in list is row name
    def addRowToTable(self, table, list):
        table.setSortingEnabled(False)

        disable_row = False

        rows = table.rowCount()
        table.setRowCount(rows + 1)

        # Sets row name
        tbl_item = QtWidgets.QTableWidgetItem()
        tbl_item.setText(str(list[0]))

        # Adds items to row
        for column, item in enumerate(list):
            tbl_item = QtWidgets.QTableWidgetItem()

            tbl_item.setText(str(item))
            # Sets color to red if addon is unmanaged
            if item == "Unmanaged" and column == 2:
                tbl_item.setForeground(QtGui.QColor("darkred"))
            # Disable row if addon is Installed. This is only applicable to remote tables.
            elif str(item).startswith("(Installed) ") and column == 1:
                tbl_item.setText(item.split("(Installed) ")[1])
                disable_row = True
            elif str(item).startswith("(Updated) ") and column == 3:
                tbl_item.setText(item.split("(Updated) ")[1])
                tbl_item.setForeground(QtGui.QColor("green"))
            elif str(item).startswith("(Outdated) ") and column == 3:
                tbl_item.setText(item.split("(Outdated) ")[1])
                tbl_item.setForeground(QtGui.QColor("crimson"))

            table.setItem(rows, column, tbl_item)

        if disable_row:
            for i in range(table.columnCount()):
                table.item(rows, i).setFlags(QtCore.Qt.ItemIsEnabled)
                table.item(rows, i).setBackground(self.installed_addons_color)

        table.setSortingEnabled(True)

    def addRowToDB(self, table, list):
        question_marks = "?"
        for i in range(len(list) - 1):
            question_marks = question_marks + ",?"

        self.c.execute(
            "INSERT INTO {table} VALUES({})".format(
                question_marks, table=table.objectName()
            ),
            (list),  # nosec
        )

    def btnBoxActivated(self):
        self.winAddonManager.accept()

    def btnLogClicked(self):
        if self.winAddonManager.txtLog.isHidden():
            self.winAddonManager.txtLog.show()
        else:
            self.winAddonManager.txtLog.hide()

    def addLog(self, message):
        self.winAddonManager.lblErrors.setText(
            "Errors: " + str(int(self.winAddonManager.lblErrors.text()[-1]) + 1)
        )
        self.logger.warning(message)
        self.winAddonManager.txtLog.append(message + "\n")

    def btnAddonsClicked(self):
        table = self.getCurrentTable()

        # If on installed tab which means remove addons
        if table.objectName().endswith("Installed"):
            uninstall_function = self.getUninstallFunctionFromTable(table)

            uninstallConfirm, addons = self.getUninstallConfirm(table)
            if uninstallConfirm:
                uninstall_function(addons, table)
                self.resetRemoteAddonsTables()

        elif self.winAddonManager.tabWidget.currentIndex() == 1:
            self.installRemoteAddons()

    def getUninstallFunctionFromTable(self, table):
        """Gives function to uninstall addon type for table"""
        if "Skins" in table.objectName():
            uninstall_function = self.uninstallSkins
        elif "Plugins" in table.objectName():
            uninstall_function = self.uninstallPlugins
        elif "Music" in table.objectName():
            uninstall_function = self.uninstallMusic
        else:
            raise IndexError(
                table.objectName() + " doesn't correspond to add-on type tab"
            )

        return uninstall_function

    def installRemoteAddons(self):
        table = self.getCurrentTable()

        addons, details = self.getSelectedAddons(table)
        if addons and details:
            for addon in addons:
                self.installRemoteAddon(addon[1], addon[2], addon[0])
                self.setRemoteAddonToInstalled(addon, table)

            self.resetRemoteAddonsTables()
            self.searchSearchBarContents()

    def getCurrentTable(self):
        """Return the table that the user currently sees based on what tabs they are in"""
        if self.winAddonManager.tabWidget.currentIndex() == 0:
            if self.currentGame.startswith("LOTRO"):
                index_installed = self.winAddonManager.tabWidgetInstalled.currentIndex()

                if index_installed == 0:
                    table = self.winAddonManager.tablePluginsInstalled
                elif index_installed == 1:
                    table = self.winAddonManager.tableSkinsInstalled
                elif index_installed == 2:
                    table = self.winAddonManager.tableMusicInstalled
            else:
                table = self.winAddonManager.tableSkinsInstalled
        elif self.winAddonManager.tabWidget.currentIndex() == 1:
            if self.currentGame.startswith("DDO"):
                table = self.winAddonManager.tableSkins
            else:
                index_remote = self.winAddonManager.tabWidgetRemote.currentIndex()

                if index_remote == 0:
                    table = self.winAddonManager.tablePlugins
                elif index_remote == 1:
                    table = self.winAddonManager.tableSkins
                elif index_remote == 2:
                    table = self.winAddonManager.tableMusic
        else:
            raise IndexError(
                str(self.winAddonManager.tabWidget.currentIndex())
                + " isn't valid main tab index"
            )

        return table

    def installRemoteAddon(self, url, name, interface_id):
        path = os.path.join(self.data_folder, "Downloads", name + ".zip")
        os.makedirs(os.path.split(path)[0], exist_ok=True)
        status = self.downloader(url, path)
        if status:
            self.installAddon(path, interface_id=interface_id)
            os.remove(path)

    def getUninstallConfirm(self, table):
        addons, details = self.getSelectedAddons(table)
        if addons and details:
            num_depends = len(details.split("\n")) - 1
            if num_depends == 1:
                plural, plural1 = "this ", " addon?"
            else:
                plural, plural1 = "these ", " addons?"
            text = (
                "Are you sure you want to remove " + plural + str(len(addons)) + plural1
            )
            if self.confirmationPrompt(text, details):
                return True, addons
            else:
                return False, addons
        else:
            return False, addons

    def getSelectedAddons(self, table):
        if table.selectedItems():
            selected_addons = []
            details = ""
            # Column count is minus one because of hidden ID column
            for item in table.selectedItems()[0 :: (table.columnCount() - 1)]:
                # Gets db row id for selected row
                selected_row = int((table.item(item.row(), 0)).text())

                selected_name = table.item(item.row(), 1).text()

                for selected_addon in self.c.execute(
                    "SELECT InterfaceID, File, Name FROM {table} WHERE rowid = ?".format(  # nosec
                        table=table.objectName()
                    ),
                    (selected_row,),
                ):
                    selected_addons.append(selected_addon)
                    details = details + selected_name + "\n"

            return selected_addons, details
        else:
            return None, None

    def uninstallPlugins(self, plugins, table):
        for plugin in plugins:
            if plugin[1].endswith(".plugin"):
                plugin_files = [plugin[1]]
            else:
                plugin_files = []
                if self.checkAddonForDependencies(plugin, table):
                    doc = defusedxml.minidom.parse(plugin[1])
                    nodes = doc.getElementsByTagName("Descriptors")[0].childNodes
                    for node in nodes:
                        if node.nodeName == "descriptor":
                            plugin_files.append(
                                os.path.join(
                                    self.data_folder_plugins,
                                    (GetText(node.childNodes).replace("\\", os.sep)),
                                )
                            )
                    # Check for startup scripts to remove them
                    nodes = doc.getElementsByTagName("PluginConfig")[0].childNodes
                    for node in nodes:
                        if node.nodeName == "StartupScript":
                            script = GetText(node.childNodes)
                            self.uninstallStartupScript(
                                script, self.data_folder_plugins
                            )
                else:
                    continue

            for plugin_file in plugin_files:
                if os.path.exists(plugin_file):
                    doc = defusedxml.minidom.parse(plugin_file)
                    nodes = doc.getElementsByTagName("Plugin")[0].childNodes
                    for node in nodes:
                        if node.nodeName == "Package":
                            plugin_folder = os.path.split(
                                GetText(node.childNodes).replace(".", os.sep)
                            )[0]

                            # Removes plugin and all related files
                            if os.path.exists(
                                self.data_folder_plugins + os.sep + plugin_folder
                            ):
                                rmtree(
                                    self.data_folder_plugins + os.sep + plugin_folder
                                )
                    if os.path.exists(plugin_file):
                        os.remove(plugin_file)
            if os.path.exists(plugin[1]):
                os.remove(plugin[1])

            self.logger.info(str(plugin) + " plugin uninstalled")

            self.setRemoteAddonToUninstalled(plugin, self.winAddonManager.tablePlugins)

        # Reloads plugins
        table.clearContents()
        self.getInstalledPlugins()

    def uninstallSkins(self, skins, table):
        for skin in skins:
            if skin[1].endswith(".skincompendium"):
                skin_path = os.path.split(skin[1])[0]

                items_row = self.parseCompendiumFile(skin[1], "SkinConfig")
                script = items_row[8]
                self.uninstallStartupScript(script, self.data_folder_skins)
            else:
                skin_path = skin[1]
            rmtree(skin_path)

            self.logger.info(str(skin) + " skin uninstalled")

            self.setRemoteAddonToUninstalled(skin, self.winAddonManager.tableSkins)

        # Reloads skins
        table.clearContents()
        self.getInstalledSkins()

    def uninstallMusic(self, music_list, table):
        for music in music_list:
            if music[1].endswith(".musiccompendium"):
                music_path = os.path.split(music[1])[0]

                items_row = self.parseCompendiumFile(music[1], "MusicConfig")
                script = items_row[8]
                self.uninstallStartupScript(script, self.data_folder_music)
            else:
                music_path = music[1]

            if music_path.endswith(".abc"):
                os.remove(music_path)
            else:
                rmtree(music_path)

            self.logger.info(str(music) + " music uninstalled")

            self.setRemoteAddonToUninstalled(music, self.winAddonManager.tableMusic)

        # Reloads music
        table.clearContents()
        self.getInstalledMusic()

    def checkAddonForDependencies(self, addon, table):
        # Turbine Utilities is treated as having ID 0
        if addon[0] == "1064":
            addon_ID = "0"
        else:
            addon_ID = addon[0]

        details = ""

        for dependent in self.c.execute(
            'SELECT Name, Dependencies FROM {table} WHERE Dependencies != ""'.format(  # nosec
                table=table.objectName()
            )
        ):
            for dependency in dependent[1].split(","):
                if dependency == addon_ID:
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
        messageBox.setIcon(QtWidgets.QMessageBox.Question)
        messageBox.setStandardButtons(messageBox.Apply | messageBox.Cancel)

        messageBox.setInformativeText(text)
        messageBox.setDetailedText(details)

        # Checks if user accepts dialogue
        if messageBox.exec() == 33554432:
            return True
        else:
            return False

    def searchSearchBarContents(self):
        """
            Used to re-search users' search when new tabs are selected
        """
        user_search = self.winAddonManager.txtSearchBar.text()
        self.txtSearchBarTextChanged(user_search)

    def tabWidgetInstalledIndexChanged(self, index):
        self.updateAddonFolderActions(index)

        # Load in installed skins on first switch to tab
        if index == 1:
            self.loadSkinsIfNotDone()

        # Load in installed music on first switch to tab
        if index == 2:
            self.loadMusicIfNotDone()

        self.searchSearchBarContents()

    def loadSkinsIfNotDone(self):
        if self.isTableEmpty(self.winAddonManager.tableSkinsInstalled):
            self.getInstalledSkins()

    def loadMusicIfNotDone(self):
        if self.isTableEmpty(self.winAddonManager.tableMusicInstalled):
            self.getInstalledMusic()

    def tabWidgetRemoteIndexChanged(self, index):
        self.updateAddonFolderActions(index)

        self.searchSearchBarContents()

    def tabWidgetIndexChanged(self, index):
        if index == 0:
            self.winAddonManager.btnAddons.setText("-")
            self.winAddonManager.btnAddons.setToolTip("Remove addons")

            index_installed = self.winAddonManager.tabWidgetInstalled.currentIndex()
            self.updateAddonFolderActions(index_installed)
        elif index == 1:
            self.winAddonManager.btnAddons.setText("+")
            self.winAddonManager.btnAddons.setToolTip("Install addons")

            index_remote = self.winAddonManager.tabWidgetRemote.currentIndex()
            self.updateAddonFolderActions(index_remote)

            # Populates remote addons tables if not done already
            if self.isTableEmpty(self.winAddonManager.tableSkins):
                if self.loadRemoteAddons():
                    self.getOutOfDateAddons()

        self.searchSearchBarContents()

    def loadRemoteAddons(self):
        if self.currentGame.startswith("LOTRO"):
            # Only keep loading remote add-ons if the first load doesn't run into issues
            if self.getRemoteAddons(self.PLUGINS_URL, self.winAddonManager.tablePlugins):
                self.getRemoteAddons(self.SKINS_URL, self.winAddonManager.tableSkins)
                self.getRemoteAddons(self.MUSIC_URL, self.winAddonManager.tableMusic)
                return True
        else:
            if self.getRemoteAddons(self.SKINS_DDO_URL, self.winAddonManager.tableSkins):
                return True

    def getRemoteAddons(self, favorites_url, table):
        # Clears rows from db table
        self.c.execute("DELETE FROM {table}".format(table=table.objectName()))  # nosec

        # Gets list of Interface IDs for installed addons
        installed_IDs = []
        for ID in self.c.execute(
            "SELECT InterfaceID FROM {table}".format(  # nosec
                table=table.objectName() + "Installed"
            )
        ):
            if ID[0]:
                installed_IDs.append(ID[0])

        try:
            addons_file = urllib.request.urlopen(favorites_url).read().decode()  # nosec
        except (urllib.error.URLError, urllib.error.HTTPError) as error:
            self.logger.error(error.reason, exc_info=True)
            self.addLog(
                "There was a network error. You may want to check your connection."
            )
            self.winAddonManager.tabWidget.setCurrentIndex(0)
            return False

        doc = defusedxml.minidom.parseString(addons_file)
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
                        "%Y-%m-%d", localtime(int(GetText(node.childNodes)))
                    )
                elif node.nodeName == "UIFileURL":
                    items_row[5] = GetText(node.childNodes)

            # Prepends name with (Installed) if already installed
            if items_row[6] in installed_IDs:
                items_row[0] = "(Installed) " + items_row[0]

            self.addRowToDB(table, items_row)

        # Populate user visible table. This should not reload the current search.
        self.searchDB(table, "")

        return True

    # Downloads file from url to path and shows progress with self.handleDownloadProgress
    def downloader(self, url, path):
        if url.lower().startswith("http"):
            try:
                urllib.request.urlretrieve(  # nosec
                    url, path, self.handleDownloadProgress
                )
            except (urllib.error.URLError, urllib.error.HTTPError) as error:
                self.logger.error(error.reason, exc_info=True)
                self.addLog(
                    "There was a network error. You may want to check your connection."
                )
                return False
        else:
            raise ValueError from None

        self.winAddonManager.progressBar.setValue(0)
        return True

    def handleDownloadProgress(self, index, frame, size):
        # Updates progress bar with download progress
        percent = 100 * index * frame // size
        self.winAddonManager.progressBar.setValue(percent)

    def Run(self):
        self.winAddonManager.exec()
        self.closeDB()

    def contextMenuRequested(self, cursor_position):
        global_cursor_position = self.winAddonManager.mapToGlobal(cursor_position)

        # It is not a local variable, because of garbage collection
        self.winAddonManager.contextMenu = self.getContextMenu(global_cursor_position)
        if self.winAddonManager.contextMenu:
            self.winAddonManager.contextMenu.popup(global_cursor_position)

    def getContextMenu(self, global_cursor_position):
        menu = QtWidgets.QMenu()

        selected_widget = QtWidgets.QApplication.instance().widgetAt(
            global_cursor_position
        )

        parent_widget = selected_widget.parent()
        if parent_widget.objectName().startswith("table"):
            self.context_menu_selected_table = parent_widget
            selected_item = self.context_menu_selected_table.itemAt(
                selected_widget.mapFromGlobal(global_cursor_position)
            )
            if selected_item:
                self.context_menu_selected_row = selected_item.row()

                # If addon has online page
                self.context_menu_selected_interface_ID = self.getTableRowInterfaceID(
                    self.context_menu_selected_table, self.context_menu_selected_row
                )
                if self.context_menu_selected_interface_ID:
                    menu.addAction(self.winAddonManager.actionShowOnLotrointerface)

                # If addon is installed
                if self.context_menu_selected_table.objectName().endswith("Installed"):
                    menu.addAction(self.winAddonManager.actionUninstallAddon)
                    menu.addAction(self.winAddonManager.actionShowAddonInFileManager)
                else:
                    # If addon in remote table is installed
                    if (
                        selected_item.background().color()
                        == self.installed_addons_color
                    ):
                        menu.addAction(self.winAddonManager.actionUninstallAddon)
                        menu.addAction(
                            self.winAddonManager.actionShowAddonInFileManager
                        )
                    else:
                        menu.addAction(self.winAddonManager.actionInstallAddon)

                # If addon has a new version available
                version_item = self.context_menu_selected_table.item(
                    self.context_menu_selected_row, 3
                )
                version_color = version_item.foreground().color()
                if version_color in [QtGui.QColor("crimson"), QtGui.QColor("green")]:
                    menu.addAction(self.winAddonManager.actionUpdateAddon)

                # If addon has a statup script
                relative_script_path = self.getRelativeStartupScriptFromInterfaceID(
                    self.context_menu_selected_table,
                    self.context_menu_selected_interface_ID,
                )
                if relative_script_path:
                    # If startup script is enabled
                    if relative_script_path in self.startupScripts:
                        menu.addAction(self.winAddonManager.actionDisableStartupScript)
                    else:
                        menu.addAction(self.winAddonManager.actionEnableStartupScript)

        # Only return menu if something has been added to it
        if not menu.isEmpty():
            return menu
        else:
            return None

    def getTableRowInterfaceID(self, table: QtWidgets.QTableWidget, row: int):
        addon_db_id = table.item(row, 0).text()

        for interface_ID in self.c.execute(
            "SELECT InterfaceID FROM {table} WHERE rowid = ?".format(  # nosec
                table=table.objectName()
            ),
            (addon_db_id,),
        ):
            if interface_ID[0]:
                return interface_ID[0]
            else:
                return None

    def actionShowOnLotrointerfaceSelected(self):
        table = self.context_menu_selected_table
        row = self.context_menu_selected_row
        interface_ID = self.getAddonListObjectFromRow(table, row)[0]

        url = self.getAddonUrlFromInterfaceID(interface_ID, table)

        if url:
            QtGui.QDesktopServices.openUrl(url)

    def getAddonUrlFromInterfaceID(
        self, interface_ID, table: QtWidgets.QTableWidget, download_url: bool = False
    ):
        """Returns info URL for addon or download URL if download_url=True"""
        # URL is only in remote version of table
        table = self.getRemoteOrLocalTableFromOne(table, remote=True)

        for addon_url in self.c.execute(
            "SELECT File FROM {table} WHERE InterfaceID = ?".format(  # nosec
                table=table.objectName()
            ),
            (interface_ID,),
        ):
            if addon_url[0]:
                if not download_url:
                    url = self.getInterfaceInfoUrl(addon_url[0])
                else:
                    url = addon_url[0]

                return url

    def getAddonFileFromInterfaceID(self, interface_ID, table):
        """Returns file location of addon"""
        # File is only in "Installed" version of table. The "File" field
        # has the download url in the remote tables.
        table = self.getRemoteOrLocalTableFromOne(table, remote=False)

        for file in self.c.execute(
            "SELECT File FROM {table} WHERE InterfaceID = ?".format(  # nosec
                table=table.objectName()
            ),
            (interface_ID,),
        ):
            if file[0]:
                return file[0]

    def showSelectedOnLotrointerface(self):
        table = self.getCurrentTable()
        selected_addons = self.getSelectedAddons(table)

        if selected_addons[0]:
            for addon in selected_addons[0]:
                info_url = self.getAddonUrlFromInterfaceID(
                    addon[0], table, download_url=False
                )
                QtGui.QDesktopServices.openUrl(info_url)

    def actionInstallAddonSelected(self):
        """
        Installs addon selected by context menu. This function
        should only be called while in one of the remote/find more
        tabs of the UI.
        """
        table = self.context_menu_selected_table
        row = self.context_menu_selected_row
        addon = self.getAddonListObjectFromRow(table, row)

        self.installRemoteAddon(addon[1], addon[2], addon[0])
        self.setRemoteAddonToInstalled(addon, table)

        self.resetRemoteAddonsTables()
        self.searchSearchBarContents()

    def actionUninstallAddonSelected(self):
        table = self.context_menu_selected_table
        row = self.context_menu_selected_row
        addon = self.getAddonListObjectFromRow(table, row, remote=False)

        if self.confirmationPrompt(
            "Are you sure you want to uninstall this addon?", addon[2]
        ):
            uninstall_function = self.getUninstallFunctionFromTable(table)

            table_installed = self.getRemoteOrLocalTableFromOne(table, remote=False)
            uninstall_function([addon], table_installed)

            self.resetRemoteAddonsTables()
            self.searchSearchBarContents()

    def getAddonListObjectFromRow(
        self, table: QtWidgets.QTableWidget, row, remote=True
    ):
        """
        Gives list of information for addon. The information is:
        [Interface ID, URL/File (depending on if remote = True or False), Name]
        """
        interface_ID = self.getTableRowInterfaceID(table, row)

        if remote:
            table_remote = self.getRemoteOrLocalTableFromOne(table, remote=True)
            file = self.getAddonUrlFromInterfaceID(
                interface_ID, table_remote, download_url=True
            )
        else:
            table_installed = self.getRemoteOrLocalTableFromOne(table, remote=False)

            if table.objectName().endswith("Installed"):
                self.reloadSearch(table_installed)

                for item in self.c.execute(
                    "SELECT File FROM {table} WHERE rowid=?".format(  # nosec
                        table=table_installed.objectName()
                    ),
                    (table_installed.item(row, 0).text(),),
                ):
                    file = item[0]
            else:
                file = self.getAddonFileFromInterfaceID(interface_ID, table_installed)

        addon = [interface_ID, file, table.item(row, 1).text()]

        return addon

    def getRemoteOrLocalTableFromOne(
        self, input_table: QtWidgets.QTableWidget, remote: bool = False
    ):
        table_name = input_table.objectName()
        # UI table object names are renamed with DDO in them when the current game is
        # DDO for DB access, but the callable name for the UI tables stays the same.
        table_name = table_name.replace("DDO", "")

        if remote:
            table = getattr(self.winAddonManager, table_name.split("Installed")[0])
            return table
        else:
            if table_name.endswith("Installed"):
                table = input_table
            else:
                table = getattr(self.winAddonManager, table_name + "Installed")
            return table

    def actionShowAddonInFileManagerSelected(self):
        table = self.context_menu_selected_table
        row = self.context_menu_selected_row
        addon = self.getAddonListObjectFromRow(table, row, remote=False)

        addon_folder = os.path.dirname(addon[1])
        QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(addon_folder))

    def actionShowPluginsFolderSelected(self):
        folder = self.data_folder_plugins
        QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(folder))

    def actionShowSkinsFolderSelected(self):
        folder = self.data_folder_skins
        QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(folder))

    def actionShowMusicFolderSelected(self):
        folder = self.data_folder_music
        QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(folder))

    def updateAddonFolderActions(self, index):
        """Makes only action for opening addon folder associated with tab visible"""
        if self.currentGame.startswith("DDO"):
            self.winAddonManager.actionShowPluginsFolderInFileManager.setVisible(False)
            self.winAddonManager.actionShowSkinsFolderInFileManager.setVisible(True)
            self.winAddonManager.actionShowMusicFolderInFileManager.setVisible(False)
        elif index == 0:
            self.winAddonManager.actionShowPluginsFolderInFileManager.setVisible(True)
            self.winAddonManager.actionShowSkinsFolderInFileManager.setVisible(False)
            self.winAddonManager.actionShowMusicFolderInFileManager.setVisible(False)
        elif index == 1:
            self.winAddonManager.actionShowPluginsFolderInFileManager.setVisible(False)
            self.winAddonManager.actionShowSkinsFolderInFileManager.setVisible(True)
            self.winAddonManager.actionShowMusicFolderInFileManager.setVisible(False)
        elif index == 2:
            self.winAddonManager.actionShowPluginsFolderInFileManager.setVisible(False)
            self.winAddonManager.actionShowSkinsFolderInFileManager.setVisible(False)
            self.winAddonManager.actionShowMusicFolderInFileManager.setVisible(True)

    def checkForUpdates(self):
        if self.loadRemoteAddons():
            self.getOutOfDateAddons()
            self.searchSearchBarContents()

    def getOutOfDateAddons(self):
        """
        Marks addons as out of date in database with '(Outdated) '
        in installed table and '(Updated) ' in remote table. These
        are prepended to the Version column.
        """
        if not self.loadRemoteDataIfNotDone():
            return

        if not self.currentGame.startswith("DDO"):
            self.loadSkinsIfNotDone()
            self.loadMusicIfNotDone()

        if self.currentGame.startswith("LOTRO"):
            tables = self.TABLE_LIST[:3]
        else:
            tables = ["tableSkinsInstalled"]

        for db_table in tables:
            table_installed = getattr(self.winAddonManager, db_table)
            table_remote = self.getRemoteOrLocalTableFromOne(
                table_installed, remote=True
            )

            addons_info_remote = {}
            for addon in self.c.execute(
                "SELECT Version, InterfaceID, rowid FROM {table_remote} WHERE"  # nosec
                " Name LIKE '(Installed) %'".format(
                    table_remote=table_remote.objectName()
                )
            ):
                addons_info_remote[addon[1]] = (addon[0], addon[2])

            out_of_date_addons = []
            for addon in self.c.execute(
                "SELECT Version, InterfaceID, rowid FROM {table_installed} WHERE"  # nosec
                " InterfaceID != ''".format(
                    table_installed=table_installed.objectName()
                )
            ):
                # Will raise KeyError if addon has Interface ID that isn't in remote table.
                try:
                    remote_addon_info = addons_info_remote[addon[1]]
                except KeyError:
                    continue

                latest_version = remote_addon_info[0]
                if addon[0] != latest_version:
                    rowid_remote = remote_addon_info[1]
                    out_of_date_addons.append((addon[2], rowid_remote, table_installed))

            for addon in out_of_date_addons:
                self.markAddonForUpdating(addon[0], addon[1], addon[2])

    def markAddonForUpdating(self, rowid_local, rowid_remote, table_installed):
        """
        Marks addon as having having updates
        available in installed and remote tables
        """
        table_remote = self.getRemoteOrLocalTableFromOne(table_installed, remote=True)

        self.c.execute(
            (
                "UPDATE {table} SET Version=('(Outdated) ' || Version) WHERE rowid=?".format(  # nosec
                    table=table_installed.objectName()
                )
            ),
            (str(rowid_local),),
        )
        self.c.execute(
            (
                "UPDATE {table} SET Version=('(Updated) ' || Version) WHERE rowid=?".format(  # nosec
                    table=table_remote.objectName()
                )
            ),
            (str(rowid_remote),),
        )

    def updateAll(self):
        if not self.loadRemoteDataIfNotDone():
            return

        if self.currentGame.startswith("LOTRO"):
            tables = self.TABLE_LIST[:3]
        else:
            tables = ["tableSkinsInstalled"]

        for db_table in tables:
            table = getattr(self.winAddonManager, db_table)
            for addon in self.c.execute(
                "SELECT InterfaceID, File, Name FROM {table} WHERE"  # nosec
                " Version LIKE '(Outdated) %'".format(table=table.objectName())
            ):
                self.updateAddon(addon, table)

        self.resetRemoteAddonsTables()
        self.searchSearchBarContents()

    def updateAddon(self, addon, table):
        uninstall_function = self.getUninstallFunctionFromTable(table)
        table_installed = self.getRemoteOrLocalTableFromOne(table, remote=False)
        table_remote = self.getRemoteOrLocalTableFromOne(table, remote=True)

        uninstall_function([addon], table_installed)

        for entry in self.c.execute(
            "SELECT File FROM {table} WHERE"  # nosec
            " InterfaceID = ?".format(table=table_remote.objectName()),
            (addon[0],),
        ):
            url = entry[0]
        self.installRemoteAddon(url, addon[2], addon[0])
        self.setRemoteAddonToInstalled(addon, table_remote)

    def actionUpdateAddonSelected(self):
        if not self.loadRemoteDataIfNotDone():
            return

        table = self.context_menu_selected_table
        row = self.context_menu_selected_row
        addon = self.getAddonListObjectFromRow(table, row, remote=False)

        self.updateAddon(addon, table)

        self.resetRemoteAddonsTables()
        self.searchSearchBarContents()

    def updateAllSelectedAddons(self):
        table = self.getCurrentTable()
        addons, details = self.getSelectedAddons(table)

        if not self.loadRemoteDataIfNotDone():
            return

        if addons:
            for addon in addons:
                if self.checkIfAddonHasUpdate(addon, table):
                    self.updateAddon(addon, table)

            self.resetRemoteAddonsTables()
            self.searchSearchBarContents()

    def checkIfAddonHasUpdate(self, addon, table):
        for entry in self.c.execute(
            "SELECT Version FROM {table} WHERE InterfaceID = ?".format(  # nosec
                table=table.objectName()
            ),
            (addon[0],),
        ):
            version = entry[0]
            if version.startswith("(Outdated) ") or version.startswith("(Updated) "):
                return True
            else:
                return False

    def loadRemoteDataIfNotDone(self):
        """
        Loads remote addons and checks if addons have updates if not done yet
        """
        # If remote addons haven't been loaded then out of date addons haven't been found.
        if self.isTableEmpty(self.winAddonManager.tableSkins):
            if self.loadRemoteAddons():
                self.getOutOfDateAddons()
        
        return True

    def actionEnableStartupScriptSelected(self):
        script = self.getRelativeStartupScriptFromInterfaceID(
            self.context_menu_selected_table, self.context_menu_selected_interface_ID
        )
        full_script_path = os.path.join(self.data_folder, script)
        if os.path.exists(full_script_path):
            self.startupScripts.append(script)
        else:
            self.addLog(
                f"'{full_script_path}' startup script does not exist, so it could not be enabled."
            )

    def actionDisableStartupScriptSelected(self):
        script = self.getRelativeStartupScriptFromInterfaceID(
            self.context_menu_selected_table, self.context_menu_selected_interface_ID
        )
        self.startupScripts.remove(script)

    def getRelativeStartupScriptFromInterfaceID(
        self, table: QtWidgets.QTableWidget, interface_ID
    ):
        """Returns path of startup script relative to game documents settings directory"""
        table_local = self.getRemoteOrLocalTableFromOne(table, remote=False)
        for entry in self.c.execute(
            f"SELECT StartupScript FROM {table_local.objectName()} WHERE InterfaceID = ?",
            (interface_ID,),
        ):
            if entry[0]:
                script = os.path.normpath(entry[0].replace("\\", "/"))
                addon_data_folder_relative = self.getAddonTypeDataFolderFromTable(
                    table_local
                ).split(self.data_folder)[1]

                script_relative_path = os.path.join(
                    addon_data_folder_relative, script
                ).strip(os.sep)
                return script_relative_path

    def getAddonTypeDataFolderFromTable(self, table: QtWidgets.QTableWidget):
        table_name = table.objectName()
        if "Plugins" in table_name:
            return self.data_folder_plugins
        elif "Skins" in table_name:
            return self.data_folder_skins
        elif "Music" in table_name:
            return self.data_folder_music
        else:
            return None

    def handleStartupScriptActivationPrompt(
        self, table: QtWidgets.QTableWidget, interface_ID: str
    ):
        """Asks user if they want to enable an add-on's startup script if present"""
        script = self.getRelativeStartupScriptFromInterfaceID(table, interface_ID)
        if script:
            script_contents = open(os.path.join(self.data_folder, script)).read()
            for name in self.c.execute(
                f"SELECT Name from {table.objectName()} WHERE InterfaceID = ?",
                (interface_ID,),
            ):
                addon_name = name[0]

            activate_script = self.confirmationPrompt(
                f"{addon_name} is requesting to run a Python script at every game launch."
                " It is highly recommended to review the script's code in the details"
                " box below to make sure it's safe.",
                script_contents,
            )
            if activate_script:
                self.startupScripts.append(script)

    def uninstallStartupScript(self, script: str, addon_data_folder: str):
        if script:
            script_path = os.path.join(
                addon_data_folder, (script.replace("\\", os.sep)),
            )

            relative_to_game_documents_dir_script = script_path.replace(
                self.data_folder, ""
            ).strip(os.sep)
            if relative_to_game_documents_dir_script in self.startupScripts:
                self.startupScripts.remove(relative_to_game_documents_dir_script)

            if os.path.exists(script_path):
                os.remove(script_path)

