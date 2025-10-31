import base64
import gzip
import io
import json
import zlib
from typing import Any, Dict, List, Optional

import nbtlib

from .item_textures import resolve_item_icon

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
    if hasattr(tag, "value"):
        return tag.value
    return tag


def _strip_color_codes(text: str) -> str:
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

        item_id = str(_tag_value(compound.get("id")))
        count = int(_tag_value(compound.get("Count", 1)))
        tag = compound.get("tag") or nbtlib.Compound()
        display = tag.get("display") or nbtlib.Compound()
        extra = tag.get("ExtraAttributes") or nbtlib.Compound()

        name = _component_to_plain(_tag_value(display.get("Name")))
        lore = [
            _component_to_plain(_tag_value(line))
            for line in (display.get("Lore") or [])
        ]

        extra_id = _tag_value(extra.get("id")) if extra else None
        rarity = _detect_rarity(extra, lore)
        leather_color = _extract_leather_color(display, extra)

        slots.append(
            {
                "slot": index,
                "id": str(extra_id or item_id),
                "mc_id": item_id,
                "name": name or item_id,
                "count": count,
                "rarity": rarity,
                "lore": lore,
                "icon_url": resolve_item_icon(str(extra_id or item_id), item_id),
                "leather_color": leather_color,
            }
        )

    return {
        "items": slots,
        "slots": len(slots),
    }
