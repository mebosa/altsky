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
                "texture": item_id,  # Use item_id directly, frontend will resolve texture via Hypixel Items API
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
