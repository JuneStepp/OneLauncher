from typing import Self
from xml.etree.ElementTree import Element

import vkbeautify
from defusedxml import ElementTree

from .game import Game, GameType
from .network.game_launcher_config import GameLauncherConfig
from .utilities import (AppSettingsParseError,
                                   CaseInsensitiveAbsolutePath,
                                   parse_app_settings_config,
                                   verify_app_settings_config)


class GameLauncherLocalConfigParseError(KeyError):
    """Config doesn't match expected .launcherconfig format"""


class GameLauncherLocalConfig():
    def __init__(self,
                 gls_datacenter_service: str,
                 datacenter_game_name: str,
                 documents_config_dir_name: str):
        self.gls_datacenter_service = gls_datacenter_service
        self.datacenter_game_name = datacenter_game_name
        self.documents_config_dir_name = documents_config_dir_name

    @classmethod
    def from_config_xml(cls, config_xml: str) -> Self:
        """Construct `GameLauncherLocalConfig` from game launcher config text.

        Args:
            config_xml (str): Contents of a .launcherconfig file

        Raises:
            GameLauncherLocalConfigParseError: config_xml doesn't match expected
            .launcherconfig format.
        """
        config_dict = parse_app_settings_config(config_xml)
        try:
            return cls(config_dict["Launcher.DataCenterService.GLS"],
                       config_dict["DataCenter.GameName"],
                       config_dict["Product.DocumentFolder"])
        except AppSettingsParseError as e:
            raise GameLauncherLocalConfigParseError(
                "Config XML doesn't follow the appSettings format") from e
        except KeyError as e:
            raise GameLauncherLocalConfigParseError(
                "Config doesn't include a required value") from e

    def _edit_config_xml_app_setting(
            self,
            app_settings_element: Element,
            key: str,
            val: str) -> None:
        """Edit a setting in an appSettings config xml.
           Setting will be added if it doesn't already exist.

        Args:
            app_settings_element (Element): appSettings xml element
            key (str): value for 'key' attribute
            val (str): value for 'value' attribute
        """
        existing_element = app_settings_element.find(f"./add[@key='{key}']")
        if existing_element is not None:
            existing_element.attrib["value"] = val
        else:
            element = Element("add", {"key": key, "value": val})
            app_settings_element.append(element)

    def to_config_xml(self, existing_xml: str | None = None) -> str:
        """Serialize into valid .launcherconfig text.

        Args:
            existing_xml (str | None, optional): Existing .launcherconfig text
                to edit. This preserves extra information in the file that
                OneLauncher doesn't use.

        Raises:
            AppSettingsParseError: `existing_xml` doesn't follow the
                                    appSettings format.
        """
        if existing_xml:
            verify_app_settings_config(existing_xml)
            root = ElementTree.fromstring(existing_xml)
            assert type(root) is Element
        else:
            root = Element("configuration")
            root.append(Element("appSettings"))

        app_settings = root.find("./appSettings")
        assert type(app_settings) is Element
        self._edit_config_xml_app_setting(
            app_settings,
            "Launcher.DataCenterService.GLS",
            self.gls_datacenter_service)
        self._edit_config_xml_app_setting(
            app_settings,
            "DataCenter.GameName",
            self.datacenter_game_name)
        self._edit_config_xml_app_setting(
            app_settings,
            "Product.DocumentFolder",
            self.documents_config_dir_name)

        return vkbeautify.xml(
            ElementTree.tostring(
                root,
                "utf-8",
                xml_declaration=True).decode())


def get_launcher_config_paths(
        search_dir: CaseInsensitiveAbsolutePath,
        game_type: GameType | None = None) -> tuple[CaseInsensitiveAbsolutePath, ...]:
    """Return all launcher config files from search_dir sorted by relevance.
       File names matching a different game type from `game_type` won't be
       returned.
    """
    config_files = list(search_dir.glob("*.launcherconfig"))

    if game_type is not None:
        # Remove launcher config files that are for other game types
        other_game_types = set(GameType) - {game_type}
        for file in config_files:
            for other_game_type in other_game_types:
                if file.name.lower(
                ) == f"{other_game_type.lower()}.launcherconfig":
                    config_files.remove(file)

    # Add legacy launcher config file to `config_files`
    legacy_path = search_dir / "TurbineLauncher.exe.config"
    if legacy_path.exists():
        config_files.append(legacy_path)

    def config_files_sorting_key(file: CaseInsensitiveAbsolutePath) -> int:
        if game_type is not None and (
                file.name.lower() == f"{game_type.lower()}.launcherconfig"):
            return 0
        elif file.suffix.lower() == ".launcherconfig":
            return 1
        elif file.name.lower() == "TurbineLauncher.exe.config".lower():
            return 2
        else:
            return 3

    return tuple(sorted(config_files, key=config_files_sorting_key))


def _get_launcher_path_based_on_client_filename(
        game: Game) -> CaseInsensitiveAbsolutePath | None:
    game_launcher_config = GameLauncherConfig.from_game(game)
    if game_launcher_config is None:
        return None

    game_client_filename = game_launcher_config.get_client_filename()[0]
    lowercase_launcher_filename = game_client_filename.lower().split('client')[
        0] + "launcher.exe"
    launcher_path = game.game_directory / lowercase_launcher_filename
    return launcher_path if launcher_path.exists() else None


def _get_launcher_path_with_hardcoded_filenames(
        game: Game) -> CaseInsensitiveAbsolutePath | None:
    match game.game_type:
        case GameType.LOTRO:
            filenames = {"LotroLauncher.exe"}
        case GameType.DDO:
            filenames = {"DNDLauncher.exe"}
        case _:
            raise ValueError("Unexpected game type")

    for filename in filenames:
        launcher_path = game.game_directory / filename
        if launcher_path.exists():
            return launcher_path

    # No hard-coded launcher filenames existed
    return None


def _get_launcher_path_with_search(
        game_directory: CaseInsensitiveAbsolutePath) -> CaseInsensitiveAbsolutePath | None:
    return next((file for file in game_directory.iterdir()
                if file.name.lower().endswith("launcher.exe")), None)


def _get_launcher_path_from_config(
        game: Game) -> CaseInsensitiveAbsolutePath | None:
    if game.standard_game_launcher_filename:
        launcher_path = game.game_directory / game.standard_game_launcher_filename
        if launcher_path.exists():
            return launcher_path

    return None


def get_standard_game_launcher_path(
        game: Game) -> CaseInsensitiveAbsolutePath | None:
    launcher_path = _get_launcher_path_from_config(game)
    if launcher_path is not None:
        return launcher_path

    launcher_path = _get_launcher_path_based_on_client_filename(game)
    if launcher_path is not None:
        return launcher_path

    launcher_path = _get_launcher_path_with_hardcoded_filenames(game)
    if launcher_path is not None:
        return launcher_path

    launcher_path = _get_launcher_path_with_search(game.game_directory)
    return launcher_path
