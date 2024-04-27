from functools import cache
from typing import Self, cast
from xml.etree.ElementTree import Element

import vkbeautify
from defusedxml import ElementTree

from .game_config import GameType
from .utilities import (
    AppSettingsParseError,
    CaseInsensitiveAbsolutePath,
    parse_app_settings_config,
    verify_app_settings_config,
)


def get_launcher_config_paths(
    search_dir: CaseInsensitiveAbsolutePath, game_type: GameType | None = None
) -> tuple[CaseInsensitiveAbsolutePath, ...]:
    """
    Return all launcher config files from search_dir sorted by relevance.
    File names matching a different game type from `game_type` won't be
    returned.
    """
    config_files = list(search_dir.glob("*.launcherconfig"))

    if game_type is not None:
        # Remove launcher config files that are for other game types
        other_game_types = set(GameType) - {game_type}
        for file in config_files:
            for other_game_type in other_game_types:
                if file.name.lower() == f"{other_game_type.lower()}.launcherconfig":
                    config_files.remove(file)

    # Add legacy launcher config files to `config_files`
    legacy_config_names = ["TurbineLauncher.exe.config"]
    if game_type == GameType.DDO or game_type is None:
        legacy_config_names.append("DNDLauncher.exe.config")
    for config_name in legacy_config_names:
        legacy_path = search_dir / config_name
        if legacy_path.exists():
            config_files.append(legacy_path)

    def config_files_sorting_key(file: CaseInsensitiveAbsolutePath) -> int:
        if game_type is not None and (
            file.name.lower() == f"{game_type.lower()}.launcherconfig"
        ):
            return 0
        elif file.suffix.lower() == ".launcherconfig":
            return 1
        elif file.name.lower() == "TurbineLauncher.exe.config".lower():
            return 2
        else:
            return 3

    return tuple(sorted(config_files, key=config_files_sorting_key))


class GameLauncherLocalConfigParseError(KeyError):
    """Config doesn't match expected .launcherconfig format"""


class GameLauncherLocalConfig:
    def __init__(
        self,
        gls_datacenter_service: str,
        datacenter_game_name: str,
        documents_config_dir_name: str,
    ):
        self.gls_datacenter_service = gls_datacenter_service
        self.datacenter_game_name = datacenter_game_name
        self.documents_config_dir_name = documents_config_dir_name

    @classmethod
    def from_config_xml(cls: type[Self], config_xml: str) -> Self:
        """Construct `GameLauncherLocalConfig` from game launcher config text.

        Args:
            config_xml (str): Contents of a .launcherconfig file

        Raises:
            GameLauncherLocalConfigParseError: config_xml doesn't match expected
            .launcherconfig format.
        """
        config_dict = parse_app_settings_config(config_xml)
        try:
            return cls(
                config_dict["Launcher.DataCenterService.GLS"],
                config_dict["DataCenter.GameName"],
                config_dict["Product.DocumentFolder"],
            )
        except AppSettingsParseError as e:
            raise GameLauncherLocalConfigParseError(
                "Config XML doesn't follow the appSettings format"
            ) from e
        except KeyError as e:
            raise GameLauncherLocalConfigParseError(
                "Config doesn't include a required value"
            ) from e

    @classmethod
    @cache
    def from_game_dir(
        cls: type[Self], *, game_directory: CaseInsensitiveAbsolutePath, game_type: GameType
    ) -> Self | None:
        """
        Simplified shortcut for getting GameLauncherLocalConfig object.
        Will return None if any exceptions are raised.
        """
        launcher_config_paths = get_launcher_config_paths(
            search_dir=game_directory, game_type=game_type
        )
        if not launcher_config_paths:
            return None
        try:
            return cls.from_config_xml(launcher_config_paths[0].read_text())
        except GameLauncherLocalConfigParseError:
            return None

    def _edit_config_xml_app_setting(
        self, app_settings_element: Element, key: str, val: str
    ) -> None:
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
            root = cast(Element, root)
        else:
            root = Element("configuration")
            root.append(Element("appSettings"))

        app_settings = root.find("./appSettings")
        app_settings = cast(Element, app_settings)
        self._edit_config_xml_app_setting(
            app_settings, "Launcher.DataCenterService.GLS", self.gls_datacenter_service
        )
        self._edit_config_xml_app_setting(
            app_settings, "DataCenter.GameName", self.datacenter_game_name
        )
        self._edit_config_xml_app_setting(
            app_settings, "Product.DocumentFolder", self.documents_config_dir_name
        )

        GameLauncherLocalConfig.from_game_dir.cache_clear()
        return vkbeautify.xml(
            ElementTree.tostring(root, "utf-8", xml_declaration=True).decode()
        )
