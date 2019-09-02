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
            doc = xml.dom.minidom.parse(plugin)

            # Adds a row to the table
            rows = self.uiAddonManager.tablePluginsInstalled.rowCount()
            self.uiAddonManager.tablePluginsInstalled.setRowCount(rows + 1)

            # Sets tag for plugin file xml search and category for unmanaged plugins
            if plugin.endswith(".plugincompendium"):
                tag = "PluginConfig"
            else:
                tag = "Information"
                item = QtWidgets.QTableWidgetItem()
                item.setForeground(QtGui.QColor("darkred"))
                item.setText("Unmanaged")
                self.uiAddonManager.tablePluginsInstalled.setItem(rows, 1, item)

            nodes = doc.getElementsByTagName(tag)[0].childNodes

            for node in nodes:
                item = QtWidgets.QTableWidgetItem()

                if node.nodeName == "Name":
                    item.setText(GetText(node.childNodes))
                    self.uiAddonManager.tablePluginsInstalled.setItem(rows, 0, item)
                elif node.nodeName == "Author":
                    item.setText(GetText(node.childNodes))
                    self.uiAddonManager.tablePluginsInstalled.setItem(rows, 3, item)
                elif node.nodeName == "Version":
                    item.setText(GetText(node.childNodes))
                    self.uiAddonManager.tablePluginsInstalled.setItem(rows, 2, item)

            c = self.conn.cursor()

            # Clears rows from table
            c.execute("DELETE FROM tablePluginsInstalled")

            # Add contents of table to the database
            for row in range(self.uiAddonManager.tablePluginsInstalled.rowCount()):
                values = ""
                for column in range(len(self.COLUMN_LIST)):
                    value = self.uiAddonManager.tablePluginsInstalled.item(row, column)
                    if value:
                        values = values + ", '" + value.text() + "'"
                    else:
                        values = values + ", ''"
                c.execute(
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
        ]

        # Connects to addons_cache database and creates it if it does not exist
        if not os.path.exists(os.path.join(self.settingsDir, "addons_cache.sqlite")):
            self.conn = sqlite3.connect(
                os.path.join(self.settingsDir, "addons_cache.sqlite")
            )
            c = self.conn.cursor()

            for table in table_list:
                c.execute(
                    "CREATE TABLE {tn} ({nf} {ft})".format(
                        tn=table, nf="Name", ft="STRING"
                    )
                )
                for column in self.COLUMN_LIST[1:]:
                    c.execute(
                        "ALTER TABLE {tn} ADD COLUMN '{cn}' {ct}".format(
                            tn=table, cn=column, ct="STRING"
                        )
                    )
        else:
            self.conn = sqlite3.connect(
                os.path.join(self.settingsDir, "addons_cache.sqlite")
            )

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
