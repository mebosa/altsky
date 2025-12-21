from __future__ import annotations

import io
import gzip
import logging
import time
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

import nbtlib
import requests

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

LOGGER = logging.getLogger(__name__)

Identifier = Optional[str]

HYPIXEL_ITEM_URL = "https://api.hypixel.net/resources/skyblock/items"
LOWEST_BIN_URL = "https://moulberry.codes/lowestbin.json"
_ACCESSORY_CATALOG: List[Dict[str, Any]] = []
_ACCESSORY_CATALOG_FETCHED_AT = 0.0
_ACCESSORY_CATALOG_TTL_SECONDS = 60 * 60  # 1 hour
_LOWEST_BIN_CACHE: Dict[str, int] = {}
_LOWEST_BIN_FETCHED_AT = 0.0
_LOWEST_BIN_TTL_SECONDS = 10 * 60  # 10 minutes

# Static upgrade chains (ported from SkyCrypt/SkyHelper + manual additions)
ACCESSORY_UPGRADES: List[List[str]] = [
    ["WOLF_TALISMAN", "WOLF_RING"],
    ["POTION_AFFINITY_TALISMAN", "RING_POTION_AFFINITY", "ARTIFACT_POTION_AFFINITY"],
    ["FEATHER_TALISMAN", "FEATHER_RING", "FEATHER_ARTIFACT"],
    ["SEA_CREATURE_TALISMAN", "SEA_CREATURE_RING", "SEA_CREATURE_ARTIFACT"],
    ["HEALING_TALISMAN", "HEALING_RING"],
    ["CANDY_TALISMAN", "CANDY_RING", "CANDY_ARTIFACT", "CANDY_RELIC"],
    ["INTIMIDATION_TALISMAN", "INTIMIDATION_RING", "INTIMIDATION_ARTIFACT", "INTIMIDATION_RELIC"],
    ["SPIDER_TALISMAN", "SPIDER_RING", "SPIDER_ARTIFACT"],
    ["RUNEBLADE_TALISMAN", "RUNEBLADE_RING", "RUNEBLADE_ARTIFACT"],
    ["RED_CLAW_TALISMAN", "RED_CLAW_RING", "RED_CLAW_ARTIFACT"],
    ["HUNTER_TALISMAN", "HUNTER_RING"],
    ["ZOMBIE_TALISMAN", "ZOMBIE_RING", "ZOMBIE_ARTIFACT"],
    ["BAT_TALISMAN", "BAT_RING", "BAT_ARTIFACT"],
    ["SPEED_TALISMAN", "SPEED_RING", "SPEED_ARTIFACT"],
    ["PERSONAL_COMPACTOR_4000", "PERSONAL_COMPACTOR_5000", "PERSONAL_COMPACTOR_6000", "PERSONAL_COMPACTOR_7000"],
    ["PERSONAL_DELETOR_4000", "PERSONAL_DELETOR_5000", "PERSONAL_DELETOR_6000", "PERSONAL_DELETOR_7000"],
    ["SCARF_STUDIES", "SCARF_THESIS", "SCARF_GRIMOIRE"],
    ["CAT_TALISMAN", "LYNX_TALISMAN", "CHEETAH_TALISMAN"],
    ["SHADY_RING", "CROOKED_ARTIFACT", "SEAL_OF_THE_FAMILY"],
    ["TREASURE_TALISMAN", "TREASURE_RING", "TREASURE_ARTIFACT"],
    [
        "BEASTMASTER_CREST_COMMON",
        "BEASTMASTER_CREST_UNCOMMON",
        "BEASTMASTER_CREST_RARE",
        "BEASTMASTER_CREST_EPIC",
        "BEASTMASTER_CREST_LEGENDARY",
    ],
    [
        "RAGGEDY_SHARK_TOOTH_NECKLACE",
        "DULL_SHARK_TOOTH_NECKLACE",
        "HONED_SHARK_TOOTH_NECKLACE",
        "SHARP_SHARK_TOOTH_NECKLACE",
        "RAZOR_SHARP_SHARK_TOOTH_NECKLACE",
    ],
    ["BAT_PERSON_TALISMAN", "BAT_PERSON_RING", "BAT_PERSON_ARTIFACT"],
    ["LUCKY_HOOF", "ETERNAL_HOOF"],
    ["WITHER_ARTIFACT", "WITHER_RELIC"],
    ["WEDDING_RING_0", "WEDDING_RING_2", "WEDDING_RING_4", "WEDDING_RING_7", "WEDDING_RING_9"],
    ["CAMPFIRE_TALISMAN_1", "CAMPFIRE_TALISMAN_4", "CAMPFIRE_TALISMAN_8", "CAMPFIRE_TALISMAN_13", "CAMPFIRE_TALISMAN_21"],
    ["JERRY_TALISMAN_GREEN", "JERRY_TALISMAN_BLUE", "JERRY_TALISMAN_PURPLE", "JERRY_TALISMAN_GOLDEN"],
    ["TITANIUM_TALISMAN", "TITANIUM_RING", "TITANIUM_ARTIFACT", "TITANIUM_RELIC"],
    ["BAIT_RING", "SPIKED_ATROCITY"],
    [
        "MASTER_SKULL_TIER_1",
        "MASTER_SKULL_TIER_2",
        "MASTER_SKULL_TIER_3",
        "MASTER_SKULL_TIER_4",
        "MASTER_SKULL_TIER_5",
        "MASTER_SKULL_TIER_6",
        "MASTER_SKULL_TIER_7",
    ],
    ["SOULFLOW_PILE", "SOULFLOW_BATTERY", "SOULFLOW_SUPERCELL"],
    ["ENDER_ARTIFACT", "ENDER_RELIC"],
    ["POWER_TALISMAN", "POWER_RING", "POWER_ARTIFACT", "POWER_RELIC"],
    ["BINGO_TALISMAN", "BINGO_RING", "BINGO_ARTIFACT", "BINGO_RELIC"],
    ["BURSTSTOPPER_TALISMAN", "BURSTSTOPPER_ARTIFACT"],
    ["ODGERS_BRONZE_TOOTH", "ODGERS_SILVER_TOOTH", "ODGERS_GOLD_TOOTH", "ODGERS_DIAMOND_TOOTH"],
    ["GREAT_SPOOK_TALISMAN", "GREAT_SPOOK_RING", "GREAT_SPOOK_ARTIFACT"],
    ["DRACONIC_TALISMAN", "DRACONIC_RING", "DRACONIC_ARTIFACT"],
    ["BURNING_KUUDRA_CORE", "FIERY_KUUDRA_CORE", "INFERNAL_KUUDRA_CORE"],
    ["VACCINE_TALISMAN", "VACCINE_RING", "VACCINE_ARTIFACT"],
    ["WHITE_GIFT_TALISMAN", "GREEN_GIFT_TALISMAN", "BLUE_GIFT_TALISMAN", "PURPLE_GIFT_TALISMAN", "GOLD_GIFT_TALISMAN"],
    ["GLACIAL_TALISMAN", "GLACIAL_RING", "GLACIAL_ARTIFACT"],
    ["CROPIE_TALISMAN", "SQUASH_RING", "FERMENTO_ARTIFACT"],
    ["KUUDRA_FOLLOWER_ARTIFACT", "KUUDRA_FOLLOWER_RELIC"],
    ["AGARIMOO_TALISMAN", "AGARIMOO_RING", "AGARIMOO_ARTIFACT"],
    ["BLOOD_DONOR_TALISMAN", "BLOOD_DONOR_RING", "BLOOD_DONOR_ARTIFACT"],
    ["LUSH_TALISMAN", "LUSH_RING", "LUSH_ARTIFACT"],
    ["ANITA_TALISMAN", "ANITA_RING", "ANITA_ARTIFACT"],
    ["PESTHUNTER_BADGE", "PESTHUNTER_RING", "PESTHUNTER_ARTIFACT"],
    # Seasonal chocolate upgrades (single chain)
    ["NIBBLE_CHOCOLATE_STICK", "SMOOTH_CHOCOLATE_BAR", "RICH_CHOCOLATE_CHUNK", "GANACHE_CHOCOLATE_SLAB", "PRESTIGE_CHOCOLATE_REALM"],
    ["COIN_TALISMAN", "RING_OF_COINS", "ARTIFACT_OF_COINS", "RELIC_OF_COINS"],
    ["SCAVENGER_TALISMAN", "SCAVENGER_RING", "SCAVENGER_ARTIFACT"],
    ["EMERALD_RING", "EMERALD_ARTIFACT"],
    ["MINERAL_TALISMAN", "GLOSSY_MINERAL_TALISMAN"],
    # Aquarium bowls
    ["SMALL_FISH_BOWL", "MEDIUM_FISH_BOWL", "LARGE_FISH_BOWL", "MINI_FISH_BOWL"],
    # Anguish line
    ["ANGUISH_TALISMAN", "ANGUISH_RING", "ANGUISH_ARTIFACT"],
    # Haste line
    ["HASTE_RING", "HASTE_ARTIFACT"],
    # Moonglade line
    ["MOONGLADE_RING", "MOONGLADE_ARTIFACT"],
]

# Items that should NOT be treated as upgrade chains (variants are equivalent)
EXCLUDED_CHAIN_IDS: Set[str] = {
    "PIGGY_BANK",
    "CRACKED_PIGGY_BANK",
    "BROKEN_PIGGY_BANK",
}

ACCESSORY_ALIASES: Dict[str, List[str]] = {
    "WEDDING_RING_0": ["WEDDING_RING_1"],
    "WEDDING_RING_2": ["WEDDING_RING_3"],
    "WEDDING_RING_4": ["WEDDING_RING_5", "WEDDING_RING_6"],
    "WEDDING_RING_7": ["WEDDING_RING_8"],
    "CAMPFIRE_TALISMAN_1": ["CAMPFIRE_TALISMAN_2", "CAMPFIRE_TALISMAN_3"],
    "CAMPFIRE_TALISMAN_4": ["CAMPFIRE_TALISMAN_5", "CAMPFIRE_TALISMAN_6", "CAMPFIRE_TALISMAN_7"],
    "CAMPFIRE_TALISMAN_8": [
        "CAMPFIRE_TALISMAN_9",
        "CAMPFIRE_TALISMAN_10",
        "CAMPFIRE_TALISMAN_11",
        "CAMPFIRE_TALISMAN_12",
    ],
    "CAMPFIRE_TALISMAN_13": [
        "CAMPFIRE_TALISMAN_14",
        "CAMPFIRE_TALISMAN_15",
        "CAMPFIRE_TALISMAN_16",
        "CAMPFIRE_TALISMAN_17",
        "CAMPFIRE_TALISMAN_18",
        "CAMPFIRE_TALISMAN_19",
        "CAMPFIRE_TALISMAN_20",
    ],
    "CAMPFIRE_TALISMAN_21": [
        "CAMPFIRE_TALISMAN_22",
        "CAMPFIRE_TALISMAN_23",
        "CAMPFIRE_TALISMAN_24",
        "CAMPFIRE_TALISMAN_25",
        "CAMPFIRE_TALISMAN_26",
        "CAMPFIRE_TALISMAN_27",
        "CAMPFIRE_TALISMAN_28",
        "CAMPFIRE_TALISMAN_29",
    ],
    "PARTY_HAT_CRAB": ["PARTY_HAT_CRAB_ANIMATED", "PARTY_HAT_SLOTH", "BALLOON_HAT_2024"],
    "PIGGY_BANK": ["BROKEN_PIGGY_BANK", "CRACKED_PIGGY_BANK"],
    "DANTE_TALISMAN": ["DANTE_RING"],
}

ACCESSORY_ALIAS_TO_CANONICAL = {
    alias: canonical for canonical, aliases in ACCESSORY_ALIASES.items() for alias in aliases
}

RARITY_ORDER = (
    "DIVINE",
    "SUPREME",
    "MYTHIC",
    "LEGENDARY",
    "VERY SPECIAL",
    "EPIC",
    "RARE",
    "UNCOMMON",
    "SPECIAL",
    "COMMON",
    "BASIC",
    "ADMIN",
)
RARITY_PRIORITY = {value: index for index, value in enumerate(RARITY_ORDER)}

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

# Known theoretical max MP as of current accessory catalog.
MAGICAL_POWER_MAX_OVERRIDE = 1935

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


def _normalize_accessory_id(item_id: Optional[str]) -> Optional[str]:
    if not item_id:
        return None
    normalized = str(item_id).strip().upper()
    normalized = normalized.replace("-", "_").replace(" ", "_")
    while "__" in normalized:
        normalized = normalized.replace("__", "_")
    return ACCESSORY_ALIAS_TO_CANONICAL.get(normalized, normalized)


def _load_accessory_catalog() -> List[Dict[str, Any]]:
    """
    Fetch and cache the Hypixel accessory catalog. Only minimal fields are kept to
    reduce payload size.
    """
    global _ACCESSORY_CATALOG, _ACCESSORY_CATALOG_FETCHED_AT
    now = time.time()
    if _ACCESSORY_CATALOG and now - _ACCESSORY_CATALOG_FETCHED_AT < _ACCESSORY_CATALOG_TTL_SECONDS:
        return _ACCESSORY_CATALOG

    try:
        response = requests.get(HYPIXEL_ITEM_URL, timeout=6)
        response.raise_for_status()
        body = response.json() or {}
        items = body.get("items") or []
    except requests.RequestException as exc:
        LOGGER.warning("Failed to fetch Hypixel accessory catalog: %s", exc)
        return _ACCESSORY_CATALOG
    except ValueError:
        LOGGER.warning("Failed to parse Hypixel accessory catalog response")
        return _ACCESSORY_CATALOG

    catalog: List[Dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict) or item.get("category") != "ACCESSORY":
            continue
        item_id = item.get("id")
        if not item_id:
            continue
        normalized_id = _normalize_accessory_id(item_id)
        if not normalized_id:
            continue
        if normalized_id != str(item_id).upper():
            continue
        name = item.get("name") or str(item_id).replace("_", " ").title()
        tier = _normalize_rarity(item.get("tier"))
        catalog.append(
            {
                "id": normalized_id,
                "name": name,
                "tier": tier,
            }
        )

    if catalog:
        _ACCESSORY_CATALOG = catalog
        _ACCESSORY_CATALOG_FETCHED_AT = now

    return _ACCESSORY_CATALOG


def _compute_missing_accessories(accessories: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int, Set[str]]:
    """
    Determine which accessories from the Hypixel catalog are not present in the
    player's bag. Returns the missing list, total catalog size, and owned ids set.
    """
    catalog = _load_accessory_catalog()
    if not catalog:
        return [], 0, set()

    owned_ids: Set[str] = set()
    for accessory in accessories:
        for key in ("id", "mc_id"):
            raw = accessory.get(key)
            normalized = _normalize_accessory_id(raw)
            if normalized:
                owned_ids.add(normalized)

    missing = [item for item in catalog if item["id"].upper() not in owned_ids]
    missing.sort(
        key=lambda item: (
            RARITY_PRIORITY.get((item.get("tier") or "").upper(), len(RARITY_PRIORITY)),
            item.get("name") or item.get("id"),
        )
    )

    # Enrich with icon hints from item resources
    enriched: List[Dict[str, Any]] = []
    for item in missing:
        resource = get_item_resource(item.get("id"))
        mc_id = None
        damage = None
        if isinstance(resource, dict):
            mc_id = resource.get("material")
            damage = resource.get("durability")

        icon_variants = resolve_item_icon_variants(item.get("id"), mc_id, damage)
        icon_url = next(
            (icon_variants.get(pack) for pack in TEXTURE_PACKS if icon_variants.get(pack)),
            None,
        )

        enriched.append(
            {
                **item,
                "mc_id": mc_id,
                "damage": damage,
                "icon_variants": icon_variants,
                "icon_url": icon_url,
            }
        )

    return enriched, len(catalog), owned_ids


def _collapse_missing_by_chain(
    missing: List[Dict[str, Any]],
    owned_ids: Set[str],
) -> List[Dict[str, Any]]:
    """
    From each upgrade chain, keep only the highest tier that is not owned.
    If a higher tier is owned, lower tiers are dropped.
    """
    upgrade_index = _build_upgrade_index()
    missing_map = {_normalize_accessory_id(item.get("id")) or str(item.get("id") or "").upper(): item for item in missing}
    chains_seen: Set[Tuple[str, ...]] = set()
    output: List[Dict[str, Any]] = []

    for item_id, item in list(missing_map.items()):
        chain = None if item_id in EXCLUDED_CHAIN_IDS else upgrade_index.get(item_id)
        if not chain:
            output.append(item)
            continue

        chain_key = tuple(chain)
        if chain_key in chains_seen:
            continue
        chains_seen.add(chain_key)

        # If the highest tier is already owned, nothing in this chain is missing.
        owned_positions = [idx for idx, cid in enumerate(chain) if cid.upper() in owned_ids]
        if owned_positions and max(owned_positions) == len(chain) - 1:
            continue

        # Determine highest missing tier in this chain
        target_id = None
        for cid in reversed(chain):
            cid_upper = cid.upper()
            if cid_upper in owned_ids:
                continue
            if cid_upper in missing_map:
                target_id = cid_upper
                break
        if target_id and target_id in missing_map:
            output.append(missing_map[target_id])

    return output


def _load_lowest_bin_prices() -> Dict[str, int]:
    """
    Fetches lowest BIN prices (community cache) with a short TTL.
    """
    global _LOWEST_BIN_CACHE, _LOWEST_BIN_FETCHED_AT
    now = time.time()
    if _LOWEST_BIN_CACHE and now - _LOWEST_BIN_FETCHED_AT < _LOWEST_BIN_TTL_SECONDS:
        return _LOWEST_BIN_CACHE

    try:
        response = requests.get(LOWEST_BIN_URL, timeout=6)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, dict):
            # Normalize keys to upper for matching
            _LOWEST_BIN_CACHE = {str(k).upper(): int(v) for k, v in data.items() if isinstance(v, (int, float))}
            _LOWEST_BIN_FETCHED_AT = now
            return _LOWEST_BIN_CACHE
    except requests.RequestException as exc:
        LOGGER.warning("Failed to fetch lowest BIN prices: %s", exc)
    except ValueError:
        LOGGER.warning("Failed to parse lowest BIN prices")

    return _LOWEST_BIN_CACHE


def _build_upgrade_index() -> Dict[str, List[str]]:
    """
    Creates a mapping of accessory id -> its upgrade chain.
    """
    index: Dict[str, List[str]] = {}
    for chain in ACCESSORY_UPGRADES:
        for item_id in chain:
            index[item_id] = chain
    return index


def _compute_max_magical_power() -> int:
    """
    Computes the theoretical maximum Magical Power based on the accessory catalog and upgrade chains.
    """
    if MAGICAL_POWER_MAX_OVERRIDE:
        return MAGICAL_POWER_MAX_OVERRIDE

    catalog = _load_accessory_catalog()
    if not catalog:
        return 0

    catalog_map = {str(item.get("id") or "").upper(): item for item in catalog}
    upgrade_index = _build_upgrade_index()

    highest_chain_ids: Set[str] = set()
    for chain in ACCESSORY_UPGRADES:
        for cid in reversed(chain):
            cid_upper = cid.upper()
            if cid_upper in catalog_map:
                highest_chain_ids.add(cid_upper)
                break

    total = 0
    for item_id, item in catalog_map.items():
        if not item_id:
            continue
        if item_id in highest_chain_ids:
            total += _magical_power_for_item(item_id, item.get("tier"))
            continue
        if item_id in upgrade_index:
            continue
        total += _magical_power_for_item(item_id, item.get("tier"))

    return total


def _classify_missing_accessories(
    missing: List[Dict[str, Any]],
    owned_ids: Set[str],
) -> Tuple[List[Dict[str, Any]], int]:
    """
    Adds classification and price/MP ratio to missing accessories.
    """
    prices = _load_lowest_bin_prices()
    upgrade_index = _build_upgrade_index()

    enriched: List[Dict[str, Any]] = []

    for item in missing:
        item_id = item.get("id") or ""
        rarity = item.get("tier")
        base_id = _normalize_accessory_id(item_id) or str(item_id).upper()
        chain = None if base_id in EXCLUDED_CHAIN_IDS else upgrade_index.get(base_id)

        category = "new"
        upgrade_from: Optional[str] = None
        if chain:
            # If any lower tier exists in inventory, treat as upgrade
            chain_pos = chain.index(base_id)
            lower_tiers = [cid for cid in chain[:chain_pos] if cid.upper() in owned_ids]
            if lower_tiers:
                category = "upgrade"
                upgrade_from = lower_tiers[-1].upper()
            # If a higher tier is already owned, skip recommending this lower tier
            higher_tiers = set(chain[chain_pos + 1 :])
            if owned_ids.intersection(higher_tiers):
                continue

        raw_price = prices.get(base_id)
        price = int(raw_price) if isinstance(raw_price, (int, float)) and raw_price > 0 else None
        mp = MAGICAL_POWER_BY_RARITY.get(_normalize_rarity(rarity) or "", 0)
        price_per_mp: Optional[float] = None
        mp_per_coin: Optional[float] = None
        raw_upgrade_price = prices.get(upgrade_from) if upgrade_from else None
        upgrade_from_price = (
            int(raw_upgrade_price)
            if isinstance(raw_upgrade_price, (int, float)) and raw_upgrade_price > 0
            else None
        )
        upgrade_mp_gain = mp
        effective_cost: Optional[int] = None
        if price is not None:
            if upgrade_from and upgrade_from_price is not None:
                effective_cost = max(0, price - upgrade_from_price)
            else:
                effective_cost = price
        if effective_cost and mp:
            price_per_mp = effective_cost / mp
            mp_per_coin = mp / effective_cost

        enriched.append(
            {
                **item,
                "category": category,
                "price": price,
                "magical_power": mp,
                "price_per_mp": price_per_mp,
                "mp_per_coin": mp_per_coin,
                "upgrade_from": upgrade_from,
                "upgrade_sell_price": upgrade_from_price if upgrade_from else None,
                "upgrade_buy_price": price if price else None,
                "upgrade_net_cost": effective_cost if upgrade_from else price,
                "upgrade_mp_gain": upgrade_mp_gain if upgrade_from else mp,
            }
        )

    enriched.sort(
        key=lambda item: (
            1 if item.get("mp_per_coin") in (None, 0) else 0,
            -(item.get("mp_per_coin") or 0),
            item.get("price") or float("inf"),
        )
    )

    return enriched, len(enriched)


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
        file = nbtlib.File.from_fileobj(io.BytesIO(payload))
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
    owned_ids: Set[str] = set()
    for acc in items:
        for key in ("id", "mc_id"):
            raw = acc.get(key)
            normalized = _normalize_accessory_id(raw) if raw else None
            if normalized:
                owned_ids.add(normalized)

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
    magical_power_max = _compute_max_magical_power()

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
    missing, missing_total, _ = _compute_missing_accessories(items)
    # Drop lower tiers if higher tiers are already owned, for both missing display and recommendations
    missing = _collapse_missing_by_chain(missing, owned_ids)
    missing_enriched, missing_count = _classify_missing_accessories(missing, set(owned_ids))

    return {
        "items": items,
        "slots": total_slots or len(items),
        "unique_count": len(unique_ids),
        "rarity_counts": rarity_counts,
        "selected_power": selected_power,
        "selected_power_label": _titleize_identifier(selected_power),
        "magical_power": magical_power,
        "magical_power_max": magical_power_max,
        "highest_magical_power": highest_magical_power,
        "tuning": tuning,
        "unlocked_powers": unlocked_powers,
        "power_stones": power_stones,
        "missing": missing,
        "missing_total": missing_total,
        "missing_count": missing_count,
        "missing_recommendations": missing_enriched,
    }
