"""
Shard data extraction for Hypixel SkyBlock.

Shards are collectible items from hunting mobs on Galatea island.
The Hypixel API provides statistics about shard hunting but not individual shard ownership.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

LOGGER = logging.getLogger(__name__)

# Shard categories with display names
SHARD_CATEGORIES = {
    "combat": "Combat",
    "fishing": "Fishing", 
    "forest": "Forest",
    "trap": "Trap",
    "salt": "Salt",
}


def extract_player_shards(member_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract shard hunting statistics from player profile data.
    
    Note: The Hypixel API provides aggregate statistics (unique_shards count, hunt counts)
    but does not expose which specific shards a player owns.
    
    Returns hunting statistics and unique shard count.
    """
    # Get shard hunting stats from player_stats
    player_stats = member_data.get("player_stats", {})
    unique_shards = int(player_stats.get("unique_shards", 0))
    shard_combat_hunts = int(player_stats.get("shard_combat_hunts", 0))
    shard_fishing_hunts = int(player_stats.get("shard_fishing_hunts", 0))
    shard_forest_hunts = int(player_stats.get("shard_forest_hunts", 0))
    shard_trap_hunts = int(player_stats.get("shard_trap_hunts", 0))
    shard_salt_hunts = int(player_stats.get("shard_salt_hunts", 0))
    
    total_hunts = (
        shard_combat_hunts + 
        shard_fishing_hunts + 
        shard_forest_hunts + 
        shard_trap_hunts + 
        shard_salt_hunts
    )
    
    return {
        "stats": {
            "unique_shards": unique_shards,
            "total_hunts": total_hunts,
            "hunts": {
                "combat": shard_combat_hunts,
                "fishing": shard_fishing_hunts,
                "forest": shard_forest_hunts,
                "trap": shard_trap_hunts,
                "salt": shard_salt_hunts,
            },
        },
        "categories": SHARD_CATEGORIES,
    }
