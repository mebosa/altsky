import logging
import os
from typing import Any, Dict, Optional

import requests

LOGGER = logging.getLogger(__name__)

_BASE_URL = os.getenv("STATSCALC_URL", "http://localhost:8082").rstrip("/")
_TIMEOUT = float(os.getenv("STATSCALC_TIMEOUT", "4"))


def calculate_stats(payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    payload는 Go statscalc 서비스가 기대하는 PlayerProfile 형태.
    """
    if not _BASE_URL:
        return None

    try:
        response = requests.post(f"{_BASE_URL}/stats", json=payload, timeout=_TIMEOUT)
        response.raise_for_status()
    except requests.RequestException as exc:
        if exc.response is not None:
             LOGGER.warning("Stats calc error response: %s", exc.response.text)
        LOGGER.warning("Stats calc request failed: %s", exc)
        return None

    try:
        body = response.json()
    except ValueError:
        LOGGER.warning("Stats calc response is not JSON")
        return None

    stats = body.get("stats")
    if isinstance(stats, dict):
        return stats
    return None
