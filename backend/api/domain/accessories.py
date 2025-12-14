from __future__ import annotations

import io
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

import nbtlib

from .item_textures import (
    TEXTURE_PACKS,
    get_item_resource,
    resolve_item_icon_variants,
)
from .wardrobe import (
    _component_to_plain,
    _component_to_colored,
    _decode_bytes,
    _detect_rarity,
    _extract_extra_texture,
    _extract_leather_color,
    _extract_skull_icon,
    _tag_value,
)

Identifier = Optional[str]

MAGICAL_POWER_BY_RARITY = {
    # Source: Hypixel Wiki (Magical Power) — per-accessory MP by rarity
    "COMMON": 3,
    "UNCOMMON": 5,
    "RARE": 8,
    "EPIC": 12,
    "LEGENDARY": 16,
    "MYTHIC": 22,
    "DIVINE": 22,
    "SPECIAL": 3,
    "VERY SPECIAL": 5,
    "SUPREME": 22,
}

DOUBLE_MAGICAL_POWER_IDS = {
    "HEGEMONY_ARTIFACT",
}

ABICASE_IDS = {
    "ABICASE",
    "ABICASE_PRO",
    "ABICASE_ULTRA",
    "ABICASE_MEGA",
    "ABICASE_XL",
}

RARITY_OVERRIDES = {
    "ABICASE": "SPECIAL",
    "ABICASE_PRO": "SPECIAL",
    "ABICASE_ULTRA": "SPECIAL",
    "ABICASE_MEGA": "SPECIAL",
    "ABICASE_XL": "SPECIAL",
}

FIXED_MAGICAL_POWER_OVERRIDES = {
    # Grants 11 Magical Power when imbued. The in-game value does not depend on rarity.
    "RIFT_PRISM": 11,
}


def _safe_int(value: Any, default: int = 0) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return default
    return default


def _seek_data_string(source: Any) -> Optional[str]:
    if not source:
        return None

    stack: List[Any] = [source]
    seen: Set[int] = set()

    while stack:
        current = stack.pop()
        if isinstance(current, dict):
            obj_id = id(current)
            if obj_id in seen:
                continue
            seen.add(obj_id)

            data_value = current.get("data")
            if isinstance(data_value, str) and len(data_value) > 16:
                return data_value

            for key in (
                "bag",
                "bag_data",
                "talisman_bag",
                "inventory",
                "contents",
                "value",
                "slot",
                "item",
            ):
                nested = current.get(key)
                if isinstance(nested, (dict, list)):
                    stack.append(nested)

            for value in current.values():
                if isinstance(value, (dict, list)):
                    stack.append(value)
        elif isinstance(current, list):
            obj_id = id(current)
            if obj_id in seen:
                continue
            seen.add(obj_id)
            for item in current:
                if isinstance(item, (dict, list)):
                    stack.append(item)

    return None


def _resolve_bag_payload(sources: Iterable[Any]) -> Optional[str]:
    for source in sources:
        encoded = _seek_data_string(source)
        if encoded:
            return encoded
    return None


def _format_identifier(value: Identifier) -> Optional[str]:
    if not value:
        return None
    normalized = str(value).strip()
    if not normalized:
        return None
    return normalized


def _titleize_identifier(value: Identifier) -> Optional[str]:
    normalized = _format_identifier(value)
    if not normalized:
        return None
    return normalized.replace("_", " ").title()


def _normalize_tuning(tuning: Any) -> Dict[str, int]:
    if not isinstance(tuning, dict):
        return {}
    result: Dict[str, int] = {}
    for key, raw in tuning.items():
        label = str(key)
        value = _safe_int(raw, 0)
        if value != 0:
            result[label] = value
    return result


def _normalize_power_stones(power_stones: Any) -> Dict[str, int]:
    if not isinstance(power_stones, dict):
        return {}
    result: Dict[str, int] = {}
    for key, raw in power_stones.items():
        label = str(key)
        value = _safe_int(raw, 0)
        if value:
            result[label] = value
    return result


def _normalize_rarity(rarity: Optional[str]) -> Optional[str]:
    if not rarity:
        return None
    normalized = str(rarity).replace("-", " ").replace("_", " ").strip()
    if not normalized:
        return None
    return " ".join(segment for segment in normalized.upper().split())


def _magical_power_for_item(item_id: Optional[str], rarity: Optional[str]) -> int:
    item_key = (item_id or "").upper()
    if item_key in ABICASE_IDS:
        # Abiphone case gives 1 MP per 2 contacts; contacts handled separately
        return 0
    normalized_rarity = _normalize_rarity(rarity) or _normalize_rarity(RARITY_OVERRIDES.get(item_key)) or ""
    override = FIXED_MAGICAL_POWER_OVERRIDES.get(item_id or "")
    if override is not None:
        return override

    base = MAGICAL_POWER_BY_RARITY.get(normalized_rarity, 0)
    if (item_id or "") in DOUBLE_MAGICAL_POWER_IDS:
        return base * 2
    return base


def _parse_accessory_items(
    encoded: Optional[str],
) -> Tuple[List[Dict[str, Any]], Dict[str, int], Set[str], int]:
    if not encoded:
        return [], {}, set(), 0

    payload = _decode_bytes(encoded)
    if not payload:
        return [], {}, set(), 0

    try:
        file = nbtlib.File.parse(io.BytesIO(payload))
    except Exception:
        return [], {}, set(), 0

    items: List[Dict[str, Any]] = []
    rarity_counts: Dict[str, int] = {}
    unique_ids: Set[str] = set()
    magical_power_total = 0
    counted_ids: Set[str] = set()

    for index, compound in enumerate(file.get("i", [])):
        if not compound or "id" not in compound:
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
        lore_entries = (display.get("Lore") or [])
        lore = [
            _component_to_plain(_tag_value(line))
            for line in lore_entries
        ]
        lore_colored = [
            _component_to_colored(_tag_value(line))
            for line in lore_entries
        ]

        extra_id_raw = _tag_value(extra.get("id")) if extra else None
        extra_id = str(extra_id_raw) if extra_id_raw else None
        raw_rarity = _detect_rarity(extra, lore)
        normalized_rarity = _normalize_rarity(raw_rarity)
        display_rarity = normalized_rarity or raw_rarity
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

        icon_variants = resolve_item_icon_variants(extra_id or item_id, item_id or None, damage)
        fallback_icon = _extract_extra_texture(extra) or _extract_skull_icon(tag)
        if fallback_icon:
            for pack in TEXTURE_PACKS:
                icon_variants.setdefault(pack, fallback_icon)

        icon_url = next(
            (icon_variants.get(pack) for pack in TEXTURE_PACKS if icon_variants.get(pack)),
            None,
        )

        modifier = _titleize_identifier(_tag_value(extra.get("modifier")))
        enrichment = _titleize_identifier(_tag_value(extra.get("talisman_enrichment")))
        recombobulated = _safe_int(_tag_value(extra.get("rarity_upgrades")), 0) > 0
        abiphone_contacts: Optional[int] = None
        if (extra_id or item_id).upper() in ABICASE_IDS:
            for line in lore:
                if "contact" in line.lower():
                    numbers = [int(part) for part in line.split() if part.isdigit()]
                    if numbers:
                        abiphone_contacts = numbers[0]
                        break

        accessory = {
            "slot": index,
            "id": extra_id or item_id,
            "mc_id": item_id,
            "name": name or item_id,
            "count": count,
            "rarity": display_rarity,
            "lore": lore,
            "lore_colored": lore_colored,
            "icon_url": icon_url,
            "icon_variants": {
                pack: url for pack, url in icon_variants.items() if url
            },
            "leather_color": leather_color,
            "modifier": modifier,
            "enrichment": enrichment,
            "recombobulated": recombobulated,
            "abiphone_contacts": abiphone_contacts,
        }

        items.append(accessory)

        if accessory["id"]:
            unique_ids.add(accessory["id"])
        if display_rarity:
            rarity_counts[display_rarity] = rarity_counts.get(display_rarity, 0) + 1

        counted_key = accessory["id"] or accessory["mc_id"]
        if counted_key and counted_key not in counted_ids:
            extra_mp = 0
            if accessory["abiphone_contacts"] is not None and (accessory["id"] or "").upper() in ABICASE_IDS:
                # Abicase: +1 MP per 2 contacts, capped at +10 MP (wiki)
                extra_mp = min(10, max(0, accessory["abiphone_contacts"] // 2))
            magical_power_total += _magical_power_for_item(accessory["id"], display_rarity) + extra_mp
            counted_ids.add(counted_key)

    return items, rarity_counts, unique_ids, magical_power_total


def parse_accessories(member: Dict[str, Any]) -> Dict[str, Any]:
    inventory = member.get("inventory") or {}
    storage = member.get("accessory_bag_storage") or inventory.get("accessory_bag_storage") or {}
    bag_contents = inventory.get("bag_contents") or {}
    talisman_bag = bag_contents.get("talisman_bag") if isinstance(bag_contents, dict) else {}

    sources = [
        storage,
        storage.get("bag_data"),
        storage.get("bag"),
        storage.get("inventory"),
        storage.get("contents"),
        bag_contents.get("talisman_bag"),
        inventory.get("accessory_bag"),
        inventory.get("talisman_bag"),
        member.get("talisman_bag"),
    ]

    encoded = _resolve_bag_payload(sources)
    items, rarity_counts, unique_ids, calculated_magical_power = _parse_accessory_items(encoded)

    bag_upgrades = storage.get("bag_upgrades") if isinstance(storage, dict) else None
    total_slots = 0
    if isinstance(bag_upgrades, dict):
        total_slots = max(
            total_slots,
            _safe_int(bag_upgrades.get("slots"), 0),
            _safe_int(bag_upgrades.get("upgrades"), 0),
        )
    if isinstance(storage, dict):
        total_slots = max(total_slots, _safe_int(storage.get("bag_size"), 0))

    storage_magical_power = _safe_int((storage or {}).get("magical_power") if isinstance(storage, dict) else 0, 0)
    bag_magical_power = _safe_int((talisman_bag or {}).get("magical_power") if isinstance(talisman_bag, dict) else 0, 0)
    storage_highest_mp = _safe_int((storage or {}).get("highest_magical_power") if isinstance(storage, dict) else 0, 0)
    bag_highest_mp = _safe_int((talisman_bag or {}).get("highest_magical_power") if isinstance(talisman_bag, dict) else 0, 0)

    # Use the most generous value provided (server authoritative numbers can include buffs or dungeon doubling).
    magical_power = max(storage_magical_power, bag_magical_power, calculated_magical_power, storage_highest_mp, bag_highest_mp)
    highest_magical_power = max(storage_highest_mp, bag_highest_mp, magical_power)

    selected_power = _format_identifier(storage.get("selected_power") if isinstance(storage, dict) else None)

    unlocked_powers = []
    if isinstance(storage, dict):
        raw_unlocked = storage.get("unlocked_powers")
        if isinstance(raw_unlocked, list):
            unlocked_powers = [
                power for power in (_format_identifier(power) for power in raw_unlocked) if power
            ]

    tuning = _normalize_tuning(storage.get("tuning") if isinstance(storage, dict) else None)
    power_stones = _normalize_power_stones(storage.get("power_stones") if isinstance(storage, dict) else None)

    return {
        "items": items,
        "slots": total_slots or len(items),
        "unique_count": len(unique_ids),
        "rarity_counts": rarity_counts,
        "selected_power": selected_power,
        "selected_power_label": _titleize_identifier(selected_power),
        "magical_power": magical_power,
        "highest_magical_power": highest_magical_power,
        "tuning": tuning,
        "unlocked_powers": unlocked_powers,
        "power_stones": power_stones,
    }
