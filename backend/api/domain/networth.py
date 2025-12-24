"""
Networth calculation module for Hypixel SkyBlock profiles.

Uses Moulberry's Lowest Bin API and Bazaar API for item pricing.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import requests
from django.core.cache import cache

from .wardrobe import _parse_inventory_items

LOGGER = logging.getLogger(__name__)

# Price API endpoints
MOULBERRY_LOWEST_BIN_URL = "https://moulberry.codes/lowestbin.json"
HYPIXEL_BAZAAR_URL = "https://api.hypixel.net/v2/skyblock/bazaar"

# Cache keys and TTL
PRICES_CACHE_KEY = "networth:prices"
PRICES_CACHE_TTL = 300  # 5 minutes

# Tier to number mapping for pet IDs
TIER_TO_NUM = {
    "COMMON": 0,
    "UNCOMMON": 1,
    "RARE": 2,
    "EPIC": 3,
    "LEGENDARY": 4,
    "MYTHIC": 5,
}

# Category multipliers for soulbound items (worth less on market)
SOULBOUND_MULTIPLIER = 0.0  # Soulbound items are not tradeable


@dataclass
class NetworthCategory:
    """Represents a category of items in networth calculation."""
    name: str
    total: float = 0.0
    items: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class NetworthResult:
    """Result of networth calculation."""
    total: float = 0.0
    unsoulbound: float = 0.0
    purse: float = 0.0
    bank: float = 0.0
    categories: Dict[str, NetworthCategory] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total": self.total,
            "unsoulbound": self.unsoulbound,
            "purse": self.purse,
            "bank": self.bank,
            "categories": {
                name: {
                    "name": cat.name,
                    "total": cat.total,
                    "item_count": len(cat.items),
                }
                for name, cat in self.categories.items()
            },
        }


def _safe_float(value: Any) -> float:
    """Safely convert value to float."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def fetch_prices() -> Dict[str, float]:
    """
    Fetch item prices from Moulberry's Lowest Bin API and Hypixel Bazaar.
    Results are cached for PRICES_CACHE_TTL seconds.
    """
    cached = cache.get(PRICES_CACHE_KEY)
    if cached:
        return cached

    prices: Dict[str, float] = {}
    
    # Fetch lowest bin prices (auction items)
    try:
        resp = requests.get(MOULBERRY_LOWEST_BIN_URL, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            for item_id, price in data.items():
                prices[item_id] = _safe_float(price)
            LOGGER.info("Fetched %d lowest bin prices", len(data))
    except Exception as e:
        LOGGER.warning("Failed to fetch lowest bin prices: %s", e)

    # Fetch bazaar prices
    try:
        resp = requests.get(HYPIXEL_BAZAAR_URL, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            products = data.get("products", {})
            for product_id, product_data in products.items():
                quick_status = product_data.get("quick_status", {})
                # Use sell price (what you'd get selling instantly)
                sell_price = _safe_float(quick_status.get("sellPrice", 0))
                if sell_price > 0:
                    # Bazaar items take precedence if also in auctions
                    prices[product_id] = sell_price
            LOGGER.info("Fetched %d bazaar prices", len(products))
    except Exception as e:
        LOGGER.warning("Failed to fetch bazaar prices: %s", e)

    if prices:
        cache.set(PRICES_CACHE_KEY, prices, PRICES_CACHE_TTL)
    
    return prices


def get_item_price(item_id: str, prices: Dict[str, float]) -> float:
    """Get price for an item ID."""
    if not item_id:
        return 0.0
    
    # Try exact match first
    if item_id in prices:
        return prices[item_id]
    
    # Try uppercase
    upper_id = item_id.upper()
    if upper_id in prices:
        return prices[upper_id]
    
    # Try without reforge prefix (e.g., "FABLED_HYPERION" -> "HYPERION")
    parts = upper_id.split("_")
    if len(parts) > 1:
        # Try removing first part (potential reforge)
        no_reforge = "_".join(parts[1:])
        if no_reforge in prices:
            return prices[no_reforge]
    
    return 0.0


def get_item_base_id(item: Dict[str, Any]) -> str:
    """
    Get the base item ID from an item, stripping reforge and other modifiers.
    """
    item_id = item.get("id", "")
    
    # Check extra_attributes for actual SkyBlock ID
    extra = item.get("extra_attributes", {}) or {}
    if extra:
        # Some items store the base ID differently
        actual_id = extra.get("id")
        if actual_id:
            return str(actual_id).upper()
    
    return item_id.upper() if item_id else ""


def is_soulbound(item: Dict[str, Any]) -> bool:
    """Check if an item is soulbound."""
    # Check lore for SOULBOUND marker
    lore = item.get("lore", [])
    if isinstance(lore, list):
        for line in lore:
            if isinstance(line, str) and "SOULBOUND" in line.upper():
                return True
    
    # Check extra attributes
    extra = item.get("extra_attributes", {}) or {}
    if extra.get("donated_museum"):
        return True
    
    return False


def calculate_item_value(item: Dict[str, Any], prices: Dict[str, float]) -> Tuple[float, bool]:
    """
    Calculate the value of a single item.
    Returns (value, is_soulbound).
    """
    if not item:
        return 0.0, False
    
    # id field is already the SkyBlock item ID (set from extra_attributes.id in parsing)
    item_id = item.get("id", "")
    if not item_id:
        return 0.0, False
    
    count = max(1, item.get("count", 1))
    soulbound = is_soulbound(item)
    
    # Try to get base price
    base_price = get_item_price(item_id, prices)
    
    # If base price is 0 and item might have tier suffix, try without it
    if base_price <= 0 and ";" in item_id:
        base_id = item_id.split(";")[0]
        base_price = get_item_price(base_id, prices)
    
    # Calculate total value
    value = base_price * count
    
    # Apply soulbound multiplier
    if soulbound:
        value *= SOULBOUND_MULTIPLIER
    
    return value, soulbound


def calculate_items_value(
    items: List[Optional[Dict[str, Any]]],
    prices: Dict[str, float],
) -> Tuple[float, float, List[Dict[str, Any]]]:
    """
    Calculate total value of a list of items.
    Returns (total_value, unsoulbound_value, valued_items).
    """
    total = 0.0
    unsoulbound = 0.0
    valued_items: List[Dict[str, Any]] = []
    unpriced_items: List[str] = []
    
    for item in items:
        if not item:
            continue
        
        value, is_sb = calculate_item_value(item, prices)
        if value <= 0:
            # Track unpriced items for debugging
            item_id = item.get("id", "unknown")
            if item_id and item_id != "unknown":
                unpriced_items.append(item_id)
            continue
        
        total += value
        if not is_sb:
            unsoulbound += value
        
        valued_items.append({
            "id": item.get("id", ""),
            "name": item.get("name", item.get("id", "")),
            "count": item.get("count", 1),
            "value": value,
            "soulbound": is_sb,
        })
    
    # Log unpriced items for debugging (sample)
    if unpriced_items:
        sample = unpriced_items[:5]
        LOGGER.debug("Unpriced items sample: %s (total: %d)", sample, len(unpriced_items))
    
    return total, unsoulbound, valued_items


def calculate_networth(
    member: Dict[str, Any],
    profile: Dict[str, Any],
    *,
    include_items: bool = False,
) -> NetworthResult:
    """
    Calculate the networth of a player's profile.
    
    Args:
        member: The player's member data from the profile
        profile: The full profile data
        include_items: Whether to include individual item details
    
    Returns:
        NetworthResult with total networth and category breakdown
    """
    prices = fetch_prices()
    result = NetworthResult()
    
    # Initialize categories
    category_configs = [
        ("purse", "Purse"),
        ("bank", "Bank"),
        ("inventory", "Inventory"),
        ("armor", "Armor"),
        ("equipment", "Equipment"),
        ("wardrobe", "Wardrobe"),
        ("enderchest", "Ender Chest"),
        ("storage", "Storage"),
        ("accessories", "Accessories"),
        ("pets", "Pets"),
        ("sacks", "Sacks"),
        ("essence", "Essence"),
    ]
    
    for cat_id, cat_name in category_configs:
        result.categories[cat_id] = NetworthCategory(name=cat_name)
    
    # === Currencies ===
    currencies = member.get("currencies", {}) or {}
    
    # Purse
    purse = _safe_float(currencies.get("coin_purse", 0))
    result.purse = purse
    result.categories["purse"].total = purse
    result.total += purse
    result.unsoulbound += purse
    
    # Bank
    banking = profile.get("banking", {}) or {}
    coop_bank = _safe_float(banking.get("balance", 0))
    
    profile_data = member.get("profile", {}) or {}
    personal_bank = _safe_float(profile_data.get("bank_account", 0))
    
    bank_total = coop_bank + personal_bank
    result.bank = bank_total
    result.categories["bank"].total = bank_total
    result.total += bank_total
    result.unsoulbound += bank_total
    
    # === Inventory ===
    inventory_data = member.get("inventory", {}) or {}
    
    # Main inventory
    inv_items = _extract_items_from_container(inventory_data.get("inv_contents"))
    inv_total, inv_unsb, inv_valued = calculate_items_value(inv_items, prices)
    result.categories["inventory"].total = inv_total
    if include_items:
        result.categories["inventory"].items = inv_valued
    result.total += inv_total
    result.unsoulbound += inv_unsb
    
    # Armor
    armor_items = _extract_items_from_container(inventory_data.get("inv_armor"))
    armor_total, armor_unsb, armor_valued = calculate_items_value(armor_items, prices)
    result.categories["armor"].total = armor_total
    if include_items:
        result.categories["armor"].items = armor_valued
    result.total += armor_total
    result.unsoulbound += armor_unsb
    
    # Equipment
    equip_items = _extract_items_from_container(inventory_data.get("equipment_contents"))
    equip_total, equip_unsb, equip_valued = calculate_items_value(equip_items, prices)
    result.categories["equipment"].total = equip_total
    if include_items:
        result.categories["equipment"].items = equip_valued
    result.total += equip_total
    result.unsoulbound += equip_unsb
    
    # Wardrobe
    wardrobe_items = _extract_items_from_container(inventory_data.get("wardrobe_contents"))
    wardrobe_total, wardrobe_unsb, wardrobe_valued = calculate_items_value(wardrobe_items, prices)
    result.categories["wardrobe"].total = wardrobe_total
    if include_items:
        result.categories["wardrobe"].items = wardrobe_valued
    result.total += wardrobe_total
    result.unsoulbound += wardrobe_unsb
    
    # Ender Chest
    ender_items = _extract_items_from_container(inventory_data.get("ender_chest_contents"))
    ender_total, ender_unsb, ender_valued = calculate_items_value(ender_items, prices)
    result.categories["enderchest"].total = ender_total
    if include_items:
        result.categories["enderchest"].items = ender_valued
    result.total += ender_total
    result.unsoulbound += ender_unsb
    
    # Storage (Backpacks)
    storage_total = 0.0
    storage_unsb = 0.0
    storage_items_all: List[Dict[str, Any]] = []
    
    backpack_contents = inventory_data.get("backpack_contents", {}) or {}
    for bp_data in backpack_contents.values():
        bp_items = _extract_items_from_container(bp_data)
        bp_total, bp_unsb, bp_valued = calculate_items_value(bp_items, prices)
        storage_total += bp_total
        storage_unsb += bp_unsb
        storage_items_all.extend(bp_valued)
    
    result.categories["storage"].total = storage_total
    if include_items:
        result.categories["storage"].items = storage_items_all
    result.total += storage_total
    result.unsoulbound += storage_unsb
    
    # === Accessories (Talisman Bag) ===
    talisman_items = _extract_items_from_container(inventory_data.get("bag_contents", {}).get("talisman_bag"))
    acc_total, acc_unsb, acc_valued = calculate_items_value(talisman_items, prices)
    result.categories["accessories"].total = acc_total
    if include_items:
        result.categories["accessories"].items = acc_valued
    result.total += acc_total
    result.unsoulbound += acc_unsb
    
    # === Pets ===
    pets_data = member.get("pets_data", {}) or {}
    pets_list = pets_data.get("pets", []) or []
    pets_total, pets_unsb = _calculate_pets_value(pets_list, prices)
    result.categories["pets"].total = pets_total
    result.total += pets_total
    result.unsoulbound += pets_unsb
    
    # === Sacks ===
    sacks_data = member.get("inventory", {}).get("sacks_counts", {}) or {}
    sacks_total = 0.0
    for item_id, count in sacks_data.items():
        price = get_item_price(item_id, prices)
        sacks_total += price * _safe_float(count)
    result.categories["sacks"].total = sacks_total
    result.total += sacks_total
    result.unsoulbound += sacks_total
    
    # === Essence ===
    essence_data = (member.get("currencies", {}) or {}).get("essence", {}) or {}
    essence_total = 0.0
    for essence_type, essence_info in essence_data.items():
        count = essence_info.get("current", 0) if isinstance(essence_info, dict) else essence_info
        essence_id = f"ESSENCE_{essence_type.upper()}"
        price = get_item_price(essence_id, prices)
        essence_total += price * _safe_float(count)
    result.categories["essence"].total = essence_total
    result.total += essence_total
    result.unsoulbound += essence_total
    
    # Log summary for debugging
    LOGGER.info(
        "Networth calculated: total=%.0f, unsoulbound=%.0f, categories=%s",
        result.total,
        result.unsoulbound,
        {k: f"{v.total:.0f}" for k, v in result.categories.items() if v.total > 0}
    )
    
    return result


def _extract_items_from_container(container: Optional[Any]) -> List[Dict[str, Any]]:
    """Extract item list from a container (may be dict with 'data' or direct list)."""
    if not container:
        return []
    
    # If it's already a list of parsed items
    if isinstance(container, list):
        return [item for item in container if item is not None]
    
    if isinstance(container, dict):
        # Raw NBT format with 'data' key - need to parse it
        data = container.get("data")
        if data:
            try:
                items = _parse_inventory_items(container)
                return [item for item in items if item is not None]
            except Exception as e:
                LOGGER.debug("Failed to parse container: %s", e)
                return []
        return []
    
    return []


def _calculate_pets_value(pets: List[Dict[str, Any]], prices: Dict[str, float]) -> Tuple[float, float]:
    """Calculate value of pets."""
    total = 0.0
    unsoulbound = 0.0
    
    for pet in pets:
        if not pet:
            continue
        
        pet_type = pet.get("type", "")
        tier = pet.get("tier", "COMMON")
        exp = pet.get("exp", 0)
        
        # Calculate level from exp for bonus pricing
        level = _estimate_pet_level(exp, tier)
        
        # Pet item ID format in Moulberry: {PET_TYPE};{TIER_NUM}
        # e.g., GOLDEN_DRAGON;4, ENDER_DRAGON;4
        tier_num = TIER_TO_NUM.get(tier, 0)
        
        # Try various ID formats
        price = 0.0
        
        # Format 1: TYPE;TIER (most common in Moulberry API)
        pet_id_1 = f"{pet_type};{tier_num}"
        price = get_item_price(pet_id_1, prices)
        
        # Format 2: With level suffix for maxed pets (e.g., GOLDEN_DRAGON;4+100)
        if price <= 0 and level >= 100:
            pet_id_lvl = f"{pet_type};{tier_num}+100"
            price = get_item_price(pet_id_lvl, prices)
        
        # Format 3: Just type with tier num
        if price <= 0:
            price = get_item_price(f"{pet_type};{tier_num}", prices)
        
        # Format 4: Try without tier
        if price <= 0:
            price = get_item_price(pet_type, prices)
        
        # Pets with held items add to value
        held_item = pet.get("heldItem")
        if held_item:
            held_price = get_item_price(held_item, prices)
            price += held_price
        
        # Pets with skins may have different value
        skin = pet.get("skin")
        if skin:
            skin_price = get_item_price(f"PET_SKIN_{skin}", prices)
            price += skin_price
        
        if price > 0:
            LOGGER.debug("Pet %s (%s, lvl %d) = %s", pet_type, tier, level, price)
        
        total += price
        unsoulbound += price  # Pets are generally tradeable
    
    return total, unsoulbound


def _estimate_pet_level(exp: float, tier: str) -> int:
    """Estimate pet level from experience."""
    # Simplified level calculation
    # Real calculation is more complex but this gives a rough estimate
    if exp <= 0:
        return 1
    
    # Approximate thresholds per tier
    tier_multipliers = {
        "COMMON": 1,
        "UNCOMMON": 1.1,
        "RARE": 1.2,
        "EPIC": 1.3,
        "LEGENDARY": 1.5,
        "MYTHIC": 2,
    }
    
    multiplier = tier_multipliers.get(tier, 1)
    
    # Very rough estimation
    if exp >= 25353230 * multiplier:  # Max level exp roughly
        return 100
    elif exp >= 4000000 * multiplier:
        return 80
    elif exp >= 1000000 * multiplier:
        return 60
    elif exp >= 200000 * multiplier:
        return 40
    elif exp >= 20000 * multiplier:
        return 20
    else:
        return max(1, int((exp / 5000) ** 0.5))
