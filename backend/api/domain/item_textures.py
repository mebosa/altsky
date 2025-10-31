import base64
import json
import logging
from functools import lru_cache
from typing import Dict, Iterable, Optional

import requests

LOGGER = logging.getLogger(__name__)
ITEMS_URL = "https://api.hypixel.net/resources/skyblock/items"
ASSET_BASE = (
    "https://raw.githubusercontent.com/InventivetalentDev/minecraft-assets/1.20.1"
    "/assets/minecraft/textures"
)

SESSION = requests.Session()
_ASSET_CACHE: Dict[str, Optional[str]] = {}


@lru_cache(maxsize=1)
def _load_item_resource_map() -> Dict[str, Dict[str, object]]:
    try:
        response = SESSION.get(ITEMS_URL, timeout=10)
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException as exc:  # pragma: no cover - network failure
        LOGGER.warning("Failed to load Hypixel item resources: %s", exc)
        return {}

    items = payload.get("items") or []
    mapping = {}
    for item in items:
        item_id = item.get("id")
        if item_id:
            mapping[item_id] = item
    return mapping


def _decode_skin_url(skin: Optional[Dict[str, str]]) -> Optional[str]:
    if not skin:
        return None
    value = skin.get("value")
    if not value:
        return None
    try:
        decoded = json.loads(base64.b64decode(value))
    except (json.JSONDecodeError, ValueError, TypeError) as exc:
        LOGGER.debug("Failed to decode skin payload: %s", exc)
        return None
    profile_id = decoded.get("profileId")
    if profile_id:
        # Render the head via crafatar for a more 3D appearance.
        return f"https://crafatar.com/renders/head/{profile_id}?overlay&scale=6"

    url = (
        decoded.get("textures", {})
        .get("SKIN", {})
        .get("url")
    )
    if not url:
        return None
    return url.replace("http://", "https://")


def _cached_asset_path(candidate: str) -> Optional[str]:
    if candidate in _ASSET_CACHE:
        return _ASSET_CACHE[candidate]

    url = f"{ASSET_BASE}/{candidate}"
    try:
        response = SESSION.head(url, timeout=5)
    except requests.RequestException:  # pragma: no cover - network failure
        _ASSET_CACHE[candidate] = None
        return None

    if response.status_code == 200:
        _ASSET_CACHE[candidate] = url
        return url

    _ASSET_CACHE[candidate] = None
    return None


def _build_material_candidates(name: str) -> Iterable[str]:
    normalized = name.lower().replace("minecraft:", "").replace(":", "_")
    normalized = normalized.replace(".", "_")

    parts = normalized.split()
    if len(parts) > 1:
        normalized = "_".join(parts)

    base = normalized
    candidates = [f"item/{base}.png"]

    if base.endswith("_block"):
        trimmed = base[:-6]
        candidates.extend(
            [
                f"block/{base}.png",
                f"block/{trimmed}.png",
                f"block/{trimmed}_side.png",
                f"block/{trimmed}_top.png",
            ]
        )
    if base.endswith("_ore"):
        trimmed = base[:-4]
        candidates.extend(
            [
                f"block/{base}.png",
                f"block/{trimmed}_ore.png",
            ]
        )
    if base.endswith("_helmet"):
        candidates.append("item/iron_helmet.png")
    if base.endswith("_chestplate"):
        candidates.append("item/iron_chestplate.png")
    if base.endswith("_leggings"):
        candidates.append("item/iron_leggings.png")
    if base.endswith("_boots"):
        candidates.append("item/iron_boots.png")

    if "_" in base:
        tail = base.split("_")[-1]
        candidates.append(f"item/{tail}.png")

    # Generic fallback
    candidates.append("item/diamond.png")

    seen = set()
    for candidate in candidates:
        if candidate not in seen:
            seen.add(candidate)
            yield candidate


def _material_texture(name: Optional[str]) -> Optional[str]:
    if not name:
        return None
    for candidate in _build_material_candidates(name):
        url = _cached_asset_path(candidate)
        if url:
            return url
    return None


def resolve_item_icon(item_id: Optional[str], mc_id: Optional[str]) -> Optional[str]:
    """
    Return an HTTPS URL pointing to an icon representing the SkyBlock item.
    Preference order:
        1. Hypixel custom skin texture
        2. Vanilla material texture (based on Hypixel materials or mc_id)
    """
    resource_map = _load_item_resource_map()
    icon_url: Optional[str] = None

    if item_id and item_id in resource_map:
        entry = resource_map[item_id]
        icon_url = _decode_skin_url(entry.get("skin"))
        if not icon_url:
            icon_url = _material_texture(entry.get("material"))

    if not icon_url and mc_id:
        icon_url = _material_texture(mc_id)

    return icon_url
