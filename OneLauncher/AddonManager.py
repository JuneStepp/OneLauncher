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
from qtpy import QtCore, QtGui, QtWidgets, uic
import os
from pkg_resources import resource_filename
from glob import glob
from xml.dom import EMPTY_NAMESPACE
from xml.dom.minidom import Document
import defusedxml.minidom
from .OneLauncherUtils import GetText
import sqlite3
from shutil import rmtree, copy, move
from zipfile import ZipFile
from urllib import request
from time import strftime, localtime


class AddonManager:
    # ID is from the order plugins are found on the filesystem. InterfaceID is
    # the unique ID for plugins on lotrointerface.com
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
    SKINS_DDO_URL = (
        "https://api.lotrointerface.com/fav/OneLauncher-Themes-DDO.xml"
    )

    def __init__(self, currentGame, osType, settingsDir, parent):
        self.settingsDir = settingsDir
        self.currentGame = currentGame
        self.parent = parent

        self.winAddonManager = QtWidgets.QDialog(
            parent, QtCore.Qt.FramelessWindowHint
        )

        uifile = resource_filename(
            __name__, "ui" + os.sep + "winAddonManager.ui"
        )

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
        self.uiAddonManager.btnAddons.setMenu(
            self.uiAddonManager.btnAddonsMenu
        )
        self.uiAddonManager.btnAddons.clicked.connect(self.btnAddonsClicked)
        self.uiAddonManager.tabWidget.currentChanged.connect(
            self.tabWidgetIndexChanged
        )
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
                os.path.expanduser("~"),
                documents_folder,
                "Dungeons and Dragons Online",
            )

            self.data_folder_skins = os.path.join(
                self.data_folder, "ui", "skins"
            )

            self.uiAddonManager.tableSkinsInstalled.setObjectName(
                "tableSkinsDDOInstalled"
            )
            self.uiAddonManager.tableSkins.setObjectName("tableSkinsDDO")
            self.getInstalledSkins()
        else:
            self.data_folder = os.path.join(
                os.path.expanduser("~"),
                documents_folder,
                "The Lord of the Rings Online",
            )

            self.data_folder_plugins = os.path.join(
                self.data_folder, "Plugins"
            )
            self.data_folder_skins = os.path.join(
                self.data_folder, "ui", "skins"
            )
            self.data_folder_music = os.path.join(self.data_folder, "Music")

            # Loads in installed plugins
            self.getInstalledPlugins()

    def tabWidgetInstalledIndexChanged(self, index):
        # Load in installed skins on first switch to tab
        if index == 1 and not self.uiAddonManager.tableSkinsInstalled.item(
            0, 0
        ):
            self.getInstalledSkins()

        # Load in installed music on first switch to tab
        if index == 2 and not self.uiAddonManager.tableMusicInstalled.item(
            0, 0
        ):
            self.getInstalledMusic()

    def getInstalledSkins(self, folders_list=None):
        if not self.uiAddonManager.tableSkinsInstalled.item(0, 1):
            folders_list = None

        os.makedirs(self.data_folder_skins, exist_ok=True)

        if not folders_list:
            folders_list = glob(os.path.join(self.data_folder_skins, "*", ""))
        else:
            folders_list = [
                os.path.join(self.data_folder_skins, folder)
                for folder in folders_list
            ]

        skins_list = []
        skins_list_compendium = []
        for folder in folders_list:
            folder = folder[:-1] + folder[-1].replace("/", "")
            skins_list.append(folder)
            for file in os.listdir(folder):
                if file.endswith(".skincompendium"):
                    skins_list_compendium.append(os.path.join(folder, file))
                    skins_list.remove(folder)
                    break

        self.addInstalledSkinstoDB(skins_list, skins_list_compendium)

    def addInstalledSkinstoDB(self, skins_list, skins_list_compendium):
        table = self.uiAddonManager.tableSkinsInstalled

        # Clears rows from db table if needed (This function is called to add
        # newly installed skins after initial load as well)
        if not table.item(0, 1):
            self.c.execute(
                "DELETE FROM {table}".format(table=table.objectName())  # nosec
            )

        for skin in skins_list_compendium:
            items_row = self.parseCompediumFile(skin, "SkinConfig")
            if self.currentGame.startswith("LOTRO"):
                items_row = self.getOnlineAddonInfo(items_row, "tableSkins")
            else:
                items_row = self.getOnlineAddonInfo(items_row, "tableSkinsDDO")
            self.addRowToDB(table.objectName(), items_row)

        for skin in skins_list:
            items_row = [""] * (len(self.COLUMN_LIST) - 1)

            items_row[0] = os.path.split(skin)[1]
            items_row[5] = skin
            items_row[1] = "Unmanaged"

            self.addRowToDB(table.objectName(), items_row)

        # Populate user visible table
        self.searchDB(self.uiAddonManager.tableSkinsInstalled, "")

    def getInstalledMusic(self, folders_list=None):
        if not self.uiAddonManager.tableMusicInstalled.item(0, 1):
            folders_list = None

        os.makedirs(self.data_folder_music, exist_ok=True)

        if not folders_list:
            folders_list = glob(os.path.join(self.data_folder_music, "*", ""))
        else:
            folders_list = [
                os.path.join(self.data_folder_music, folder)
                for folder in folders_list
            ]

        music_list = []
        music_list_compendium = []
        for folder in folders_list:
            folder = folder[:-1] + folder[-1].replace("/", "")
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

        self.addInstalledMusictoDB(music_list, music_list_compendium)

    def addInstalledMusictoDB(self, music_list, music_list_compendium):
        table = self.uiAddonManager.tableMusicInstalled

        # Clears rows from db table if needed (This function is called
        # to add newly installed music after initial load as well)
        if not table.item(0, 1):
            self.c.execute("DELETE FROM tableMusicInstalled")

        for music in music_list_compendium:
            items_row = self.parseCompediumFile(music, "MusicConfig")
            items_row = self.getOnlineAddonInfo(items_row, "tableMusic")
            self.addRowToDB(table.objectName(), items_row)

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

            self.addRowToDB(table.objectName(), items_row)

        # Populate user visible table
        self.searchDB(table, "")

    def getInstalledPlugins(self, folders_list=None):
        if not self.uiAddonManager.tablePluginsInstalled.item(0, 1):
            folders_list = None
        os.makedirs(self.data_folder_plugins, exist_ok=True)

        if not folders_list:
            folders_list = glob(
                os.path.join(self.data_folder_plugins, "*", "")
            )
        else:
            folders_list = [
                os.path.join(self.data_folder_plugins, folder)
                for folder in folders_list
            ]

        # Finds all plugins and adds their .plugincompendium files to a list
        plugins_list_compendium = []
        plugins_list = []
        for folder in folders_list:
            for file in os.listdir(folder):
                if file.endswith(".plugincompendium"):
                    plugins_list_compendium.append(os.path.join(folder, file))
                elif file.endswith(".plugin"):
                    plugins_list.append(os.path.join(folder, file))

        plugins_list, plugins_list_compendium = self.removeManagedPluginsFromList(
            plugins_list, plugins_list_compendium
        )

        self.addInstalledPluginstoDB(plugins_list, plugins_list_compendium)

    def removeManagedPluginsFromList(
        self, plugins_list, plugins_list_compendium
    ):
        for plugin in plugins_list_compendium:
            doc = defusedxml.minidom.parse(plugin)
            nodes = doc.getElementsByTagName("Descriptors")[0].childNodes

            for node in nodes:
                if node.nodeName == "descriptor":
                    try:
                        plugins_list.remove(
                            os.path.join(
                                self.data_folder_plugins,
                                (
                                    GetText(node.childNodes).replace(
                                        "\\", os.sep
                                    )
                                ),
                            )
                        )
                    except ValueError:
                        self.addLog(plugin + " has misconfigured descriptors")

        return plugins_list, plugins_list_compendium

    def addInstalledPluginstoDB(self, plugins_list, plugins_list_compendium):
        table = self.uiAddonManager.tablePluginsInstalled

        # Clears rows from db table if needed (This function is called to
        # add newly installed plugins after initial load as well)
        if not table.item(0, 1):
            self.c.execute("DELETE FROM tablePluginsInstalled")

        for plugin in plugins_list_compendium + plugins_list:
            # Sets tag for plugin file xml search and category for unmanaged plugins
            if plugin.endswith(".plugincompendium"):
                items_row = self.parseCompediumFile(plugin, "PluginConfig")
                items_row = self.getOnlineAddonInfo(items_row, "tablePlugins")

                dependencies = ""
                doc = defusedxml.minidom.parse(plugin)
                if doc.getElementsByTagName("Dependencies"):
                    nodes = doc.getElementsByTagName("Dependencies")[
                        0
                    ].childNodes
                    for node in nodes:
                        if node.nodeName == "dependency":
                            dependencies = (
                                dependencies + "," + (GetText(node.childNodes))
                            )
                items_row[7] = dependencies[1:]
            else:
                items_row = self.parseCompediumFile(plugin, "Information")
                items_row[1] = "Unmanaged"

            self.addRowToDB(table.objectName(), items_row)

        # Populate user visible table
        self.searchDB(self.uiAddonManager.tablePluginsInstalled, "")

    # Returns list of common values for compendium or .plugin files
    def parseCompediumFile(self, file, tag):
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
        # Connects to addons_cache database and creates it if it does not exist
        if not os.path.exists(
            os.path.join(self.settingsDir, "addons_cache.sqlite")
        ):
            self.conn = sqlite3.connect(
                os.path.join(self.settingsDir, "addons_cache.sqlite")
            )
            self.c = self.conn.cursor()

            for table in self.TABLE_LIST:
                self.c.execute(
                    "CREATE VIRTUAL TABLE {tbl_nm} USING FTS5({clmA}, {clmB}, {clmC}, "
                    "{clmD}, {clmE}, {clmF}, {clmG}, {clmH})".format(
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

    def installAddon(self, addon, interface_id=""):
        # Install .abc files
        if addon.endswith(".abc"):
            if self.currentGame.startswith("DDO"):
                self.addLog("DDO does not support .abc/music files")
                return

            copy(addon, self.data_folder_music)

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
                for entry in files_list:
                    if entry.endswith(".plugin"):
                        if self.currentGame.startswith("DDO"):
                            self.addLog("DDO does not support plugins")
                            return

                        addon_type = "Plugin"
                        table = self.uiAddonManager.tablePlugins
                        folder = entry.split("/")[0]
                        path = self.data_folder_plugins
                        file.extractall(path=path)

                        plugins_list = []
                        plugins_list_compendium = []
                        for entry in files_list:
                            if len(entry.split("/")) == 2:
                                if entry.endswith(".plugin"):
                                    plugins_list.append(
                                        os.path.join(
                                            self.data_folder_plugins, entry
                                        )
                                    )
                                elif entry.endswith(".plugincompendium"):
                                    plugins_list_compendium.append(
                                        os.path.join(
                                            self.data_folder_plugins, entry
                                        )
                                    )

                        if not plugins_list_compendium:
                            if interface_id:
                                compendium_file = self.generateCompendiumFile(
                                    files_list,
                                    folder,
                                    interface_id,
                                    addon_type,
                                    path,
                                    table.objectName(),
                                )
                                plugins_list_compendium.append(compendium_file)

                        plugins_list, plugins_list_compendium = self.removeManagedPluginsFromList(
                            plugins_list, plugins_list_compendium
                        )

                        self.addInstalledPluginstoDB(
                            plugins_list, plugins_list_compendium
                        )

                        self.installAddonRemoteDependencies(
                            table.objectName() + "Installed"
                        )
                        return
                    elif entry.endswith(".abc"):
                        if self.currentGame.startswith("DDO"):
                            self.addLog(
                                "DDO does not support .abc/music files"
                            )
                            return

                        addon_type = "Music"
                        table = self.uiAddonManager.tableMusic

                        path, folder = self.getAddonInstallationFolder(
                            entry, addon, files_list, self.data_folder_music
                        )
                        file.extractall(path=path)

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

                        self.installAddonRemoteDependencies(
                            table.objectName() + "Installed"
                        )
                        return
                if not addon_type:
                    addon_type = "Skin"
                    table = self.uiAddonManager.tableSkins
                    path, folder = self.getAddonInstallationFolder(
                        entry, addon, files_list, self.data_folder_skins
                    )
                    file.extractall(path=path)

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

                    self.installAddonRemoteDependencies(
                        table.objectName() + "Installed"
                    )
                    return

    # Installs the dependencies for the last installed addon
    def installAddonRemoteDependencies(self, table):
        # Gets dependencies for last column in db
        for item in self.c.execute(
            "SELECT Dependencies FROM {table} ORDER BY rowid DESC LIMIT 1".format(  # nosec
                table=table
            )
        ):
            dependencies = item[0]

        for dependencie in dependencies.split(","):
            if dependencie:
                # 0 is the arbitrary ID for Turbine Utilities. 1064 is the ID
                # of OneLauncher's upload of the utilities on LotroInterface
                if dependencie == "0":
                    dependencie = "1064"

                for item in self.c.execute(  # nosec
                    "SELECT File, Name FROM {table} WHERE InterfaceID = ? AND InterfaceID NOT IN "
                    "(SELECT InterfaceID FROM {table_installed})".format(
                        table=table.split("Installed")[0],
                        table_installed=table,
                    ),
                    (dependencie,),
                ):
                    self.installRemoteAddon(item[0], item[1], dependencie)

    # Gets folder and makes one if there is no root folder
    def getAddonInstallationFolder(
        self, entry, addon, files_list, data_folder
    ):
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
                folders_list = glob(
                    os.path.join(data_folder, folders, "*", "")
                )
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
        # Return if a compendium file already exists
        for file in files_list:
            if file.endswith(addon_type.lower() + "compendium"):
                return

        for row in self.c.execute(
            "SELECT * FROM {table} WHERE InterfaceID = ?".format(  # nosec
                table=table
            ),
            (interface_id,),
        ):
            if row[0]:
                doc = Document()
                mainNode = doc.createElementNS(
                    EMPTY_NAMESPACE, addon_type + "Config"
                )
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
                    doc.createTextNode(
                        "%s" % (self.getInterfaceInfoUrl(row[5]))
                    )
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
                                doc.createTextNode(
                                    "%s"
                                    % (folder + "\\" + os.path.split(file)[1])
                                )
                            )
                            descriptorsNode.appendChild(tempNode)

                # Can't add dependencies, because they are defined in compendium files
                tempNode = doc.createElementNS(EMPTY_NAMESPACE, "Dependencies")
                mainNode.appendChild(tempNode)

                # Write compendium file

                # Path includes folder when one has to be generated
                if path.endswith(folder):
                    folder = ""

                compendium_file = os.path.join(
                    path,
                    folder,
                    row[0] + "." + addon_type.lower() + "compendium",
                )
                with open(compendium_file, "w+") as file:
                    file.write(doc.toxml())

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
            if self.uiAddonManager.tabWidget.currentIndex() == 0:
                # If in PluginsInstalled tab
                if self.uiAddonManager.tabWidgetInstalled.currentIndex() == 0:
                    self.searchDB(
                        self.uiAddonManager.tablePluginsInstalled, text
                    )
                # If in SkinsInstalled tab
                elif (
                    self.uiAddonManager.tabWidgetInstalled.currentIndex() == 1
                ):
                    self.searchDB(
                        self.uiAddonManager.tableSkinsInstalled, text
                    )
                # If in MusicInstalled tab
                elif (
                    self.uiAddonManager.tabWidgetInstalled.currentIndex() == 2
                ):
                    self.searchDB(
                        self.uiAddonManager.tableMusicInstalled, text
                    )
            # If in Find More tab
            elif self.uiAddonManager.tabWidget.currentIndex() == 1:
                # If in Plugins tab
                if self.uiAddonManager.tabWidgetFindMore.currentIndex() == 0:
                    self.searchDB(self.uiAddonManager.tablePlugins, text)
                # If in Skins tab
                elif self.uiAddonManager.tabWidgetFindMore.currentIndex() == 1:
                    self.searchDB(self.uiAddonManager.tableSkins, text)
                # If in Music tab
                elif self.uiAddonManager.tabWidgetFindMore.currentIndex() == 2:
                    self.searchDB(self.uiAddonManager.tableMusic, text)
        else:
            # If in Installed tab
            if self.uiAddonManager.tabWidget.currentIndex() == 0:
                self.searchDB(self.uiAddonManager.tableSkinsInstalled, text)
            # If in Find More tab
            elif self.uiAddonManager.tabWidget.currentIndex() == 1:
                self.searchDB(self.uiAddonManager.tableSkins, text)

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
                    for item in table.findItems(
                        row[1], QtCore.Qt.MatchExactly
                    ):
                        if int((table.item(item.row(), 0)).text()) == row[0]:
                            duplicate = True
                            break
                    if not duplicate:
                        self.addRowToTable(table, row)
        else:
            # Shows all plugins if the search bar is empty
            for row in self.c.execute(
                "SELECT rowid, * FROM {table}".format(  # nosec
                    table=table.objectName()
                )
            ):
                self.addRowToTable(table, row)

            self.uiAddonManager.txtSearchBar.clear()

    # Adds row to a visible table. First value in list is row name
    def addRowToTable(self, table, list):
        table.setSortingEnabled(False)

        disable_row = False
        installed_color = QtGui.QColor()
        installed_color.setRgb(63, 73, 83)

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
            elif str(item).startswith("(Installed)") and i == 1:
                tbl_item.setText(item.split("(Installed) ")[1])
                disable_row = True
            table.setItem(rows, i, tbl_item)

        if disable_row:
            for i in range(table.columnCount()):
                table.item(rows, i).setFlags(QtCore.Qt.ItemIsEnabled)
                table.item(rows, i).setBackground(installed_color)

        table.setSortingEnabled(True)

    def addRowToDB(self, table, list):
        question_marks = "?"
        for i in range(len(list) - 1):
            question_marks = question_marks + ",?"

        self.c.execute(
            "INSERT INTO {table} VALUES({})".format(
                question_marks, table=table
            ),
            (list),  # nosec
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
                elif (
                    self.uiAddonManager.tabWidgetInstalled.currentIndex() == 1
                ):
                    table = self.uiAddonManager.tableSkinsInstalled
                    uninstall_class = self.uninstallSkins
                elif (
                    self.uiAddonManager.tabWidgetInstalled.currentIndex() == 2
                ):
                    table = self.uiAddonManager.tableMusicInstalled
                    uninstall_class = self.uninstallMusic
            else:
                table = self.uiAddonManager.tableSkinsInstalled
                uninstall_class = self.uninstallSkins

            uninstallConfirm, addons = self.getUninstallConfirm(table)
            if uninstallConfirm:
                uninstall_class(addons, table)
                self.loadRemoteAddons()

        elif self.uiAddonManager.tabWidget.currentIndex() == 1:
            self.installRemoteAddons()

    def installRemoteAddons(self):
        if self.currentGame.startswith("DDO"):
            table = self.uiAddonManager.tableSkins
        else:
            if self.uiAddonManager.tabWidgetFindMore.currentIndex() == 0:
                table = self.uiAddonManager.tablePlugins
            elif self.uiAddonManager.tabWidgetFindMore.currentIndex() == 1:
                table = self.uiAddonManager.tableSkins
            elif self.uiAddonManager.tabWidgetFindMore.currentIndex() == 2:
                table = self.uiAddonManager.tableMusic

        addons, details = self.getSelectedAddons(table)
        if addons and details:
            for addon in addons:
                self.installRemoteAddon(addon[1], addon[2], addon[0])

        self.loadRemoteAddons()

    def installRemoteAddon(self, url, name, interface_id):
        path = os.path.join(self.data_folder, "Downloads", name + ".zip")
        os.makedirs(os.path.split(path)[0], exist_ok=True)
        self.downloader(url, path)
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
                "Are you sure you want to remove "
                + plural
                + str(len(addons))
                + plural1
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
            for item in table.selectedItems()[
                0 :: (len(self.COLUMN_LIST) - 4)
            ]:
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
                    nodes = doc.getElementsByTagName("Descriptors")[
                        0
                    ].childNodes
                    for node in nodes:
                        if node.nodeName == "descriptor":
                            plugin_files.append(
                                os.path.join(
                                    self.data_folder_plugins,
                                    (
                                        GetText(node.childNodes).replace(
                                            "\\", os.sep
                                        )
                                    ),
                                )
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
                                self.data_folder_plugins
                                + os.sep
                                + plugin_folder
                            ):
                                rmtree(
                                    self.data_folder_plugins
                                    + os.sep
                                    + plugin_folder
                                )
                    if os.path.exists(plugin_file):
                        os.remove(plugin_file)
            if os.path.exists(plugin[1]):
                os.remove(plugin[1])

        # Reloads plugins
        table.clearContents()
        self.getInstalledPlugins()

    def uninstallSkins(self, skins, table):
        for skin in skins:
            if skin[1].endswith(".skincompendium"):
                skin = os.path.split(skin[1])[0]
            else:
                skin = skin[1]
            rmtree(skin)

            # Reloads skins
            table.clearContents()
            self.getInstalledSkins()

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
            if not self.uiAddonManager.tableSkins.item(0, 0):
                self.loadRemoteAddons()

    def loadRemoteAddons(self):
        if self.currentGame.startswith("LOTRO"):
            self.getRemoteAddons(
                self.PLUGINS_URL, self.uiAddonManager.tablePlugins
            )
            self.getRemoteAddons(
                self.SKINS_URL, self.uiAddonManager.tableSkins
            )
            self.getRemoteAddons(
                self.MUSIC_URL, self.uiAddonManager.tableMusic
            )
        else:
            self.getRemoteAddons(
                self.SKINS_DDO_URL, self.uiAddonManager.tableSkins
            )

    def getRemoteAddons(self, favorites_url, table):
        # Clears rows from db table
        self.c.execute(
            "DELETE FROM {table}".format(table=table.objectName())  # nosec
        )

        # Gets list of Interface IDs for installed addons
        installed_IDs = []
        for ID in self.c.execute(
            "SELECT InterfaceID FROM {table}".format(  # nosec
                table=table.objectName() + "Installed"
            )
        ):
            if ID[0]:
                installed_IDs.append(ID[0])

        addons_file = request.urlopen(favorites_url).read().decode()  # nosec
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
                        "%m-%d-%Y", localtime(int(GetText(node.childNodes)))
                    )
                elif node.nodeName == "UIFileURL":
                    items_row[5] = GetText(node.childNodes)

            # Prepends name with (Installed) if already installed
            if items_row[6] in installed_IDs:
                items_row[0] = "(Installed) " + items_row[0]

            self.addRowToDB(table.objectName(), items_row)

        # Populate user visible table
        self.searchDB(table, "")

    # Downloads file from url to path and shows progress with self.handleDownloadProgress
    def downloader(self, url, path):
        if url.lower().startswith("http"):
            request.urlretrieve(  # nosec
                url, path, self.handleDownloadProgress
            )
        else:
            raise ValueError from None

        self.uiAddonManager.progressBar.setValue(0)

    def handleDownloadProgress(self, index, frame, size):
        # Updates progress bar with download progress
        percent = 100 * index * frame // size
        self.uiAddonManager.progressBar.setValue(percent)

    def Run(self):
        self.winAddonManager.exec()
        self.closeDB()
