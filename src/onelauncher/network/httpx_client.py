from functools import cache
from typing import Final

import httpx2

from ..official_clients import (
    get_official_servers_httpx_client,
    get_official_servers_httpx_client_sync,
    is_official_game_server,
)

CONNECTION_RETRIES: Final[int] = 3
LIMITS: Final = httpx2.Limits(max_connections=12)


@cache
def _get_default_httpx_client() -> httpx2.AsyncClient:
    transport = httpx2.AsyncHTTPTransport(retries=CONNECTION_RETRIES)
    return httpx2.AsyncClient(limits=LIMITS, transport=transport)


@cache
def _get_default_httpx_client_sync() -> httpx2.Client:
    transport = httpx2.HTTPTransport(retries=CONNECTION_RETRIES, limits=LIMITS)
    return httpx2.Client(transport=transport)


def get_httpx_client(url: str) -> httpx2.AsyncClient:
    return (
        get_official_servers_httpx_client()
        if is_official_game_server(url)
        else _get_default_httpx_client()
    )


def get_httpx_client_sync(url: str) -> httpx2.Client:
    return (
        get_official_servers_httpx_client_sync()
        if is_official_game_server(url)
        else _get_default_httpx_client_sync()
    )
