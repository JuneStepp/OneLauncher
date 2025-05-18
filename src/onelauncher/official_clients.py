###########################################################################
# Information and configuration specific to official game clients.
#
# Based on PyLotRO
# (C) 2009 AJackson <ajackson@bcs.org.uk>
#
# Based on LotROLinux
# (C) 2007-2008 AJackson <ajackson@bcs.org.uk>
#
#
# (C) 2019-2025 June Stepp <contact@JuneStepp.me>
#
# This file is part of OneLauncher
#
# OneLauncher is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# OneLauncher is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with OneLauncher.  If not, see <http://www.gnu.org/licenses/>.
###########################################################################
import logging
import socket
import ssl
from functools import cache
from pathlib import Path
from typing import Final, assert_never
from urllib.parse import urlparse

import httpx

from onelauncher import resources
from onelauncher.game_config import GameType

logger = logging.getLogger(__name__)

LOTRO_GLS_PREVIEW_DOMAIN = "gls-bullroarer.lotro.com"
LOTRO_GLS_DOMAINS: Final = [
    "gls.lotro.com",
    "gls-auth.lotro.com",  # Same as gls.lotro.com
    LOTRO_GLS_PREVIEW_DOMAIN,
]
# Same as main gls domain, but ssl certificate isn't valid for this domain.
LOTRO_GLS_INVALID_SSL_DOMAIN: Final = "moria.gls.lotro.com"

DDO_GLS_PREVIEW_DOMAIN: Final = "gls-lm.ddo.com"
DDO_GLS_PREVIEW_IP: Final = "198.252.160.33"
DDO_GLS_DOMAINS: Final = [
    "gls.ddo.com",
    "gls-auth.ddo.com",  # Same as gls.ddo.com
    DDO_GLS_PREVIEW_DOMAIN,
]

# Forums where RSS feeds used as newsfeeds are
LOTRO_FORMS_DOMAINS: Final = [
    "forums.lotro.com",
    "forums-old.lotro.com",
]
DDO_FORMS_DOMAINS: Final = [
    "forums.ddo.com",
    "forums-old.ddo.com",
]
# DDO preview client provides broken news URL template. This info is used
# to fix it.
DDO_PREVIEW_BROKEN_NEWS_URL_TEMPLATE: Final = (
    "http://www.ddo.com/index.php?option=com_bca-rss-syndicator&feed_id=3"
)
DDO_PREVIEW_NEWS_URL_TEMPLATE: Final = "https://forums.ddo.com/index.php?forums/lamannia-news-and-official-discussions.20/index.rss"


# There may be specific better ciphers that can be used instead of just
# lowering the security level. I'm not knowledgable on this topic though.
OFFICIAL_CLIENT_CIPHERS: Final = "DEFAULT@SECLEVEL=1"

CONNECTION_RETRIES: Final[int] = 3


def is_official_game_server(url: str) -> bool:
    netloc = urlparse(url).netloc.lower()
    return (
        netloc
        in LOTRO_GLS_DOMAINS
        + LOTRO_FORMS_DOMAINS
        + DDO_GLS_DOMAINS
        + DDO_FORMS_DOMAINS
        + [LOTRO_GLS_INVALID_SSL_DOMAIN, DDO_GLS_PREVIEW_IP]
    )


def is_gls_url_for_preview_client(url: str) -> bool:
    netloc = urlparse(url).netloc.lower()
    return netloc in [
        LOTRO_GLS_PREVIEW_DOMAIN,
        DDO_GLS_PREVIEW_DOMAIN,
        DDO_GLS_PREVIEW_IP,
    ]


class DDOPreviewIPDoesNotMatchDomainError(httpx.RequestError):
    """Expected IP to match the DDO preview GLS server domain IP"""


def _httpx_request_hook_sync(request: httpx.Request) -> None:
    # Force HTTPS. It's supported by all the official servers, but most URLs
    # default to HTTP.
    request.url = request.url.copy_with(scheme="https")

    # Change "moria.gls.lotro.com" domains to "gls.lotro.com".
    # This is necessary, because the SSL certificate used by
    # "moria.gls.lotro.com" is only valid for "*.lotro.com" and "lotro.com".
    if request.url.host.lower().startswith(LOTRO_GLS_INVALID_SSL_DOMAIN):
        request.url = request.url.copy_with(
            host=request.url.host.lower().replace(
                LOTRO_GLS_INVALID_SSL_DOMAIN, LOTRO_GLS_DOMAINS[0], 1
            )
        )

    # Change DDO preview server IP to domain name.
    # This is to make HTTPS work properly.
    if request.url.host.lower().startswith(DDO_GLS_PREVIEW_IP):
        try:
            # Verify that DDO preview server still matches the expected IP
            if socket.gethostbyname(DDO_GLS_PREVIEW_DOMAIN) != DDO_GLS_PREVIEW_IP:
                raise DDOPreviewIPDoesNotMatchDomainError(
                    "IP doesn't match the DDO preview GLS server domain IP"
                )
        except OSError as e:
            raise httpx.RequestError(
                "Connection error while verifying DDO preview GLS server IP"
            ) from e

        request.url = request.url.copy_with(host=DDO_GLS_PREVIEW_DOMAIN)


async def _httpx_request_hook(request: httpx.Request) -> None:
    _httpx_request_hook_sync(request)


def get_official_servers_ssl_context() -> ssl.SSLContext:
    """
    Return SSLContext configured for the lower security of the official servers
    """
    ssl_context = httpx.create_ssl_context()
    ssl_context.verify_mode = ssl.CERT_REQUIRED
    ssl_context.set_ciphers(OFFICIAL_CLIENT_CIPHERS)
    return ssl_context


@cache
def get_official_servers_httpx_client() -> httpx.AsyncClient:
    """Return httpx client configured to work with official game servers"""
    transport = httpx.AsyncHTTPTransport(
        verify=get_official_servers_ssl_context(), retries=CONNECTION_RETRIES
    )
    return httpx.AsyncClient(
        verify=get_official_servers_ssl_context(),
        event_hooks={"request": [_httpx_request_hook]},
        transport=transport,
    )


@cache
def get_official_servers_httpx_client_sync() -> httpx.Client:
    """Return httpx client configured to work with official game servers"""
    transport = httpx.HTTPTransport(
        verify=get_official_servers_ssl_context(), retries=CONNECTION_RETRIES
    )
    return httpx.Client(
        verify=get_official_servers_ssl_context(),
        event_hooks={"request": [_httpx_request_hook_sync]},
        transport=transport,
    )


def get_game_icon(game_type: GameType) -> Path:
    match game_type:
        case GameType.LOTRO:
            return resources.data_dir / "images/lotro_icon.ico"
        case GameType.DDO:
            return resources.data_dir / "images/ddo_icon.ico"
        case _:
            assert_never(game_type)
