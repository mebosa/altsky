import logging
import os

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

LOGGER = logging.getLogger(__name__)

# Global session for connection pooling
session = requests.Session()

_retry_total = int(os.getenv("HTTP_RETRY_TOTAL", "2"))
_retry_backoff = float(os.getenv("HTTP_RETRY_BACKOFF", "0.5"))

_retry = Retry(
    total=_retry_total,
    connect=_retry_total,
    read=_retry_total,
    status=_retry_total,
    backoff_factor=_retry_backoff,
    status_forcelist=(429, 500, 502, 503, 504),
    allowed_methods=frozenset({"GET", "POST"}),
    respect_retry_after_header=True,
    raise_on_status=False,
)

_adapter = HTTPAdapter(pool_connections=10, pool_maxsize=20, max_retries=_retry)
session.mount('http://', _adapter)
session.mount('https://', _adapter)

# Avoid leaking secrets in outbound request logs; keep UA stable for upstream debugging.
session.headers.setdefault(
    "User-Agent",
    os.getenv("HTTP_USER_AGENT", "altsky/1 (+https://altsky.info)"),
)

def get_session():
    return session
