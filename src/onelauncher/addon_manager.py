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
# (C) 2019-2025 June Stepp <contact@JuneStepp.me>
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
import html
import logging
import re
import sqlite3
import ssl
import urllib
import xml.dom.minidom
import xml.etree.ElementTree as ET
import zipfile
from collections.abc import Callable, Iterator, Sequence
from functools import partial
from pathlib import Path
from shutil import copy, copytree, move, rmtree
from tempfile import TemporaryDirectory
from time import localtime, strftime
from typing import Final, Literal, NamedTuple, TypeAlias, assert_never, overload
from xml.dom import EMPTY_NAMESPACE
from xml.dom.minicompat import NodeList
from xml.dom.minidom import Element

import attrs
import certifi
import defusedxml.minidom  # type: ignore[import-untyped]
import qtawesome
from httpx import HTTPError
from PySide6 import QtCore, QtGui, QtWidgets
from typing_extensions import override

from onelauncher.network.httpx_client import get_httpx_client_sync
from onelauncher.qtapp import get_qapp
from onelauncher.ui.qtdesigner.custom_widgets import QWidgetWithStylePreview

from .__about__ import __title__
from .addons.startup_script import StartupScript
from .config import platform_dirs
from .config_manager import ConfigManager
from .game_config import GameConfigID, GameType
from .game_launcher_local_config import GameLauncherLocalConfig
from .game_utilities import get_game_settings_dir
from .ui.addon_manager_uic import Ui_winAddonManager
from .utilities import CaseInsensitiveAbsolutePath

logger = logging.getLogger(__name__)


# Just to fix type hints
class Document(xml.dom.minidom.Document):
    @override
    # The type hints for this didn't include the return type or that it accepts
    # `EMPTY_NAMESPACE` which is equal to `None`.
    def createElementNS(self, namespaceURI: str | None, qualifiedName: str) -> Element:
        return super().createElementNS(namespaceURI, qualifiedName)  # type: ignore[arg-type,no-any-return]


class Addon(NamedTuple):
    interface_id: str
    file: str
    """File is the URL if the addon is remote."""
    name: str


@attrs.define
class AddonInfo(Sequence[str]):
    # DON'T CHANGE THE ORDER OF THESE FIELDS. This is a wrapper over what used to be
    # normal sequences of strings.
    name: str | Literal[""] = ""
    category: str | Literal[""] = ""
    version: str | Literal[""] = ""
    author: str | Literal[""] = ""
    latest_release: str | Literal[""] = ""
    file: str | Literal[""] = ""
    """File is the URL if the addon is remote."""
    interface_id: str | Literal[""] = ""
    dependencies: str | Literal[""] = ""
    startup_script: str | Literal[""] = ""

    @override
    def __iter__(self) -> Iterator[str | Literal[""]]:
        yield from attrs.astuple(self)

    @override
    def __len__(self) -> int:
        return len(attrs.astuple(self))

    @overload
    def __getitem__(self, int: int, /) -> str: ...
    @overload
    def __getitem__(self, slice: slice, /) -> Sequence[str]: ...

    @override
    def __getitem__(self, key: int | slice) -> str | tuple[str, ...]:
        return attrs.astuple(self).__getitem__(key)

    def __setitem__(self, index: int, value: str) -> None:
        setattr(self, tuple(attrs.asdict(self).keys())[index], value)


def GetText(nodelist: NodeList[Element]) -> str:
    return "".join(
        node.data  # type: ignore[attr-defined]
        for node in nodelist
        if node.nodeType in [node.TEXT_NODE, node.CDATA_SECTION_NODE]
    )


class AddonManagerWindow(QWidgetWithStylePreview):
    # ID is from the order plugins are found on the filesystem. InterfaceID is
    # the unique ID for plugins on lotrointerface.com
    # Don't change order of list
    COLUMN_LIST: Final = (
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
    )
    TableWidgetColumnName: TypeAlias = Literal[
        "ID",
        "Name",
        "Category",
        "Version",
        "Author",
        "Latest Release",
    ]
    TABLE_WIDGET_COLUMNS: Final[tuple[TableWidgetColumnName, ...]] = (
        "ID",
        "Name",
        "Category",
        "Version",
        "Author",
        "Latest Release",
    )
    # Used for type hints, since the typeshed type hint for `Sequence.index()` has `Any`
    # for the value.
    TABLE_WIDGET_COLUMN_INDEXES: Final[dict[TableWidgetColumnName, int]] = {
        column_name: i for i, column_name in enumerate(TABLE_WIDGET_COLUMNS)
    }
    # Don't change order of list
    TABLE_LIST: Final[tuple[str, ...]] = (
        "tablePluginsInstalled",
        "tableSkinsInstalled",
        "tableMusicInstalled",
        "tablePlugins",
        "tableSkins",
        "tableMusic",
        "tableSkinsDDO",
        "tableSkinsDDOInstalled",
    )
    SourceTabName: TypeAlias = Literal["Installed", "Find More"]
    SOURCE_TAB_NAMES: Final[tuple[SourceTabName, ...]] = (
        "Installed",
        "Find More",
    )
    AddonTypeTabName: TypeAlias = Literal["Plugins", "Skins", "Music"]
    TAB_NAMES_LOTRO: Final[tuple[AddonTypeTabName, ...]] = ("Plugins", "Skins", "Music")
    TAB_NAMES_DDO: Final[tuple[AddonTypeTabName, ...]] = ("Skins",)

    PLUGINS_URL = "https://api.lotrointerface.com/fav/OneLauncher-Plugins.xml"
    SKINS_URL = "https://api.lotrointerface.com/fav/OneLauncher-Themes.xml"
    MUSIC_URL = "https://api.lotrointerface.com/fav/OneLauncher-Music.xml"
    SKINS_DDO_URL = "https://api.lotrointerface.com/fav/OneLauncher-Themes-DDO.xml"

    CATEGORY_UNMANAGED: Final = "Unmanaged"
    """Category name for unmanaged addons"""

    def __init__(
        self,
        config_manager: ConfigManager,
        game_id: GameConfigID,
        launcher_local_config: GameLauncherLocalConfig,
    ):
        super().__init__()
        self.config_manager = config_manager
        self.game_id: GameConfigID = game_id
        self.ui = Ui_winAddonManager()
        self.ui.setupUi(self)

        game_config = self.config_manager.get_game_config(self.game_id)

        self.setWindowTitle(f"Addons Manager - {game_config.name}")

        color_scheme_changed = get_qapp().styleHints().colorSchemeChanged

        for source_tab_name in self.SOURCE_TAB_NAMES:
            self.ui.tabBarSource.addTab(source_tab_name)
        self.ui.tabBarSource.setExpanding(True)
        self.ui.tabBarSource.currentChanged.connect(self.tabBarIndexChanged)
        self.tab_names: tuple[AddonManagerWindow.AddonTypeTabName, ...]
        if game_config.game_type == GameType.LOTRO:
            self.tab_names = self.TAB_NAMES_LOTRO
        elif game_config.game_type == GameType.DDO:
            self.tab_names = self.TAB_NAMES_DDO
        else:
            assert_never(game_config.game_type)
        for addon_tab_name in self.tab_names:
            self.ui.tabBarInstalled.addTab(addon_tab_name)
            self.ui.tabBarRemote.addTab(addon_tab_name)
        # Bar won't show up without setting a minimum size
        self.ui.tabBarInstalled.setMinimumSize(1, 1)
        self.ui.tabBarRemote.setMinimumSize(1, 1)
        self.ui.tabBarInstalled.currentChanged.connect(self.tabBarInstalledIndexChanged)
        self.ui.tabBarRemote.currentChanged.connect(self.tabBarRemoteIndexChanged)

        self.btnAddonsMenu = QtWidgets.QMenu()
        self.btnAddonsMenu.addAction(self.ui.actionUpdateSelectedAddons)
        self.ui.actionUpdateSelectedAddons.triggered.connect(self.updateSelectedAddons)
        self.btnAddonsMenu.addAction(self.ui.actionShowSelectedOnLotrointerface)
        self.ui.actionShowSelectedOnLotrointerface.triggered.connect(
            self.showSelectedOnLotrointerface
        )
        self.btnAddonsMenu.addAction(self.ui.actionShowSelectedAddonsInFileManager)
        self.ui.actionShowSelectedAddonsInFileManager.triggered.connect(
            self.show_selected_addons_in_file_manager
        )
        self.btnAddonsMenu.addAction(self.ui.actionAddonImport)
        self.ui.actionAddonImport.triggered.connect(self.actionAddonImportSelected)
        self.btnAddonsMenu.addAction(self.ui.actionShowPluginsFolderInFileManager)
        self.ui.actionShowPluginsFolderInFileManager.triggered.connect(
            self.actionShowPluginsFolderSelected
        )
        self.btnAddonsMenu.addAction(self.ui.actionShowSkinsFolderInFileManager)
        self.ui.actionShowSkinsFolderInFileManager.triggered.connect(
            self.actionShowSkinsFolderSelected
        )
        self.btnAddonsMenu.addAction(self.ui.actionShowMusicFolderInFileManager)
        self.ui.actionShowMusicFolderInFileManager.triggered.connect(
            self.actionShowMusicFolderSelected
        )
        self.btnAddonsMenu.aboutToShow.connect(self.update_addons_button_actions)
        self.ui.btnAddons.setMenu(self.btnAddonsMenu)
        self.ui.btnAddons.clicked.connect(self.btnAddonsClicked)
        self.update_btn_addons()
        color_scheme_changed.connect(self.update_btn_addons)

        self.ui.actionInstallAddon.triggered.connect(self.actionInstallAddonSelected)
        self.ui.actionUninstallAddon.triggered.connect(
            self.actionUninstallAddonSelected
        )
        self.ui.actionUpdateAddon.triggered.connect(self.actionUpdateAddonSelected)

        self.ui.actionEnableStartupScript.triggered.connect(
            self.actionEnableStartupScriptSelected
        )
        self.ui.actionDisableStartupScript.triggered.connect(
            self.actionDisableStartupScriptSelected
        )
        self.ui.actionShowAddonInFileManager.triggered.connect(
            self.actionShowAddonInFileManagerSelected
        )

        # Will only show when a downlaod is hapenning
        self.ui.progressBar.setVisible(False)

        get_check_for_updates_icon = partial(qtawesome.icon, "fa5s.sync-alt")
        self.ui.btnCheckForUpdates.setIcon(get_check_for_updates_icon())
        self.ui.btnCheckForUpdates_2.setIcon(get_check_for_updates_icon())
        color_scheme_changed.connect(
            lambda: self.ui.btnCheckForUpdates.setIcon(get_check_for_updates_icon())
        )
        color_scheme_changed.connect(
            lambda: self.ui.btnCheckForUpdates_2.setIcon(get_check_for_updates_icon())
        )
        self.ui.btnCheckForUpdates.pressed.connect(self.checkForUpdates)
        self.ui.btnCheckForUpdates_2.pressed.connect(self.checkForUpdates)
        self.ui.btnUpdateAll.pressed.connect(self.updateAll)

        self.ui.txtSearchBar.setFocus()
        self.ui.txtSearchBar.textChanged.connect(self.txtSearchBarTextChanged)

        # The order of these should match
        self.ui_tables_installed: Final[tuple[QtWidgets.QTableWidget, ...]] = (
            self.ui.tablePluginsInstalled,
            self.ui.tableSkinsInstalled,
            self.ui.tableMusicInstalled,
        )
        self.ui_tables_remote: Final[tuple[QtWidgets.QTableWidget, ...]] = (
            self.ui.tablePlugins,
            self.ui.tableSkins,
            self.ui.tableMusic,
        )
        for table in self.ui_tables_installed + self.ui_tables_remote:
            table.setColumnCount(len(self.TABLE_WIDGET_COLUMNS))
            table.setHorizontalHeaderLabels(self.TABLE_WIDGET_COLUMNS)
            table.hideColumn(self.TABLE_WIDGET_COLUMN_INDEXES["ID"])
            table.sortItems(self.TABLE_WIDGET_COLUMN_INDEXES["Name"])

            table.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
            table.customContextMenuRequested.connect(
                partial(self.contextMenuRequested, table=table)
            )
        self.ui.actionShowOnLotrointerface.triggered.connect(
            self.actionShowOnLotrointerfaceSelected
        )

        self.openDB()

        self.data_folder = get_game_settings_dir(
            game_config=self.config_manager.get_game_config(self.game_id),
            launcher_local_config=launcher_local_config,
        )
        if game_config.game_type == GameType.DDO:
            self.data_folder_skins = self.data_folder / "ui/skins"
            self.ui.tableSkinsInstalled.setObjectName("tableSkinsDDOInstalled")
            self.ui.tableSkins.setObjectName("tableSkinsDDO")
        else:
            self.data_folder_plugins = self.data_folder / "Plugins"
            self.data_folder_skins = self.data_folder / "ui/skins"
            self.data_folder_music = self.data_folder / "Music"
        # This will load up whatever's needed for the initial tab. Ex. Plugins
        self.tabBarInstalledIndexChanged(self.ui.tabBarInstalled.currentIndex())

    def getInstalledSkins(self, folders_list: list[Path] | None = None) -> None:
        if self.isTableEmpty(self.ui.tableSkinsInstalled):
            folders_list = None

        self.data_folder_skins.mkdir(parents=True, exist_ok=True)

        if not folders_list:
            folders_list = [
                path for path in self.data_folder_skins.glob("*") if path.is_dir()
            ]

        skins_list = []
        skins_list_compendium = []
        for folder in folders_list:
            skins_list.append(folder)
            for file in folder.iterdir():
                if file.suffix == ".skincompendium":
                    skins_list_compendium.append(file)
                    skins_list.remove(folder)
                    break

        self.addInstalledSkinsToDB(skins_list, skins_list_compendium)

    def addInstalledSkinsToDB(
        self, skins_list: list[Path], skins_list_compendium: list[Path]
    ) -> None:
        table = self.ui.tableSkinsInstalled

        # Clears rows from db table if needed (This function is called to add
        # newly installed skins after initial load as well)
        if self.isTableEmpty(table):
            self.c.execute(
                f"DELETE FROM {table.objectName()}"  # nosec  # noqa: S608
            )

        for skin in skins_list_compendium:
            addon_info = self.parseCompendiumFile(skin, "SkinConfig")
            if addon_info is None:
                continue
            addon_info = self.getOnlineAddonInfo(
                addon_info, self.ui.tableSkins.objectName()
            )
            self.addRowToDB(table, addon_info)

        for skin in skins_list:
            addon_info = AddonInfo(
                name=skin.name, file=str(skin), category=self.CATEGORY_UNMANAGED
            )
            self.addRowToDB(table, addon_info)

        # Populate user visible table
        self.reloadSearch(self.ui.tableSkinsInstalled)

    def getInstalledMusic(self, folders_list: list[Path] | None = None) -> None:
        if self.isTableEmpty(self.ui.tableMusicInstalled):
            folders_list = None

        self.data_folder_music.mkdir(parents=True, exist_ok=True)

        if not folders_list:
            folders_list = [
                path for path in self.data_folder_music.glob("*") if path.is_dir()
            ]

        music_list = []
        music_list_compendium = []
        for folder in folders_list:
            music_list.append(folder)
            for file in folder.iterdir():
                if file.suffix == ".musiccompendium":
                    music_list_compendium.append(folder / file)
                    music_list.remove(folder)
                    break

        music_list.extend(
            file for file in self.data_folder_music.iterdir() if file.suffix == ".abc"
        )
        self.addInstalledMusicToDB(music_list, music_list_compendium)

    def parse_abc_file(self, abc_path: Path) -> tuple[str, str]:
        with abc_path.open() as file:
            song_name = ""
            author = ""
            for _ in range(3):
                line = file.readline().strip()
                if line.startswith("T: "):
                    song_name = line[3:]
                if line.startswith("Z: "):
                    author = (
                        line[18:] if line.startswith("Z: Transcribed by ") else line[3:]
                    )

            return song_name, author

    def addInstalledMusicToDB(
        self, music_list: list[Path], music_list_compendium: list[Path]
    ) -> None:
        table = self.ui.tableMusicInstalled

        # Clears rows from db table if needed (This function is called
        # to add newly installed music after initial load as well)
        if self.isTableEmpty(table):
            self.c.execute("DELETE FROM tableMusicInstalled")

        for music in music_list_compendium:
            addon_info = self.parseCompendiumFile(music, "MusicConfig")
            if addon_info is None:
                continue
            addon_info = self.getOnlineAddonInfo(addon_info, "tableMusic")
            self.addRowToDB(table, addon_info)

        for music in music_list:
            addon_info = AddonInfo(
                name=music.stem, file=str(music), category=self.CATEGORY_UNMANAGED
            )
            if music.suffix == ".abc":
                song_name, addon_info.author = self.parse_abc_file(music)
                if song_name:
                    addon_info.name = song_name
            self.addRowToDB(table, addon_info)

        # Populate user visible table
        self.reloadSearch(table)

    def getInstalledPlugins(
        self, folders_list: list[CaseInsensitiveAbsolutePath] | None = None
    ) -> None:
        if self.isTableEmpty(self.ui.tablePluginsInstalled):
            folders_list = None

        self.data_folder_plugins.mkdir(parents=True, exist_ok=True)

        if not folders_list:
            folders_list = [
                path for path in self.data_folder_plugins.glob("*") if path.is_dir()
            ]

        # Finds all plugins and adds their .plugincompendium files to a list
        plugins_list_compendium = []
        plugins_list = []
        for folder in folders_list:
            for file in folder.glob("**/*.plugin*"):
                if file.suffix == ".plugincompendium":
                    # .plugincompenmdium file should be in author folder of plugin
                    if file.parent == folder:
                        plugins_list_compendium.append(file)
                elif file.suffix == ".plugin":
                    plugins_list.append(file)

        self.removeManagedPluginsFromList(plugins_list, plugins_list_compendium)

        self.addInstalledPluginsToDB(plugins_list, plugins_list_compendium)

    def removeManagedPluginsFromList(
        self,
        plugin_files: list[CaseInsensitiveAbsolutePath],
        compendium_files: list[CaseInsensitiveAbsolutePath],
    ) -> None:
        """Removes plugin files from plugin_files that aren't managed by a compendium file"""
        for compendium_file in compendium_files:
            try:
                doc = defusedxml.minidom.parse(str(compendium_file))
            except xml.parsers.expat.ExpatError:
                logger.warning(
                    f"`.plugincompendium` file has invalid XML: {compendium_file}",
                    exc_info=True,
                )
                continue
            nodes = doc.getElementsByTagName("Descriptors")[0].childNodes

            for node in nodes:
                if node.nodeName == "descriptor":
                    descriptor_path = self.data_folder_plugins / (
                        GetText(node.childNodes).replace("\\", "/")
                    )

                    # Remove descriptor plugin file from plugin_files
                    descriptor_plugin_files = [
                        file for file in plugin_files if file == descriptor_path
                    ]
                    for file in descriptor_plugin_files:
                        plugin_files.remove(file)

                    if not descriptor_path.exists():
                        logger.error(f"{compendium_file} has misconfigured descriptors")

    def addInstalledPluginsToDB(
        self,
        plugin_files: list[CaseInsensitiveAbsolutePath],
        compendium_files: list[CaseInsensitiveAbsolutePath],
    ) -> None:
        table = self.ui.tablePluginsInstalled

        # Clears rows from db table if needed (This function is called to
        # add newly installed plugins after initial load as well)
        if self.isTableEmpty(table):
            self.c.execute("DELETE FROM tablePluginsInstalled")

        for file in compendium_files + plugin_files:
            # Sets tag for plugin file xml search and category for unmanaged
            # plugins
            if file.suffix == ".plugincompendium":
                addon_info = self.parseCompendiumFile(file, "PluginConfig")
                if addon_info is None:
                    continue
                addon_info = self.getOnlineAddonInfo(addon_info, "tablePlugins")
            else:
                addon_info = self.parseCompendiumFile(file, "Information")
                if addon_info is None:
                    continue
                addon_info.category = self.CATEGORY_UNMANAGED

            self.addRowToDB(table, addon_info)

        # Populate user visible table
        self.reloadSearch(self.ui.tablePluginsInstalled)

    def getAddonDependencies(self, dependencies_node: Element) -> str:
        dependencies = ""
        for node in dependencies_node.childNodes:
            if node.nodeName == "dependency":
                dependencies = f"{dependencies},{GetText(node.childNodes)}"
        return dependencies[1:]

    def parseCompendiumFile(self, file: Path, tag: str) -> AddonInfo | None:
        """Returns list of common values for compendium or .plugin files"""
        addon_info = AddonInfo()

        try:
            doc = defusedxml.minidom.parse(str(file))
        except xml.parsers.expat.ExpatError:
            logger.exception(f"Compendium file has invalid XML: {file}")
            return None
        nodes = doc.getElementsByTagName(tag)[0].childNodes
        for node in nodes:
            if node.nodeName == "Name":
                addon_info.name = GetText(node.childNodes)
            elif node.nodeName == "Author":
                addon_info.author = GetText(node.childNodes)
            elif node.nodeName == "Version":
                addon_info.version = GetText(node.childNodes)
            elif node.nodeName == "Id":
                addon_info.interface_id = GetText(node.childNodes)
            elif node.nodeName == "Dependencies":
                addon_info.dependencies = self.getAddonDependencies(node)
            elif node.nodeName == "StartupScript":
                addon_info.startup_script = GetText(node.childNodes)
        addon_info.file = str(file)

        return addon_info

    def getOnlineAddonInfo(
        self, addon_info: AddonInfo, remote_addons_table: str
    ) -> AddonInfo:
        for info in self.c.execute(
            f"SELECT Category, LatestRelease FROM {remote_addons_table} WHERE InterfaceID == ?",  # noqa: S608
            (addon_info[6],),
        ):
            addon_info.category = info[0]
            addon_info.latest_release = info[1]

        # Unmanaged if not in online cache
        if not addon_info.category:
            addon_info.category = self.CATEGORY_UNMANAGED

        return addon_info

    def openDB(self) -> None:
        """
        Opens addons_cache database and creates new database if
        one doesn't exist or the current one has an outdated structure
        """
        addons_cache_db_path = platform_dirs.user_cache_path / "addons_cache.sqlite"
        if addons_cache_db_path.exists():
            # Connects to addons_cache database
            self.conn = sqlite3.connect(str(addons_cache_db_path))
            self.c = self.conn.cursor()

            # Replace old database if its structure is out of date
            if self.isCurrentDBOutdated():
                self.closeDB()
                addons_cache_db_path.unlink()
                self.createDB()
        else:
            self.createDB()

    def isCurrentDBOutdated(self) -> bool:
        """
        Checks if currently loaded database's structure is up to date.
        Returns True if it is outdated and False otherwise.
        """

        tables_dict: dict[str, list[str]] = {}
        # SQL returns all the columns in all the tables labled with what table
        # they're from
        column_data: tuple[str, str]
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
            if table not in tables_dict:
                return True

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

        # Only return False if there are no extra tables
        return bool(tables_dict)

    def createDB(self) -> None:
        """Creates ans sets up addons_cache database"""
        self.conn = sqlite3.connect(
            str(platform_dirs.user_cache_path / "addons_cache.sqlite")
        )
        self.c = self.conn.cursor()

        for table in self.TABLE_LIST:
            self.c.execute(
                "CREATE VIRTUAL TABLE {tbl_nm} USING FTS5({clmA}, {clmB}, {clmC}, "  # noqa: UP032
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

    def closeDB(self) -> None:
        self.conn.commit()
        self.conn.close()

    def actionAddonImportSelected(self) -> None:
        # DDO doesn't support playing music from .abc files
        if self.config_manager.get_game_config(self.game_id).game_type == GameType.DDO:
            addon_formats = "*.zip *.rar"
        else:
            addon_formats = "*.zip *.rar *.abc"

        file_names = QtWidgets.QFileDialog.getOpenFileNames(
            self,
            "Addon Files/Archives",
            str(Path("~").expanduser()),
            addon_formats,
        )

        if file_names[0]:
            for file in file_names[0]:
                self.installAddon(Path(file))

    def installAddon(self, addon_path: Path, interface_id: str = "") -> None:
        # Install .abc files
        if addon_path.suffix == ".abc":
            self.installAbcFile(addon_path)
            return
        elif addon_path.suffix == ".rar":
            logger.error(
                f"{__title__} does not support .rar archives, because it"
                " is a proprietary format that would require and external "
                "program to extract"
            )
            return
        elif addon_path.suffix == ".zip":
            self.installZipAddon(addon_path, interface_id)

    def installAbcFile(self, addon_path: Path) -> None:
        if self.config_manager.get_game_config(self.game_id).game_type == GameType.DDO:
            logger.error("DDO does not support .abc/music files")
            return

        copy(str(addon_path), self.data_folder_music)
        logger.debug(f"ABC file installed at {addon_path}")

        # Plain .abc files are installed to base music directory,
        # so what is scanned can't be controlled
        self.ui.tableMusicInstalled.clearContents()
        self.getInstalledMusic()

    def installZipAddon(self, addon_path: Path, interface_id: str) -> None:
        with TemporaryDirectory() as tmp_dir_name:
            tmp_dir = CaseInsensitiveAbsolutePath(tmp_dir_name)

            # Extract addon to temporary directory.
            with zipfile.ZipFile(addon_path, "r") as archive:
                # Addons without any files aren't valid
                if all(zip_info.is_dir() for zip_info in archive.infolist()):
                    logger.error("Addon Zip is empty")
                    return

                archive.extractall(tmp_dir)

            self.clean_temp_addon_folder(tmp_dir)

            for path in tmp_dir.glob("**/*.*"):
                if path.suffix == ".plugin":
                    self.install_plugin(tmp_dir, interface_id)
                    return
                elif path.suffix == ".abc":
                    if (
                        self.install_music(tmp_dir, interface_id, addon_path.stem)
                        is not False
                    ):
                        return
            self.install_skin(tmp_dir, interface_id, addon_path.stem)

    def install_plugin(
        self, tmp_dir: CaseInsensitiveAbsolutePath, interface_id: str
    ) -> None:
        """Install plugin from temporary directory"""
        if self.config_manager.get_game_config(self.game_id).game_type == GameType.DDO:
            logger.error("DDO does not support plugins")
            return

        table = self.ui.tablePlugins

        author_folders = list(tmp_dir.glob("*/"))

        # Filter out common dependency folder names
        # that are sometimes included with plugins.
        filtered_author_folders = [
            folder
            for folder in author_folders
            if folder.name.lower() not in ["turbine", "turbineplugins"]
        ]
        # Use non-filtered author folders if there are no author
        # folders left after filtering.
        # Ex. When installing the filtered libraries standalone.
        author_folders = filtered_author_folders or author_folders

        # There can only be one author folder. That is where the
        # compendium file goes. What appear to be extra author
        # folders are usually included dependencies (grr.. there
        # is compendium syntax for that). The true author folder
        # where the actual plugin files are must be determined.
        if len(author_folders) > 1:
            # The most likely author folder is where a
            # .plugincompendium file is.
            if author_folders_compendium := [
                folder
                for folder in author_folders
                if list(folder.glob("*.plugincompendium"))
            ]:
                author_folder = author_folders_compendium[0]
            # The next most likely author folder is where
            # .plugin files are. Dependencies may also
            # have .plugin files though.
            elif author_folders_plugin := [
                folder for folder in author_folders if list(folder.glob("*.plugin"))
            ]:
                author_folder = author_folders_plugin[0]
            else:
                logger.error("Plugin doesn't have an author folder with a .plugin file")
                return
        else:
            author_folder = author_folders[0]

        # .plugin files should always be in the author folder. All others
        # will be ignored by both me and the game.
        plugin_files = list(author_folder.glob("*.plugin"))

        existing_compendium_file = self.get_existing_compendium_file(author_folder)
        if existing_compendium_file is False:
            return

        compendium_files: list[CaseInsensitiveAbsolutePath] = []
        # Only make compendium file for addons installed from online
        if interface_id:
            compendium_file = self.generateCompendiumFile(
                author_folder,
                interface_id,
                "Plugin",
                table.objectName(),
                existing_compendium_file,
            )
            compendium_files.append(compendium_file)
        # Remove compendium files from manually installed addons.
        # This is to limit confusion since there is no way to verify
        # that compendium files from manually installed addons have
        # correct information. ex. They could have some random interface_id
        # suggesting they're the wrong addon and end up getting replaced
        # by the addon for that ID during the updating process.
        elif existing_compendium_file:
            existing_compendium_file.unlink()

        # Move plugin from temp directory to actual plugins directory
        for path in tmp_dir.glob("*/"):
            copytree(path, self.data_folder_plugins / path.name, dirs_exist_ok=True)

        # Make plugin and compendium file paths point to their new location
        plugin_files = [
            self.data_folder_plugins / file.relative_to(tmp_dir)
            for file in plugin_files
        ]
        compendium_files = [
            self.data_folder_plugins / file.relative_to(tmp_dir)
            for file in compendium_files
        ]

        self.removeManagedPluginsFromList(plugin_files, compendium_files)

        self.addInstalledPluginsToDB(plugin_files, compendium_files)

        self.handleStartupScriptActivationPrompt(table, interface_id)
        logger.debug(
            "Installed plugin corresponding to "
            f"{plugin_files} )"
            f"{compendium_files}"
        )

        self.installAddonRemoteDependencies(f"{table.objectName()}Installed")

    def get_existing_compendium_file(
        self, tmp_search_dir: CaseInsensitiveAbsolutePath
    ) -> CaseInsensitiveAbsolutePath | None | Literal[False]:
        """
        Return existing compendium file, None, or False if there are multiple.

        Args:
            tmp_search_dir (Path): Directory to check for compendium files in.
                                   It has to be a temporary folder the addon
                                   has been extracted to or compendium files
                                   from other addons will be detected.
        """
        existing_compendium_files = list(tmp_search_dir.glob("*.*compendium"))
        if len(existing_compendium_files) > 1:
            logger.error("Addon has multiple compendium files")
            return False
        elif len(existing_compendium_files) == 1:
            return existing_compendium_files[0]
        return None

    def install_music(
        self, tmp_dir: CaseInsensitiveAbsolutePath, interface_id: str, addon_name: str
    ) -> None | Literal[False]:
        if self.config_manager.get_game_config(self.game_id).game_type == GameType.DDO:
            logger.error("DDO does not support .abc/music files")
            return None

        # Some plugins have .abc files, but music collections
        # shouldn't have .plugin files.
        if list(tmp_dir.glob("**/*.plugin")):
            return False

        table = self.ui.tableMusic

        root_dir = self.fix_improper_root_dir_addon(tmp_dir, addon_name)

        existing_compendium_file = self.get_existing_compendium_file(root_dir)
        if existing_compendium_file is False:
            return None

        if interface_id:
            self.generateCompendiumFile(
                root_dir,
                interface_id,
                "Music",
                table.objectName(),
                existing_compendium_file,
            )

        # Move the addon into the real data folder
        copytree(root_dir, self.data_folder_music / root_dir.name, dirs_exist_ok=True)
        root_dir = self.data_folder_music / root_dir.name

        self.getInstalledMusic(folders_list=[root_dir])

        self.handleStartupScriptActivationPrompt(table, interface_id)

        logger.debug(f"{addon_name} music installed at {root_dir}")

        self.installAddonRemoteDependencies(f"{table.objectName()}Installed")
        return None

    def install_skin(
        self, tmp_dir: CaseInsensitiveAbsolutePath, interface_id: str, addon_name: str
    ) -> None:
        table = self.ui.tableSkins

        root_dir = self.fix_improper_root_dir_addon(tmp_dir, addon_name)

        existing_compendium_file = self.get_existing_compendium_file(root_dir)
        if existing_compendium_file is False:
            return

        if interface_id:
            self.generateCompendiumFile(
                root_dir,
                interface_id,
                "Skin",
                table.objectName(),
                existing_compendium_file,
            )

        # Move the addon into the real data folder
        copytree(root_dir, self.data_folder_skins / root_dir.name, dirs_exist_ok=True)
        root_dir = self.data_folder_skins / root_dir.name

        self.getInstalledSkins(folders_list=[root_dir])

        self.handleStartupScriptActivationPrompt(table, interface_id)

        logger.debug(f"{addon_name} skin installed at {root_dir}")

        self.installAddonRemoteDependencies(f"{table.objectName()}Installed")

    def installAddonRemoteDependencies(self, table_name: str) -> None:
        """Installs the dependencies for the last installed addon"""
        # Get dependencies for last column in db
        dependencies: str | None = None
        for item in self.c.execute(
            f"SELECT Dependencies FROM {table_name} ORDER BY rowid DESC LIMIT 1"  # noqa: S608
        ):
            dependencies = item[0]
        if dependencies is None:
            raise ValueError("Addon dependencies not found in DB")

        for dependency in dependencies.split(","):
            if not dependency:
                continue
            # 0 is the arbitrary ID for Turbine Utilities. 1064 is the ID
            # of OneLauncher's upload of the utilities on LotroInterface
            interface_id = "1064" if dependency == "0" else dependency

            for item in self.c.execute(  # nosec
                f"SELECT File, Name FROM {table_name.split('Installed')[0]} WHERE InterfaceID = ? AND InterfaceID NOT IN (SELECT InterfaceID FROM {table_name})",  # noqa: S608
                (interface_id,),
            ):
                self.installRemoteAddon(item[0], item[1], interface_id)

    def fix_improper_root_dir_addon(
        self, addon_tmp_dir: CaseInsensitiveAbsolutePath, addon_name: str
    ) -> CaseInsensitiveAbsolutePath:
        """Moves addon to new folder if the top of the directory tree
           is anything but one folder and no files. This should only be
           used for skins and music.

        Args:
            addon_tmp_dir (Path): Temporary directory where the addon has been extracted.
            addon_name (str): Name to give the new folder if it is made.

        Returns:
            (Path): Root dir of the addon. Where the compendium file should go.
        """
        temp_dir_contents = list(addon_tmp_dir.glob("*"))

        # If there is already a root dir and nothing else
        if len(temp_dir_contents) == 1 and temp_dir_contents[0].is_dir():
            return temp_dir_contents[0]

        with TemporaryDirectory() as tmp_dir_name:
            tmp_dir = CaseInsensitiveAbsolutePath(tmp_dir_name)

            # Move addon_tmp_dir contents to new temporary folder.
            # This is to prevent issues with addon_name being the
            # same as one of the existing folders in addon_tmp_dir.
            for path in temp_dir_contents:
                move(path, tmp_dir)

            # Make new folder to be the addon root dir
            new_addon_root_dir = addon_tmp_dir / addon_name
            new_addon_root_dir.mkdir()

            # Move all of the original contents of addon_tmp_dir
            # into the new root dir.
            for path in tmp_dir.glob("*"):
                move(path, new_addon_root_dir)

        return new_addon_root_dir

    def clean_temp_addon_folder(self, addon_dir: Path) -> None:
        """Scans temp folder for invalid folder names like "ui" or
           "plugins" and moves stuff out of them. Addon authors put
           files in invalid folders when they want the user to extract
           the file somewere higher up the folder tree than where their
           work ends up. This is usually done for user convenience.

        Args:
            addon_dir (Path): Temporary folder where addon has been extracted.
        """
        invalid_folder_names = [
            "ui",
            "skins",
            "plugins",
            "music",
            "my documents",
            "documents",
            "the lord of the rings online",
            "dungeons and dragons online",
            "dungeons & dragons online",
        ]
        with TemporaryDirectory() as tmp_dir_name:
            tmp_dir = Path(tmp_dir_name)

            while True:  # This outer loop is to check for nested invalid directories.
                invalid_dir = None
                for potential_invalid_dir in addon_dir.glob("*/"):
                    if potential_invalid_dir.name.lower() in invalid_folder_names:
                        invalid_dir = potential_invalid_dir
                        # Move everything from the invalid directory to a temporary one.
                        # This is done to prevent issues when a folder in the invalid folder
                        # has the same name as the invalid folder.
                        for path in invalid_dir.glob("*"):
                            move(str(path), str(tmp_dir))

                        invalid_dir.rmdir()

                        # Move files that were originally in the invalid folder
                        # to the root addon_dir.
                        # Now the whole loop can run again to check for nested invalid
                        # folders that have now been moved to the root addon_dir.
                        for path in tmp_dir.glob("*"):
                            move(str(path), str(addon_dir))

                # Stop loop if there were no more invalid folders discovered.
                if invalid_dir is None:
                    break

    def generateCompendiumFile(
        self,
        tmp_addon_root_dir: CaseInsensitiveAbsolutePath,
        interface_id: str,
        addon_type: str,
        table: str,
        existing_compendium_file: CaseInsensitiveAbsolutePath | None = None,
    ) -> CaseInsensitiveAbsolutePath:
        """
        Generate compendium file for addon. If there is an existing one
        data that can only be gotten from it will be gathered and put
        in the new file. The old one will be removed.

        Args:
            tmp_addon_root_dir (Path): Where the compendium file goes. In the
                                       case of plugins it should be the author's
                                       name. This has to be the addon root dir
                                       while it is still in a temporary directory
                                       for propper .plugin file detection.
            interface_id (str): [description]
            addon_type (str): The type of the addon. ("Plugin", "Music", "Skin")
            table (str): The database table name for the addon type. Used to get remote
                         addon information.
            existing_compendium_file (Path, optional): An existing compendium file to
                                                       extract data from. Defaults to None.
        """
        dependencies = ""
        startup_python_script = ""
        # Get dependencies and startup_python_script from existing compendium
        # file if present.
        if existing_compendium_file:
            existing_compendium_values = self.parseCompendiumFile(
                existing_compendium_file, f"{addon_type.title()}Config"
            )
            if existing_compendium_values is not None:
                dependencies = existing_compendium_values[7]
                startup_python_script = existing_compendium_values[8]
            existing_compendium_file.unlink()

        for row in self.c.execute(
            f"SELECT * FROM {table} WHERE InterfaceID = ?",  # noqa: S608
            (interface_id,),
        ):
            if row[0]:
                doc = Document()
                mainNode = doc.createElementNS(
                    EMPTY_NAMESPACE, f"{addon_type.title()}Config"
                )
                doc.appendChild(mainNode)

                tempNode = doc.createElementNS(EMPTY_NAMESPACE, "Id")
                tempNode.appendChild(doc.createTextNode(f"{row[6]}"))
                mainNode.appendChild(tempNode)

                tempNode = doc.createElementNS(EMPTY_NAMESPACE, "Name")
                tempNode.appendChild(doc.createTextNode(f"{row[0]}"))
                mainNode.appendChild(tempNode)

                tempNode = doc.createElementNS(EMPTY_NAMESPACE, "Version")
                tempNode.appendChild(doc.createTextNode(f"{row[2]}"))
                mainNode.appendChild(tempNode)

                tempNode = doc.createElementNS(EMPTY_NAMESPACE, "Author")
                tempNode.appendChild(doc.createTextNode(f"{row[3]}"))
                mainNode.appendChild(tempNode)

                tempNode = doc.createElementNS(EMPTY_NAMESPACE, "InfoUrl")
                tempNode.appendChild(
                    doc.createTextNode(f"{self.getInterfaceInfoUrl(row[5])}")
                )
                mainNode.appendChild(tempNode)

                tempNode = doc.createElementNS(EMPTY_NAMESPACE, "DownloadUrl")
                tempNode.appendChild(doc.createTextNode(f"{row[5]}"))
                mainNode.appendChild(tempNode)

                if addon_type.title() == "Plugin":
                    # Add plugin's .plugin file descriptors
                    descriptorsNode = doc.createElementNS(
                        EMPTY_NAMESPACE, "Descriptors"
                    )
                    mainNode.appendChild(descriptorsNode)
                    for plugin_file in tmp_addon_root_dir.glob("*.plugin"):
                        tempNode = doc.createElementNS(EMPTY_NAMESPACE, "descriptor")
                        tempNode.appendChild(
                            doc.createTextNode(
                                f"{tmp_addon_root_dir.name}\\{plugin_file.name}"
                            )
                        )
                        descriptorsNode.appendChild(tempNode)

                # Can't add dependencies, because they are defined in
                # compendium files
                dependenciesNode = doc.createElementNS(EMPTY_NAMESPACE, "Dependencies")
                mainNode.appendChild(dependenciesNode)

                # If compendium file from addon already existed with
                # dependencies
                if dependencies:
                    for dependency in dependencies.split(","):
                        tempNode = doc.createElementNS(EMPTY_NAMESPACE, "dependency")
                        tempNode.appendChild(doc.createTextNode(f"{dependency}"))
                        dependenciesNode.appendChild(tempNode)

                # Can't add startup script, because it is defined in compendium
                # files
                startupScriptNode = doc.createElementNS(
                    EMPTY_NAMESPACE, "StartupScript"
                )
                # If compendium file from add-n already existed with startup
                # script
                if startup_python_script:
                    startupScriptNode.appendChild(
                        doc.createTextNode(f"{startup_python_script}")
                    )
                mainNode.appendChild(startupScriptNode)

                # Write compendium file
                compendium_file = (
                    tmp_addon_root_dir / f"{row[0]}.{addon_type.lower()}compendium"
                )
                with compendium_file.open("w+") as file:
                    # Use ElementTree for prettification. Minidom isn't great at it.
                    etree_element = ET.XML(doc.toxml())
                    ET.indent(etree_element)
                    file.write(ET.tostring(etree_element, encoding="unicode"))

                return compendium_file

        raise KeyError(f"No DB entry for Interface ID {interface_id} found")

    def getInterfaceInfoUrl(self, download_url: str) -> str:
        """Replaces "download" with "info" in download url to make info url

        An example is: https://www.lotrointerface.com/downloads/download1078-VitalTarget
                   to: https://www.lotrointerface.com/downloads/info1078-VitalTarget
        """
        return download_url.replace("/downloads/download", "/downloads/info")

    def txtSearchBarTextChanged(self, text: str) -> None:
        index = self.ui.tabBarSource.currentIndex()
        if self.SOURCE_TAB_NAMES[index] == "Installed":
            index_installed = self.ui.tabBarInstalled.currentIndex()
            if self.tab_names[index_installed] == "Plugins":
                self.searchDB(self.ui.tablePluginsInstalled, text)
            elif self.tab_names[index_installed] == "Skins":
                self.searchDB(self.ui.tableSkinsInstalled, text)
            elif self.tab_names[index_installed] == "Music":
                self.searchDB(self.ui.tableMusicInstalled, text)
        # If in Find More tab
        elif self.SOURCE_TAB_NAMES[index] == "Find More":
            index_remote = self.ui.tabBarRemote.currentIndex()
            if self.tab_names[index_remote] == "Plugins":
                self.searchDB(self.ui.tablePlugins, text)
            elif self.tab_names[index_remote] == "Skins":
                self.searchDB(self.ui.tableSkins, text)
            elif self.tab_names[index_remote] == "Music":
                self.searchDB(self.ui.tableMusic, text)

    def optimizeTableColumnWidths(self, table: QtWidgets.QTableWidget) -> None:
        prioritized_column = self.TABLE_WIDGET_COLUMN_INDEXES["Name"]
        table.resizeColumnToContents(prioritized_column)
        columns_with = sum(
            [
                table.columnWidth(i)
                for i in range(table.columnCount())
                if not table.isColumnHidden(i)
            ]
        )
        if columns_with > table.viewport().width():
            table.horizontalHeader().setMaximumSectionSize(
                table.fontMetrics().boundingRect("A Somewhat Long Addon Name").width()
            )
            table.resizeColumnToContents(prioritized_column)
            table.horizontalHeader().setMaximumSectionSize(-1)

    def searchDB(self, table: QtWidgets.QTableWidget, text: str) -> None:
        table.clearContents()
        table.setRowCount(0)

        if text:
            for word in text.split():
                search_word = f"%{word}%"

                for result in self.c.execute(
                    # nosec
                    f"SELECT rowid, * FROM {table.objectName()} WHERE Author LIKE ? OR Category LIKE ? OR Name LIKE ?",  # noqa: S608
                    (search_word, search_word, search_word),
                ):
                    rowid = result[0]
                    addon_info = AddonInfo(*result[1:])
                    # Detects duplicates from multi-word search
                    duplicate = False
                    for item in table.findItems(
                        addon_info.name, QtCore.Qt.MatchFlag.MatchExactly
                    ):
                        if (
                            int(
                                (
                                    table.item(
                                        item.row(),
                                        self.TABLE_WIDGET_COLUMN_INDEXES["ID"],
                                    )
                                ).text()
                            )
                            == rowid
                        ):
                            duplicate = True
                            break
                    if not duplicate:
                        self.addRowToTable(table, rowid=rowid, addon_info=addon_info)
        else:
            # Shows all plugins if the search bar is empty
            for result in self.c.execute(
                # nosec
                f"SELECT rowid, * FROM {table.objectName()}"  # noqa: S608
            ):
                self.addRowToTable(
                    table, rowid=result[0], addon_info=AddonInfo(*result[1:])
                )

        self.optimizeTableColumnWidths(table)

    def isTableEmpty(self, table: QtWidgets.QTableWidget) -> bool:
        return not table.item(0, self.TABLE_WIDGET_COLUMN_INDEXES["Name"])

    def reloadSearch(self, table: QtWidgets.QTableWidget) -> None:
        """Re-searches the current search"""
        self.searchDB(table, self.ui.txtSearchBar.text())

    def resetRemoteAddonsTables(self) -> None:
        for table in self.ui_tables_remote:
            if not self.isTableEmpty(table):
                self.searchDB(table, "")

    def setRemoteAddonToUninstalled(
        self, addon: Addon, remote_table: QtWidgets.QTableWidget
    ) -> None:
        self.c.execute(
            f"UPDATE {remote_table.objectName()} SET Name = ? WHERE InterfaceID == ?",  # nosec  # noqa: S608
            (
                addon[2],
                addon[0],
            ),
        )

        # Removes indicator that a new version of an installed addon is out if present.
        # This is important, because addons are uninstalled and then reinstalled
        # during the update process.
        self.c.execute(
            # nosec
            f"UPDATE {remote_table.objectName()} SET Version = REPLACE(Version,'(Updated) ', '') WHERE "  # noqa: S608
            "Version LIKE '(Updated) %'"
        )

    def setRemoteAddonToInstalled(
        self, addon: Addon, remote_table: QtWidgets.QTableWidget
    ) -> None:
        self.c.execute(
            f"UPDATE {remote_table.objectName()} SET Name = ? WHERE InterfaceID == ?",  # noqa: S608
            (
                f"(Installed) {addon[2]}",
                addon[0],
            ),
        )

    # Adds row to a visible table. First value in list is row name
    def addRowToTable(
        self, table: QtWidgets.QTableWidget, rowid: int | str, addon_info: AddonInfo
    ) -> None:
        table.setSortingEnabled(False)

        rows = table.rowCount()
        table.setRowCount(rows + 1)

        disable_row = False
        for column_index, column_name in enumerate(self.TABLE_WIDGET_COLUMNS):
            tbl_item = QtWidgets.QTableWidgetItem()
            if column_name == "ID":
                tbl_item.setText(str(rowid))
            elif column_name == "Name":
                # Disable row if addon is Installed. This is only applicable to
                # remote tables.
                if addon_info.name.startswith("(Installed) "):
                    tbl_item.setText(addon_info.name.split("(Installed) ")[1])
                    disable_row = True
                else:
                    tbl_item.setText(addon_info.name)
            elif column_name == "Category":
                tbl_item.setText(addon_info.category)
                # Set color to red if addon is unmanaged
                if addon_info.category == self.CATEGORY_UNMANAGED:
                    tbl_item.setForeground(QtGui.QColor("darkred"))
            elif column_name == "Version":
                if addon_info.version.startswith("(Updated) "):
                    tbl_item.setText(addon_info.version.split("(Updated) ")[1])
                    tbl_item.setForeground(QtGui.QColor("green"))
                elif addon_info.version.startswith("(Outdated) "):
                    tbl_item.setText(addon_info.version.split("(Outdated) ")[1])
                    tbl_item.setForeground(QtGui.QColor("crimson"))
                else:
                    tbl_item.setText(addon_info.version)
            elif column_name == "Author":
                tbl_item.setText(addon_info.author)
            elif column_name == "Latest Release":
                tbl_item.setText(addon_info.latest_release)
            else:
                assert_never(column_name)
            table.setItem(rows, column_index, tbl_item)

        if disable_row:
            for i in range(table.columnCount()):
                table.item(rows, i).setFlags(QtCore.Qt.ItemFlag.NoItemFlags)

        table.setSortingEnabled(True)

    def addRowToDB(self, table: QtWidgets.QTableWidget, addon_info: AddonInfo) -> None:
        if table in self.ui_tables_installed:
            addon_info.file = str(
                CaseInsensitiveAbsolutePath(addon_info.file).relative_to(
                    self.data_folder
                )
            )

        question_marks = "?"
        for _ in range(len(addon_info) - 1):
            question_marks += ",?"

        self.c.execute(
            f"INSERT INTO {table.objectName()} VALUES({question_marks})", addon_info
        )

    def btnAddonsClicked(self) -> None:
        table = self.getCurrentTable()

        # If on installed tab which means remove addons
        if table in self.ui_tables_installed:
            uninstall_function = self.getUninstallFunctionFromTable(table)

            uninstallConfirm, addons = self.getUninstallConfirm(table)
            if uninstallConfirm:
                uninstall_function(addons, table)
                self.resetRemoteAddonsTables()
        elif self.SOURCE_TAB_NAMES[self.ui.tabBarSource.currentIndex()] == "Find More":
            self.installRemoteAddons()

    def getUninstallFunctionFromTable(
        self, table: QtWidgets.QTableWidget
    ) -> Callable[[list[Addon], QtWidgets.QTableWidget], None]:
        """Gives function to uninstall addon type for table"""
        if "Skins" in table.objectName():
            return self.uninstallSkins
        elif "Plugins" in table.objectName():
            return self.uninstallPlugins
        elif "Music" in table.objectName():
            return self.uninstallMusic
        else:
            raise IndexError(
                f"{table.objectName()} doesn't correspond to addon type tab"
            )

    def installRemoteAddons(self) -> None:
        table = self.getCurrentTable()

        addons, details = self.getSelectedAddons(table)
        if addons and details:
            for addon in addons:
                self.installRemoteAddon(addon[1], addon[2], addon[0])
                self.setRemoteAddonToInstalled(addon, table)

            self.resetRemoteAddonsTables()
            self.searchSearchBarContents()

    def getCurrentTable(self) -> QtWidgets.QTableWidget:
        """Return the table that the user currently sees based on what tabs they are in"""
        source_tab = self.SOURCE_TAB_NAMES[self.ui.tabBarSource.currentIndex()]
        if source_tab == "Installed":
            addons_tab = self.tab_names[self.ui.tabBarInstalled.currentIndex()]
            if addons_tab == "Plugins":
                table = self.ui.tablePluginsInstalled
            elif addons_tab == "Skins":
                table = self.ui.tableSkinsInstalled
            elif addons_tab == "Music":
                table = self.ui.tableMusicInstalled
            else:
                assert_never(addons_tab)
        elif source_tab == "Find More":
            addons_tab = self.tab_names[self.ui.tabBarRemote.currentIndex()]
            if addons_tab == "Plugins":
                table = self.ui.tablePlugins
            elif addons_tab == "Skins":
                table = self.ui.tableSkins
            elif addons_tab == "Music":
                table = self.ui.tableMusic
            else:
                assert_never(addons_tab)
        else:
            assert_never(source_tab)
        return table

    def installRemoteAddon(self, url: str, name: str, interface_id: str) -> None:
        with TemporaryDirectory() as tmp_dir_name:
            tmp_dir = Path(tmp_dir_name)

            path = tmp_dir / f"{name}.zip"
            status = self.downloader(url, path)
            if status:
                self.installAddon(path, interface_id=interface_id)
                path.unlink()

    def getUninstallConfirm(
        self, table: QtWidgets.QTableWidget
    ) -> tuple[bool, list[Addon]]:
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

    def getSelectedAddons(
        self, table: QtWidgets.QTableWidget
    ) -> tuple[list[Addon], str | None]:
        if not table.selectedItems():
            return [], None
        selected_addons: list[Addon] = []
        details = ""
        # Column count is minus one because of hidden ID column
        for item in table.selectedItems()[0 :: (table.columnCount() - 1)]:
            # Gets db row id for selected row
            selected_row = int(
                (table.item(item.row(), self.TABLE_WIDGET_COLUMN_INDEXES["ID"])).text()
            )

            selected_name = table.item(
                item.row(), self.TABLE_WIDGET_COLUMN_INDEXES["Name"]
            ).text()

            for selected_addon in self.c.execute(
                f"SELECT InterfaceID, File, Name FROM {table.objectName()} WHERE rowid = ?",  # noqa: S608
                (selected_row,),
            ):
                selected_addons.append(
                    Addon(
                        interface_id=selected_addon[0],
                        file=str(self.data_folder / selected_addon[1]),
                        name=selected_addon[2],
                    )
                )
                details = details + selected_name + "\n"

        return selected_addons, details

    def uninstallPlugins(
        self, plugins: list[Addon], table: QtWidgets.QTableWidget
    ) -> None:
        for plugin in plugins:
            if plugin[1].endswith(".plugin"):
                plugin_files = [Path(plugin[1])]
            else:
                plugin_files = []
                if self.checkAddonForDependencies(plugin, table):
                    try:
                        doc = defusedxml.minidom.parse(plugin[1])
                    except xml.parsers.expat.ExpatError:
                        logger.warning(
                            f"`.plugincompendium` file has invalid XML: {plugin[1]}",
                            exc_info=True,
                        )
                        continue
                    nodes = doc.getElementsByTagName("Descriptors")[0].childNodes
                    for node in nodes:
                        if node.nodeName == "descriptor":
                            plugin_files.append(
                                self.data_folder_plugins
                                / (GetText(node.childNodes).replace("\\", "/"))
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

            plugin_folder: CaseInsensitiveAbsolutePath | None = None
            for plugin_file in plugin_files:
                if plugin_file.exists():
                    try:
                        doc = defusedxml.minidom.parse(str(plugin_file))
                    except xml.parsers.expat.ExpatError:
                        logger.warning(
                            f"`.plugin` file has invalid XML: {plugin_file}",
                            exc_info=True,
                        )
                    else:
                        nodes = doc.getElementsByTagName("Plugin")[0].childNodes
                        for node in nodes:
                            if node.nodeName == "Package":
                                plugin_folder = self.data_folder_plugins / (
                                    "/".join(GetText(node.childNodes).split(".")[:2])
                                )

                                # Removes plugin and all related files
                                if plugin_folder.exists():
                                    rmtree(plugin_folder)

                    plugin_file.unlink(missing_ok=True)
            Path(plugin.file).unlink(missing_ok=True)

            # Remove author folder if there are no other plugins in it
            if plugin_folder:
                author_dir = plugin_folder.parent
                if not list(author_dir.glob("*")):
                    author_dir.rmdir()

            logger.debug(f"{plugin} plugin uninstalled")

            self.setRemoteAddonToUninstalled(plugin, self.ui.tablePlugins)

        # Reloads plugins
        table.clearContents()
        self.getInstalledPlugins()

    def uninstallSkins(self, skins: list[Addon], table: QtWidgets.QTableWidget) -> None:
        for skin in skins:
            if skin[1].endswith(".skincompendium"):
                skin_path = Path(skin[1]).parent

                addon_info = self.parseCompendiumFile(Path(skin[1]), "SkinConfig")
                if addon_info is not None:
                    self.uninstallStartupScript(
                        script=addon_info.startup_script,
                        addon_data_folder=self.data_folder_skins,
                    )
            else:
                skin_path = Path(skin.file)
            rmtree(skin_path)

            logger.debug(f"{skin} skin uninstalled")

            self.setRemoteAddonToUninstalled(skin, self.ui.tableSkins)

        # Reloads skins
        table.clearContents()
        self.getInstalledSkins()

    def uninstallMusic(
        self, music_list: list[Addon], table: QtWidgets.QTableWidget
    ) -> None:
        for music in music_list:
            if music[1].endswith(".musiccompendium"):
                music_path = Path(music[1]).parent

                items_row = self.parseCompendiumFile(Path(music[1]), "MusicConfig")
                if items_row is not None:
                    script = items_row[8]
                    self.uninstallStartupScript(script, self.data_folder_music)
            else:
                music_path = Path(music[1])

            if music_path.suffix == ".abc":
                music_path.unlink()
            else:
                rmtree(music_path)

            logger.debug(f"{music} music uninstalled")

            self.setRemoteAddonToUninstalled(music, self.ui.tableMusic)

        # Reloads music
        table.clearContents()
        self.getInstalledMusic()

    def checkAddonForDependencies(
        self, addon: Addon, table: QtWidgets.QTableWidget
    ) -> bool:
        # Turbine Utilities is treated as having ID 0
        addon_ID = "0" if addon[0] == "1064" else addon[0]
        details = ""

        for dependent in self.c.execute(
            f'SELECT Name, Dependencies FROM {table.objectName()} WHERE Dependencies != ""'  # noqa: S608
        ):
            for dependency in dependent[1].split(","):
                if dependency == addon_ID:
                    details = details + dependent[0] + "\n"

        if details:
            num_depends = len(details.split("\n")) - 1
            plural = " addon depends" if num_depends == 1 else " addons deppend"
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

    def confirmationPrompt(self, text: str, details: str) -> bool:
        messageBox = QtWidgets.QMessageBox(self)
        messageBox.setWindowFlag(QtCore.Qt.WindowType.FramelessWindowHint)
        messageBox.setIcon(QtWidgets.QMessageBox.Icon.Question)
        messageBox.setStandardButtons(
            messageBox.StandardButton.Apply | messageBox.StandardButton.Cancel
        )

        messageBox.setInformativeText(text)
        messageBox.setDetailedText(details)

        # Checks if user accepts dialogue
        return messageBox.exec() == QtWidgets.QMessageBox.StandardButton.Apply

    def searchSearchBarContents(self) -> None:
        """
        Used to re-search users' search when new tabs are selected
        """
        user_search = self.ui.txtSearchBar.text()
        self.txtSearchBarTextChanged(user_search)

    def tabBarInstalledIndexChanged(self, index: int) -> None:
        if self.tab_names[index] == "Plugins":
            self.ui.stackedWidgetInstalled.setCurrentWidget(
                self.ui.pagePluginsInstalled
            )
            # Load in installed plugins on first switch to tab
            self.loadPluginsIfNotDone()
        elif self.tab_names[index] == "Skins":
            self.ui.stackedWidgetInstalled.setCurrentWidget(self.ui.pageSkinsInstalled)
            # Load in installed skins on first switch to tab
            self.loadSkinsIfNotDone()
        elif self.tab_names[index] == "Music":
            self.ui.stackedWidgetInstalled.setCurrentWidget(self.ui.pageMusicInstalled)
            # Load in installed music on first switch to tab
            self.loadMusicIfNotDone()

        self.searchSearchBarContents()

    def loadPluginsIfNotDone(self) -> None:
        if self.isTableEmpty(self.ui.tablePluginsInstalled):
            self.getInstalledPlugins()

    def loadSkinsIfNotDone(self) -> None:
        if self.isTableEmpty(self.ui.tableSkinsInstalled):
            self.getInstalledSkins()

    def loadMusicIfNotDone(self) -> None:
        if self.isTableEmpty(self.ui.tableMusicInstalled):
            self.getInstalledMusic()

    def tabBarRemoteIndexChanged(self, index: int) -> None:
        if self.tab_names[index] == "Plugins":
            self.ui.stackedWidgetRemote.setCurrentWidget(self.ui.pagePluginsRemote)
        if self.tab_names[index] == "Skins":
            self.ui.stackedWidgetRemote.setCurrentWidget(self.ui.pageSkinsRemote)
        elif self.tab_names[index] == "Music":
            self.ui.stackedWidgetRemote.setCurrentWidget(self.ui.pageMusicRemote)
        self.searchSearchBarContents()

    def update_btn_addons(self) -> None:
        index = self.ui.tabBarSource.currentIndex()
        if self.SOURCE_TAB_NAMES[index] == "Installed":
            self.ui.btnAddons.setIcon(qtawesome.icon("fa5s.minus"))
            self.ui.btnAddons.setToolTip("Remove addons")
        elif self.SOURCE_TAB_NAMES[index] == "Find More":
            self.ui.btnAddons.setIcon(qtawesome.icon("fa5s.plus"))
            self.ui.btnAddons.setToolTip("Install addons")

    def tabBarIndexChanged(self, index: int) -> None:
        self.update_btn_addons()
        if self.SOURCE_TAB_NAMES[index] == "Installed":
            self.ui.stackedWidgetSource.setCurrentWidget(self.ui.pageInstalled)
        elif self.SOURCE_TAB_NAMES[index] == "Find More":
            self.ui.stackedWidgetSource.setCurrentWidget(self.ui.pageRemote)

            # Handle the first time this tab is swtiched to.
            # Populate remote addons tables if not done already.
            if self.isTableEmpty(self.ui.tableSkins) and self.loadRemoteAddons():
                self.getOutOfDateAddons()
                # Make sure correct stacked widget page is selected
                self.tabBarRemoteIndexChanged(self.ui.tabBarRemote.currentIndex())

        self.searchSearchBarContents()

    def loadRemoteAddons(self) -> bool:
        if (
            self.config_manager.get_game_config(self.game_id).game_type
            == GameType.LOTRO
        ):
            # Only keep loading remote addons if the first load doesn't run
            # into issues
            if self.getRemoteAddons(self.PLUGINS_URL, self.ui.tablePlugins):
                self.getRemoteAddons(self.SKINS_URL, self.ui.tableSkins)
                self.getRemoteAddons(self.MUSIC_URL, self.ui.tableMusic)
                return True
        elif self.getRemoteAddons(self.SKINS_DDO_URL, self.ui.tableSkins):
            return True

        return False

    def unescape_lotrointerface_feed_unicode(self, escaped_string: str) -> str:
        """
        Convert feed escaped characters to Unicode characters. This shouold be used with
        strings that have alread had the XML unesaaped.

        Unicode characters in LotroInterface feeds are escaped with an ampersand followed
        by the Unicode character number. Ex. `&1088`.
        """
        return html.unescape(
            # Convert to HTML escape notation by adding `#`.
            re.sub(
                r"&(\d+);",
                lambda match: f"&#{match.group(1)};",  # type: ignore[str-bytes-safe]
                escaped_string,
            )
        )

    def getRemoteAddons(
        self, favorites_url: str, table: QtWidgets.QTableWidget
    ) -> bool:
        # Clears rows from db table
        self.c.execute(f"DELETE FROM {table.objectName()}")  # noqa: S608

        # Gets list of Interface IDs for installed addons
        installed_IDs = []
        for ID in self.c.execute(
            f"SELECT InterfaceID FROM {table.objectName() + 'Installed'}"  # noqa: S608
        ):
            if ID[0]:
                installed_IDs.append(ID[0])

        try:
            addons_file_response = get_httpx_client_sync(favorites_url).get(
                favorites_url
            )
            addons_file_response.raise_for_status()
        except HTTPError:
            logger.exception(
                "There was a network error. You may want to check your connection."
            )
            self.ui.tabBarSource.setCurrentIndex(0)
            return False

        try:
            doc = defusedxml.minidom.parseString(addons_file_response.text)
        except xml.parsers.expat.ExpatError:
            logger.exception(
                "Addons feed has invalid XML. Please report this error if it continues."
            )
            return False

        tags = doc.getElementsByTagName("Ui")
        for tag in tags:
            addon_info = AddonInfo()
            nodes = tag.childNodes
            for node in nodes:
                if node.nodeName == "UIName":
                    addon_info.name = GetText(node.childNodes)
                    addon_info.name = self.unescape_lotrointerface_feed_unicode(
                        addon_info.name
                    )
                    # Sanitize
                    addon_info.name = addon_info.name.replace("/", "-").replace(
                        "\\", "-"
                    )
                elif node.nodeName == "UIAuthorName":
                    addon_info.author = GetText(node.childNodes)
                    addon_info.author = self.unescape_lotrointerface_feed_unicode(
                        addon_info.author
                    )
                elif node.nodeName == "UICategory":
                    addon_info.category = GetText(node.childNodes)
                elif node.nodeName == "UID":
                    addon_info.interface_id = GetText(node.childNodes)
                elif node.nodeName == "UIVersion":
                    addon_info.version = GetText(node.childNodes)
                elif node.nodeName == "UIUpdated":
                    addon_info.latest_release = strftime(
                        "%Y-%m-%d", localtime(int(GetText(node.childNodes)))
                    )
                elif node.nodeName == "UIFileURL":
                    addon_info.file = GetText(node.childNodes)

            # Prepends name with (Installed) if already installed
            if addon_info.interface_id in installed_IDs:
                addon_info.name = f"(Installed) {addon_info.name}"

            self.addRowToDB(table, addon_info)

        # Populate user visible table. This should not reload the current
        # search.
        self.searchDB(table, "")

        return True

    # Downloads file from url to path and shows progress with
    # self.handleDownloadProgress
    def downloader(self, url: str, path: Path) -> bool:
        if url.lower().startswith("http"):
            try:
                self.ui.progressBar.setValue(0)
                self.ui.progressBar.setVisible(True)
                ssl._create_default_https_context = partial(
                    ssl.create_default_context, cafile=certifi.where()
                )
                urllib.request.urlretrieve(  # noqa: S310
                    url, path, self.handleDownloadProgress
                )
            except (urllib.error.URLError, urllib.error.HTTPError):
                logger.exception(
                    "There was a network error. You may want to check your connection."
                )
                self.ui.progressBar.setVisible(False)
                return False
        else:
            raise ValueError from None
        self.ui.progressBar.setVisible(False)
        return True

    def handleDownloadProgress(self, index: int, frame: int, size: int) -> None:
        # Updates progress bar with download progress
        percent = 100 * index * frame // size
        self.ui.progressBar.setValue(percent)

    @override
    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        self.closeDB()
        super().closeEvent(event)

    def contextMenuRequested(
        self, cursor_position: QtCore.QPoint, table: QtWidgets.QTableWidget
    ) -> None:
        self.context_menu_selected_table = table
        selected_item: QtWidgets.QTableWidgetItem | None = (
            self.context_menu_selected_table.itemAt(cursor_position)
        )
        if not selected_item:
            self.contextMenu = None
            return
        self.context_menu_selected_row = selected_item.row()
        menu = QtWidgets.QMenu()

        # If addon has online page
        self.context_menu_selected_interface_ID = self.getTableRowInterfaceID(
            table=self.context_menu_selected_table,
            row=self.context_menu_selected_row,
        )
        if self.context_menu_selected_interface_ID:
            menu.addAction(self.ui.actionShowOnLotrointerface)

        # If addon is installed
        if (
            self.context_menu_selected_table.objectName().endswith("Installed")
            or QtCore.Qt.ItemFlag.ItemIsEnabled not in selected_item.flags()
        ):
            menu.addAction(self.ui.actionUninstallAddon)
            menu.addAction(self.ui.actionShowAddonInFileManager)
        else:
            menu.addAction(self.ui.actionInstallAddon)

        # If addon has a new version available
        version_item = self.context_menu_selected_table.item(
            self.context_menu_selected_row, self.TABLE_WIDGET_COLUMN_INDEXES["Version"]
        )
        version_color = version_item.foreground().color()
        if version_color in [QtGui.QColor("crimson"), QtGui.QColor("green")]:
            menu.addAction(self.ui.actionUpdateAddon)

        # If addon has a statup script
        if self.context_menu_selected_interface_ID:
            relative_script_path = self.getRelativeStartupScriptFromInterfaceID(
                table=self.context_menu_selected_table,
                interface_ID=self.context_menu_selected_interface_ID,
            )
            if relative_script_path:
                # If startup script is enabled
                relative_script_paths = [
                    script.relative_path
                    for script in self.config_manager.read_game_config_file(
                        self.game_id
                    ).addons.enabled_startup_scripts
                ]
                if relative_script_path in relative_script_paths:
                    menu.addAction(self.ui.actionDisableStartupScript)
                else:
                    menu.addAction(self.ui.actionEnableStartupScript)

        # It is not a local variable, because of garbage collection
        self.contextMenu = None if menu.isEmpty() else menu
        if self.contextMenu:
            self.contextMenu.popup(table.mapToGlobal(cursor_position))

    def getTableRowInterfaceID(
        self, table: QtWidgets.QTableWidget, row: int
    ) -> str | None:
        addon_db_id = table.item(row, self.TABLE_WIDGET_COLUMN_INDEXES["ID"]).text()

        interface_ID: str
        for interface_ID in self.c.execute(
            f"SELECT InterfaceID FROM {table.objectName()} WHERE rowid = ?",  # noqa: S608
            (addon_db_id,),
        ):
            if interface_ID[0]:
                return interface_ID[0]
            else:
                return None
        return None

    def actionShowOnLotrointerfaceSelected(self) -> None:
        table = self.context_menu_selected_table
        row = self.context_menu_selected_row
        if addon_info := self.getAddonObjectFromRow(table, row):
            interface_ID = addon_info[0]
        else:
            return

        if url := self.getAddonUrlFromInterfaceID(interface_ID, table):
            QtGui.QDesktopServices.openUrl(url)

    def getAddonUrlFromInterfaceID(
        self,
        interface_ID: str,
        table: QtWidgets.QTableWidget,
        download_url: bool = False,
    ) -> str:
        """Returns info URL for addon or download URL if download_url=True"""
        # URL is only in remote version of table
        table = self.getRemoteOrLocalTableFromOne(table, remote=True)

        addon_url: tuple[str]
        for addon_url in self.c.execute(
            f"SELECT File FROM {table.objectName()} WHERE InterfaceID = ?",  # noqa: S608
            (interface_ID,),
        ):
            if addon_url[0]:
                return (
                    addon_url[0]
                    if download_url
                    else self.getInterfaceInfoUrl(addon_url[0])
                )
        raise ValueError("No addon URL founnd for interface ID", interface_ID)

    def getAddonFileFromInterfaceID(
        self, interface_ID: str, table: QtWidgets.QTableWidget
    ) -> str | None:
        """Returns file location of addon"""
        # File is only in "Installed" version of table. The "File" field
        # has the download url in the remote tables.
        table = self.getRemoteOrLocalTableFromOne(table, remote=False)

        file: tuple[str]
        for file in self.c.execute(
            f"SELECT File FROM {table.objectName()} WHERE InterfaceID = ?",  # noqa: S608
            (interface_ID,),
        ):
            if file[0]:
                return str(self.data_folder / file[0])
        raise ValueError("No addon File founnd for interface ID", interface_ID)

    def showSelectedOnLotrointerface(self) -> None:
        table = self.getCurrentTable()
        selected_addons = self.getSelectedAddons(table)

        for addon in selected_addons[0]:
            info_url = self.getAddonUrlFromInterfaceID(
                addon[0], table, download_url=False
            )
            QtGui.QDesktopServices.openUrl(info_url)

    def actionInstallAddonSelected(self) -> None:
        """
        Installs addon selected by context menu. This function
        should only be called while in one of the remote/find more
        tabs of the UI.
        """
        table = self.context_menu_selected_table
        row = self.context_menu_selected_row
        addon = self.getAddonObjectFromRow(table, row)
        if not addon:
            return

        self.installRemoteAddon(addon[1], addon[2], addon[0])
        self.setRemoteAddonToInstalled(addon, table)

        self.resetRemoteAddonsTables()
        self.searchSearchBarContents()

    def actionUninstallAddonSelected(self) -> None:
        table = self.context_menu_selected_table
        row = self.context_menu_selected_row
        addon = self.getAddonObjectFromRow(table, row, remote=False)
        if not addon:
            return

        if self.confirmationPrompt(
            "Are you sure you want to uninstall this addon?", addon[2]
        ):
            uninstall_function = self.getUninstallFunctionFromTable(table)

            table_installed = self.getRemoteOrLocalTableFromOne(table, remote=False)
            uninstall_function([addon], table_installed)

            self.resetRemoteAddonsTables()
            self.searchSearchBarContents()

    def getAddonObjectFromRow(
        self, table: QtWidgets.QTableWidget, row: int, remote: bool = True
    ) -> Addon | None:
        """
        Gives list of information for addon. The information is:
        [Interface ID, URL/File (depending on if remote = True or False), Name]
        """
        interface_ID = self.getTableRowInterfaceID(table, row)
        if not interface_ID:
            return None

        file = None
        if remote:
            table_remote = self.getRemoteOrLocalTableFromOne(table, remote=True)
            file = self.getAddonUrlFromInterfaceID(
                interface_ID, table_remote, download_url=True
            )
        else:
            table_installed = self.getRemoteOrLocalTableFromOne(table, remote=False)

            if table.objectName().endswith("Installed"):
                self.reloadSearch(table_installed)

                item: tuple[str]
                for item in self.c.execute(
                    f"SELECT File FROM {table_installed.objectName()} WHERE rowid=?",  # noqa: S608
                    (
                        table_installed.item(
                            row, self.TABLE_WIDGET_COLUMN_INDEXES["ID"]
                        ).text(),
                    ),
                ):
                    file = str(self.data_folder / item[0])
            else:
                file = self.getAddonFileFromInterfaceID(interface_ID, table_installed)

        if not file:
            return None

        return Addon(
            interface_id=interface_ID,
            file=file,
            name=table.item(row, self.TABLE_WIDGET_COLUMN_INDEXES["Name"]).text(),
        )

    def getRemoteOrLocalTableFromOne(
        self, input_table: QtWidgets.QTableWidget, remote: bool = False
    ) -> QtWidgets.QTableWidget:
        if input_table in self.ui_tables_installed:
            table_index = self.ui_tables_installed.index(input_table)
        elif input_table in self.ui_tables_remote:
            table_index = self.ui_tables_remote.index(input_table)
        else:
            raise ValueError("Table isn't local or remote", input_table)

        if remote:
            return self.ui_tables_remote[table_index]
        else:
            return self.ui_tables_installed[table_index]

    def show_addon_in_file_manager(self, addon: Addon) -> None:
        if Path(addon[1]).is_file():
            addon_folder = Path(addon[1]).parent
        else:
            addon_folder = Path(addon[1])
        QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(str(addon_folder)))

    def actionShowAddonInFileManagerSelected(self) -> None:
        table = self.context_menu_selected_table
        row = self.context_menu_selected_row
        addon = self.getAddonObjectFromRow(table, row, remote=False)
        if not addon:
            return
        self.show_addon_in_file_manager(addon)

    def show_selected_addons_in_file_manager(self) -> None:
        table = self.getCurrentTable()
        selected_addons = self.getSelectedAddons(table)

        for addon in selected_addons[0]:
            self.show_addon_in_file_manager(addon)

    def actionShowPluginsFolderSelected(self) -> None:
        folder = self.data_folder_plugins
        QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(str(folder)))

    def actionShowSkinsFolderSelected(self) -> None:
        folder = self.data_folder_skins
        QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(str(folder)))

    def actionShowMusicFolderSelected(self) -> None:
        folder = self.data_folder_music
        QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(str(folder)))

    def update_addons_button_actions(self) -> None:
        """Only show relevant actions"""
        source_tab = self.SOURCE_TAB_NAMES[self.ui.tabBarSource.currentIndex()]
        if source_tab == "Installed":
            addons_tab = self.tab_names[self.ui.tabBarInstalled.currentIndex()]
        elif source_tab == "Find More":
            addons_tab = self.tab_names[self.ui.tabBarRemote.currentIndex()]
        else:
            assert_never(source_tab)
        if addons_tab == "Plugins":
            self.ui.actionShowPluginsFolderInFileManager.setVisible(True)
            self.ui.actionShowSkinsFolderInFileManager.setVisible(False)
            self.ui.actionShowMusicFolderInFileManager.setVisible(False)
        elif addons_tab == "Skins":
            self.ui.actionShowPluginsFolderInFileManager.setVisible(False)
            self.ui.actionShowSkinsFolderInFileManager.setVisible(True)
            self.ui.actionShowMusicFolderInFileManager.setVisible(False)
        elif addons_tab == "Music":
            self.ui.actionShowPluginsFolderInFileManager.setVisible(False)
            self.ui.actionShowSkinsFolderInFileManager.setVisible(False)
            self.ui.actionShowMusicFolderInFileManager.setVisible(True)
        else:
            assert_never(addons_tab)

        # These actions can only be used when at least one addon is selected
        if self.getCurrentTable().selectedItems():
            self.ui.actionUpdateSelectedAddons.setVisible(True)
            self.ui.actionShowSelectedOnLotrointerface.setVisible(True)
            self.ui.actionShowSelectedAddonsInFileManager.setVisible(True)
        else:
            self.ui.actionUpdateSelectedAddons.setVisible(False)
            self.ui.actionShowSelectedOnLotrointerface.setVisible(False)
            self.ui.actionShowSelectedAddonsInFileManager.setVisible(False)

    def checkForUpdates(self) -> None:
        if self.loadRemoteAddons():
            self.getOutOfDateAddons()
            self.searchSearchBarContents()

    def getOutOfDateAddons(self) -> None:
        """
        Marks addons as out of date in database with '(Outdated) '
        in installed table and '(Updated) ' in remote table. These
        are prepended to the Version column.
        """
        if not self.loadRemoteDataIfNotDone():
            return

        game_config = self.config_manager.get_game_config(self.game_id)
        if game_config.game_type != GameType.DDO:
            self.loadSkinsIfNotDone()
            self.loadMusicIfNotDone()

        if game_config.game_type == GameType.LOTRO:
            tables = self.TABLE_LIST[:3]
        else:
            tables = ("tableSkinsInstalled",)

        for db_table in tables:
            table_installed: QtWidgets.QTableWidget = getattr(self.ui, db_table)
            table_remote = self.getRemoteOrLocalTableFromOne(
                table_installed, remote=True
            )

            addons_info_remote = {
                addon[1]: (addon[0], addon[2])
                for addon in self.c.execute(
                    f"SELECT Version, InterfaceID, rowid FROM {table_remote.objectName()} WHERE"  # noqa: S608
                    f" Name LIKE '(Installed) %'"
                )
            }

            for addon in self.c.execute(
                f"SELECT Version, InterfaceID, rowid FROM {table_installed.objectName()} WHERE"  # noqa: S608
                f" InterfaceID != ''"
            ):
                # Will raise KeyError if addon has Interface ID that isn't in
                # remote table.
                try:
                    remote_addon_info = addons_info_remote[addon[1]]
                except KeyError:
                    continue

                latest_version = remote_addon_info[0]
                if addon[0] != latest_version:
                    rowid_remote = remote_addon_info[1]
                    self.markAddonForUpdating(
                        rowid_local=addon[2],
                        rowid_remote=rowid_remote,
                        table_installed=table_installed,
                    )

    def markAddonForUpdating(
        self,
        rowid_local: str | int,
        rowid_remote: str | int,
        table_installed: QtWidgets.QTableWidget,
    ) -> None:
        """
        Marks addon as having having updates
        available in installed and remote tables
        """
        table_remote = self.getRemoteOrLocalTableFromOne(table_installed, remote=True)

        self.c.execute(
            (
                f"UPDATE {table_installed.objectName()} SET Version=('(Outdated) ' || Version) WHERE rowid=?"  # noqa: S608
            ),
            (str(rowid_local),),
        )
        self.c.execute(
            (
                f"UPDATE {table_remote.objectName()} SET Version=('(Updated) ' || Version) WHERE rowid=?"  # noqa: S608
            ),
            (str(rowid_remote),),
        )

    def updateAll(self) -> None:
        if not self.loadRemoteDataIfNotDone():
            return None

        if (
            self.config_manager.get_game_config(self.game_id).game_type
            == GameType.LOTRO
        ):
            tables = self.TABLE_LIST[:3]
        else:
            tables = ("tableSkinsInstalled",)

        for db_table in tables:
            table = getattr(self.ui, db_table)
            for addon in self.c.execute(
                f"SELECT InterfaceID, File, Name FROM {table.objectName()} WHERE Version LIKE '(Outdated) %'"  # noqa: S608
            ):
                self.updateAddon(
                    Addon(
                        interface_id=addon[0],
                        file=str(self.data_folder / addon[1]),
                        name=addon[2],
                    ),
                    table,
                )

        self.resetRemoteAddonsTables()
        self.searchSearchBarContents()

    def updateAddon(self, addon: Addon, table: QtWidgets.QTableWidget) -> None:
        uninstall_function = self.getUninstallFunctionFromTable(table)
        table_installed = self.getRemoteOrLocalTableFromOne(table, remote=False)
        table_remote = self.getRemoteOrLocalTableFromOne(table, remote=True)

        uninstall_function([addon], table_installed)

        url: str | None = None
        for entry in self.c.execute(
            f"SELECT File FROM {table_remote.objectName()} WHERE InterfaceID = ?",  # noqa: S608
            (addon[0],),
        ):
            url = entry[0]
        if url is None:
            raise ValueError("Addon not found in DB", addon)
        self.installRemoteAddon(url, addon[2], addon[0])
        self.setRemoteAddonToInstalled(addon, table_remote)

    def actionUpdateAddonSelected(self) -> None:
        if not self.loadRemoteDataIfNotDone():
            return

        table = self.context_menu_selected_table
        row = self.context_menu_selected_row
        addon = self.getAddonObjectFromRow(table, row, remote=False)

        if not addon:
            return

        self.updateAddon(addon, table)

        self.resetRemoteAddonsTables()
        self.searchSearchBarContents()

    def updateSelectedAddons(self) -> None:
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

    def checkIfAddonHasUpdate(
        self, addon: Addon, table: QtWidgets.QTableWidget
    ) -> bool | None:
        for entry in self.c.execute(
            f"SELECT Version FROM {table.objectName()} WHERE InterfaceID = ?",  # noqa: S608
            (addon[0],),
        ):
            version: str = entry[0]
            return bool(
                version.startswith("(Outdated) ") or version.startswith("(Updated) ")
            )
        return None

    def loadRemoteDataIfNotDone(self) -> bool:
        """
        Loads remote addons and checks if addons have updates if not done yet
        """
        # If remote addons haven't been loaded then out of date addons haven't
        # been found.
        if not self.loadRemoteAddons():
            return False
        if self.isTableEmpty(self.ui.tableSkins):
            self.getOutOfDateAddons()
        return True

    def actionEnableStartupScriptSelected(self) -> None:
        if not self.context_menu_selected_interface_ID:
            return
        script = self.getRelativeStartupScriptFromInterfaceID(
            self.context_menu_selected_table, self.context_menu_selected_interface_ID
        )
        if not script:
            return
        full_script_path = self.data_folder / script
        if full_script_path.exists():
            game_config = self.config_manager.read_game_config_file(self.game_id)
            updated_addons_section = attrs.evolve(
                game_config.addons,
                enabled_startup_scripts=(
                    *game_config.addons.enabled_startup_scripts,
                    StartupScript(script),
                ),
            )
            self.config_manager.update_game_config_file(
                self.game_id,
                attrs.evolve(game_config, addons=updated_addons_section),
            )
        else:
            logger.error(
                f"'{full_script_path}' startup script does not exist, so it could not be enabled."
            )

    def actionDisableStartupScriptSelected(self) -> None:
        if self.context_menu_selected_interface_ID:
            relative_script_path = self.getRelativeStartupScriptFromInterfaceID(
                self.context_menu_selected_table,
                self.context_menu_selected_interface_ID,
            )
            game_config = self.config_manager.read_game_config_file(self.game_id)
            updated_addons_section = attrs.evolve(
                game_config.addons,
                enabled_startup_scripts=tuple(
                    script
                    for script in game_config.addons.enabled_startup_scripts
                    if script.relative_path != relative_script_path
                ),
            )
            self.config_manager.update_game_config_file(
                game_id=self.game_id,
                config=attrs.evolve(game_config, addons=updated_addons_section),
            )

    def getRelativeStartupScriptFromInterfaceID(
        self, table: QtWidgets.QTableWidget, interface_ID: str
    ) -> Path | None:
        """Returns path of startup script relative to game documents settings directory"""
        table_local = self.getRemoteOrLocalTableFromOne(table, remote=False)
        entry: tuple[str]
        for entry in self.c.execute(
            f"SELECT StartupScript FROM {table_local.objectName()} WHERE InterfaceID = ?",  # noqa: S608
            (interface_ID,),
        ):
            if entry[0]:
                script = entry[0].replace("\\", "/")
                addon_data_folder_relative = self.getAddonTypeDataFolderFromTable(
                    table_local
                ).relative_to(self.data_folder)
                return addon_data_folder_relative / script
        return None

    def getAddonTypeDataFolderFromTable(
        self, table: QtWidgets.QTableWidget
    ) -> CaseInsensitiveAbsolutePath:
        table_name = table.objectName()
        if "Plugins" in table_name:
            return self.data_folder_plugins
        elif "Skins" in table_name:
            return self.data_folder_skins
        elif "Music" in table_name:
            return self.data_folder_music
        else:
            raise ValueError("Addons table not recognized")

    def handleStartupScriptActivationPrompt(
        self, table: QtWidgets.QTableWidget, interface_ID: str
    ) -> None:
        """Ask user if they want to enable an addon's startup script if present"""
        if script := self.getRelativeStartupScriptFromInterfaceID(table, interface_ID):
            addon_name: str | None = None
            for name in self.c.execute(
                f"SELECT Name from {table.objectName()} WHERE InterfaceID = ?",  # noqa: S608
                (interface_ID,),
            ):
                addon_name = name[0]
            if addon_name is None:
                raise ValueError("No addon name found for Interface ID", interface_ID)
            script_contents = (self.data_folder / script).open().read()

            if self.confirmationPrompt(
                f"{addon_name} is requesting to run a Python script at every game launch."
                " It is highly recommended to review the script's code in the details"
                " box below to make sure it's safe.",
                script_contents,
            ):
                game_config = self.config_manager.read_game_config_file(self.game_id)
                updated_addons_section = attrs.evolve(
                    game_config.addons,
                    enabled_startup_scripts=(
                        *game_config.addons.enabled_startup_scripts,
                        StartupScript(script),
                    ),
                )
                self.config_manager.update_game_config_file(
                    self.game_id,
                    attrs.evolve(game_config, addons=updated_addons_section),
                )

    def uninstallStartupScript(
        self, script: str, addon_data_folder: CaseInsensitiveAbsolutePath
    ) -> None:
        if script:
            script_path = addon_data_folder / (script.replace("\\", "/"))

            relative_to_game_documents_dir_script = script_path.relative_to(
                self.data_folder
            )

            game_config = self.config_manager.read_game_config_file(self.game_id)
            updated_addons_section = attrs.evolve(
                game_config.addons,
                enabled_startup_scripts=tuple(
                    script
                    for script in game_config.addons.enabled_startup_scripts
                    if script.relative_path != relative_to_game_documents_dir_script
                ),
            )
            self.config_manager.update_game_config_file(
                game_id=self.game_id,
                config=attrs.evolve(game_config, addons=updated_addons_section),
            )
            script_path.unlink(missing_ok=True)
