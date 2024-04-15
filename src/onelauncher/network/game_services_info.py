import logging
from typing import Self

import zeep.exceptions
from asyncache import cached
from cachetools import TTLCache
from httpx import HTTPError

from ..game import Game
from .soap import GLSServiceError, get_soap_client
from .world import World


class GameServicesInfo:
    def __init__(
        self,
        gls_datacenter_service: str,
        game_datacenter_name: str,
        auth_server: str,
        patch_server: str,
        launcher_config_url: str,
        worlds: set[World],
    ) -> None:
        self._gls_datacenter_service = gls_datacenter_service
        self._game_datacenter_name = game_datacenter_name
        self._auth_server = auth_server
        self._patch_server = patch_server
        self._launcher_config_url = launcher_config_url
        self._worlds = worlds

    @classmethod
    @cached(cache=TTLCache(maxsize=48, ttl=60 * 2))
    async def from_url(
        cls: type[Self], gls_datacenter_service: str, game_datacenter_name: str
    ) -> Self:
        """
        Raises:
            HTTPError: Network error
            GLSServiceError: Non-network issue with the GLS service
        """
        datacenter_dict = await cls._get_datacenter_dict(
            gls_datacenter_service, game_datacenter_name
        )
        try:
            return cls(
                gls_datacenter_service,
                game_datacenter_name,
                datacenter_dict["AuthServer"],
                datacenter_dict["PatchServer"],
                datacenter_dict["LauncherConfigurationServer"],
                cls._get_worlds(datacenter_dict, gls_datacenter_service),
            )
        except KeyError as e:
            raise GLSServiceError(
                "GetDatacenters response missing required value"
            ) from e

    @classmethod
    async def from_game(cls: type[Self], game: Game) -> Self | None:
        """Simplified shortcut for getting `GameServicesInfo` object.
        Will return `None` if any exceptions are raised."""
        try:
            return await cls.from_url(
                game.gls_datacenter_service, game.datacenter_game_name
            )
        except (HTTPError, GLSServiceError, AttributeError):
            return None

    @property
    def gls_datacenter_service(self) -> str:
        return self._gls_datacenter_service

    @property
    def game_datacenter_name(self) -> str:
        return self._game_datacenter_name

    @property
    def auth_server(self) -> str:
        return self._auth_server

    @property
    def patch_server(self) -> str:
        return self._patch_server

    @property
    def launcher_config_url(self) -> str:
        return self._launcher_config_url

    @property
    def worlds(self) -> set[World]:
        return self._worlds

    @staticmethod
    def _get_worlds(
        datacenter_dict: dict, gls_datacenter_service: str | None
    ) -> set[World]:
        """Return set of game `World` objects

        Raises:
            KeyError: GetDatacenters response missing Worlds details
        """
        world_dicts = datacenter_dict["Worlds"]["World"]
        return {
            World(
                world_dict["Name"],
                world_dict["ChatServerUrl"],
                world_dict["StatusServerUrl"],
                gls_datacenter_service,
            )
            for world_dict in world_dicts
        }

    @staticmethod
    async def _get_datacenter_dict(
        gls_datacenter_service: str, game_datacenter_name: str
    ) -> dict:
        """Return dictionary of GetDatacenters SOAP operation response.

        Raises:
            HTTPError: Network error
            GLSServiceError: Non-network issue with the GLS service

        Returns:
            dict: Parsed GetDatacenters response
        """
        client = get_soap_client(gls_datacenter_service)

        try:
            return (await client.service.GetDatacenters(game=game_datacenter_name))[0]
        except zeep.exceptions.Error as e:
            raise GLSServiceError("Error while parsing GetDatacenters response") from e
        except AttributeError as e:
            raise GLSServiceError("Service has no GetDatacenters operation") from e


logger = logging.getLogger("main")
