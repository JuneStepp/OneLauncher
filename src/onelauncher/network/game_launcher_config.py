import logging
from typing import Self

from asyncache import cached
from cachetools import TTLCache
from httpx import HTTPError

from ..game_config import ClientType, GameConfig
from ..official_clients import (
    DDO_PREVIEW_BROKEN_NEWS_URL_TEMPLATE,
    DDO_PREVIEW_NEWS_URL_TEMPLATE,
)
from ..resources import OneLauncherLocale
from ..utilities import AppSettingsParseError, parse_app_settings_config
from .game_services_info import GameServicesInfo
from .httpx_client import get_httpx_client

logger = logging.getLogger(__name__)


class GameLauncherConfigParseError(KeyError):
    """Config doesn't match expected game launcher config format"""


class NoGameClientFilenameError(Exception):
    """No game client filenames for any supported client type provided"""


class GameLauncherConfig:
    def __init__(
        self,
        client_win64_filename: str | None,
        client_win32_filename: str | None,
        client_win32_legacy_filename: str | None,
        client_launch_args_template: str,
        client_crash_server_arg: str | None,
        client_auth_server_arg: str | None,
        client_gls_ticket_lifetime_arg: str | None,
        client_default_upload_throttle_mbps_arg: str | None,
        client_bug_url_arg: str | None,
        client_support_url_arg: str | None,
        client_support_service_url_arg: str | None,
        high_res_patch_arg: str | None,
        patching_product_code: str,
        login_queue_url: str,
        login_queue_params_template: str,
        newsfeed_url_template: str,
    ) -> None:
        """
        Raises:
            NoGameClientFilenameError: All game client filenames are None.

        """
        self._client_win64_filename = client_win64_filename
        self._client_win32_filename = client_win32_filename
        self._client_win32_legacy_filename = client_win32_legacy_filename
        self._client_launch_args_template = client_launch_args_template
        self._client_crash_server_arg = client_crash_server_arg
        self._client_auth_server_arg = client_auth_server_arg
        self._client_gls_ticket_lifetime_arg = client_gls_ticket_lifetime_arg
        self._client_default_upload_throttle_mbps_arg = (
            client_default_upload_throttle_mbps_arg
        )
        self._client_bug_url_arg = client_bug_url_arg
        self._client_support_url_arg = client_support_url_arg
        self._client_support_service_url_arg = client_support_service_url_arg
        self._high_res_patch_arg = high_res_patch_arg
        self._patching_product_code = patching_product_code
        self._login_queue_url = login_queue_url
        self._login_queue_params_template = login_queue_params_template
        if newsfeed_url_template == DDO_PREVIEW_BROKEN_NEWS_URL_TEMPLATE:
            # Fix broken DDO Preview server newsfeed URL
            self._newsfeed_url_template = DDO_PREVIEW_NEWS_URL_TEMPLATE
        else:
            self._newsfeed_url_template = newsfeed_url_template

        # Dictionary is ordered according to client type similarity from a user
        # perspective. See unit tests for `self.get_client_filename`
        self.client_type_mapping = {
            ClientType.WIN64: self._client_win64_filename,
            ClientType.WIN32: self._client_win32_filename,
            ClientType.WIN32_LEGACY: self._client_win32_legacy_filename,
        }

        # Raise error if all client filenames in `self.client_type_mapping` are
        # `None`
        if not [val for val in self.client_type_mapping.values() if val is not None]:
            raise NoGameClientFilenameError(
                "All client filenames are `None`. At least one must be provided."
            )

    @classmethod
    def from_xml(cls: type[Self], appsettings_config_xml: str) -> Self:
        """
        Raises:
            GameLauncherConfigParseError: Config doesn't match expected game
                                          launcher config format

        """
        try:
            config_dict = parse_app_settings_config(appsettings_config_xml)

            client_win64_filename = config_dict.get("GameClient.WIN64.Filename")
            client_win32_filename = config_dict.get("GameClient.WIN32.Filename")
            client_win32_legacy_filename = config_dict.get(
                "GameClient.WIN32Legacy.Filename"
            )
            if not (
                client_win64_filename
                or client_win32_filename
                or client_win32_legacy_filename
            ):
                # In past game versions, there was only one client. It was
                # accessed with "GameClient.Filename"
                client_win32_legacy_filename = config_dict["GameClient.Filename"]

            if "GameClient.WIN32.ArgTemplate" in config_dict:
                arg_template = config_dict["GameClient.WIN32.ArgTemplate"]
            else:
                # Before more client types were added, the launch arguments
                # template was accessed with "GameClient.ArgTemplate"
                arg_template = config_dict["GameClient.ArgTemplate"]

            return cls(
                client_win64_filename,
                client_win32_filename,
                client_win32_legacy_filename,
                arg_template,
                config_dict.get("GameClient.Arg.crashreceiver"),
                config_dict.get("GameClient.Arg.authserverurl"),
                config_dict.get("GameClient.Arg.glsticketlifetime"),
                config_dict.get("GameClient.Arg.DefaultUploadThrottleMbps"),
                config_dict.get("GameClient.Arg.bugurl"),
                config_dict.get("GameClient.Arg.supporturl"),
                config_dict.get("GameClient.Arg.supportserviceurl"),
                config_dict.get("GameClient.HighResPatchArg"),
                config_dict["Patching.ProductCode"],
                config_dict["WorldQueue.LoginQueue.URL"],
                config_dict["WorldQueue.TakeANumber.Parameters"],
                config_dict["URL.NewsFeed"],
            )
        except AppSettingsParseError as e:
            raise GameLauncherConfigParseError(
                "Config XML doesn't follow the appSettings format"
            ) from e
        except KeyError as e:
            raise GameLauncherConfigParseError(
                "Config doesn't include a required value"
            ) from e
        except NoGameClientFilenameError as e:
            raise GameLauncherConfigParseError(
                "Config doesn't include any client filenames of a supported client type"
            ) from e

    @classmethod
    @cached(cache=TTLCache(maxsize=48, ttl=60 * 2))
    async def from_url(cls: type[Self], config_url: str) -> Self:
        """
        Raises:
            HTTPError: Network error while downloading the config XML
            GameLauncherConfigParseError: Config doesn't match expected game
                                          launcher config format
        """
        config_xml = await cls._get_config_xml(config_url)
        return cls.from_xml(config_xml)

    @classmethod
    async def from_game_config(cls: type[Self], game_config: GameConfig) -> Self | None:
        """Simplified shortcut for getting `GameLauncherConfig` object.
        Will return `None` if any exceptions are raised."""
        try:
            game_services_info = await GameServicesInfo.from_game_config(game_config)
            if game_services_info is None:
                return None
            return await cls.from_url(game_services_info.launcher_config_url)
        except (HTTPError, GameLauncherConfigParseError):
            return None

    @staticmethod
    async def _get_config_xml(config_url: str) -> str:
        """Return world queue config appsettings xml from url

        Raises:
            HTTPError: Network error while downloading the config XML
        """
        response = await get_httpx_client(config_url).get(config_url)
        response.raise_for_status()
        return response.text

    def get_specific_client_filename(self, client_type: ClientType) -> str | None:
        """Return filename or None if unavailable, for client of type `client_type`"""
        return self.client_type_mapping[client_type]

    def get_client_filename(
        self, preferred_client_type: ClientType | None = None
    ) -> tuple[str, ClientType]:
        """Return available client filename and associated ClientType.
        Client filename will be first available according to
        `self.client_type_mapping` or closest in type to
        `preferred_client_type`, if the argument is not `None`.
        """
        # Return first available client filename if no client type if preferred
        if preferred_client_type is None:
            for client_type, client_filename in self.client_type_mapping.items():
                if client_filename is not None:
                    return client_filename, client_type
            raise ValueError("All values are `None` in `self.client_type_mapping`")

        client_filename = self.get_specific_client_filename(preferred_client_type)

        # Choose new client_filename if requested one is None.
        # Code finds one that isn't None with client type that
        # is closest to client_type parameter of this function.
        new_client_type = None
        if client_filename is None:
            keys = list(self.client_type_mapping.keys())
            while client_filename is None:
                client_type_index = keys.index(preferred_client_type)
                if client_type_index == len(keys) - 1:
                    new_client_type_index = client_type_index - 1
                else:
                    new_client_type_index = client_type_index + 1

                new_client_type = keys[new_client_type_index]
                client_filename = self.client_type_mapping[new_client_type]
                keys.pop(new_client_type_index)

            logger.warning(
                "No client_filename for %s found. Returning filename for %s",
                preferred_client_type,
                new_client_type,
            )

        return client_filename, new_client_type or preferred_client_type

    @property
    def client_launch_args_template(self) -> str:
        return self._client_launch_args_template

    @property
    def client_crash_server_arg(self) -> str | None:
        return self._client_crash_server_arg

    @property
    def client_auth_server_arg(self) -> str | None:
        """Auth server URL for refreshing the GLS ticket."""
        return self._client_auth_server_arg

    @property
    def client_gls_ticket_lifetime_arg(self) -> str | None:
        """The lifetime of GLS tickets."""
        return self._client_gls_ticket_lifetime_arg

    @property
    def client_default_upload_throttle_mbps_arg(self) -> str | None:
        return self._client_default_upload_throttle_mbps_arg

    @property
    def client_bug_url_arg(self) -> str | None:
        """The url that should be used for reporting bugs."""
        return self._client_bug_url_arg

    @property
    def client_support_url_arg(self) -> str | None:
        """URL that should be used for in game support."""
        return self._client_support_url_arg

    @property
    def client_support_service_url_arg(self) -> str | None:
        """URL that should be used for auto submission of in game support tickets."""
        return self._client_support_service_url_arg

    @property
    def high_res_patch_arg(self) -> str | None:
        """
        Argument used to tell the client that the high resolution
        texture dat file was not updated. This will cause
        the client to not switch into high-res textures mode."""
        return self._high_res_patch_arg

    @property
    def patching_product_code(self) -> str:
        return self._patching_product_code

    @property
    def login_queue_url(self) -> str:
        return self._login_queue_url

    @property
    def login_queue_params_template(self) -> str:
        return self._login_queue_params_template

    def get_newfeed_url(self, locale: OneLauncherLocale) -> str:
        return self._newsfeed_url_template.replace(
            "{lang}", locale.lang_tag.split("-")[0]
        )
