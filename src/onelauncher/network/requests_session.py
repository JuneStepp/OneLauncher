import logging
import socket
import ssl
from functools import cache
from typing import Final
from urllib.parse import urlparse, urlunparse

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.ssl_ import create_urllib3_context

# There may be specific better ciphers that can be used instead of just
# lowering the security level. I'm not knowledgable on this topic though.
_OFFICIAL_CLIENT_CIPHERS: Final = "DEFAULT@SECLEVEL=1"

_DDO_GLS_PREVIEW_DOMAIN: Final = "gls-lm.ddo.com"
_DDO_GLS_PREVIEW_IP: Final = "198.252.160.33"
_OFFICIAL_CLIENT_URL_PREFIXES_NO_SCHEMA: Final = {
    # Forums where RSS feeds used as newsfeeds are
    "forums.ddo.com/",
    "forums.lotro.com/",
    # GLS Servers
    "gls.ddo.com",
    _DDO_GLS_PREVIEW_DOMAIN,
    "gls.lotro.com",
    "gls-bullroarer.lotro.com",
    "gls-auth.ddo.com",  # Same as gls.ddo.com
    "gls-auth.lotro.com",  # Same as gls.lotro.com
}


class _OfficialClientAdapter(HTTPAdapter):
    """
    A TransportAdapter configured for the lower security of
    the official LOTRO and DDO servers. Also, forces HTTPS.
    """

    def init_poolmanager(self, *args, **kwargs):
        context = create_urllib3_context(
            cert_reqs=ssl.CERT_REQUIRED,
            ciphers=_OFFICIAL_CLIENT_CIPHERS)
        kwargs['ssl_context'] = context
        return super(
            _OfficialClientAdapter,
            self).init_poolmanager(
            *args,
            **kwargs)

    def proxy_manager_for(self, *args, **kwargs):
        context = create_urllib3_context(
            cert_reqs=ssl.CERT_REQUIRED,
            ciphers=_OFFICIAL_CLIENT_CIPHERS)
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
            request.url = request.url.lower().replace("moria.gls.lotro", "gls.lotro", 1)
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
                        _DDO_GLS_PREVIEW_DOMAIN) != _DDO_GLS_PREVIEW_IP:
                    raise DDOPreviewIPDoesNotMatchDomainError(
                        "IP doesn't match the DDO preview GLS server domain IP")
            except OSError as e:
                raise requests.RequestException(
                    "Connection error while verifying DDO preview "
                    "GLS server IP") from e
        
            parsed_url = urlparse(request.url)
            request.url = urlunparse(parsed_url._replace(
                netloc=_DDO_GLS_PREVIEW_DOMAIN))
        return super(_DDOPreviewGLSAdapter, self).send(request, **kwargs)


@cache
def get_requests_session() -> requests.Session:
    session = requests.Session()

    for prefix in _OFFICIAL_CLIENT_URL_PREFIXES_NO_SCHEMA:
        session.mount(f"https://{prefix}", _OfficialClientAdapter())
        # HTTP will be changed to HTTPS
        session.mount(f"http://{prefix}", _OfficialClientAdapter())
    session.mount("https://moria.gls.lotro.com", _MoriaGLSAdapter())
    session.mount("http://moria.gls.lotro.com", _MoriaGLSAdapter())
    session.mount(f"https://{_DDO_GLS_PREVIEW_IP}", _DDOPreviewGLSAdapter())
    session.mount(f"http://{_DDO_GLS_PREVIEW_IP}", _DDOPreviewGLSAdapter())

    return session


logger = logging.getLogger("main")
