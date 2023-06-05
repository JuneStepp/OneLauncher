from functools import cache

import requests

from .. import official_clients


@cache
def get_requests_session() -> requests.Session:
    session = requests.Session()
    official_clients.configure_requests_session(session)
    return session
