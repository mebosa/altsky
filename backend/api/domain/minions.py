from typing import List, Dict, Any, Set

# Minion slots based on unique tiers crafted
MINION_SLOTS = {
    0: 5, 5: 6, 15: 7, 30: 8, 50: 9, 75: 10,
    100: 11, 125: 12, 150: 13, 175: 14, 200: 15,
    225: 16, 250: 17, 275: 18, 300: 19, 350: 20,
    400: 21, 450: 22, 500: 23, 550: 24, 600: 25, 650: 26
}

# All minions categorized by type
MINIONS = {
    "farming": {
        "COCOA": {"name": "Cocoa", "maxTier": 12},
        "PUMPKIN": {"name": "Pumpkin", "maxTier": 12},
        "CHICKEN": {"name": "Chicken", "maxTier": 12},
        "MUSHROOM": {"name": "Mushroom", "maxTier": 12},
        "CACTUS": {"name": "Cactus", "maxTier": 12},
        "PIG": {"name": "Pig", "maxTier": 12},
        "WHEAT": {"name": "Wheat", "maxTier": 12},
        "COW": {"name": "Cow", "maxTier": 12},
        "RABBIT": {"name": "Rabbit", "maxTier": 12},
        "SUGAR_CANE": {"name": "Sugar Cane", "maxTier": 12},
        "MELON": {"name": "Melon", "maxTier": 12},
        "NETHER_WARTS": {"name": "Nether Wart", "maxTier": 12},
        "CARROT": {"name": "Carrot", "maxTier": 12},
        "POTATO": {"name": "Potato", "maxTier": 12},
        "SHEEP": {"name": "Sheep", "maxTier": 12},
    },
    "mining": {
        "HARD_STONE": {"name": "Hard Stone", "maxTier": 12},
        "RED_SAND": {"name": "Red Sand", "maxTier": 12},
        "MYCELIUM": {"name": "Mycelium", "maxTier": 12},
        "COBBLESTONE": {"name": "Cobblestone", "maxTier": 12},
        "OBSIDIAN": {"name": "Obsidian", "maxTier": 12},
        "GLOWSTONE": {"name": "Glowstone", "maxTier": 12},
        "GRAVEL": {"name": "Gravel", "maxTier": 11},
        "SAND": {"name": "Sand", "maxTier": 11},
        "ICE": {"name": "Ice", "maxTier": 12},
        "SNOW": {"name": "Snow", "maxTier": 12},
        "COAL": {"name": "Coal", "maxTier": 12},
        "IRON": {"name": "Iron", "maxTier": 12},
        "GOLD": {"name": "Gold", "maxTier": 12},
        "DIAMOND": {"name": "Diamond", "maxTier": 12},
        "LAPIS": {"name": "Lapis", "maxTier": 12},
        "REDSTONE": {"name": "Redstone", "maxTier": 12},
        "EMERALD": {"name": "Emerald", "maxTier": 12},
        "MITHRIL": {"name": "Mithril", "maxTier": 12},
        "QUARTZ": {"name": "Quartz", "maxTier": 12},
        "ENDER_STONE": {"name": "End Stone", "maxTier": 11},
    },
    "combat": {
        "ZOMBIE": {"name": "Zombie", "maxTier": 11},
        "REVENANT": {"name": "Revenant", "maxTier": 12},
        "SKELETON": {"name": "Skeleton", "maxTier": 11},
        "CREEPER": {"name": "Creeper", "maxTier": 11},
        "SPIDER": {"name": "Spider", "maxTier": 11},
        "TARANTULA": {"name": "Tarantula", "maxTier": 11},
        "CAVESPIDER": {"name": "Cave Spider", "maxTier": 11},
        "BLAZE": {"name": "Blaze", "maxTier": 12},
        "MAGMA_CUBE": {"name": "Magma Cube", "maxTier": 12},
        "ENDERMAN": {"name": "Enderman", "maxTier": 11},
        "GHAST": {"name": "Ghast", "maxTier": 12},
        "SLIME": {"name": "Slime", "maxTier": 11},
        "VOIDLING": {"name": "Voidling", "maxTier": 11},
        "INFERNO": {"name": "Inferno", "maxTier": 11},
        "VAMPIRE": {"name": "Vampire", "maxTier": 11},
    },
    "foraging": {
        "OAK": {"name": "Oak", "maxTier": 11},
        "BIRCH": {"name": "Birch", "maxTier": 11},
        "SPRUCE": {"name": "Spruce", "maxTier": 11},
        "DARK_OAK": {"name": "Dark Oak", "maxTier": 11},
        "ACACIA": {"name": "Acacia", "maxTier": 11},
        "JUNGLE": {"name": "Jungle", "maxTier": 11},
        "FLOWER": {"name": "Flower", "maxTier": 12},
    },
    "fishing": {
        "FISHING": {"name": "Fishing", "maxTier": 11},
        "CLAY": {"name": "Clay", "maxTier": 11},
    },
}

def get_minion_slots(unlocked_tiers: int) -> Dict[str, Any]:
    """Calculate minion slots based on unlocked unique tiers"""
    thresholds = sorted(MINION_SLOTS.keys())
    current_slots = 5
    next_threshold = None
    tiers_needed = None
    
    for i, threshold in enumerate(thresholds):
        if unlocked_tiers >= threshold:
            current_slots = MINION_SLOTS[threshold]
            if i + 1 < len(thresholds):
                next_threshold = thresholds[i + 1]
                tiers_needed = next_threshold - unlocked_tiers
        else:
            next_threshold = threshold
            tiers_needed = threshold - unlocked_tiers
            break
    
    return {
        "current": current_slots,
        "next_threshold": next_threshold,
        "tiers_until_next": tiers_needed
    }


def parse_minions(member: Dict[str, Any]) -> Dict[str, Any]:
    crafted_generators = member.get("crafted_generators", [])
    
    # Parse crafted generators into minion ID -> list of tiers
    minion_tiers: Dict[str, List[int]] = {}
    
    for generator in crafted_generators:
        parts = generator.rsplit("_", 1)
        if len(parts) != 2:
            continue
            
        minion_id = parts[0]
        try:
            tier = int(parts[1])
        except ValueError:
            continue
            
        if minion_id not in minion_tiers:
            minion_tiers[minion_id] = []
        
        if tier not in minion_tiers[minion_id]:
            minion_tiers[minion_id].append(tier)
    
    # Build category-based output
    categories: Dict[str, Any] = {}
    total_unlocked_tiers = 0
    total_minions = 0
    maxed_minions = 0
    total_unlockable_tiers = 0
    
    for category, minion_defs in MINIONS.items():
        cat_minions = []
        cat_unlocked = 0
        cat_maxed = 0
        cat_unlockable = 0
        
        for minion_id, minion_info in minion_defs.items():
            tiers = sorted(list(set(minion_tiers.get(minion_id, []))))
            max_tier = max(tiers) if tiers else 0
            max_possible = minion_info["maxTier"]
            unlocked_count = len(tiers)
            
            cat_minions.append({
                "id": minion_id,
                "name": minion_info["name"],
                "tiers": tiers,
                "tier": max_tier,
                "maxTier": max_possible,
                "unlockedTiers": unlocked_count,
                "isMaxed": max_tier >= max_possible
            })
            
            cat_unlocked += unlocked_count
            cat_unlockable += max_possible
            if max_tier >= max_possible:
                cat_maxed += 1
        
        # Sort minions by name
        cat_minions.sort(key=lambda x: x["name"])
        
        categories[category] = {
            "minions": cat_minions,
            "totalMinions": len(cat_minions),
            "maxedMinions": cat_maxed,
            "unlockedTiers": cat_unlocked,
            "unlockableTiers": cat_unlockable
        }
        
        total_unlocked_tiers += cat_unlocked
        total_minions += len(cat_minions)
        maxed_minions += cat_maxed
        total_unlockable_tiers += cat_unlockable
    
    # Calculate minion slots
    slots = get_minion_slots(total_unlocked_tiers)
    
    return {
        "categories": categories,
        "totalMinions": total_minions,
        "maxedMinions": maxed_minions,
        "unlockedTiers": total_unlocked_tiers,
        "unlockableTiers": total_unlockable_tiers,
        "slots": slots
    }
