"""
Collection data processing for Hypixel SkyBlock profiles.
"""
from typing import Dict, Any, List, Optional
import time
import logging
import requests

LOGGER = logging.getLogger(__name__)

# Collection resources cache
_COLLECTIONS_CACHE: Dict[str, Any] = {}
_COLLECTIONS_FETCHED_AT = 0.0
_COLLECTIONS_TTL_SECONDS = 60 * 60  # 1 hour (rarely changes)

# Item ID to texture mapping for common items
COLLECTION_TEXTURES: Dict[str, str] = {
    # Farming
    "WHEAT": "wheat",
    "CARROT_ITEM": "carrot",
    "POTATO_ITEM": "potato",
    "PUMPKIN": "pumpkin",
    "MELON": "melon",
    "SEEDS": "seeds",
    "RED_MUSHROOM": "red_mushroom",
    "BROWN_MUSHROOM": "brown_mushroom",
    "INK_SACK:3": "cocoa_beans",
    "CACTUS": "cactus",
    "SUGAR_CANE": "sugar_cane",
    "FEATHER": "feather",
    "LEATHER": "leather",
    "PORK": "porkchop",
    "RAW_CHICKEN": "raw_chicken",
    "MUTTON": "mutton",
    "RABBIT": "rabbit",
    "NETHER_STALK": "nether_wart",
    
    # Mining
    "COBBLESTONE": "cobblestone",
    "COAL": "coal",
    "IRON_INGOT": "iron_ingot",
    "GOLD_INGOT": "gold_ingot",
    "DIAMOND": "diamond",
    "INK_SACK:4": "lapis_lazuli",
    "EMERALD": "emerald",
    "REDSTONE": "redstone",
    "QUARTZ": "nether_quartz",
    "OBSIDIAN": "obsidian",
    "GLOWSTONE_DUST": "glowstone_dust",
    "GRAVEL": "gravel",
    "ICE": "ice",
    "NETHERRACK": "netherrack",
    "SAND": "sand",
    "ENDER_STONE": "end_stone",
    "MITHRIL_ORE": "prismarine_crystals",
    "HARD_STONE": "stone",
    "GEMSTONE_COLLECTION": "emerald",
    "MYCEL": "mycelium",
    "RED_SAND": "red_sand",
    "SULPHUR": "sulphur",
    "SNOW_BALL": "snowball",
    "TITANIUM": "iron_ingot",
    "STARFALL": "nether_star",
    "GLACITE": "packed_ice",
    "UMBER": "brown_dye",
    "TUNGSTEN": "iron_block",
    
    # Combat
    "ROTTEN_FLESH": "rotten_flesh",
    "BONE": "bone",
    "STRING": "string",
    "SPIDER_EYE": "spider_eye",
    "SULPHUR_ORE": "sulphur",
    "GUNPOWDER": "gunpowder",
    "ENDER_PEARL": "ender_pearl",
    "GHAST_TEAR": "ghast_tear",
    "SLIME_BALL": "slime_ball",
    "BLAZE_ROD": "blaze_rod",
    "MAGMA_CREAM": "magma_cream",
    "CHILI_PEPPER": "blaze_powder",
    
    # Foraging
    "LOG": "oak_log",
    "LOG:1": "spruce_log",
    "LOG:2": "birch_log",
    "LOG_2:1": "dark_oak_log",
    "LOG_2": "acacia_log",
    "LOG:3": "jungle_log",
    
    # Fishing
    "RAW_FISH": "raw_fish",
    "RAW_FISH:1": "salmon",
    "RAW_FISH:2": "clownfish",
    "RAW_FISH:3": "pufferfish",
    "PRISMARINE_SHARD": "prismarine_shard",
    "PRISMARINE_CRYSTALS": "prismarine_crystals",
    "CLAY_BALL": "clay_ball",
    "WATER_LILY": "lily_pad",
    "INK_SACK": "ink_sac",
    "SPONGE": "sponge",
    "MAGMAFISH": "magma_cream",
    
    # Rift
    "AGARICUS_CAP": "red_mushroom",
    "CADUCOUS_STEM": "stick",
    "WILTED_BERBERIS": "dead_bush",
    "HALF_EATEN_CARROT": "carrot",
    "HEMOVIBE": "redstone",
    "LIVING_METAL_HEART": "iron_block",
    "EFFERVESCENT_SOUL": "ghast_tear",
}

# Category icons
CATEGORY_META: Dict[str, Dict[str, str]] = {
    "FARMING": {"name": "Farming", "icon": "🌾", "color": "#7cd95a"},
    "MINING": {"name": "Mining", "icon": "⛏️", "color": "#5ac8d9"},
    "COMBAT": {"name": "Combat", "icon": "⚔️", "color": "#d95a5a"},
    "FORAGING": {"name": "Foraging", "icon": "🌲", "color": "#8b5a2b"},
    "FISHING": {"name": "Fishing", "icon": "🎣", "color": "#5a9cd9"},
    "RIFT": {"name": "Rift", "icon": "🌀", "color": "#a855f7"},
    "BOSS": {"name": "Boss", "icon": "💀", "color": "#ff6b6b"},
}


def _fetch_collection_resources() -> Dict[str, Any]:
    """Fetch collection tier requirements from Hypixel API with caching."""
    global _COLLECTIONS_CACHE, _COLLECTIONS_FETCHED_AT
    
    now = time.time()
    if _COLLECTIONS_CACHE and now - _COLLECTIONS_FETCHED_AT < _COLLECTIONS_TTL_SECONDS:
        return _COLLECTIONS_CACHE
    
    try:
        response = requests.get(
            'https://api.hypixel.net/v2/resources/skyblock/collections',
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        
        if data.get('success') and 'collections' in data:
            _COLLECTIONS_CACHE = data['collections']
            _COLLECTIONS_FETCHED_AT = now
            return _COLLECTIONS_CACHE
            
    except requests.RequestException as exc:
        LOGGER.warning("Failed to fetch collection resources: %s", exc)
    except (ValueError, KeyError) as exc:
        LOGGER.warning("Failed to parse collection resources: %s", exc)
    
    return _COLLECTIONS_CACHE


def _get_tier_from_amount(tiers: List[Dict[str, Any]], amount: int) -> int:
    """Calculate the current tier based on collected amount."""
    tier = 0
    for tier_data in tiers:
        if amount >= tier_data.get('amountRequired', float('inf')):
            tier = tier_data.get('tier', 0)
        else:
            break
    return tier


def _get_next_tier_requirement(
    tiers: List[Dict[str, Any]], 
    current_tier: int
) -> Optional[int]:
    """Get the amount required for the next tier."""
    for tier_data in tiers:
        if tier_data.get('tier', 0) == current_tier + 1:
            return tier_data.get('amountRequired')
    return None


def _format_amount(amount: int) -> str:
    """Format large numbers with K/M/B suffix."""
    if amount >= 1_000_000_000:
        return f"{amount / 1_000_000_000:.1f}B"
    if amount >= 1_000_000:
        return f"{amount / 1_000_000:.1f}M"
    if amount >= 1_000:
        return f"{amount / 1_000:.1f}K"
    return str(amount)


def extract_collections_from_profile(member_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Extract and process collection data from a player profile.
    
    Args:
        member_data: The member data from the profile API response
        
    Returns:
        Processed collection data organized by category, or None if not available
    """
    raw_collections = member_data.get('collection', {})
    if not raw_collections:
        return None
    
    # Fetch tier requirements
    collection_resources = _fetch_collection_resources()
    if not collection_resources:
        # Return raw data if we can't fetch resources
        return {"raw": raw_collections}
    
    output: Dict[str, Any] = {
        "categories": {},
        "totalCollections": 0,
        "maxedCollections": 0,
        "totalTiers": 0,
        "unlockedTiers": 0,
    }
    
    category_order = ["FARMING", "MINING", "COMBAT", "FORAGING", "FISHING", "RIFT"]
    
    for category_id in category_order:
        category_data = collection_resources.get(category_id)
        if not category_data:
            continue
        
        category_name = category_data.get('name', category_id.title())
        items_data = category_data.get('items', {})
        
        collections_list: List[Dict[str, Any]] = []
        category_maxed = 0
        category_total_tiers = 0
        category_unlocked_tiers = 0
        
        for item_id, item_info in items_data.items():
            item_name = item_info.get('name', item_id)
            max_tier = item_info.get('maxTiers', 0)
            tiers = item_info.get('tiers', [])
            
            # Player's collected amount
            amount = raw_collections.get(item_id, 0)
            
            # Calculate current tier
            current_tier = _get_tier_from_amount(tiers, amount)
            
            # Get next tier requirement
            next_tier_req = _get_next_tier_requirement(tiers, current_tier)
            
            # Progress to next tier
            progress = 0
            if next_tier_req and current_tier < max_tier:
                # Find current tier requirement
                current_tier_req = 0
                for t in tiers:
                    if t.get('tier') == current_tier:
                        current_tier_req = t.get('amountRequired', 0)
                        break
                
                if next_tier_req > current_tier_req:
                    progress = ((amount - current_tier_req) / (next_tier_req - current_tier_req)) * 100
                    progress = max(0, min(100, progress))
            elif current_tier >= max_tier:
                progress = 100
            
            is_maxed = current_tier >= max_tier
            
            collections_list.append({
                "id": item_id,
                "name": item_name,
                "amount": amount,
                "amountFormatted": _format_amount(amount),
                "tier": current_tier,
                "maxTier": max_tier,
                "isMaxed": is_maxed,
                "progress": round(progress, 1),
                "nextTierReq": next_tier_req,
                "nextTierReqFormatted": _format_amount(next_tier_req) if next_tier_req else None,
                "texture": COLLECTION_TEXTURES.get(item_id, "barrier"),
            })
            
            category_total_tiers += max_tier
            category_unlocked_tiers += current_tier
            if is_maxed:
                category_maxed += 1
        
        # Sort by amount (descending), then by name
        collections_list.sort(key=lambda x: (-x['tier'], -x['amount'], x['name']))
        
        meta = CATEGORY_META.get(category_id, {"name": category_id.title(), "icon": "📦", "color": "#888"})
        
        output["categories"][category_id.lower()] = {
            "name": meta["name"],
            "icon": meta["icon"],
            "color": meta["color"],
            "collections": collections_list,
            "totalCollections": len(collections_list),
            "maxedCollections": category_maxed,
            "totalTiers": category_total_tiers,
            "unlockedTiers": category_unlocked_tiers,
        }
        
        output["totalCollections"] += len(collections_list)
        output["maxedCollections"] += category_maxed
        output["totalTiers"] += category_total_tiers
        output["unlockedTiers"] += category_unlocked_tiers
    
    return output
