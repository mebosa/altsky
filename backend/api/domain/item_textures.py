import base64
import json
import logging
import os
import zipfile
from functools import lru_cache
from io import BytesIO
from typing import Dict, Iterable, Iterator, Literal, Optional, Set, Tuple

import requests

try:
    from PIL import Image  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover - optional dependency
    Image = None

LOGGER = logging.getLogger(__name__)
ITEMS_URL = "https://api.hypixel.net/resources/skyblock/items"
ASSET_BASE = (
    "https://raw.githubusercontent.com/InventivetalentDev/minecraft-assets/1.20.1"
    "/assets/minecraft/textures"
)
FURFSKY_TEXTURES_PATH = os.path.join(os.path.dirname(__file__), "furfsky_textures")
FURFSKY_TEXTURES_ZIP = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "furfsky.zip")
)
NEU_ICON_BASE_URL = (
    "https://raw.githubusercontent.com/Moulberry/NotEnoughUpdates-REPO/master/items"
)
NEU_TEXTURE_CACHE = os.path.join(os.path.dirname(__file__), "texture_cache")

SESSION = requests.Session()
_ASSET_CACHE: Dict[str, Optional[str]] = {}
_TALL_TEXTURE_NOTICE_EMITTED = False
_NEU_ICON_MISSING: Set[str] = set()

TexturePack = Literal["furfsky", "vanilla"]
TEXTURE_PACKS: Tuple[TexturePack, ...] = ("furfsky", "vanilla")

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

FURFSKY_ICON_ALIASES: Dict[str, str] = {
    "ranchers_boots": "rancher_boots.png",
    "melon_helmet": "melon.png",
}


def _furfsky_zip_path() -> Optional[str]:
    if os.path.exists(FURFSKY_TEXTURES_ZIP):
        return FURFSKY_TEXTURES_ZIP
    return None


@lru_cache(maxsize=1)
def _furfsky_zip_index() -> Dict[str, str]:
    zip_path = _furfsky_zip_path()
    if not zip_path:
        return {}

    def _entry_score(path: str) -> int:
        lowered = path.lower()
        score = 0
        if "/icons/" in lowered:
            score += 10
        if "/model/" in lowered or "/models/" in lowered:
            score -= 5
        if lowered.endswith("_icon.png"):
            score += 5
        if "/items/" in lowered:
            score += 2
        return score

    try:
        with zipfile.ZipFile(zip_path, "r") as zip_file:
            mapping: Dict[str, str] = {}
            scores: Dict[str, int] = {}
            for entry in zip_file.infolist():
                if entry.is_dir():
                    continue
                if not entry.filename.lower().endswith(".png"):
                    continue
                name = os.path.basename(entry.filename)
                score = _entry_score(entry.filename)
                if name not in mapping or score > scores.get(name, -999):
                    mapping[name] = entry.filename
                    scores[name] = score
    except zipfile.BadZipFile as exc:
        LOGGER.warning("Failed to index FurSky texture pack: %s", exc)
        return {}

    return mapping


def furfsky_texture_exists(filename: str) -> bool:
    if not filename:
        return False

    local_path = os.path.join(FURFSKY_TEXTURES_PATH, filename)
    if os.path.exists(local_path):
        return True

    return filename in _furfsky_zip_index()


def load_furfsky_texture(filename: str) -> Optional[bytes]:
    if not filename:
        return None

    try:
        for root in (FURFSKY_TEXTURES_PATH, NEU_TEXTURE_CACHE):
            if not root:
                continue
            local_path = os.path.join(root, filename)
            if os.path.exists(local_path):
                with open(local_path, "rb") as handle:
                    payload = handle.read()
                return _normalize_texture_payload(payload)

        mapping = _furfsky_zip_index()
        relative = mapping.get(filename)
        zip_path = _furfsky_zip_path()
        if not relative or not zip_path:
            return None

        with zipfile.ZipFile(zip_path, "r") as zip_file:
            payload = zip_file.read(relative)
        return _normalize_texture_payload(payload)
    except (KeyError, OSError, zipfile.BadZipFile) as exc:
        LOGGER.warning("Failed to extract %s from FurSky zip: %s", filename, exc)
    except Exception:  # pragma: no cover - defensive
        LOGGER.exception("Unexpected error while loading FurSky texture %s", filename)

    return None


def _normalize_texture_payload(payload: bytes) -> bytes:
    if not payload or Image is None:
        return payload

    global _TALL_TEXTURE_NOTICE_EMITTED
    try:
        with Image.open(BytesIO(payload)) as image:
            width, height = image.size
            if (
                width <= 0
                or height <= 0
                or height <= width
                or height % width != 0
                or height < width * 2
            ):
                return payload

            frame_height = width
            cropped = image.crop((0, 0, width, frame_height))
            buffer = BytesIO()
            cropped.save(buffer, format="PNG")
            if not _TALL_TEXTURE_NOTICE_EMITTED:
                LOGGER.debug(
                    "Trimmed tall FurSky texture to the first frame (w=%s h=%s)",
                    width,
                    height,
                )
                _TALL_TEXTURE_NOTICE_EMITTED = True
            return buffer.getvalue()
    except Exception:
        LOGGER.debug("Failed to normalize FurSky texture payload", exc_info=True)
        return payload


def _normalize_identifier(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    normalized = str(value).lower()
    normalized = normalized.replace("minecraft:", "")
    for ch in (" ", "-", ":", ".", "'"):
        normalized = normalized.replace(ch, "_")
    while "__" in normalized:
        normalized = normalized.replace("__", "_")
    normalized = normalized.strip("_")
    return normalized or None


def _furfsky_icon_candidates(value: Optional[str]) -> Iterator[str]:
    normalized = _normalize_identifier(value)
    if not normalized:
        return

    yield f"{normalized}.png"

    # Some icons are stored without trailing suffixes; try a few variants.
    suffix_map = {
        "_helmet": ("_head", "_cap"),
        "_chestplate": ("_chest",),
        "_leggings": ("_legs", "_pant"),
        "_boots": ("_feet",),
    }
    for suffix, variants in suffix_map.items():
        if normalized.endswith(suffix):
            stem = normalized[: -len(suffix)]
            for variant in variants:
                yield f"{stem}{variant}.png"


def _furfsky_icon_override(*values: Optional[str]) -> Optional[str]:
    for value in values:
        normalized = _normalize_identifier(value)
        if normalized:
            alias_candidate = FURFSKY_ICON_ALIASES.get(normalized)
            if alias_candidate and furfsky_texture_exists(alias_candidate):
                return f"/api/static/{alias_candidate}"

        for candidate in _furfsky_icon_candidates(value):
            if furfsky_texture_exists(candidate):
                return f"/api/static/{candidate}"
        neu_texture = _ensure_neu_texture(value)
        if neu_texture:
            return f"/api/static/{neu_texture}"
    return None


def _ensure_neu_texture(identifier: Optional[str]) -> Optional[str]:
    normalized = _normalize_identifier(identifier)
    if not normalized:
        return None

    neu_key = normalized.upper()
    if neu_key in _NEU_ICON_MISSING:
        return None

    filename = f"neu_{neu_key}.png"
    os.makedirs(NEU_TEXTURE_CACHE, exist_ok=True)
    local_path = os.path.join(NEU_TEXTURE_CACHE, filename)
    if os.path.exists(local_path):
        return filename

    url = f"{NEU_ICON_BASE_URL}/{neu_key}.png"
    try:
        response = SESSION.get(url, timeout=6)
    except requests.RequestException:
        return None

    if response.status_code != 200 or not response.content:
        _NEU_ICON_MISSING.add(neu_key)
        return None

    try:
        with open(local_path, "wb") as handle:
            handle.write(response.content)
    except OSError:
        return None

    return filename


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
    if furfsky_texture_exists(filename):
        return f"/api/static/{filename}"
    return None


def _material_texture(
    name: Optional[str],
    durability: Optional[int] = None,
    pack: TexturePack = "furfsky",
) -> Optional[str]:
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

    normalized_pack = "vanilla" if str(pack).lower() == "vanilla" else "furfsky"

    for candidate in _build_material_candidates(str(normalized), durability):
        if normalized_pack == "furfsky":
            local_path = _local_asset_path(candidate)
            if local_path:
                return local_path

        url = _cached_asset_path(candidate)
        if url:
            return url
    return None


def _normalize_pack(pack: str) -> TexturePack:
    return "vanilla" if str(pack).lower() == "vanilla" else "furfsky"


def resolve_item_icon_for_pack(
    item_id: Optional[str],
    mc_id: Optional[str],
    damage: Optional[int] = None,
    pack: TexturePack = "furfsky",
) -> Optional[str]:
    """
    Resolve an icon URL for the requested texture pack.
    Preference order:
        1. Hypixel custom skin texture
        2. Pack-specific overrides (FurSky only)
        3. Vanilla material texture, using Hypixel material hints/durability
        4. Vanilla material texture derived from the raw mc_id/damage combo
    """
    normalized_pack = _normalize_pack(pack)
    resource_map = _load_item_resource_map()
    icon_url: Optional[str] = None

    entry = resource_map.get(item_id) if item_id else None
    entry_durability: Optional[int] = None
    entry_material = None
    entry_internal = None

    if entry:
        icon_url = _decode_skin_url(entry.get("skin"))  # type: ignore[arg-type]
        entry_material = entry.get("material")
        entry_durability = entry.get("durability")
        entry_internal = entry.get("internalname")

    # FurSky: try override on internal name first
    if normalized_pack == "furfsky" and icon_url:
        return icon_url

    if normalized_pack == "furfsky":
        override = _furfsky_icon_override(item_id, entry_internal if entry_internal else None)
        if override:
            return override

    if icon_url:
        return icon_url

    icon_url = _material_texture(entry_material, entry_durability, pack=normalized_pack)
    if icon_url:
        return icon_url

    if not mc_id:
        return None

    effective_durability = damage if damage is not None else entry_durability
    if normalized_pack == "furfsky":
        override = _furfsky_icon_override(mc_id)
        if override:
            return override

    return _material_texture(mc_id, effective_durability, pack=normalized_pack)


def resolve_item_icon_variants(
    item_id: Optional[str],
    mc_id: Optional[str],
    damage: Optional[int] = None,
) -> Dict[TexturePack, Optional[str]]:
    variants: Dict[TexturePack, Optional[str]] = {}
    for pack in TEXTURE_PACKS:
        variants[pack] = resolve_item_icon_for_pack(item_id, mc_id, damage, pack=pack)
    return variants


def resolve_item_icon(
    item_id: Optional[str],
    mc_id: Optional[str],
    damage: Optional[int] = None,
) -> Optional[str]:
    return resolve_item_icon_for_pack(item_id, mc_id, damage, pack="furfsky")
