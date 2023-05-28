import logging
from typing import Final, Optional, Tuple
from urllib.parse import urlparse, urlunparse

from ..resources import data_dir
import xmlschema
from cachetools import TTLCache, cached
from . import session


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
        data_dir / "network" / "schemas" / "world_status.xsd")

    def __init__(
            self,
            name: str,
            chat_server_url: str,
            status_server_url: str,
            gls_datacenter_service: Optional[str] = None):
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
    def get_status(self) -> WorldStatus:
        """Return current world status info

        Raises:
            RequestException: Network error while downloading the status XML
            WorldUnavailableError: World is unavailable
            XMLSchemaValidationError: Status XML doesn't match schema

        Returns:
            dict: Dictionary representation of world status.
                  See `self._WORLD_STATUS_SCHEMA` schema file for what to expect.
        """
        status_dict = self._get_status_dict(self.status_server_url)
        queue_urls: Tuple[str, ...] = tuple(
            url for url in status_dict["queueurls"].split(";") if url)
        login_servers: Tuple[str, ...] = tuple(
            server for server in status_dict["loginservers"].split(";") if server)
        return WorldStatus(queue_urls[0], login_servers[0])

    def _get_status_dict(self, status_server_url: str) -> dict:
        """Return world status dictionary

        Raises:
            RequestException: Network error while downloading the status XML
            WorldUnavailableError: World is unavailable
            XMLSchemaValidationError: Status XML doesn't match schema

        Returns:
            dict: Dictionary representation of world status.
                  See `self._WORLD_STATUS_SCHEMA` schema file for what to expect.
        """
        response = session.get(status_server_url, timeout=10)

        if response.status_code == 404:
            # Fix broken status URLs for LOTRO legendary servers
            if self._gls_datacenter_service:
                parsed_status_url = urlparse(status_server_url)
                if parsed_status_url.path.lower().endswith("/statusserver.aspx"):
                    parsed_gls_service = urlparse(self._gls_datacenter_service)
                    url_fixed_netloc = parsed_status_url._replace(
                        netloc=parsed_gls_service.netloc)
                    return self._get_status_dict(urlunparse(url_fixed_netloc))

            # 404 response generally means world is unavailable
            raise WorldUnavailableError(f"{self} world unavailable")

        response.raise_for_status()

        return self._WORLD_STATUS_SCHEMA.to_dict(response.text)

    def __str__(self) -> str:
        return self.name


logger = logging.getLogger("main")
