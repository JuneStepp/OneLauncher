import logging
from typing import override
from urllib.parse import urlparse, urlunparse

import httpx
import trio
import zeep.exceptions
from zeep import AsyncClient, Settings
from zeep.cache import Base, InMemoryCache
from zeep.loader import load_external_async
from zeep.transports import AsyncTransport
from zeep.wsdl.wsdl import Definition, Document

from .httpx_client import get_httpx_client

logger = logging.getLogger(__name__)

# `zeep.transports` includes full web requests in debug logs. That means sensitive
# information like user passwords can end up in logs.
logging.getLogger("zeep.transports").setLevel(logging.INFO)


class GLSServiceError(Exception):
    """Non-network error with the GLS service"""


class FullyAsyncTransport(AsyncTransport):
    """Async transport that loads remote data like wsdl async."""

    def __init__(
        self,
        client: httpx.AsyncClient,
        cache: Base | None = None,
        timeout: int = 300,
        operation_timeout: int | None = None,
        verify_ssl: bool = True,
        proxy: httpx.Proxy | None = None,
    ):
        super().__init__(  # type: ignore[no-untyped-call]
            client=client,
            wsdl_client=client,
            cache=cache,
            timeout=timeout,
            operation_timeout=operation_timeout,
            verify_ssl=verify_ssl,
            proxy=proxy,
        )

    @override
    async def load(self, url: str) -> bytes:
        if not url:
            raise ValueError("No url given to load")

        scheme = urlparse(url).scheme
        if scheme in ("http", "https", "file"):
            if self.cache:
                response = self.cache.get(url)
                if response:
                    return bytes(response)

            content = await self._async_load_remote_data(url)

            if self.cache:
                self.cache.add(url, content)

            return content
        else:
            path = await trio.Path(url).expanduser()
            return await path.read_bytes()

    async def _async_load_remote_data(self, url: str) -> bytes:
        response = await self.client.get(url)
        result = response.read()

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise zeep.exceptions.TransportError(  # type: ignore[no-untyped-call]
                status_code=response.status_code
            ) from exc
        return result


class AsyncDocument(Document):
    def __init__(
        self,
        location: str,
        transport: AsyncTransport,
        base: str | None = None,
        settings: Settings | None = None,
    ):
        super().__init__(
            location=location,
            transport=transport,  # type: ignore[arg-type]
            base=base,
            settings=settings,
        )

    @override
    def load(self, location: str) -> None:
        return

    async def load_async(self, location: str) -> None:
        document = await load_external_async(
            url=location,  # type: ignore[arg-type]
            transport=self.transport,
            base_url=self.location,
            settings=self.settings,
        )

        root_definitions = Definition(self, document, self.location)  # type: ignore[no-untyped-call]
        root_definitions.resolve_imports()

        # Make the wsdl definitions public
        self.messages = root_definitions.messages
        self.port_types = root_definitions.port_types
        self.bindings = root_definitions.bindings
        self.services = root_definitions.services


async def get_soap_client(gls_service: str) -> AsyncClient:
    """Return configured SOAP client from GLS service URL

    Args:
        gls_service (str): GLS service URL

    Raises:
        HTTPError: Network error while downloading the service description
        GLSServiceError: Error while parsing the service description

    Returns:
        Client: Zeep SOAP client
    """
    parsed_url = urlparse(gls_service)
    # Transform base service link into link to the service description
    wsdl_url = urlunparse(parsed_url._replace(query="WSDL"))

    cache = InMemoryCache(timeout=5 * 60)  # type: ignore[no-untyped-call]
    # Make transport to use caching and the SSL configs in `session`
    transport = FullyAsyncTransport(
        client=get_httpx_client(wsdl_url),
        cache=cache,
    )
    settings = Settings()
    try:
        document = AsyncDocument(
            location=wsdl_url, transport=transport, settings=settings
        )
        await document.load_async(wsdl_url)
        return AsyncClient(wsdl=document, transport=transport, settings=settings)  # type: ignore[no-untyped-call]
    except zeep.exceptions.Error as e:
        raise GLSServiceError("Error while parsing the service description") from e
