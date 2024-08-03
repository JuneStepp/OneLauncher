import logging
from typing import Any, Final
from urllib.parse import urlparse, urlunparse

import httpx
import xmlschema
from asyncache import cached
from cachetools import TTLCache
from typing_extensions import override

from ..resources import data_dir
from .httpx_client import get_httpx_client

logger = logging.getLogger(__name__)


class WorldUnavailableError(Exception):
    """World is unavailable."""


class WorldStatus:
    def __init__(self, queue_url: str, login_server: str) -> None:
        self._queue_url = queue_url
        self._login_server = login_server

    @property
    def queue_url(self) -> str:
        """URL used to queue for world login.
        Will be an empty string, if no queueing is needed."""
        return self._queue_url

    @property
    def login_server(self) -> str:
        return self._login_server


class World:
    _WORLD_STATUS_SCHEMA: Final = xmlschema.XMLSchema(
        data_dir / "network" / "schemas" / "world_status.xsd"
    )

    def __init__(
        self,
        name: str,
        chat_server_url: str,
        status_server_url: str,
        gls_datacenter_service: str | None = None,
    ):
        self._name = name
        self._chat_server_url = chat_server_url
        self._status_server_url = status_server_url
        self._gls_datacenter_service = gls_datacenter_service

    @property
    def name(self) -> str:
        return self._name

    @property
    def chat_server_url(self) -> str:
        return self._chat_server_url

    @property
    def status_server_url(self) -> str:
        return self._status_server_url

    @cached(cache=TTLCache(maxsize=1, ttl=60))
    async def get_status(self) -> WorldStatus:
        """Return current world status info

        Raises:
            HTTPError: Network error while downloading the status XML
            WorldUnavailableError: World is unavailable
            XMLSchemaValidationError: Status XML doesn't match schema
        """
        status_dict = await self._get_status_dict(self.status_server_url)
        queue_urls: tuple[str, ...] = tuple(
            url for url in status_dict["queueurls"].split(";") if url
        )
        login_servers: tuple[str, ...] = tuple(
            server for server in status_dict["loginservers"].split(";") if server
        )
        return WorldStatus(queue_urls[0], login_servers[0])

    async def _get_status_dict(self, status_server_url: str) -> dict[str, Any]:
        """Return world status dictionary

        Raises:
            HTTPError: Network error while downloading the status XML
            WorldUnavailableError: World is unavailable
            XMLSchemaValidationError: Status XML doesn't match schema

        Returns:
            dict: Dictionary representation of world status.
                  See `self._WORLD_STATUS_SCHEMA` schema file for what to expect.
        """
        response = await get_httpx_client(status_server_url).get(status_server_url)

        if response.status_code == httpx.codes.NOT_FOUND or not response.text:
            # Fix broken status URLs for some LOTRO legendary servers
            if self._gls_datacenter_service:
                parsed_status_url = urlparse(status_server_url)
                parsed_gls_service = urlparse(self._gls_datacenter_service)
                if (
                    parsed_status_url.path.lower().endswith("/statusserver.aspx")
                    and parsed_status_url.netloc.lower()
                    != parsed_gls_service.netloc.lower()
                ):
                    # Some legendary servers have an IP that doesn't work instead of
                    # a domain for the netloc. Having the domain also helps OneLauncher
                    # enforce HTTPS correctly.
                    url_fixed_netloc = parsed_status_url._replace(
                        netloc=parsed_gls_service.netloc
                    )
                    # The "Mordor" legendary server path starts with "GLS.STG.DataCenterServer"
                    # instead of "GLS.DataCenterServer".
                    gls_path_prefix = parsed_gls_service.path.lower().split(
                        "/service.asmx", maxsplit=1
                    )[0]
                    url_fixed_path = url_fixed_netloc._replace(
                        path=f"{gls_path_prefix}/StatusServer.aspx"
                    )
                    return await self._get_status_dict(urlunparse(url_fixed_path))

            # 404 response generally means world is unavailable.
            # Empty `response.text` also means the world is unavailable. Got an empty but
            # successful response during an unexpected worlds downtime on 2024/30/31.
            raise WorldUnavailableError(f"{self} world unavailable")

        response.raise_for_status()

        return self._WORLD_STATUS_SCHEMA.to_dict(response.text)  # type: ignore[return-value]

    @override
    def __str__(self) -> str:
        return self.name
