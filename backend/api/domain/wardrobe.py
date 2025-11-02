import base64
import binascii
import gzip
import io
import json
import zlib
from typing import Any, Dict, List, Optional

import nbtlib

from .item_textures import resolve_item_icon, get_item_resource

RARITY_KEYWORDS = {
    "COMMON",
    "UNCOMMON",
    "RARE",
    "EPIC",
    "LEGENDARY",
    "MYTHIC",
    "DIVINE",
    "SPECIAL",
    "VERY SPECIAL",
    "SUPREME",
}


def _decode_bytes(data: str) -> Optional[bytes]:
    if not data:
        return None
    try:
        raw = base64.b64decode(data)
    except (ValueError, TypeError):
        return None

    for decoder in (gzip.decompress, zlib.decompress):
        try:
            return decoder(raw)
        except OSError:
            continue
    return raw


def _tag_value(tag: Any) -> Any:
    if tag is None:
        return None
    if hasattr(tag, "value"):
        return tag.value
    if hasattr(tag, "unpack"):
        try:
            return tag.unpack()
        except Exception:
            return tag
    return tag


def _strip_color_codes(text: str) -> str:
    if not text:
        return ""
    out = []
    skip = False
    for ch in text:
        if skip:
            skip = False
            continue
        if ch == "§":
            skip = True
            continue
        out.append(ch)
    return "".join(out).strip()


def _component_to_plain(component: Any) -> str:
    if component is None:
        return ""
    if isinstance(component, str):
        try:
            parsed = json.loads(component)
        except json.JSONDecodeError:
            return _strip_color_codes(component)
        return _component_to_plain(parsed)
    if isinstance(component, (int, float)):
        return str(component)
    if isinstance(component, list):
        return "".join(_component_to_plain(part) for part in component)
    if isinstance(component, dict):
        pieces = []
        if "text" in component:
            pieces.append(_component_to_plain(component["text"]))
        if "translate" in component:
            pieces.append(_component_to_plain(component["translate"]))
        if "extra" in component:
            pieces.append(_component_to_plain(component["extra"]))
        if "color" in component and not pieces:
            pieces.append(str(component["color"]))
        return "".join(pieces)
    return _strip_color_codes(str(component))


def _detect_rarity(extra: Dict[str, Any], lore: List[str]) -> Optional[str]:
    raw_rarity = _tag_value(extra.get("rarity")) if extra else None
    if raw_rarity:
        return str(raw_rarity).upper()

    if lore:
        last_line = _strip_color_codes(lore[-1]).upper()
        for keyword in RARITY_KEYWORDS:
            if keyword in last_line:
                return keyword
    return None


def _extract_leather_color(display: nbtlib.Compound, extra: nbtlib.Compound) -> Optional[str]:
    color_tag = None
    if display and "color" in display:
        color_tag = display.get("color")
    elif extra and "color" in extra:
        color_tag = extra.get("color")

    if color_tag is None:
        return None

    try:
        value = int(_tag_value(color_tag))
    except (TypeError, ValueError):
        return None

    value = max(0, min(value, 0xFFFFFF))
    return f"#{value:06x}"


def _decode_texture_value(encoded: str) -> Optional[str]:
    if not encoded:
        return None
    try:
        decoded = base64.b64decode(encoded)
    except (binascii.Error, ValueError, TypeError):
        return None

    try:
        payload = json.loads(decoded.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
        return None

    profile_id = payload.get("profileId")
    if isinstance(profile_id, str):
        stripped = profile_id.replace("-", "")
        if len(stripped) == 32:
            return f"https://crafatar.com/renders/head/{stripped}?overlay&scale=6"

    textures = payload.get("textures")
    if isinstance(textures, dict):
        skin = textures.get("SKIN")
        if isinstance(skin, dict):
            url = skin.get("url")
            if isinstance(url, str) and url:
                return url.replace("http://", "https://")
    return None


def _extract_extra_texture(extra: nbtlib.Compound) -> Optional[str]:
    if not extra:
        return None

    texture_value = extra.get("texture") or extra.get("Texture")
    if texture_value is not None:
        candidate = _tag_value(texture_value)
        if isinstance(candidate, dict):
            candidate = candidate.get("value")
        if isinstance(candidate, (bytes, bytearray)):
            try:
                candidate = candidate.decode("utf-8")
            except UnicodeDecodeError:
                candidate = ""
        if isinstance(candidate, str):
            decoded = _decode_texture_value(candidate)
            if decoded:
                return decoded

    skin_value = extra.get("skin")
    if isinstance(skin_value, nbtlib.Compound):
        payload = {str(k): _tag_value(v) for k, v in skin_value.items()}
        candidate = payload.get("value") or payload.get("texture")
        if isinstance(candidate, str):
            decoded = _decode_texture_value(candidate)
            if decoded:
                return decoded
        url_candidate = payload.get("url")
        if isinstance(url_candidate, str) and url_candidate:
            return url_candidate.replace("http://", "https://")
    return None


def _extract_skull_icon(tag: nbtlib.Compound) -> Optional[str]:
    if not tag:
        return None

    skull_owner = tag.get("SkullOwner")
    if not isinstance(skull_owner, nbtlib.Compound):
        return None

    properties = skull_owner.get("Properties")
    if isinstance(properties, nbtlib.Compound):
        textures = properties.get("textures")
        if textures:
            for entry in textures:
                value = _tag_value(entry.get("Value") or entry.get("value"))
                if isinstance(value, (bytes, bytearray)):
                    try:
                        value = value.decode("utf-8")
                    except UnicodeDecodeError:
                        continue
                if isinstance(value, str):
                    decoded = _decode_texture_value(value)
                    if decoded:
                        return decoded

    profile_id = _tag_value(skull_owner.get("Id"))
    if isinstance(profile_id, str) and profile_id:
        stripped = profile_id.replace("-", "")
        if len(stripped) == 32:
            return f"https://crafatar.com/renders/head/{stripped}?overlay&scale=6"
    return None


def parse_wardrobe(wardrobe_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Decode the wardrobe NBT payload into a list of slots with plain text metadata.
    """
    if not wardrobe_data:
        return {"items": [], "slots": 0}

    encoded = wardrobe_data.get("data")
    payload = _decode_bytes(encoded)
    if not payload:
        return {"items": [], "slots": 0}

    file = nbtlib.File.parse(io.BytesIO(payload))
    slots: List[Optional[Dict[str, Any]]] = []

    for index, compound in enumerate(file.get("i", [])):
        if not compound or "id" not in compound:
            slots.append(None)
            continue

        item_id_raw = _tag_value(compound.get("id"))
        item_id = str(item_id_raw) if item_id_raw is not None else ""

        count_raw = _tag_value(compound.get("Count", 1))
        try:
            count = int(count_raw)
        except (TypeError, ValueError):
            count = 1

        tag = compound.get("tag") or nbtlib.Compound()
        display = tag.get("display") or nbtlib.Compound()
        extra = tag.get("ExtraAttributes") or nbtlib.Compound()

        name = _component_to_plain(_tag_value(display.get("Name")))
        lore = [
            _component_to_plain(_tag_value(line))
            for line in (display.get("Lore") or [])
        ]

        extra_id_raw = _tag_value(extra.get("id")) if extra else None
        extra_id = str(extra_id_raw) if extra_id_raw else None
        rarity = _detect_rarity(extra, lore)
        leather_color = _extract_leather_color(display, extra)
        if not leather_color:
            resource = get_item_resource(extra_id or item_id)
            color_meta = resource.get("color") if isinstance(resource, dict) else None
            if isinstance(color_meta, str):
                parts = [p.strip() for p in color_meta.split(",") if p.strip()]
                if len(parts) == 3:
                    try:
                        r, g, b = (int(part) for part in parts)
                    except ValueError:
                        pass
                    else:
                        r = max(0, min(r, 255))
                        g = max(0, min(g, 255))
                        b = max(0, min(b, 255))
                        leather_color = f"#{r:02x}{g:02x}{b:02x}"
        damage_raw = _tag_value(compound.get("Damage"))
        try:
            damage = int(damage_raw)
        except (TypeError, ValueError):
            damage = None

        icon_url = resolve_item_icon(extra_id or item_id, item_id or None, damage)
        if not icon_url:
            icon_url = _extract_extra_texture(extra) or _extract_skull_icon(tag)

        slots.append(
            {
                "slot": index,
                "id": extra_id or item_id,
                "mc_id": item_id,
                "name": name or item_id,
                "count": count,
                "rarity": rarity,
                "lore": lore,
                "icon_url": icon_url,
                "leather_color": leather_color,
            }
        )

    return {
        "items": slots,
        "slots": len(slots),
    }
