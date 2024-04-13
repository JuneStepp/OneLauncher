from typing import Self
from xml.etree.ElementTree import Element

import vkbeautify
from defusedxml import ElementTree

from .utilities import (
    AppSettingsParseError,
    parse_app_settings_config,
    verify_app_settings_config,
)


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
            assert type(root) is Element
        else:
            root = Element("configuration")
            root.append(Element("appSettings"))

        app_settings = root.find("./appSettings")
        assert type(app_settings) is Element
        self._edit_config_xml_app_setting(
            app_settings, "Launcher.DataCenterService.GLS", self.gls_datacenter_service
        )
        self._edit_config_xml_app_setting(
            app_settings, "DataCenter.GameName", self.datacenter_game_name
        )
        self._edit_config_xml_app_setting(
            app_settings, "Product.DocumentFolder", self.documents_config_dir_name
        )

        return vkbeautify.xml(
            ElementTree.tostring(root, "utf-8", xml_declaration=True).decode()
        )
