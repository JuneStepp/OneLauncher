from functools import cache
from typing import Final

import httpx

from ..official_clients import (
    get_official_servers_httpx_client,
    get_official_servers_httpx_client_sync,
    is_official_game_server,
)

CONNECTION_RETRIES: Final[int] = 3


@cache
def _get_default_httpx_client() -> httpx.AsyncClient:
    transport = httpx.AsyncHTTPTransport(retries=CONNECTION_RETRIES)
    return httpx.AsyncClient(transport=transport)


@cache
def _get_default_httpx_client_sync() -> httpx.Client:
    transport = httpx.HTTPTransport(retries=CONNECTION_RETRIES)
    return httpx.Client(transport=transport)


def get_httpx_client(url: str) -> httpx.AsyncClient:
    return (
        get_official_servers_httpx_client()
        if is_official_game_server(url)
        else _get_default_httpx_client()
    )


def get_httpx_client_sync(url: str) -> httpx.Client:
    return (
        get_official_servers_httpx_client_sync()
        if is_official_game_server(url)
        else _get_default_httpx_client_sync()
    )
