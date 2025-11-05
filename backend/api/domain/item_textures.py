import base64
import json
import logging
import os
from functools import lru_cache
from typing import Dict, Iterable, Optional

import requests

LOGGER = logging.getLogger(__name__)
ITEMS_URL = "https://api.hypixel.net/resources/skyblock/items"
ASSET_BASE = (
    "https://raw.githubusercontent.com/InventivetalentDev/minecraft-assets/1.20.1"
    "/assets/minecraft/textures"
)
FURFSKY_TEXTURES_PATH = os.path.join(os.path.dirname(__file__), "furfsky_textures")

SESSION = requests.Session()
_ASSET_CACHE: Dict[str, Optional[str]] = {}

LEGACY_DYE_COLORS = [
    "white",
    "orange",
    "magenta",
    "light_blue",
    "yellow",
    "lime",
    "pink",
    "gray",
    "light_gray",
    "cyan",
    "purple",
    "blue",
    "brown",
    "green",
    "red",
    "black",
]

LEGACY_ID_ALIASES = {
    35: "wool",
    95: "stained_glass",
    98: "stone_bricks",
    159: "stained_clay",
    160: "stained_glass_pane",
    162: "log2",
    171: "carpet",
    236: "concrete",
    237: "concrete_powder",
}

COLOR_TEMPLATE_MAP = {
    "carpet": ["block/{color}_carpet.png"],
    "concrete": ["block/{color}_concrete.png"],
    "concrete_powder": ["block/{color}_concrete_powder.png"],
    "glazed_terracotta": ["block/{color}_glazed_terracotta.png"],
    "shulker_box": ["block/{color}_shulker_box.png"],
    "stained_clay": ["block/{color}_terracotta.png"],
    "stained_glass": ["block/{color}_stained_glass.png"],
    "stained_glass_pane": ["block/{color}_stained_glass_pane.png"],
    "stained_hardened_clay": ["block/{color}_terracotta.png"],
    "terracotta": ["block/{color}_terracotta.png"],
    "wool": ["block/{color}_wool.png"],
    "ink_sack": ["item/{color}_dye.png"],
}

MATERIAL_ALIASES = {
    "gold_helmet": "golden_helmet",
    "gold_chestplate": "golden_chestplate",
    "gold_leggings": "golden_leggings",
    "gold_boots": "golden_boots",
    "gold_sword": "golden_sword",
    "gold_horse_armor": "golden_horse_armor",
    "golden_apple": "golden_apple",
}


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


def get_item_resource(item_id: Optional[str]) -> Optional[Dict[str, object]]:
    if not item_id:
        return None
    mapping = _load_item_resource_map()
    return mapping.get(item_id)


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
    textures = decoded.get("textures", {})
    skin_meta = textures.get("SKIN", {}) if isinstance(textures, dict) else {}
    texture_url = skin_meta.get("url") if isinstance(skin_meta, dict) else None
    if isinstance(texture_url, str) and texture_url:
        texture_url = texture_url.replace("http://", "https://")
        if texture_url.startswith("https://textures.minecraft.net/texture/"):
            texture_hash = texture_url.rsplit("/", 1)[-1]
            if texture_hash:
                return f"https://mc-heads.net/head/{texture_hash}/160"
        return texture_url

    profile_id = decoded.get("profileId")
    if isinstance(profile_id, str) and profile_id:
        # Render the head via crafatar for a more 3D appearance.
        return f"https://crafatar.com/renders/head/{profile_id}?overlay&scale=6"

    return None


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


def _color_from_damage(durability: Optional[int]) -> Optional[str]:
    if durability is None:
        return None
    try:
        idx = int(durability) & 15
    except (TypeError, ValueError):
        return None
    if 0 <= idx < len(LEGACY_DYE_COLORS):
        return LEGACY_DYE_COLORS[idx]
    return None


def _build_material_candidates(name: str, durability: Optional[int] = None) -> Iterable[str]:
    normalized = name.lower().replace("minecraft:", "").replace(":", "_")
    normalized = MATERIAL_ALIASES.get(normalized, normalized)
    normalized = normalized.replace(".", "_")

    parts = normalized.split()
    if len(parts) > 1:
        normalized = "_".join(parts)

    base = normalized

    color = _color_from_damage(durability)
    if color:
        color_key = base
        if color_key.endswith("_pane"):
            color_key = color_key  # already handled by map
        if color_key in COLOR_TEMPLATE_MAP:
            for template in COLOR_TEMPLATE_MAP[color_key]:
                yield template.format(color=color)
        elif color_key.endswith("_shulker_box"):
            yield f"block/{color}_shulker_box.png"

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


def _local_asset_path(candidate: str) -> Optional[str]:
    filename = os.path.basename(candidate)
    file_path = os.path.join(FURFSKY_TEXTURES_PATH, filename)
    if os.path.exists(file_path):
        return f"/api/static/{filename}"
    return None


def _material_texture(name: Optional[str], durability: Optional[int] = None) -> Optional[str]:
    if not name:
        return None
    normalized = name
    if isinstance(name, bytes):
        try:
            normalized = name.decode("utf-8")
        except UnicodeDecodeError:
            normalized = str(name)
    try:
        numeric = int(normalized)
    except (TypeError, ValueError):
        numeric = None
    else:
        normalized = LEGACY_ID_ALIASES.get(numeric, str(normalized))

    normalized = MATERIAL_ALIASES.get(str(normalized).lower(), str(normalized))

    for candidate in _build_material_candidates(str(normalized), durability):
        local_path = _local_asset_path(candidate)
        if local_path:
            return local_path

        url = _cached_asset_path(candidate)
        if url:
            return url
    return None


def resolve_item_icon(
    item_id: Optional[str],
    mc_id: Optional[str],
    damage: Optional[int] = None,
) -> Optional[str]:
    """
    Return an HTTPS URL pointing to an icon representing the SkyBlock item.
    Preference order:
        1. Hypixel custom skin texture
        2. Vanilla material texture, using Hypixel material hints/durability
        3. Vanilla material texture derived from the raw mc_id/damage combo
    """
    resource_map = _load_item_resource_map()
    icon_url: Optional[str] = None

    entry = resource_map.get(item_id) if item_id else None
    entry_durability: Optional[int] = None

    if entry:
        icon_url = _decode_skin_url(entry.get("skin"))  # type: ignore[arg-type]
        entry_material = entry.get("material")
        entry_durability = entry.get("durability")
        if not icon_url:
            icon_url = _material_texture(entry_material, entry_durability)

    if not icon_url and mc_id:
        effective_durability = damage if damage is not None else entry_durability
        icon_url = _material_texture(mc_id, effective_durability)

    return icon_url
