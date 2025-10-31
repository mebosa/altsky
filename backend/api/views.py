import os
from typing import Any, Dict, Optional, Tuple

import requests
from django.core.cache import cache
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response

from .domain.profile_summary import summarize_profile

HYPIXEL_PROFILES_URL = "https://api.hypixel.net/v2/skyblock/profiles"


def _fetch_hypixel_profiles(uuid: str) -> Tuple[Optional[Dict[str, Any]], Optional[Response]]:
    api_key = os.getenv("HYPIXEL_API_KEY")
    if not api_key:
        return None, Response({"error": "HYPIXEL_API_KEY missing"}, status=500)

    try:
        response = requests.get(
            HYPIXEL_PROFILES_URL,
            params={"uuid": uuid},
            headers={"API-Key": api_key},
            timeout=12,
        )
    except requests.RequestException as exc:
        return None, Response({"error": "hypixel_request_failed", "detail": str(exc)}, status=502)

    if response.status_code == 429:
        return None, Response({"error": "rate_limited"}, status=429)

    if response.status_code != 200:
        return None, Response(
            {"error": "hypixel_http_error", "status": response.status_code, "text": response.text},
            status=502,
        )

    body = response.json()
    if body.get("success") is False:
        return None, Response({"error": "hypixel_error", "detail": body}, status=502)

    profiles = body.get("profiles") or []
    if not profiles:
        return None, Response({"error": "no_profiles"}, status=404)

    return body, None


@api_view(["GET"])
def health(_: Request) -> Response:
    return Response({"ok": True})


@api_view(["GET"])
def player_lookup(_: Request, name: str) -> Response:
    cache_key = f"uuid:{name.lower()}"
    uuid = cache.get(cache_key)
    if not uuid:
        result = requests.get(
            f"https://api.mojang.com/users/profiles/minecraft/{name}",
            timeout=5,
        )
        if result.status_code in (204, 404):
            return Response({"error": "player_not_found"}, status=404)
        result.raise_for_status()
        uuid = result.json().get("id")
        cache.set(cache_key, uuid, 3600)
    return Response({"name": name, "uuid": uuid})


@api_view(["GET"])
def hypixel_profile(_: Request, uuid: str) -> Response:
    """
    Raw SkyBlock profile list from Hypixel for the given Minecraft UUID.
    """
    body, error = _fetch_hypixel_profiles(uuid)
    if error:
        return error
    return Response(body)


@api_view(["GET"])
def hypixel_profile_summary(_: Request, uuid: str, profile_id: str) -> Response:
    """
    Enriched summary for a specific profile belonging to the given UUID.
    """
    body, error = _fetch_hypixel_profiles(uuid)
    if error:
        return error

    profiles = body.get("profiles") or []
    target = None
    for candidate in profiles:
        if candidate.get("profile_id") == profile_id or candidate.get("uuid") == profile_id:
            target = candidate
            break

    if not target:
        return Response({"error": "profile_not_found"}, status=404)

    summary = summarize_profile(uuid, target)
    if not summary:
        return Response({"error": "member_not_in_profile"}, status=404)

    return Response(
        {
            "ok": True,
            "last_updated": body.get("last_updated") or body.get("lastUpdated"),
            **summary,
        }
    )
