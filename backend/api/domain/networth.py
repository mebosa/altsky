"""
Networth calculation module for Hypixel SkyBlock profiles.

Uses Moulberry's Lowest Bin API and Bazaar API for item pricing.
Calculates additional value from enchants, stars, reforges, HPB, gems, etc.
"""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import requests
from django.core.cache import cache

from .wardrobe import _parse_inventory_items
from ..http_client import session

LOGGER = logging.getLogger(__name__)

# C++ 확장 모듈 로드 시도
try:
    import altsky_cpp
    USE_CPP_PARSER = True
except ImportError:
    USE_CPP_PARSER = False
    LOGGER.warning("altsky_cpp module not found in networth, using Python implementation")

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

# ===== Application Worth (from SkyHelper-Networth) =====
# These represent the resale value percentage of applied upgrades
APPLICATION_WORTH = {
    # 0.5 tier
    "enrichment": 0.5,
    "farming_for_dummies": 0.5,
    "wood_singularity": 0.5,
    "gemstone_power_scroll": 0.5,
    # 0.6 tier
    "art_of_war": 0.6,
    "fuming_hpb": 0.6,
    "gemstone_slots": 0.6,
    "runes": 0.6,
    # 0.7 tier
    "tuned_transmission": 0.7,
    "pocket_sack": 0.7,
    # 0.75 tier
    "essence": 0.75,
    "silex": 0.75,
    # 0.8 tier
    "art_of_peace": 0.8,
    "divan_powder_coating": 0.8,
    "enchant_upgrades": 0.8,
    "jalapeno_book": 0.8,
    "mana_disintegrator": 0.8,
    "recombobulator": 0.8,
    "thunder_in_a_bottle": 0.8,
    # 0.85 tier
    "enchantments": 0.85,
    # 0.9 tier
    "dye": 0.9,
    "gemstone_chambers": 0.9,
    # 1.0 tier (full value)
    "reforge": 1.0,
    "master_star": 1.0,
    "gemstone": 1.0,
    "hpb": 1.0,
    "necron_scroll": 1.0,
    "pet_item": 1.0,
    "etherwarp": 1.0,
    "polarvoid_book": 1.0,
    "rod_part": 1.0,
    "drill_part": 1.0,
}

# ===== Additional Value Constants =====

# Hot Potato Book values (per book)
HPB_VALUE = 80_000  # Regular HPB
FUMING_HPB_VALUE = 1_000_000  # Fuming HPB (books 11-15)

# Master Stars values
MASTER_STAR_VALUES = {
    1: 15_000_000,   # First Master Star
    2: 30_000_000,   # Second Master Star
    3: 50_000_000,   # Third Master Star
    4: 80_000_000,   # Fourth Master Star  
    5: 120_000_000,  # Fifth Master Star
}

# Dungeon star essence costs (approximate market value)
STAR_ESSENCE_VALUES = {
    1: 100_000,
    2: 200_000,
    3: 400_000,
    4: 800_000,
    5: 1_600_000,
}

# Recombobulator value
RECOMBOBULATOR_VALUE = 8_000_000

# Art of War value
ART_OF_WAR_VALUE = 15_000_000

# Gemstone slot unlock values (approximate)
GEMSTONE_SLOT_VALUES = {
    "JADE": 500_000,
    "AMBER": 500_000,
    "TOPAZ": 500_000,
    "SAPPHIRE": 500_000,
    "AMETHYST": 500_000,
    "JASPER": 1_000_000,
    "RUBY": 500_000,
    "OPAL": 1_000_000,
}

# Gemstone quality multipliers
GEMSTONE_QUALITY = {
    "ROUGH": 0,
    "FLAWED": 0.1,
    "FINE": 0.3,
    "FLAWLESS": 0.6,
    "PERFECT": 1.0,
}

# Common enchant prices (will be overwritten by bazaar prices)
ENCHANT_BASE_VALUES = {
    # Ultimate enchants
    "ultimate_jerry": 5_000_000,
    "ultimate_bank": 10_000_000,
    "ultimate_chimera": 150_000_000,
    "ultimate_duplex": 30_000_000,
    "ultimate_fatal_tempo": 100_000_000,
    "ultimate_flash": 20_000_000,
    "ultimate_habanero_tactics": 50_000_000,
    "ultimate_inferno": 80_000_000,
    "ultimate_last_stand": 15_000_000,
    "ultimate_legion": 100_000_000,
    "ultimate_no_pain_no_gain": 10_000_000,
    "ultimate_one_for_all": 50_000_000,
    "ultimate_refrigerate": 5_000_000,
    "ultimate_rend": 30_000_000,
    "ultimate_soul_eater": 80_000_000,
    "ultimate_swarm": 50_000_000,
    "ultimate_wisdom": 10_000_000,
    # High value enchants
    "big_brain": 5_000_000,
    "counter_strike": 3_000_000,
    "divine_gift": 10_000_000,
    "ferocious_mana": 5_000_000,
    "hardened_mana": 5_000_000,
    "mana_vampire": 5_000_000,
    "pristine": 3_000_000,
    "strong_mana": 5_000_000,
    "vicious": 3_000_000,
}


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
        resp = session.get(MOULBERRY_LOWEST_BIN_URL, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            for item_id, price in data.items():
                prices[item_id] = _safe_float(price)
            LOGGER.info("Fetched %d lowest bin prices", len(data))
    except Exception as e:
        LOGGER.warning("Failed to fetch lowest bin prices: %s", e)

    # Fetch bazaar prices
    try:
        resp = session.get(HYPIXEL_BAZAAR_URL, timeout=10)
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

    # Manual overrides for missing essences
    if "ESSENCE_FOREST" not in prices:
        prices["ESSENCE_FOREST"] = 10.0  # Default price for Forest Essence

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
    # Check extra attributes first (most reliable)
    extra = item.get("extra_attributes", {}) or {}
    if extra.get("donated_museum"):
        return True
    
    lore = item.get("lore", [])
    lore_colored = item.get("lore_colored", [])

    if USE_CPP_PARSER:
        # Ensure lists are strings (handle potential None or non-string items if any)
        # C++ expects vector<string>, so we need to be careful.
        # Assuming lore and lore_colored are lists of strings as per type hint.
        # But let's be safe.
        safe_lore = [str(l) for l in lore] if lore else []
        safe_lore_colored = [str(l) for l in lore_colored] if lore_colored else []
        return altsky_cpp.is_soulbound(safe_lore, safe_lore_colored)

    # Check lore for SOULBOUND marker (with or without color codes)
    # SkyBlock uses: "§8§l* §8Co-op Soulbound §8§l*" or "§8§l* §8Soulbound §8§l*"
    
    # Check colored lore first (more accurate)
    if isinstance(lore_colored, list):
        for line in lore_colored:
            if isinstance(line, str):
                if "Soulbound" in line or "SOULBOUND" in line:
                    return True
    
    # Fallback to plain lore
    if isinstance(lore, list):
        for line in lore:
            if isinstance(line, str):
                line_upper = line.upper()
                if "SOULBOUND" in line_upper or "CO-OP SOULBOUND" in line_upper:
                    return True
    
    return False


def calculate_item_value(item: Dict[str, Any], prices: Dict[str, float]) -> Tuple[float, bool]:
    """
    Calculate the value of a single item including all modifiers.
    Returns (value, is_soulbound).
    Uses extra_attributes for accurate modifier detection.
    """
    if not item:
        return 0.0, False
    
    # id field is already the SkyBlock item ID (set from extra_attributes.id in parsing)
    item_id = item.get("id", "")
    if not item_id:
        return 0.0, False
    
    count = max(1, item.get("count", 1))
    soulbound = is_soulbound(item)
    
    # Get extra_attributes from parsed item
    extra = item.get("extra_attributes", {}) or {}
    lore = item.get("lore", []) or []
    
    # Try to get base price
    base_price = get_item_price(item_id, prices)
    
    # If base price is 0 and item might have tier suffix, try without it
    if base_price <= 0 and ";" in item_id:
        base_id = item_id.split(";")[0]
        base_price = get_item_price(base_id, prices)
    
    # Calculate total value starting with base
    value = base_price * count
    
    # === Calculate additional value from modifiers ===
    additional_value = 0.0
    
    # 1. Hot Potato Books (from extra_attributes.hot_potato_count)
    additional_value += _calculate_hpb_value_from_extra(extra, prices)
    
    # 2. Stars (from extra_attributes.dungeon_item_level)
    additional_value += _calculate_star_value_from_extra(extra, item, prices)
    
    # 3. Recombobulator (from extra_attributes.rarity_upgrades)
    additional_value += _calculate_recomb_value_from_extra(extra, prices)
    
    # 4. Art of War (from extra_attributes.art_of_war_count)
    additional_value += _calculate_art_of_war_from_extra(extra, prices)
    
    # 5. Enchants (from extra_attributes.enchantments)
    additional_value += _calculate_enchant_value_from_extra(extra, prices)
    
    # 6. Gemstones (from extra_attributes.gems)
    additional_value += _calculate_gem_value_from_extra(extra, prices)
    
    # 7. Skin value (for items with skins)
    additional_value += _calculate_skin_value(item, prices)
    
    # 8. Reforge stone value
    additional_value += _calculate_reforge_value_from_extra(extra, prices)
    
    # 9. Necron Blade Scrolls
    additional_value += _calculate_scroll_value_from_extra(extra, prices)
    
    # 10. Farming for Dummies
    additional_value += _calculate_ffd_value_from_extra(extra, prices)
    
    # 11. Wood Singularity
    additional_value += _calculate_wood_singularity_from_extra(extra, prices)
    
    # 12. Enrichment (Accessories)
    additional_value += _calculate_enrichment_from_extra(extra, prices)
    
    # 13. Transmission Tuner
    additional_value += _calculate_transmission_tuner_from_extra(extra, prices)
    
    # 14. Upgrade Level (Crimson etc)
    additional_value += _calculate_upgrade_level_from_extra(extra, item_id, prices)
    
    # 15. Prestige Level (Kuudra)
    additional_value += _calculate_prestige_level_from_extra(extra, item_id, prices)
    
    # 16. Silex (Efficiency > 5)
    additional_value += _calculate_silex_from_extra(extra, item_id, prices)
    
    # 17. Etherwarp Conduit
    additional_value += _calculate_etherwarp_from_extra(extra, prices)
    
    # 18. Pocket Sack-in-a-Sack
    additional_value += _calculate_pocket_sack_from_extra(extra, prices)
    
    # 19. Polarvoid Book
    additional_value += _calculate_polarvoid_from_extra(extra, prices)
    
    # 20. Jalapeno Book
    additional_value += _calculate_jalapeno_from_extra(extra, prices)
    
    # 21. Gemstone Power Scroll
    additional_value += _calculate_power_scroll_from_extra(extra, prices)
    
    # 22. Mana Disintegrator
    additional_value += _calculate_mana_disintegrator_from_extra(extra, prices)
    
    # 23. Dye
    additional_value += _calculate_dye_from_extra(extra, prices)
    
    value += additional_value
    
    # Apply soulbound multiplier
    if soulbound:
        value *= SOULBOUND_MULTIPLIER
    
    return value, soulbound


def _calculate_hpb_value_from_extra(extra: Dict[str, Any], prices: Dict[str, float]) -> float:
    """Calculate Hot Potato Book value from extra_attributes."""
    hpb_count = extra.get("hot_potato_count", 0)
    if not hpb_count:
        return 0.0
    
    try:
        hpb_count = int(hpb_count)
    except (TypeError, ValueError):
        return 0.0
    
    value = 0.0
    
    # Get actual prices from API
    hpb_price = get_item_price("HOT_POTATO_BOOK", prices)
    fuming_price = get_item_price("FUMING_POTATO_BOOK", prices)
    
    # First 10 are regular HPB (100% value)
    regular = min(hpb_count, 10)
    regular_value = regular * (hpb_price if hpb_price > 0 else HPB_VALUE)
    value += regular_value * APPLICATION_WORTH.get("hpb", 1.0)
    
    # 11-15 are Fuming HPB (60% resale value)
    if hpb_count > 10:
        fuming = min(hpb_count - 10, 5)
        fuming_value = fuming * (fuming_price if fuming_price > 0 else FUMING_HPB_VALUE)
        value += fuming_value * APPLICATION_WORTH.get("fuming_hpb", 0.6)
    
    return value


def _calculate_star_value_from_extra(extra: Dict[str, Any], item: Dict[str, Any], prices: Dict[str, float]) -> float:
    """Calculate star value from extra_attributes.dungeon_item_level."""
    value = 0.0
    
    dungeon_level = extra.get("dungeon_item_level")
    if dungeon_level is None:
        # Fallback to item name star counting
        item_name = item.get("name", "")
        normal_stars = item_name.count("✪")
        master_stars = item_name.count("⚝")
        
        for i in range(1, normal_stars + 1):
            star_value = STAR_ESSENCE_VALUES.get(i, 1_000_000)
            value += star_value * APPLICATION_WORTH.get("essence", 0.75)
        
        for i in range(1, master_stars + 1):
            master_value = MASTER_STAR_VALUES.get(i, 50_000_000)
            value += master_value * APPLICATION_WORTH.get("master_star", 1.0)
        
        return value
    
    try:
        level = int(str(dungeon_level).rstrip('b'))  # Handle "6b" format
    except (TypeError, ValueError):
        return 0.0
    
    # Normal dungeon stars (1-5) - essence cost
    normal_stars = min(level, 5)
    for i in range(1, normal_stars + 1):
        essence_value = STAR_ESSENCE_VALUES.get(i, 1_000_000)
        value += essence_value * APPLICATION_WORTH.get("essence", 0.75)
    
    # Master stars (6-10, represented as 1-5 master stars) - full value
    if level > 5:
        master_count = min(level - 5, 5)
        master_star_ids = ["FIRST_MASTER_STAR", "SECOND_MASTER_STAR", "THIRD_MASTER_STAR", "FOURTH_MASTER_STAR", "FIFTH_MASTER_STAR"]
        for i in range(master_count):
            star_id = master_star_ids[i] if i < len(master_star_ids) else master_star_ids[-1]
            star_price = get_item_price(star_id, prices)
            if star_price > 0:
                value += star_price * APPLICATION_WORTH.get("master_star", 1.0)
            else:
                value += MASTER_STAR_VALUES.get(i + 1, 50_000_000) * APPLICATION_WORTH.get("master_star", 1.0)
    
    return value


def _calculate_recomb_value_from_extra(extra: Dict[str, Any], prices: Dict[str, float]) -> float:
    """Calculate recombobulator value from extra_attributes."""
    rarity_upgrades = extra.get("rarity_upgrades")
    if rarity_upgrades and int(rarity_upgrades) >= 1:
        recomb_price = get_item_price("RECOMBOBULATOR_3000", prices)
        base_value = recomb_price if recomb_price > 0 else RECOMBOBULATOR_VALUE
        return base_value * APPLICATION_WORTH.get("recombobulator", 0.8)
    return 0.0


def _calculate_art_of_war_from_extra(extra: Dict[str, Any], prices: Dict[str, float]) -> float:
    """Calculate Art of War value from extra_attributes."""
    aow_count = extra.get("art_of_war_count", 0)
    if aow_count:
        try:
            count = int(aow_count)
            aow_price = get_item_price("THE_ART_OF_WAR", prices)
            base_value = count * (aow_price if aow_price > 0 else ART_OF_WAR_VALUE)
            return base_value * APPLICATION_WORTH.get("art_of_war", 0.6)
        except (TypeError, ValueError):
            pass
    return 0.0


def _calculate_enchant_value_from_extra(extra: Dict[str, Any], prices: Dict[str, float]) -> float:
    """Calculate enchant value from extra_attributes.enchantments dict."""
    enchants = extra.get("enchantments", {})
    if not isinstance(enchants, dict):
        return 0.0
    
    value = 0.0
    enchant_worth = APPLICATION_WORTH.get("enchantments", 0.85)
    
    for enchant_name, level in enchants.items():
        if not isinstance(enchant_name, str):
            continue
        try:
            level = int(level)
        except (TypeError, ValueError):
            continue
        
        # Format: ENCHANTMENT_SOUL_EATER_5
        enchant_id = f"ENCHANTMENT_{enchant_name.upper()}_{level}"
        enchant_price = get_item_price(enchant_id, prices)
        
        if enchant_price > 0:
            # Apply worth reduction for applied enchants
            value += enchant_price * enchant_worth
    
    return value


def _calculate_gem_value_from_extra(extra: Dict[str, Any], prices: Dict[str, float]) -> float:
    """Calculate gemstone value from extra_attributes.gems."""
    gems_data = extra.get("gems", {})
    if not isinstance(gems_data, dict):
        return 0.0
    
    value = 0.0
    
    # Handle both old and new gem format
    for key, gem_info in gems_data.items():
        if key in ("unlocked_slots", "formatted", "unlockedSlots"):
            continue
        
        gem_type = None
        gem_tier = None
        
        if isinstance(gem_info, dict):
            # New format: {"quality": "PERFECT", "type": "SAPPHIRE"}
            gem_tier = gem_info.get("quality") or gem_info.get("tier")
            gem_type = gem_info.get("type")
        elif isinstance(gem_info, str):
            # Old format: key like "COMBAT_0_gem" with value "SAPPHIRE"
            gem_type = gem_info
            # Try to get quality from corresponding key
            quality_key = key.replace("_gem", "")
            quality_info = gems_data.get(quality_key, {})
            if isinstance(quality_info, dict):
                gem_tier = quality_info.get("quality")
        
        if gem_type and gem_tier:
            # Format: PERFECT_SAPPHIRE_GEM
            gem_id = f"{gem_tier}_{gem_type}_GEM".upper()
            gem_price = get_item_price(gem_id, prices)
            if gem_price > 0:
                value += gem_price
    
    return value


def _calculate_reforge_value_from_extra(extra: Dict[str, Any], prices: Dict[str, float]) -> float:
    """Calculate reforge stone value."""
    # Common reforge to stone mappings
    REFORGE_STONES = {
        "renowned": "DRAGON_HORN",
        "ancient": "PRECURSOR_GEAR",
        "withered": "WITHER_BLOOD",
        "loving": "RED_SCARF",
        "spiritual": "SPIRIT_STONE",
        "fabled": "DRAGON_CLAW",
        "suspicious": "SUSPICIOUS_VIAL",
        "aote_stone": "AOTE_STONE",
        "submerged": "DEEP_SEA_ORB",
        "warped": "WARPED_STONE",
    }
    
    modifier = extra.get("modifier", "")
    if isinstance(modifier, str) and modifier.lower() in REFORGE_STONES:
        stone_id = REFORGE_STONES[modifier.lower()]
        stone_price = get_item_price(stone_id, prices)
        return stone_price if stone_price > 0 else 0
    return 0.0


def _calculate_scroll_value_from_extra(extra: Dict[str, Any], prices: Dict[str, float]) -> float:
    """Calculate Necron Blade scroll value."""
    scrolls = extra.get("ability_scroll", [])
    if not isinstance(scrolls, list):
        return 0.0
    
    value = 0.0
    for scroll_id in scrolls:
        if isinstance(scroll_id, str):
            scroll_price = get_item_price(scroll_id.upper(), prices)
            if scroll_price > 0:
                value += scroll_price
    return value


def _calculate_ffd_value_from_extra(extra: Dict[str, Any], prices: Dict[str, float]) -> float:
    """Calculate Farming For Dummies value."""
    ffd_count = extra.get("farming_for_dummies_count", 0)
    if ffd_count:
        try:
            count = int(ffd_count)
            ffd_price = get_item_price("FARMING_FOR_DUMMIES", prices)
            base_value = count * (ffd_price if ffd_price > 0 else 1_000_000)
            return base_value * APPLICATION_WORTH.get("farming_for_dummies", 0.5)
        except (TypeError, ValueError):
            pass
    return 0.0


def _calculate_skin_value(item: Dict[str, Any], prices: Dict[str, float]) -> float:
    """Calculate skin value from item."""
    skin_url = item.get("skin_url")
    if not skin_url:
        return 0.0
    
    # Try to extract skin ID from URL or other sources
    item_id = item.get("id", "")
    
    # Some skins have specific IDs
    skin_patterns = [
        f"{item_id}_SKIN",
        f"SKIN_{item_id}",
    ]
    
    for skin_id in skin_patterns:
        skin_price = get_item_price(skin_id, prices)
        if skin_price > 0:
            return skin_price
    
    return 0.0


def _calculate_wood_singularity_from_extra(extra: Dict[str, Any], prices: Dict[str, float]) -> float:
    """Calculate Wood Singularity value."""
    ws_count = extra.get("wood_singularity_count", 0)
    if ws_count:
        try:
            count = int(ws_count)
            ws_price = get_item_price("WOOD_SINGULARITY", prices)
            return count * (ws_price if ws_price > 0 else 5_000_000) * APPLICATION_WORTH.get("wood_singularity", 1.0)
        except (TypeError, ValueError):
            pass
    return 0.0


def _calculate_enrichment_from_extra(extra: Dict[str, Any], prices: Dict[str, float]) -> float:
    """Calculate Enrichment value for accessories."""
    enrichment = extra.get("talisman_enrichment", "")
    if enrichment and isinstance(enrichment, str):
        enrichment_id = f"TALISMAN_ENRICHMENT_{enrichment.upper()}"
        enrichment_price = get_item_price(enrichment_id, prices)
        if enrichment_price > 0:
            return enrichment_price * APPLICATION_WORTH.get("enrichment", 0.5)
    return 0.0


def _calculate_transmission_tuner_from_extra(extra: Dict[str, Any], prices: Dict[str, float]) -> float:
    """Calculate Transmission Tuner value."""
    tuner_count = extra.get("tuned_transmission", 0)
    if tuner_count:
        try:
            count = int(tuner_count)
            tuner_price = get_item_price("TRANSMISSION_TUNER", prices)
            return count * (tuner_price if tuner_price > 0 else 8_000_000)
        except (TypeError, ValueError):
            pass
    return 0.0


def _calculate_upgrade_level_from_extra(extra: Dict[str, Any], item_id: str, prices: Dict[str, float]) -> float:
    """Calculate upgrade level value for Crimson items."""
    upgrade_level = extra.get("upgrade_level", 0)
    if not upgrade_level:
        return 0.0
    
    try:
        level = int(upgrade_level)
    except (TypeError, ValueError):
        return 0.0
    
    # Crimson Essence cost per level varies by item
    # Average: ~5-15M per level for high-tier items
    essence_cost_map = {
        "TERROR_": 3_500_000,
        "HOLLOW_": 3_000_000,
        "FERVOR_": 2_500_000,
        "BURNING_": 2_000_000,
        "FIERY_": 2_000_000,
        "INFERNAL_": 5_000_000,
        "AURORA_": 3_500_000,
    }
    
    cost_per_level = 3_000_000  # default
    for prefix, cost in essence_cost_map.items():
        if item_id.upper().startswith(prefix):
            cost_per_level = cost
            break
    
    return level * cost_per_level * APPLICATION_WORTH.get("essence", 0.75)


def _calculate_prestige_level_from_extra(extra: Dict[str, Any], item_id: str, prices: Dict[str, float]) -> float:
    """Calculate prestige value for Kuudra items."""
    prestige = extra.get("dungeon_item_tier")  # Kuudra uses same field sometimes
    if prestige is None:
        return 0.0
    
    try:
        level = int(prestige)
    except (TypeError, ValueError):
        return 0.0
    
    # Prestige items have tier-based essence costs
    if level <= 0:
        return 0.0
    
    # Check if it's a Kuudra item (Crimson items)
    crimson_items = ["TERROR", "HOLLOW", "FERVOR", "BURNING", "FIERY", "INFERNAL", "AURORA"]
    is_crimson = any(c in item_id.upper() for c in crimson_items)
    
    if not is_crimson:
        return 0.0
    
    # Rough estimate for prestige value
    # T1: ~10M, T2: ~30M, T3: ~100M, T4: ~300M, T5: ~1B
    prestige_values = {1: 10_000_000, 2: 30_000_000, 3: 100_000_000, 4: 300_000_000, 5: 1_000_000_000}
    base_value = prestige_values.get(level, 0)
    
    return base_value * APPLICATION_WORTH.get("essence", 0.75)


def _calculate_silex_from_extra(extra: Dict[str, Any], item_id: str, prices: Dict[str, float]) -> float:
    """
    Calculate Silex value from efficiency enchant level.
    Silex is required to get efficiency > 5 (or > 6 for Stonk).
    """
    enchants = extra.get("enchantments", {})
    if not isinstance(enchants, dict):
        return 0.0
    
    efficiency_level = enchants.get("efficiency", 0)
    try:
        efficiency_level = int(efficiency_level)
    except (TypeError, ValueError):
        return 0.0
    
    # Base efficiency is 5, but Stonk starts with 6
    base_efficiency = 6 if item_id.upper() == "STONK_PICKAXE" else 5
    
    # Silex count = efficiency level - base efficiency
    silex_count = max(0, efficiency_level - base_efficiency)
    
    if silex_count > 0:
        silex_price = get_item_price("SIL_EX", prices)
        return silex_count * (silex_price if silex_price > 0 else 4_500_000) * APPLICATION_WORTH.get("silex", 0.75)
    
    return 0.0


def _calculate_etherwarp_from_extra(extra: Dict[str, Any], prices: Dict[str, float]) -> float:
    """Calculate Etherwarp Conduit value from extra_attributes.ethermerge."""
    ethermerge = extra.get("ethermerge")
    if ethermerge:
        conduit_price = get_item_price("ETHERWARP_CONDUIT", prices)
        return (conduit_price if conduit_price > 0 else 15_000_000) * APPLICATION_WORTH.get("etherwarp", 1.0)
    return 0.0


def _calculate_pocket_sack_from_extra(extra: Dict[str, Any], prices: Dict[str, float]) -> float:
    """Calculate Pocket Sack-in-a-Sack value."""
    sack_pss = extra.get("sack_pss", 0)
    if sack_pss:
        try:
            count = int(sack_pss)
            sack_price = get_item_price("POCKET_SACK_IN_A_SACK", prices)
            return count * (sack_price if sack_price > 0 else 12_000_000) * APPLICATION_WORTH.get("pocket_sack", 0.7)
        except (TypeError, ValueError):
            pass
    return 0.0


def _calculate_polarvoid_from_extra(extra: Dict[str, Any], prices: Dict[str, float]) -> float:
    """Calculate Polarvoid Book value."""
    polarvoid = extra.get("polarvoid", 0)
    if polarvoid:
        try:
            count = int(polarvoid)
            pv_price = get_item_price("POLARVOID_BOOK", prices)
            return count * (pv_price if pv_price > 0 else 2_500_000) * APPLICATION_WORTH.get("polarvoid_book", 1.0)
        except (TypeError, ValueError):
            pass
    return 0.0


def _calculate_jalapeno_from_extra(extra: Dict[str, Any], prices: Dict[str, float]) -> float:
    """Calculate Jalapeno Book value."""
    jalapeno = extra.get("jalapeno_count", 0)
    if jalapeno:
        try:
            count = int(jalapeno)
            jal_price = get_item_price("JALAPENO_BOOK", prices)
            return count * (jal_price if jal_price > 0 else 31_000_000) * APPLICATION_WORTH.get("jalapeno_book", 0.8)
        except (TypeError, ValueError):
            pass
    return 0.0


def _calculate_power_scroll_from_extra(extra: Dict[str, Any], prices: Dict[str, float]) -> float:
    """Calculate Gemstone Power Scroll value."""
    power_scroll = extra.get("power_ability_scroll")
    if power_scroll and isinstance(power_scroll, str):
        scroll_price = get_item_price(power_scroll.upper(), prices)
        if scroll_price > 0:
            return scroll_price * APPLICATION_WORTH.get("gemstone_power_scroll", 0.5)
    return 0.0


def _calculate_mana_disintegrator_from_extra(extra: Dict[str, Any], prices: Dict[str, float]) -> float:
    """Calculate Mana Disintegrator value."""
    mana_disintegrator = extra.get("mana_disintegrator_count", 0)
    if mana_disintegrator:
        try:
            count = int(mana_disintegrator)
            md_price = get_item_price("MANA_DISINTEGRATOR", prices)
            return count * (md_price if md_price > 0 else 1_500_000) * APPLICATION_WORTH.get("mana_disintegrator", 0.8)
        except (TypeError, ValueError):
            pass
    return 0.0


def _calculate_dye_from_extra(extra: Dict[str, Any], prices: Dict[str, float]) -> float:
    """Calculate Dye value from applied dye."""
    dye = extra.get("dye_item")
    if dye and isinstance(dye, str):
        dye_price = get_item_price(dye.upper(), prices)
        if dye_price > 0:
            return dye_price * APPLICATION_WORTH.get("dye", 0.9)
    return 0.0


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
        ("personal_vault", "Personal Vault"),
        ("accessories", "Accessories"),
        ("pets", "Pets"),
        ("sacks", "Sacks"),
        ("essence", "Essence"),
        ("fishing_bag", "Fishing Bag"),
        ("potion_bag", "Potion Bag"),
        ("candy_inventory", "Candy Inventory"),
        ("museum", "Museum"),
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
    inv_contents = inventory_data.get("inv_contents")
    inv_items = _extract_items_from_container(inv_contents)
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
    wardrobe_contents = inventory_data.get("wardrobe_contents")
    wardrobe_items = _extract_items_from_container(wardrobe_contents)
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
    
    for bp_key, bp_data in backpack_contents.items():
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
    
    # === Personal Vault ===
    personal_vault = _extract_items_from_container(inventory_data.get("personal_vault_contents"))
    vault_total, vault_unsb, vault_valued = calculate_items_value(personal_vault, prices)
    result.categories["personal_vault"].total = vault_total
    if include_items:
        result.categories["personal_vault"].items = vault_valued
    result.total += vault_total
    result.unsoulbound += vault_unsb
    
    # === Bag Contents ===
    bag_contents = inventory_data.get("bag_contents", {}) or {}
    
    # === Accessories (Talisman Bag) ===
    talisman_items = _extract_items_from_container(bag_contents.get("talisman_bag"))
    acc_total, acc_unsb, acc_valued = calculate_items_value(talisman_items, prices)
    result.categories["accessories"].total = acc_total
    if include_items:
        result.categories["accessories"].items = acc_valued
    result.total += acc_total
    result.unsoulbound += acc_unsb
    
    # === Fishing Bag ===
    fishing_items = _extract_items_from_container(bag_contents.get("fishing_bag"))
    fishing_total, fishing_unsb, fishing_valued = calculate_items_value(fishing_items, prices)
    result.categories["fishing_bag"].total = fishing_total
    if include_items:
        result.categories["fishing_bag"].items = fishing_valued
    result.total += fishing_total
    result.unsoulbound += fishing_unsb
    
    # === Potion Bag ===
    potion_items = _extract_items_from_container(bag_contents.get("potion_bag"))
    potion_total, potion_unsb, potion_valued = calculate_items_value(potion_items, prices)
    result.categories["potion_bag"].total = potion_total
    if include_items:
        result.categories["potion_bag"].items = potion_valued
    result.total += potion_total
    result.unsoulbound += potion_unsb
    
    # === Candy Inventory ===
    candy_inv = member.get("shared_inventory", {}) or {}
    candy_items = _extract_items_from_container(candy_inv.get("candy_inventory_contents"))
    candy_total, candy_unsb, candy_valued = calculate_items_value(candy_items, prices)
    result.categories["candy_inventory"].total = candy_total
    if include_items:
        result.categories["candy_inventory"].items = candy_valued
    result.total += candy_total
    result.unsoulbound += candy_unsb
    
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
    """Calculate value of pets with level-based pricing."""
    total = 0.0
    unsoulbound = 0.0
    
    # Soulbound pets (cannot be traded)
    SOULBOUND_PETS = {
        "GRANDMA_WOLF", "BINGO", 
        "KUUDRA", "MONTEZUMA", "WISP", "SUBZERO_WISP", "DARK_CACAO", 
        "SPIRIT",
    }
    
    # Pet candy reduces value (candied pets are worth less)
    CANDY_PENALTY_PER_CANDY = 0.01  # 1% reduction per candy, up to 10 candies
    
    for pet in pets:
        if not pet:
            continue
        
        pet_type = pet.get("type", "")
        tier = pet.get("tier", "COMMON")
        exp = pet.get("exp", 0)
        candy_used = pet.get("candyUsed", 0)
        
        # Calculate level from exp
        level = _estimate_pet_level(exp, tier)
        
        # Pet item ID format in Moulberry: {PET_TYPE};{TIER_NUM}
        # Level variants: {PET_TYPE};{TIER_NUM}+100 or +200
        tier_num = TIER_TO_NUM.get(tier, 0)
        base_pet_id = f"{pet_type};{tier_num}"
        
        # Get level-based price from Moulberry API
        price = _get_pet_price_by_level(pet_type, tier_num, level, prices)
        
        # Fallback: try base price without level
        if price <= 0:
            price = get_item_price(base_pet_id, prices)
        
        # Fallback: try without tier
        if price <= 0:
            price = get_item_price(pet_type, prices)
        
        # Pets with held items add to value
        held_item = pet.get("heldItem")
        if held_item:
            held_price = get_item_price(held_item, prices)
            price += held_price * APPLICATION_WORTH.get("pet_item", 1.0)
        
        # Pets with skins may have different value
        skin = pet.get("skin")
        if skin:
            skin_price = get_item_price(f"PET_SKIN_{skin}", prices)
            price += skin_price
        
        # Apply candy penalty (candied pets are worth less)
        if candy_used > 0:
            candy_penalty = min(candy_used, 10) * CANDY_PENALTY_PER_CANDY
            price *= (1.0 - candy_penalty)
        
        if price > 0:
            LOGGER.debug("Pet %s (%s, lvl %d, candy=%d) = %s", pet_type, tier, level, candy_used, price)
        
        total += price
        
        # Soulbound pets don't count toward unsoulbound
        if pet_type not in SOULBOUND_PETS:
            unsoulbound += price
    
    return total, unsoulbound


def _get_pet_price_by_level(pet_type: str, tier_num: int, level: int, prices: Dict[str, float]) -> float:
    """
    Get pet price based on level using Moulberry's level-based pricing.
    
    Moulberry format:
    - {PET};{TIER} = Level 1 base price
    - {PET};{TIER}+100 = Level 100 price
    - {PET};{TIER}+200 = Level 200 price (Golden Dragon only)
    
    For levels between 1-100, interpolate between base and +100 price.
    """
    base_pet_id = f"{pet_type};{tier_num}"
    lvl100_pet_id = f"{pet_type};{tier_num}+100"
    lvl200_pet_id = f"{pet_type};{tier_num}+200"
    
    base_price = get_item_price(base_pet_id, prices)
    lvl100_price = get_item_price(lvl100_pet_id, prices)
    lvl200_price = get_item_price(lvl200_pet_id, prices)
    
    # For level 200 pets (e.g., Golden Dragon)
    if level >= 200 and lvl200_price > 0:
        return lvl200_price
    
    # For level 100+ pets
    if level >= 100:
        if lvl100_price > 0:
            # If pet can go to 200 and we have lvl200 price, interpolate
            if lvl200_price > 0 and level > 100:
                # Interpolate between 100 and 200
                progress = (level - 100) / 100.0
                return lvl100_price + (lvl200_price - lvl100_price) * progress
            return lvl100_price
        # Fallback to base price if no lvl100 price available
        return base_price if base_price > 0 else 0.0
    
    # For levels 1-99, interpolate between base and lvl100 price
    if base_price > 0:
        if lvl100_price > 0:
            # Interpolate: value increases with level
            # But not linear - early levels are cheap, later levels more expensive
            # Using a curve that accelerates as level increases
            progress = level / 100.0
            # Quadratic curve: slower start, faster finish
            curved_progress = progress ** 1.5
            return base_price + (lvl100_price - base_price) * curved_progress
        else:
            # No lvl100 price, just use base with level bonus
            # Assume lvl100 is worth ~20% more than lvl1 for common pets
            level_multiplier = 1.0 + (level / 100.0) * 0.2
            return base_price * level_multiplier
    
    return 0.0


def _estimate_pet_level(exp: float, tier: str) -> int:
    """Estimate pet level from experience using actual SkyBlock XP tables."""
    if exp <= 0:
        return 1
    
    # Cumulative XP required for each level (actual SkyBlock values)
    # These are the XP thresholds for levels 1-100 for legendary pets
    PET_LEVELS = [
        0, 100, 210, 330, 460, 605, 765, 940, 1130, 1340,  # 1-10
        1570, 1820, 2095, 2395, 2725, 3085, 3485, 3925, 4415, 4955,  # 11-20
        5555, 6215, 6945, 7745, 8625, 9585, 10635, 11785, 13045, 14425,  # 21-30
        15935, 17585, 19385, 21345, 23475, 25785, 28285, 30985, 33905, 37065,  # 31-40
        40485, 44185, 48185, 52535, 57285, 62485, 68185, 74485, 81485, 89285,  # 41-50
        97985, 107685, 118485, 130485, 143785, 158485, 174685, 192485, 211985, 233285,  # 51-60
        256485, 281685, 309085, 338885, 371285, 406485, 444685, 486085, 530885, 579285,  # 61-70
        631485, 687685, 748085, 812885, 882285, 956485, 1035685, 1120085, 1209885, 1305285,  # 71-80
        1406485, 1513685, 1627085, 1746985, 1873685, 2007485, 2148685, 2297485, 2454285, 2619385,  # 81-90
        2792985, 2975285, 3166485, 3366785, 3576385, 3795485, 4024285, 4263085, 4512085, 4771385,  # 91-100
    ]
    
    # For golden dragon (levels 100-200), additional XP is needed
    # Approximate: each level after 100 requires about 5M XP more
    PET_LEVELS_200 = PET_LEVELS.copy()
    for i in range(100):
        # Levels 101-200 require significantly more XP
        PET_LEVELS_200.append(PET_LEVELS_200[-1] + 5000000 + (i * 100000))
    
    # Tier offset adjustments (lower tiers need less XP per level)
    tier_offsets = {
        "COMMON": 0,      # Levels 1-100 only, starts at index 0
        "UNCOMMON": 6,    # Starts 6 levels worth of XP lower
        "RARE": 11,       # Starts 11 levels worth of XP lower
        "EPIC": 16,       # Starts 16 levels worth of XP lower
        "LEGENDARY": 20,  # Full XP table
        "MYTHIC": 20,     # Same as legendary, but can go to 200
    }
    
    offset = tier_offsets.get(tier, 20)
    max_level = 200 if tier == "MYTHIC" else 100
    
    # Find the level for this XP amount
    levels_table = PET_LEVELS_200 if tier == "MYTHIC" else PET_LEVELS
    
    # Adjust XP based on tier offset
    adjusted_exp = exp
    if offset < 20:
        # Lower tier pets need less XP - scale it up to match legendary table
        scale_factor = 1.0 + (20 - offset) * 0.05
        adjusted_exp = exp * scale_factor
    
    # Binary search for level
    level = 1
    for i, threshold in enumerate(levels_table):
        if adjusted_exp >= threshold:
            level = min(i + 1, max_level)
        else:
            break
    
    return level
