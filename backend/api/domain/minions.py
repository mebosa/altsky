from typing import List, Dict, Any, Set, Optional
import time
import logging
import requests
from ..http_client import session

LOGGER = logging.getLogger(__name__)

# Bazaar price cache
_BAZAAR_CACHE: Dict[str, Dict[str, float]] = {}
_BAZAAR_FETCHED_AT = 0.0
_BAZAAR_TTL_SECONDS = 5 * 60  # 5 minutes

# Minion slots based on unique tiers crafted
MINION_SLOTS = {
    0: 5, 5: 6, 15: 7, 30: 8, 50: 9, 75: 10,
    100: 11, 125: 12, 150: 13, 175: 14, 200: 15,
    225: 16, 250: 17, 275: 18, 300: 19, 350: 20,
    400: 21, 450: 22, 500: 23, 550: 24, 600: 25, 650: 26
}

# Elizabeth community shop upgrades add +1 slot each (up to 5 slots)
ELIZABETH_SLOT_UPGRADES_MAX = 5


def _fetch_bazaar_prices() -> Dict[str, Dict[str, float]]:
    """Fetch bazaar prices from Hypixel API with caching"""
    global _BAZAAR_CACHE, _BAZAAR_FETCHED_AT
    
    now = time.time()
    if _BAZAAR_CACHE and now - _BAZAAR_FETCHED_AT < _BAZAAR_TTL_SECONDS:
        return _BAZAAR_CACHE
    
    try:
        response = session.get('https://api.hypixel.net/v2/skyblock/bazaar', timeout=8)
        response.raise_for_status()
        data = response.json()
        
        if data.get('success') and 'products' in data:
            prices = {}
            for product_id, product_data in data['products'].items():
                quick_status = product_data.get('quick_status', {})
                prices[product_id] = {
                    'buyPrice': quick_status.get('buyPrice', 0),
                    'sellPrice': quick_status.get('sellPrice', 0)
                }
            
            _BAZAAR_CACHE = prices
            _BAZAAR_FETCHED_AT = now
            return prices
            
    except requests.RequestException as exc:
        LOGGER.warning("Failed to fetch bazaar prices: %s", exc)
    except (ValueError, KeyError) as exc:
        LOGGER.warning("Failed to parse bazaar data: %s", exc)
    
    return _BAZAAR_CACHE


# Minion base materials for crafting cost calculation
# Maps minion_id -> list of (item_id, enchanted_item_id) for bazaar lookup
MINION_MATERIALS = {
    # Farming
    "COCOA": ("COCOA_BEANS", "ENCHANTED_COCOA"),
    "PUMPKIN": ("PUMPKIN", "ENCHANTED_PUMPKIN"),
    "CHICKEN": ("RAW_CHICKEN", "ENCHANTED_RAW_CHICKEN"),
    "MUSHROOM": ("RED_MUSHROOM", "ENCHANTED_RED_MUSHROOM"),
    "CACTUS": ("CACTUS", "ENCHANTED_CACTUS_GREEN"),
    "PIG": ("PORK", "ENCHANTED_PORK"),
    "WHEAT": ("WHEAT", "ENCHANTED_BREAD"),
    "COW": ("RAW_BEEF", "ENCHANTED_RAW_BEEF"),
    "RABBIT": ("RABBIT", "ENCHANTED_RABBIT"),
    "SUGAR_CANE": ("SUGAR_CANE", "ENCHANTED_SUGAR"),
    "MELON": ("MELON", "ENCHANTED_MELON"),
    "NETHER_WARTS": ("NETHER_STALK", "ENCHANTED_NETHER_STALK"),
    "CARROT": ("CARROT_ITEM", "ENCHANTED_CARROT"),
    "POTATO": ("POTATO_ITEM", "ENCHANTED_POTATO"),
    "SHEEP": ("MUTTON", "ENCHANTED_MUTTON"),
    # Mining
    "HARD_STONE": ("HARD_STONE", "ENCHANTED_HARD_STONE"),
    "RED_SAND": ("RED_SAND", "ENCHANTED_RED_SAND_CUBE"),
    "MYCELIUM": ("MYCEL", "ENCHANTED_MYCELIUM"),
    "COBBLESTONE": ("COBBLESTONE", "ENCHANTED_COBBLESTONE"),
    "OBSIDIAN": ("OBSIDIAN", "ENCHANTED_OBSIDIAN"),
    "GLOWSTONE": ("GLOWSTONE_DUST", "ENCHANTED_GLOWSTONE_DUST"),
    "GRAVEL": ("GRAVEL", "ENCHANTED_FLINT"),
    "SAND": ("SAND", "ENCHANTED_SAND"),
    "ICE": ("ICE", "ENCHANTED_ICE"),
    "SNOW": ("SNOW_BALL", "ENCHANTED_SNOW_BLOCK"),
    "COAL": ("COAL", "ENCHANTED_COAL"),
    "IRON": ("IRON_INGOT", "ENCHANTED_IRON"),
    "GOLD": ("GOLD_INGOT", "ENCHANTED_GOLD"),
    "DIAMOND": ("DIAMOND", "ENCHANTED_DIAMOND"),
    "LAPIS": ("INK_SACK:4", "ENCHANTED_LAPIS_LAZULI"),
    "REDSTONE": ("REDSTONE", "ENCHANTED_REDSTONE"),
    "EMERALD": ("EMERALD", "ENCHANTED_EMERALD"),
    "MITHRIL": ("MITHRIL_ORE", "ENCHANTED_MITHRIL"),
    "QUARTZ": ("QUARTZ", "ENCHANTED_QUARTZ"),
    "ENDER_STONE": ("ENDER_STONE", "ENCHANTED_ENDSTONE"),
    # Combat
    "ZOMBIE": ("ROTTEN_FLESH", "ENCHANTED_ROTTEN_FLESH"),
    "REVENANT": ("REVENANT_FLESH", "ENCHANTED_ROTTEN_FLESH"),
    "SKELETON": ("BONE", "ENCHANTED_BONE"),
    "CREEPER": ("SULPHUR", "ENCHANTED_GUNPOWDER"),
    "SPIDER": ("STRING", "ENCHANTED_STRING"),
    "TARANTULA": ("TARANTULA_WEB", "ENCHANTED_STRING"),
    "CAVESPIDER": ("STRING", "ENCHANTED_STRING"),
    "BLAZE": ("BLAZE_ROD", "ENCHANTED_BLAZE_ROD"),
    "MAGMA_CUBE": ("MAGMA_CREAM", "ENCHANTED_MAGMA_CREAM"),
    "ENDERMAN": ("ENDER_PEARL", "ENCHANTED_ENDER_PEARL"),
    "GHAST": ("GHAST_TEAR", "ENCHANTED_GHAST_TEAR"),
    "SLIME": ("SLIME_BALL", "ENCHANTED_SLIME_BALL"),
    "VOIDLING": ("NULL_ATOM", "ENCHANTED_ENDER_PEARL"),
    "INFERNO": ("INFERNO_VERTEX", "ENCHANTED_BLAZE_ROD"),
    "VAMPIRE": ("VAMPIRE_FANG", "ENCHANTED_ROTTEN_FLESH"),
    # Foraging
    "OAK": ("LOG", "ENCHANTED_OAK_LOG"),
    "BIRCH": ("LOG:2", "ENCHANTED_BIRCH_LOG"),
    "SPRUCE": ("LOG:1", "ENCHANTED_SPRUCE_LOG"),
    "DARK_OAK": ("LOG_2:1", "ENCHANTED_DARK_OAK_LOG"),
    "ACACIA": ("LOG_2", "ENCHANTED_ACACIA_LOG"),
    "JUNGLE": ("LOG:3", "ENCHANTED_JUNGLE_LOG"),
    "FLOWER": ("RED_ROSE", "ENCHANTED_RED_ROSE"),
    "SUNFLOWER": ("SUNFLOWER", "ENCHANTED_SUNFLOWER"),
    "MOONFLOWER": ("MOONFLOWER", "ENCHANTED_MOONFLOWER"),
    # Fishing
    "FISHING": ("RAW_FISH", "ENCHANTED_RAW_FISH"),
    "CLAY": ("CLAY_BALL", "ENCHANTED_CLAY_BALL"),
}

# Tier crafting requirements: tier -> (base_per_slot, uses_enchanted)
# Tier 1-4 use base materials, Tier 5+ use enchanted materials
# 8 slots around the center (tool or previous tier minion)
TIER_CRAFTING = {
    1: (10, False),   # 80 base items total
    2: (20, False),   # 160 base items
    3: (40, False),   # 320 base items
    4: (64, False),   # 512 base items
    5: (1, True),     # 8 enchanted items
    6: (2, True),     # 16 enchanted items
    7: (4, True),     # 32 enchanted items
    8: (8, True),     # 64 enchanted items
    9: (16, True),    # 128 enchanted items
    10: (32, True),   # 256 enchanted items
    11: (64, True),   # 512 enchanted items
    12: (128, True),  # 1024 enchanted items
}


def _calculate_craft_cost(minion_id: str, tier: int, bazaar_prices: Dict[str, Dict[str, float]]) -> Optional[int]:
    """Calculate the total bazaar cost to craft a minion tier from materials only (excludes previous tier)"""
    if tier < 1 or tier > 12:
        return None
    
    materials = MINION_MATERIALS.get(minion_id)
    if not materials:
        return None
    
    tier_info = TIER_CRAFTING.get(tier)
    if not tier_info:
        return None
    
    per_slot, uses_enchanted = tier_info
    total_slots = 8  # 8 slots around center
    total_needed = per_slot * total_slots
    
    item_id = materials[1] if uses_enchanted else materials[0]
    
    # Handle items with metadata (like LOG:2)
    bazaar_key = item_id.replace(":", "-")
    if ":" in item_id:
        # Try alternate formats
        base_id = item_id.split(":")[0]
        metadata = item_id.split(":")[1]
        bazaar_key = f"{base_id}:{metadata}"
    
    price_data = bazaar_prices.get(bazaar_key) or bazaar_prices.get(item_id)
    
    if not price_data or price_data.get('buyPrice', 0) <= 0:
        return None
    
    return int(price_data['buyPrice'] * total_needed)


def _get_minion_upgrade_cost(minion_id: str, from_tier: int, to_tier: int, bazaar_prices: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
    """Calculate cost to upgrade minion from one tier to another
    
    Returns dict with:
    - craftCost: int or None - estimated cost to craft from bazaar materials
    - materials: str - description of materials needed
    """
    # Calculate material cost for the target tier
    craft_cost = _calculate_craft_cost(minion_id, to_tier, bazaar_prices)
    
    # Get material info for display
    materials = MINION_MATERIALS.get(minion_id)
    tier_info = TIER_CRAFTING.get(to_tier, (0, False))
    per_slot, uses_enchanted = tier_info
    total_needed = per_slot * 8
    
    material_name = ""
    if materials:
        item_id = materials[1] if uses_enchanted else materials[0]
        # Clean up item name for display
        material_name = item_id.replace("_", " ").replace("ENCHANTED ", "Ench ").title()
        material_name = f"{total_needed}x {material_name}"
    
    return {
        'craftCost': craft_cost,
        'materials': material_name,
        'usesEnchanted': uses_enchanted
    }

# Minecraft heads base URL
MC_HEADS_BASE = "https://mc-heads.net/head"

# All minions categorized by type with textures
MINIONS = {
    "farming": {
        "COCOA": {"name": "Cocoa", "maxTier": 12, "texture": "acb680e96f6177cd8ffaf27e9625d8b544d720afc50738801818d0e745c0e5f7"},
        "PUMPKIN": {"name": "Pumpkin", "maxTier": 12, "texture": "f3fb663e843a7da787e290f23c8af2f97f7b6f572fa59a0d4d02186db6eaabb7"},
        "CHICKEN": {"name": "Chicken", "maxTier": 12, "texture": "a04b7da13b0a97839846aa5648f5ac6736ba0ca9fbf38cd366916e417153fd7f"},
        "MUSHROOM": {"name": "Mushroom", "maxTier": 12, "texture": "4a3b58341d196a9841ef1526b367209cbc9f96767c24f5f587cf413d42b74a93"},
        "CACTUS": {"name": "Cactus", "maxTier": 12, "texture": "ef93ec6e67a6cd272c9a9684b67df62584cb084a265eee3cde141d20e70d7d72"},
        "PIG": {"name": "Pig", "maxTier": 12, "texture": "a9bb5f0c56408c73cfa412345c8fc51f75b6c7311ae60e7099c4781c48760562"},
        "WHEAT": {"name": "Wheat", "maxTier": 12, "texture": "bbc571c5527336352e2fee2b40a9edfa2e809f64230779aa01253c6aa535881b"},
        "COW": {"name": "Cow", "maxTier": 12, "texture": "c2fd8976e1b64aebfd38afbe62aa1429914253df3417ace1f589e5cf45fbd717"},
        "RABBIT": {"name": "Rabbit", "maxTier": 12, "texture": "ef59c052d339bb6305cad370fd8c52f58269a957dfaf433a255597d95e68a373"},
        "SUGAR_CANE": {"name": "Sugar Cane", "maxTier": 12, "texture": "2fced0e80f0d7a5d1f45a1a7217e6a99ea9720156c63f6efc84916d4837fabde"},
        "MELON": {"name": "Melon", "maxTier": 12, "texture": "95d54539ac8d3fba9696c91f4dcc7f15c320ab86029d5c92f12359abd4df811e"},
        "NETHER_WARTS": {"name": "Nether Wart", "maxTier": 12, "texture": "71a4620bb3459c1c2fa74b210b1c07b4a02254351f75173e643a0e009a63f558"},
        "CARROT": {"name": "Carrot", "maxTier": 12, "texture": "4baea990b45d330998cb0c1f8515c27b24f93bff1df0db056e647f8200d03b9d"},
        "POTATO": {"name": "Potato", "maxTier": 12, "texture": "7dda35a044cb0374b516015d991a0f65bf7d0fb6566e350496642cf2059ff1d9"},
        "SHEEP": {"name": "Sheep", "maxTier": 12, "texture": "fd15d4b8bce708f77f963f1b4e87b1b969fef1766a3e9b67b249c59d5e80e8c5"},
    },
    "mining": {
        "HARD_STONE": {"name": "Hard Stone", "maxTier": 12, "texture": "1e8bab9493708beda34255606d5883b8762746bcbe6c94e8ca78a77a408c8ba8"},
        "RED_SAND": {"name": "Red Sand", "maxTier": 12, "texture": "9d24991435e4e7fb1a9ad23db75c80aec300d003ec0c5963e0ed658634027889"},
        "MYCELIUM": {"name": "Mycelium", "maxTier": 12, "texture": "fc8ebad72b77df3990e07bc869a99a8f8962d3c19c76e39d99553cae4131cc8"},
        "COBBLESTONE": {"name": "Cobblestone", "maxTier": 12, "texture": "2f93289a82bd2a06cbbe61b733cfdc1f1bd93c4340f7a90abd9bdda774109071"},
        "OBSIDIAN": {"name": "Obsidian", "maxTier": 12, "texture": "320c29ab966637cb9aecc34ee76d5a0130461e0c4fdb08cdaf80939fa1209102"},
        "GLOWSTONE": {"name": "Glowstone", "maxTier": 12, "texture": "20f4d7c26b0310990a7d3a3b45948b95dd4ab407a16a4b6d3b7cb4fba031aeed"},
        "GRAVEL": {"name": "Gravel", "maxTier": 11, "texture": "7458507ed31cf9a38986ac8795173c609637f03da653f30483a721d3fbe602d"},
        "SAND": {"name": "Sand", "maxTier": 11, "texture": "81f8e2ad021eefd1217e650e848b57622144d2bf8a39fbd50dab937a7eac10de"},
        "ICE": {"name": "Ice", "maxTier": 12, "texture": "e500064321b12972f8e5750793ec1c823da4627535e9d12feaee78394b86dabe"},
        "SNOW": {"name": "Snow", "maxTier": 12, "texture": "f6d180684c3521c9fc89478ba4405ae9ce497da8124fa0da5a0126431c4b78c3"},
        "COAL": {"name": "Coal", "maxTier": 12, "texture": "425b8d2ea965c780652d29c26b1572686fd74f6fe6403b5a3800959feb2ad935"},
        "IRON": {"name": "Iron", "maxTier": 12, "texture": "af435022cb3809a68db0fccfa8993fc1954dc697a7181494905b03fdda035e4a"},
        "GOLD": {"name": "Gold", "maxTier": 12, "texture": "f6da04ed8c810be29bba53c62e712d65cfb25238117b94d7e85a4615775bf14f"},
        "DIAMOND": {"name": "Diamond", "maxTier": 12, "texture": "2354bbe604dfe58bf92e7729730d0c8e37844e831ee3816d7e8427c27a1824a2"},
        "LAPIS": {"name": "Lapis", "maxTier": 12, "texture": "64fd97b9346c1208c1db3957530cdfc5789e3e65943786b0071cf2b2904a6b5c"},
        "REDSTONE": {"name": "Redstone", "maxTier": 12, "texture": "1edefcf1a89d687a0a4ecf1589977af1e520fc673c48a0434be426612e8faa67"},
        "EMERALD": {"name": "Emerald", "maxTier": 12, "texture": "9bf57f3401b130c6b53808f2b1e119cc7b984622dac7077bbd53454e1f65bbf0"},
        "MITHRIL": {"name": "Mithril", "maxTier": 12, "texture": "c62fa670ff8599b32ab344195ba15f3ef64c3a8aa8a37821c08375950cb74cd0"},
        "QUARTZ": {"name": "Quartz", "maxTier": 12, "texture": "d270093be62dfd3019f908043db570b5dfd366fd5345fccf9da340e75c701a60"},
        "ENDER_STONE": {"name": "End Stone", "maxTier": 11, "texture": "7994be3dcfbb4ed0a5a7495b7335af1a3ced0b5888b5007286a790767c3b57e6"},
    },
    "combat": {
        "ZOMBIE": {"name": "Zombie", "maxTier": 11, "texture": "196063a884d3901c41f35b69a8c9f401c61ac9f6330f964f80c35352c3e8bfb0"},
        "REVENANT": {"name": "Revenant", "maxTier": 12, "texture": "a3dce8555923558d8d74c2a2b261b2b2d630559db54ef97ed3f9c30e9a20aba"},
        "SKELETON": {"name": "Skeleton", "maxTier": 11, "texture": "2fe009c5cfa44c05c88e5df070ae2533bd682a728e0b33bfc93fd92a6e5f3f64"},
        "CREEPER": {"name": "Creeper", "maxTier": 11, "texture": "54a92c2f8c1b3774e80492200d0b2218d7b019314a73c9cb5b9f04cfcacec471"},
        "SPIDER": {"name": "Spider", "maxTier": 11, "texture": "e77c4c284e10dea038f004d7eb43ac493de69f348d46b5c1f8ef8154ec2afdd0"},
        "TARANTULA": {"name": "Tarantula", "maxTier": 11, "texture": "97e86007064c9ce26eb4bad8ac9aa30aac309e70a9e0b615936318dea40a721"},
        "CAVESPIDER": {"name": "Cave Spider", "maxTier": 11, "texture": "5d815df973bcd01ee8dfdb3bd74f0b7cb8fef2a70559e4faa5905127bbb4a435"},
        "BLAZE": {"name": "Blaze", "maxTier": 12, "texture": "3208fbd64e97c6e00853d36b3a201e4803cae43dcbd6936a3cece050912e1f20"},
        "MAGMA_CUBE": {"name": "Magma Cube", "maxTier": 12, "texture": "18c9a7a24da7e3182e4f62fa62762e21e1680962197c7424144ae1d2c42174f7"},
        "ENDERMAN": {"name": "Enderman", "maxTier": 11, "texture": "e460d20ba1e9cd1d4cfd6d5fb0179ff41597ac6d2461bd7ccdb58b20291ec46e"},
        "GHAST": {"name": "Ghast", "maxTier": 12, "texture": "2478547d122ec83a818b46f3b13c5230429559e40c7d144d4ec225f92c1494b3"},
        "SLIME": {"name": "Slime", "maxTier": 11, "texture": "c95eced85db62c922724efca804ea0060c4a87fcdedf2fd5c4f9ac1130a6eb26"},
        "VOIDLING": {"name": "Voidling", "maxTier": 11, "texture": "3a851ed2ce5c2c0523af772d206d9555e2e1383ec87946e6ff4c51186e29ef7f"},
        "INFERNO": {"name": "Inferno", "maxTier": 11, "texture": "665c54366f88fb3280b1c3fc500ce2b799c8dd327ab6d41c9bc959488f5cfd92"},
        "VAMPIRE": {"name": "Vampire", "maxTier": 11, "texture": "5b0c2db42e90f83fae6551c96e83669211a77c2c155c54d1523af3079f9565ed"},
    },
    "foraging": {
        "OAK": {"name": "Oak", "maxTier": 11, "texture": "57e4a30f361204ea9cded3fbff850160731a0081cc452cfe26aed48e97f6364b"},
        "BIRCH": {"name": "Birch", "maxTier": 11, "texture": "eb74109dbb88178afb7a9874afc682904cedb3df75978a51f7beeb28f924251"},
        "SPRUCE": {"name": "Spruce", "maxTier": 11, "texture": "7ba04bfe516955fd43932dcb33bd5eac20b38a231d9fa8415b3fb301f60f7363"},
        "DARK_OAK": {"name": "Dark Oak", "maxTier": 11, "texture": "5ecdc8d6b2b7e081ed9c36609052c91879b89730b9953adbc987e25bf16c5581"},
        "ACACIA": {"name": "Acacia", "maxTier": 11, "texture": "42183eaf5b133b838db13d145247e389ab4b4f33c67846363792dc3d82b524c0"},
        "JUNGLE": {"name": "Jungle", "maxTier": 11, "texture": "2fe73d981690c1be346a16331819c4e8800859fcdc3e5153718c6ad45861924c"},
        "FLOWER": {"name": "Flower", "maxTier": 12, "texture": "baa7c59b2f792d8d091aecacf47a19f8ab93f3fd3c48f6930b1c2baeb09e0f9b"},
        "SUNFLOWER": {"name": "Sunflower", "maxTier": 12, "texture": "baa7c59b2f792d8d091aecacf47a19f8ab93f3fd3c48f6930b1c2baeb09e0f9b"},
        "MOONFLOWER": {"name": "Moonflower", "maxTier": 12, "texture": "baa7c59b2f792d8d091aecacf47a19f8ab93f3fd3c48f6930b1c2baeb09e0f9b"},
    },
    "fishing": {
        "FISHING": {"name": "Fishing", "maxTier": 12, "texture": "53ea0fd89524db3d7a3544904933830b4fc8899ef60c113d948bb3c4fe7aabb1"},
        "CLAY": {"name": "Clay", "maxTier": 12, "texture": "af9b312c8f53da289060e6452855072e07971458abbf338ddec351e16c171ff8"},
    },
}

def get_minion_slots(unlocked_tiers: int, community_upgrades: int = 0) -> Dict[str, Any]:
    """Calculate minion slots based on unlocked unique tiers and community upgrades"""
    thresholds = sorted(MINION_SLOTS.keys())
    base_slots = 5
    next_threshold = None
    tiers_needed = None
    
    for i, threshold in enumerate(thresholds):
        if unlocked_tiers >= threshold:
            base_slots = MINION_SLOTS[threshold]
            if i + 1 < len(thresholds):
                next_threshold = thresholds[i + 1]
                tiers_needed = next_threshold - unlocked_tiers
        else:
            next_threshold = threshold
            tiers_needed = threshold - unlocked_tiers
            break
    
    # Add Elizabeth community shop upgrades (max 5 extra slots)
    community_bonus = min(community_upgrades, ELIZABETH_SLOT_UPGRADES_MAX)
    total_slots = base_slots + community_bonus
    
    return {
        "current": total_slots,
        "fromUniques": base_slots,
        "fromCommunity": community_bonus,
        "next_threshold": next_threshold,
        "tiers_until_next": tiers_needed
    }


def parse_minions(member: Dict[str, Any], profile: Dict[str, Any] = None) -> Dict[str, Any]:
    # crafted_generators is nested under player_data in Hypixel API v2
    player_data = member.get("player_data", {})
    crafted_generators = player_data.get("crafted_generators", [])
    
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
    
    # Fetch bazaar prices for cost calculation
    bazaar_prices = _fetch_bazaar_prices()
    
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
            texture = minion_info.get("texture", "")
            
            # Calculate next tier cost (if not maxed)
            next_tier_cost = None
            if max_tier < max_possible:
                next_tier = max_tier + 1
                cost_info = _get_minion_upgrade_cost(minion_id, max_tier, next_tier, bazaar_prices)
                next_tier_cost = cost_info
            
            cat_minions.append({
                "id": minion_id,
                "name": minion_info["name"],
                "tiers": tiers,
                "tier": max_tier,
                "maxTier": max_possible,
                "unlockedTiers": unlocked_count,
                "isMaxed": max_tier >= max_possible,
                "texture": f"{MC_HEADS_BASE}/{texture}" if texture else "",
                "nextTierCost": next_tier_cost
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
    # Get community upgrades for minion slots (from profile level)
    community_slot_upgrades = 0
    if profile:
        community_upgrades = profile.get("community_upgrades", {})
        upgrade_states = community_upgrades.get("upgrade_states", [])
        for upgrade in upgrade_states:
            if upgrade.get("upgrade") == "minion_slots":
                tier = upgrade.get("tier", 0)
                if tier > community_slot_upgrades:
                    community_slot_upgrades = tier
    
    slots = get_minion_slots(total_unlocked_tiers, community_slot_upgrades)
    
    # Build missing minions list - minions that are not maxed, sorted by upgrade cost
    missing_minions = []
    for cat_key, cat_data in categories.items():
        cat_meta = {
            "farming": {"name": "Farming", "icon": "🌾"},
            "mining": {"name": "Mining", "icon": "⛏️"},
            "combat": {"name": "Combat", "icon": "⚔️"},
            "foraging": {"name": "Foraging", "icon": "🌲"},
            "fishing": {"name": "Fishing", "icon": "🎣"}
        }.get(cat_key, {"name": cat_key.title(), "icon": "📦"})
        
        for minion in cat_data["minions"]:
            if not minion["isMaxed"]:
                # Calculate upgrade cost for next tier
                next_tier = minion["tier"] + 1 if minion["tier"] < minion["maxTier"] else None
                upgrade_cost = None
                # Note: Minions are not tradeable on AH, so no price lookup available
                # Could add bazaar-based crafting cost calculation in future
                
                missing_minions.append({
                    **minion,
                    "category": cat_key,
                    "categoryName": cat_meta["name"],
                    "categoryIcon": cat_meta["icon"],
                    "slotsPerTier": 1,
                    "tiersRemaining": minion["maxTier"] - minion["unlockedTiers"],
                    "nextTier": next_tier,
                    "upgradeCost": upgrade_cost
                })
    
    # Sort missing minions: prioritize those with prices, then by cost per slot
    def sort_key(m):
        cost = m.get("upgradeCost")
        if cost is not None:
            return (0, cost, m["tiersRemaining"])
        else:
            return (1, 999999999, m["tiersRemaining"])
    
    missing_minions.sort(key=sort_key)
    
    return {
        "categories": categories,
        "totalMinions": total_minions,
        "maxedMinions": maxed_minions,
        "unlockedTiers": total_unlocked_tiers,
        "unlockableTiers": total_unlockable_tiers,
        "slots": slots,
        "missingMinions": missing_minions,
        "missingCount": len(missing_minions)
    }
