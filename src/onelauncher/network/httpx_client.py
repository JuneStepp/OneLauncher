from functools import cache

import httpx

from ..official_clients import (
    get_official_servers_httpx_client,
    get_official_servers_httpx_client_sync,
    is_official_game_server)


@cache
def _get_default_httpx_client() -> httpx.AsyncClient:
    return httpx.AsyncClient()


@cache
def _get_default_httpx_client_sync() -> httpx.Client:
    return httpx.Client()


def get_httpx_client(url: str) -> httpx.AsyncClient:
    return get_official_servers_httpx_client(
    ) if is_official_game_server(url) else _get_default_httpx_client()


def get_httpx_client_sync(url: str) -> httpx.Client:
    return get_official_servers_httpx_client_sync(
    ) if is_official_game_server(url) else _get_default_httpx_client_sync()
