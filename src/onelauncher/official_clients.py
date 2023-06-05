# coding=utf-8
###########################################################################
# Information specific to official game clients. See `.network.requests_session`
#
# Based on PyLotRO
# (C) 2009 AJackson <ajackson@bcs.org.uk>
#
# Based on LotROLinux
# (C) 2007-2008 AJackson <ajackson@bcs.org.uk>
#
#
# (C) 2019-2023 June Stepp <contact@JuneStepp.me>
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
from typing import Final
from urllib.parse import urlparse, urlunparse

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.ssl_ import create_urllib3_context

LOTRO_GLS_PREVIEW_DOMAIN = "gls-bullroarer.lotro.com"
LOTRO_GLS_DOMAINS: Final = [
    "gls.lotro.com",
    "gls-auth.lotro.com",  # Same as gls.lotro.com
    LOTRO_GLS_PREVIEW_DOMAIN,
]
# Same as main gls domain, but ssl certificate isn't valid for this domain.
LOTRO_GLS_INVALID_SSL_DOMAIN: Final = "moria.gls.lotro.com"
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
DDO_PREVIEW_BROKEN_NEWS_URL_TEMPLATE: Final = "http://www.ddo.com/index.php?option=com_bca-rss-syndicator&feed_id=3"
DDO_PREVIEW_NEWS_URL_TEMPLATE: Final = "https://forums.ddo.com/index.php?forums/lamannia-news-and-official-discussions.20/index.rss"
DDO_GLS_PREVIEW_DOMAIN: Final = "gls-lm.ddo.com"
DDO_GLS_PREVIEW_IP: Final = "198.252.160.33"
DDO_GLS_DOMAINS: Final = [
    "gls.ddo.com",
    "gls-auth.ddo.com",  # Same as gls.ddo.com
    DDO_GLS_PREVIEW_DOMAIN,
]

# There may be specific better ciphers that can be used instead of just
# lowering the security level. I'm not knowledgable on this topic though.
OFFICIAL_CLIENT_CIPHERS: Final = "DEFAULT@SECLEVEL=1"


class _OfficialClientAdapter(HTTPAdapter):
    """
    A TransportAdapter configured for the lower security of
    the official LOTRO and DDO servers. Also, forces HTTPS.
    """

    def init_poolmanager(self, *args, **kwargs):
        context = create_urllib3_context(
            cert_reqs=ssl.CERT_REQUIRED,
            ciphers=OFFICIAL_CLIENT_CIPHERS)
        kwargs['ssl_context'] = context
        return super(
            _OfficialClientAdapter,
            self).init_poolmanager(
            *args,
            **kwargs)

    def proxy_manager_for(self, *args, **kwargs):
        context = create_urllib3_context(
            cert_reqs=ssl.CERT_REQUIRED,
            ciphers=OFFICIAL_CLIENT_CIPHERS)
        kwargs['ssl_context'] = context
        return super(
            _OfficialClientAdapter,
            self).proxy_manager_for(
            *args,
            **kwargs)

    def send(self, request: requests.PreparedRequest, **kwargs) -> requests.Response:  # type: ignore
        if request.url:
            parsed_url = urlparse(request.url)
            # Make sure URL uses HTTPS
            request.url = urlunparse(parsed_url._replace(scheme="https"))
        return super(_OfficialClientAdapter, self).send(request, **kwargs)


class _MoriaGLSAdapter(_OfficialClientAdapter):
    """
    A subclass of `_OfficialClientAdapter` that changes "moria.gls.lotro.com"
    domains to "gls.lotro.com".

    This is necessary, because the SSL certificate used by "moria.gls.lotro.com"
    is only valid for "*.lotro.com" and "lotro.com".
    """

    def send(self, request: requests.PreparedRequest, **kwargs) -> requests.Response:  # type: ignore
        if request.url:
            request.url = request.url.lower().replace(
                LOTRO_GLS_INVALID_SSL_DOMAIN, LOTRO_GLS_DOMAINS[0], 1)
        return super(_MoriaGLSAdapter, self).send(request, **kwargs)


class DDOPreviewIPDoesNotMatchDomainError(requests.RequestException):
    """Expected IP to match the DDO preview GLS server domain IP"""


class _DDOPreviewGLSAdapter(_OfficialClientAdapter):
    """
    A subclass of `_OfficialClientAdapter` that changes DDO Preview server IP
    to domain name. This is to make HTTPS work properly.
    """

    def send(self, request: requests.PreparedRequest, **kwargs) -> requests.Response:  # type: ignore
        if request.url:
            try:
                # Verify that DDO preview server still matches the expected IP
                if socket.gethostbyname(
                        DDO_GLS_PREVIEW_DOMAIN) != DDO_GLS_PREVIEW_IP:
                    raise DDOPreviewIPDoesNotMatchDomainError(
                        "IP doesn't match the DDO preview GLS server domain IP")
            except OSError as e:
                raise requests.RequestException(
                    "Connection error while verifying DDO preview "
                    "GLS server IP") from e

            parsed_url = urlparse(request.url)
            request.url = urlunparse(parsed_url._replace(
                netloc=DDO_GLS_PREVIEW_DOMAIN))
        return super(_DDOPreviewGLSAdapter, self).send(request, **kwargs)


def configure_requests_session(session: requests.Session) -> None:
    """Configure requests session to work with official game servers"""
    for prefix in LOTRO_GLS_DOMAINS + LOTRO_FORMS_DOMAINS + \
            DDO_GLS_DOMAINS + DDO_FORMS_DOMAINS:
        session.mount(f"https://{prefix}", _OfficialClientAdapter())
        # HTTP will be changed to HTTPS
        session.mount(f"http://{prefix}", _OfficialClientAdapter())
    session.mount(
        f"https://{LOTRO_GLS_INVALID_SSL_DOMAIN}",
        _MoriaGLSAdapter())
    session.mount(f"http://{LOTRO_GLS_INVALID_SSL_DOMAIN}", _MoriaGLSAdapter())
    session.mount(f"https://{DDO_GLS_PREVIEW_IP}", _DDOPreviewGLSAdapter())
    session.mount(f"http://{DDO_GLS_PREVIEW_IP}", _DDOPreviewGLSAdapter())


logger = logging.getLogger("main")
