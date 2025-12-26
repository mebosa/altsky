import base64
import binascii
import gzip
import io
import json
import zlib
from typing import Any, Dict, List, Optional

import nbtlib

from .item_textures import (
    TEXTURE_PACKS,
    decode_texture_value,
    get_item_resource,
    resolve_item_icon_variants,
)

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


LEGACY_COLOR_CODES = {
    "black": "0",
    "dark_blue": "1",
    "dark_green": "2",
    "dark_aqua": "3",
    "dark_red": "4",
    "dark_purple": "5",
    "gold": "6",
    "gray": "7",
    "grey": "7",
    "dark_gray": "8",
    "dark_grey": "8",
    "blue": "9",
    "green": "a",
    "aqua": "b",
    "red": "c",
    "light_purple": "d",
    "yellow": "e",
    "white": "f",
}

LEGACY_FORMAT_CODES = {
    "obfuscated": "k",
    "bold": "l",
    "strikethrough": "m",
    "underline": "n",
    "italic": "o",
}


def _component_to_colored(component: Any) -> str:
    if component is None:
        return ""
    if isinstance(component, str):
        try:
            parsed = json.loads(component)
        except json.JSONDecodeError:
            return str(component)
        return _component_to_colored(parsed)
    if isinstance(component, (int, float)):
        return str(component)
    if isinstance(component, list):
        return "".join(_component_to_colored(part) for part in component)
    if isinstance(component, dict):
        pieces = []
        prefix = ""
        color = component.get("color")
        if isinstance(color, str):
            code = LEGACY_COLOR_CODES.get(color.lower())
            if code:
                prefix += f"§{code}"
        for attr, code in LEGACY_FORMAT_CODES.items():
            if component.get(attr):
                prefix += f"§{code}"
        if prefix:
            pieces.append(prefix)
        if "text" in component:
            pieces.append(_component_to_colored(component["text"]))
        if "translate" in component:
            pieces.append(_component_to_colored(component["translate"]))
        if "extra" in component:
            pieces.append(_component_to_colored(component["extra"]))
        if prefix:
            pieces.append("§r")
        return "".join(pieces)
    return str(component)


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


# SkyBlock backpack color name to hex mapping
BACKPACK_COLOR_MAP = {
    'BLACK': '#1D1D21',
    'BLUE': '#3C44AA',
    'BROWN': '#835432',
    'CYAN': '#169C9C',
    'GRAY': '#474F52',
    'GREY': '#474F52',
    'GREEN': '#5E7C16',
    'LIGHT_BLUE': '#3AB3DA',
    'LIGHT_GRAY': '#9D9D97',
    'LIGHT_GREY': '#9D9D97',
    'LIME': '#80C71F',
    'MAGENTA': '#C74EBD',
    'ORANGE': '#F9801D',
    'PINK': '#F38BAA',
    'PURPLE': '#8932B8',
    'RED': '#B02E26',
    'WHITE': '#F9FFFE',
    'YELLOW': '#FED83D',
}


def _extract_leather_color(display: nbtlib.Compound, extra: nbtlib.Compound) -> Optional[str]:
    color_tag = None
    
    # Check display.color (standard leather armor - integer)
    if display and "color" in display:
        color_tag = display.get("color")
        try:
            value = int(_tag_value(color_tag))
            value = max(0, min(value, 0xFFFFFF))
            return f"#{value:06x}"
        except (TypeError, ValueError):
            pass
    
    # Check ExtraAttributes.color (integer)
    if extra and "color" in extra:
        color_tag = extra.get("color")
        try:
            value = int(_tag_value(color_tag))
            value = max(0, min(value, 0xFFFFFF))
            return f"#{value:06x}"
        except (TypeError, ValueError):
            pass
    
    # Check ExtraAttributes.backpack_color (SkyBlock backpacks - string like "BLUE", "RED")
    if extra and "backpack_color" in extra:
        color_name = _tag_value(extra.get("backpack_color"))
        if isinstance(color_name, str):
            color_name = color_name.upper().strip()
            if color_name in BACKPACK_COLOR_MAP:
                return BACKPACK_COLOR_MAP[color_name]

    return None


# Rune textures mapping - each rune type has a unique texture hash from NEU repo
# These are actual textures from NotEnoughUpdates-REPO
RUNE_TEXTURES = {
    "ANTLERS": "3c3b15ff40b381d6084f677c7864610c53b25a6aaa840696fcdc0da630b35f37",
    "AXE_FADING_GREEN": "d56d420b2b904debd7be3a157d330e17264f1cf302a2d2022b9e46538653b8b0",
    "AXE_FADING_WHITE": "771cadef7545fcb881a4eebaaec93ef2fa5f1e0e99b60d26805cf9c60113f49",
    "AXE_SOUL_SLICE": "5911d19c29f29a11a2a2a231d2dafaaed078cfa78a1f4bd94ef5625b076ebcb7",
    "BARK_TUNES": "d56d1157226e10c63dff08cfb59104873c9315dba128ef62e18a27d4dba04a42",
    "BITE": "43a1ad4fcc42fb63c681328e42d63c83ca193b333af2a426728a25a8cc600692",
    "BLAZING_SUN": "7e817ce13016e9c3d90ca9d3d46c74efd81ad1c210c177a3cddb2cd4954fcb0e",
    "BLOOD_2": "e02677053dc54245dac4b399d14aae21ee71a010bd9c336c8ecee1a0dbe8f58b",
    "BLOOMING": "1f9203e46ad838b21c806c787dbba63cfed62849a82cd7e7233e5b44af19d8f8",
}


def _extract_rune_texture(extra: nbtlib.Compound) -> Optional[str]:
    """Extract rune texture from ExtraAttributes if this is a rune item."""
    if not extra:
        return None
    
    # Check if this item has runes data
    runes = extra.get("runes")
    if not runes:
        return None
    
    # Runes is a compound with rune_name: level pairs
    # e.g., {"BLOOD": 3} or {"SNAKE": 1}
    if isinstance(runes, nbtlib.Compound):
        for rune_name in runes:
            rune_name_str = str(rune_name).upper()
            # Try to get texture from our mapping
            if rune_name_str in RUNE_TEXTURES:
                texture_hash = RUNE_TEXTURES[rune_name_str]
                return f"https://mc-heads.net/head/{texture_hash}"
            # If not in our mapping, the item's own texture will be used via _extract_extra_texture
            return None
    
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
            decoded = decode_texture_value(candidate)
            if decoded:
                return decoded

    skin_value = extra.get("skin")
    if isinstance(skin_value, nbtlib.Compound):
        payload = {str(k): _tag_value(v) for k, v in skin_value.items()}
        candidate = payload.get("value") or payload.get("texture")
        if isinstance(candidate, str):
            decoded = decode_texture_value(candidate)
            if decoded:
                return decoded
        url_candidate = payload.get("url")
        if isinstance(url_candidate, str) and url_candidate:
            url_candidate = url_candidate.replace("http://", "https://")
            # Convert raw texture URL to mc-heads rendered head
            if url_candidate.startswith("https://textures.minecraft.net/texture/"):
                texture_hash = url_candidate.rsplit("/", 1)[-1]
                if texture_hash:
                    return f"https://mc-heads.net/head/{texture_hash}"
            return url_candidate
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
                    decoded = decode_texture_value(value)
                    if decoded:
                        return decoded

    profile_id = _tag_value(skull_owner.get("Id"))
    if isinstance(profile_id, str) and profile_id:
        stripped = profile_id.replace("-", "")
        if len(stripped) == 32:
            return f"https://crafatar.com/renders/head/{stripped}?overlay&scale=6"
    return None


def _extract_skin_url(tag: nbtlib.Compound) -> Optional[str]:
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
                    decoded = decode_texture_value(value, prefer_raw_skin=True)
                    if decoded:
                        return decoded
    return None


def _parse_inventory_items(data: Optional[Dict[str, Any]]) -> List[Optional[Dict[str, Any]]]:
    if not data:
        return []

    encoded = data.get("data")
    payload = _decode_bytes(encoded) if isinstance(encoded, str) else None
    if not payload:
        return []

    try:
        file = nbtlib.File.from_fileobj(io.BytesIO(payload))
    except Exception:
        return []

    slots: List[Optional[Dict[str, Any]]] = []
    for index, compound in enumerate(file.get("i", [])):
        slot_index = index
        if compound:
            slot_tag = compound.get("Slot") if isinstance(compound, nbtlib.Compound) else None
            if slot_tag is None and isinstance(compound, nbtlib.Compound):
                slot_tag = compound.get("slot")
            if slot_tag is not None:
                try:
                    slot_index = int(_tag_value(slot_tag))
                except (TypeError, ValueError):
                    slot_index = index
        if slot_index < 0:
            slot_index = index

        item = _parse_compound_item(compound, slot_index)
        if slot_index >= len(slots):
            slots.extend([None] * (slot_index + 1 - len(slots)))
        slots[slot_index] = item
    return slots


def _parse_compound_item(
    compound: Optional[nbtlib.Compound], index: int
) -> Optional[Dict[str, Any]]:
    if not compound or "id" not in compound:
        return None

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

    # Filter out "SkyBlock Menu" which is a client-side menu item
    if name and "SkyBlock Menu" in name:
        return None

    # Filter out likely placeholder items
    # 7: Bedrock, 166: Barrier - these are never valid player items
    if item_id in {"7", "166"}:
        return None

    # Filter out Stone (1) and Glass Panes (160, 102) if they appear to be placeholders
    # Placeholders often have no custom name (or empty name) and no lore
    if item_id in {"1", "160", "102"}:
        has_custom_name = bool(name and name.strip())
        has_lore = bool(display.get("Lore"))
        has_extra = bool(extra)
        
        if not has_custom_name and not has_lore and not has_extra:
            return None

    lore_entries = display.get("Lore") or []
    lore = [_component_to_plain(_tag_value(line)) for line in lore_entries]
    lore_colored = [_component_to_colored(_tag_value(line)) for line in lore_entries]

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

    # For skull items (id 397 with damage 3), prioritize extracting textures from NBT first
    # These have their textures in SkullOwner, not from material lookup
    is_player_head = (item_id == "397" and damage == 3) or item_id == "minecraft:player_head"
    
    # Try rune texture first (for rune items), then fall back to extra texture or skull icon
    skull_texture = _extract_rune_texture(extra) or _extract_extra_texture(extra) or _extract_skull_icon(tag)
    
    if is_player_head and skull_texture:
        # For player heads, always use the skull texture, don't even try material lookup
        icon_variants = {pack: skull_texture for pack in TEXTURE_PACKS}
    else:
        icon_variants = resolve_item_icon_variants(extra_id or item_id, item_id or None, damage)
        if skull_texture:
            for pack in TEXTURE_PACKS:
                icon_variants.setdefault(pack, skull_texture)

    icon_url = next(
        (icon_variants.get(pack) for pack in TEXTURE_PACKS if icon_variants.get(pack)),
        None,
    )

    skin_url = _extract_skin_url(tag)

    # Extract extra attributes for networth calculation
    extra_attributes = {}
    if extra:
        for key in extra:
            val = _tag_value(extra.get(key))
            if val is not None:
                # Handle nested compounds/lists
                if isinstance(val, dict):
                    extra_attributes[key] = val
                elif isinstance(val, list):
                    extra_attributes[key] = [
                        _tag_value(v) if hasattr(v, '__iter__') else v for v in val
                    ]
                else:
                    extra_attributes[key] = val

    return {
        "slot": index,
        "id": extra_id or item_id,
        "mc_id": item_id,
        "name": name or item_id,
        "count": count,
        "rarity": rarity,
        "lore": lore,
        "lore_colored": lore_colored,
        "icon_url": icon_url,
        "icon_variants": {pack: url for pack, url in icon_variants.items() if url},
        "leather_color": leather_color,
        "skin_url": skin_url,
        "extra_attributes": extra_attributes,
    }


def _normalize_equipped_items(
    armor_items: List[Optional[Dict[str, Any]]],
) -> List[Optional[Dict[str, Any]]]:
    """
    Hypixel stores inv_armor as [boots, leggings, chestplate, helmet].
    Reorder into [helmet, chestplate, leggings, boots] for UI display.
    """
    if not armor_items:
        return []

    order_map = {3: 0, 2: 1, 1: 2, 0: 3}
    normalized: List[Optional[Dict[str, Any]]] = [None, None, None, None]
    for index, item in enumerate(armor_items):
        target = order_map.get(index)
        if target is None:
            continue
        normalized[target] = item
    return normalized


def parse_wardrobe(
    wardrobe_data: Dict[str, Any],
    armor_data: Optional[Dict[str, Any]] = None,
    equipped_slot: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Decode the wardrobe NBT payload into a list of slots with plain text metadata
    and capture the actively equipped armor from inv_armor if available.
    """
    slots = _parse_inventory_items(wardrobe_data)
    armor_items = _parse_inventory_items(armor_data) if armor_data else []
    equipped_items = _normalize_equipped_items(armor_items) if armor_items else []
    if equipped_items and not any(equipped_items):
        equipped_items = []

    # If we have an equipped slot and equipped items, ensure they appear in the wardrobe slots
    # if those slots are currently empty.
    if equipped_slot is not None and equipped_items:
        # equipped_slot is 1-based index of the set
        set_index = equipped_slot - 1
        if set_index >= 0:
            bank_index = set_index // 9
            col_index = set_index % 9
            base_slot = bank_index * 36 + col_index

            # Indices for helmet, chestplate, leggings, boots
            indices = [base_slot, base_slot + 9, base_slot + 18, base_slot + 27]

            # Ensure slots list is large enough
            max_idx = max(indices)
            if len(slots) <= max_idx:
                slots.extend([None] * (max_idx - len(slots) + 1))

            for i, slot_idx in enumerate(indices):
                if i < len(equipped_items) and equipped_items[i]:
                    # Only fill if empty. If it's equipped, the item in wardrobe might be missing.
                    if slots[slot_idx] is None:
                        # We need to clone the item and set the correct slot index
                        item = equipped_items[i].copy()
                        item["slot"] = slot_idx
                        slots[slot_idx] = item

    return {
        "items": slots,
        "slots": len(slots),
        "equipped_items": equipped_items,
    }
