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
import xml.dom.minidom
from .OneLauncherUtils import GetText
import sqlite3


class AddonManager:
    COLUMN_LIST = ["Name", "Category", "Version", "Author", "Modified"]

    def __init__(self, currentGame, osType, settingsDir, parent):
        self.settingsDir = settingsDir
        self.currentGame = currentGame

        self.winAddonManager = QtWidgets.QDialog(parent, QtCore.Qt.FramelessWindowHint)

        uifile = resource_filename(__name__, "ui" + os.sep + "winAddonManager.ui")

        Ui_dlgAddonManager, base_class = uic.loadUiType(uifile)
        self.uiAddonManager = Ui_dlgAddonManager()
        self.uiAddonManager.setupUi(self.winAddonManager)

        self.uiAddonManager.btnBox.rejected.connect(self.btnBoxActivated)

        self.uiAddonManager.btnAddAddonMenu = QtWidgets.QMenu()
        self.uiAddonManager.btnAddAddonMenu.addAction(
            self.uiAddonManager.actionAddonImport
        )
        self.uiAddonManager.actionAddonImport.triggered.connect(
            self.actionAddonImportSelected
        )
        self.uiAddonManager.btnAddAddon.setMenu(self.uiAddonManager.btnAddAddonMenu)

        self.uiAddonManager.txtLog.hide()
        self.uiAddonManager.btnLog.clicked.connect(self.btnLogClicked)

        self.uiAddonManager.txtSearchBar.textChanged.connect(
            self.txtSearchBarTextChanged
        )

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

            data_folder = os.path.join(
                os.path.expanduser("~"), documents_folder, "Dungeons and Dragons Online"
            )
            # self.getInstalledThemes(data_folder)

        else:
            data_folder = os.path.join(
                os.path.expanduser("~"),
                documents_folder,
                "The Lord of the Rings Online",
            )

            self.getInstalledPlugins(data_folder)
            # self.getInstalledThemes(data_folder)
            # self.getInstalledMusic(data_folder)

    def getInstalledPlugins(self, data_folder):
        data_folder = os.path.join(data_folder, "Plugins")
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
                item = QtWidgets.QTableWidgetItem()

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
        for plugin in plugins_list_compendium + plugins_list:
            items_row = [""] * 4

            doc = xml.dom.minidom.parse(plugin)

            # Sets tag for plugin file xml search and category for unmanaged plugins
            if plugin.endswith(".plugincompendium"):
                tag = "PluginConfig"
            else:
                tag = "Information"
                items_row[1] = "Unmanaged"

            nodes = doc.getElementsByTagName(tag)[0].childNodes
            for node in nodes:
                if node.nodeName == "Name":
                    items_row[0] = GetText(node.childNodes)
                elif node.nodeName == "Author":
                    items_row[3] = GetText(node.childNodes)
                elif node.nodeName == "Version":
                    items_row[2] = GetText(node.childNodes)

            self.addRowToTable(self.uiAddonManager.tablePluginsInstalled, items_row)

            # Clears rows from db table
            self.c.execute("DELETE FROM tablePluginsInstalled")

            # Add contents of table to the database
            for row in range(self.uiAddonManager.tablePluginsInstalled.rowCount()):
                values = ""
                for column in range(len(self.COLUMN_LIST)):
                    value = self.uiAddonManager.tablePluginsInstalled.item(row, column)
                    if value:
                        values = values + ", '" + value.text() + "'"
                    else:
                        values = values + ", ''"
                self.c.execute(
                    "INSERT INTO tablePluginsInstalled values({values})".format(
                        values=values[1:]
                    )
                )

    def openDB(self):
        table_list = [
            "tablePluginsInstalled",
            "tableThemesInstalled",
            "tableMusicInstalled",
            "tablePlugins",
            "tableThemes",
            "tableMusic",
            "tableThemesDDO",
            "tableThemesDDOInstalled",
        ]

        # Connects to addons_cache database and creates it if it does not exist
        if not os.path.exists(os.path.join(self.settingsDir, "addons_cache.sqlite")):
            self.conn = sqlite3.connect(
                os.path.join(self.settingsDir, "addons_cache.sqlite")
            )
            self.c = self.conn.cursor()

            for table in table_list:
                self.c.execute(
                    "CREATE VIRTUAL TABLE {tbl_nm} USING FTS5({clmA}, {clmB}, {clmC}, {clmD}, {clmE})".format(
                        tbl_nm=table,
                        clmA=self.COLUMN_LIST[0],
                        clmB=self.COLUMN_LIST[1],
                        clmC=self.COLUMN_LIST[2],
                        clmD=self.COLUMN_LIST[3],
                        clmE=self.COLUMN_LIST[4],
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

    # def getInstalledThemes(self, data_folder):
    #     pass

    # def getInstalledMusic(self, data_folder):
    #     pass

    def actionAddonImportSelected(self):
        filenames = QtWidgets.QFileDialog.getOpenFileNames(
            self.winAddonManager,
            "Addon Files/Archives",
            os.path.expanduser("~"),
            "*.zip *.abc",
        )

        if filenames:
            for file in filenames:
                print(file)

    def txtSearchBarTextChanged(self, text):
        if self.currentGame.startswith("LOTRO"):
            # If in Installed tab
            if self.uiAddonManager.tabWidget.currentIndex() == 0:
                # If in PluginsInstalled tab
                if self.uiAddonManager.tabWidgetInstalled.currentIndex() == 0:
                    self.searchDB(self.uiAddonManager.tablePluginsInstalled, text)

    def searchDB(self, table, text):
        table.clearContents()
        table.setRowCount(0)

        if text:
            for word in text.split():
                search_word = "%" + word + "%"

                for row in self.c.execute(
                    "SELECT * FROM {table} WHERE Author LIKE ? OR Category LIKE ? OR Name LIKE ?".format(
                        table=table.objectName()
                    ),
                    (search_word, search_word, search_word),
                ):
                    # Detects duplicates from multi-word search
                    if not table.findItems(row[0], QtCore.Qt.MatchExactly):
                        # Sets items onto the visible table
                        self.addRowToTable(table, row)
        else:
            # Shows all plugins if the search bar is empty
            for row in self.c.execute(
                "SELECT * FROM {table}".format(table=table.objectName())
            ):
                self.addRowToTable(table, row)

    def addRowToTable(self, table, list):
        table.setSortingEnabled(False)

        rows = table.rowCount()
        table.setRowCount(rows + 1)
        for i, item in enumerate(list):
            tbl_item = QtWidgets.QTableWidgetItem()

            tbl_item.setText(item)
            # Sets color to red if plugin is unmanaged
            if item == "Unmanaged" and i == 1:
                tbl_item.setForeground(QtGui.QColor("darkred"))
            table.setItem(rows, i, tbl_item)

        table.setSortingEnabled(True)

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

    def Run(self):
        self.winAddonManager.exec_()
        self.closeDB()
