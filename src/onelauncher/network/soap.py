import logging
from urllib.parse import urlparse, urlunparse

import zeep.exceptions
from zeep import AsyncClient
from zeep.cache import InMemoryCache
from zeep.transports import AsyncTransport

from .httpx_client import get_httpx_client, get_httpx_client_sync


class GLSServiceError(Exception):
    """Non-network error with the GLS service"""


def get_soap_client(gls_service: str) -> AsyncClient:
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

    cache = InMemoryCache(timeout=5 * 60)
    # Make transport to use caching and the SSL configs in `session`
    transport = AsyncTransport(
        client=get_httpx_client(wsdl_url),
        wsdl_client=get_httpx_client_sync(wsdl_url),
        cache=cache,
    )

    try:
        return AsyncClient(wsdl_url, transport=transport)
    except zeep.exceptions.Error as e:
        raise GLSServiceError("Error while parsing the service description") from e


logger = logging.getLogger("main")
