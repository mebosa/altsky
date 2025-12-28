"""
Shard data extraction for Hypixel SkyBlock.

Shards are collectible items from hunting mobs on Galatea island.
The Hypixel API provides statistics about shard hunting.
We also scan the player's inventory to find which specific shards they own.
"""

from __future__ import annotations

import logging
import base64
import gzip
import io
from typing import Any, Dict, List, Set, Optional

try:
    import nbtlib
    NBT_AVAILABLE = True
except ImportError:
    NBT_AVAILABLE = False

LOGGER = logging.getLogger(__name__)

# Shard categories with display names
SHARD_CATEGORIES = {
    "combat": "Combat",
    "fishing": "Fishing", 
    "forest": "Forest",
    "trap": "Trap",
    "salt": "Salt",
}

SHARD_DATA = {
    "SHARD_SALMON": {"name": "Salmon Shard", "rarity": "RARE"},
    "SHARD_MEGALITH": {"name": "Megalith Shard", "rarity": "RARE"},
    "SHARD_CARROT_KING": {"name": "Carrot King Shard", "rarity": "RARE"},
    "SHARD_BAL": {"name": "Bal Shard", "rarity": "RARE"},
    "SHARD_DODO": {"name": "Dodo Shard", "rarity": "RARE"},
    "SHARD_BITBUG": {"name": "Bitbug Shard", "rarity": "RARE"},
    "SHARD_PEST": {"name": "Pest Shard", "rarity": "RARE"},
    "SHARD_LAVA_FLAME": {"name": "Lava Flame Shard", "rarity": "RARE"},
    "THUNDER_SHARDS": {"name": "Thunder Shards", "rarity": "RARE"},
    "SHARD_OBSIDIAN_DEFENDER": {"name": "Obsidian Defender Shard", "rarity": "RARE"},
    "SHARD_TIAMAT": {"name": "Tiamat Shard", "rarity": "RARE"},
    "SHARD_SPHINX": {"name": "Sphinx Shard", "rarity": "RARE"},
    "SHARD_WITHER_SPECTER": {"name": "Wither Specter Shard", "rarity": "RARE"},
    "SHARD_PRINCE": {"name": "Prince Shard", "rarity": "RARE"},
    "SHARD_TROGLOBYTE": {"name": "Troglobyte Shard", "rarity": "RARE"},
    "SHARD_KING_MINOS": {"name": "King Minos Shard", "rarity": "RARE"},
    "SHARD_BOREAL_OWL": {"name": "Boreal Owl Shard", "rarity": "RARE"},
    "SHARD_GOLDEN_GHOUL": {"name": "Golden Ghoul Shard", "rarity": "RARE"},
    "SHARD_TEMPEST": {"name": "Tempest Shard", "rarity": "RARE"},
    "SHARD_NIGHT_SQUID": {"name": "Night Squid Shard", "rarity": "RARE"},
    "SHARD_WARTYBUG": {"name": "Wartybug Shard", "rarity": "RARE"},
    "SHARD_HUMMINGBIRD": {"name": "Hummingbird Shard", "rarity": "RARE"},
    "SHARD_GECKO": {"name": "Gecko Shard", "rarity": "RARE"},
    "SHARD_BASILISK": {"name": "Basilisk Shard", "rarity": "RARE"},
    "SHARD_PYTHON": {"name": "Python Shard", "rarity": "RARE"},
    "SHARD_SKELETOR": {"name": "Skeletor Shard", "rarity": "RARE"},
    "SHARD_THORN": {"name": "Thorn Shard", "rarity": "RARE"},
    "SHARD_BEZAL": {"name": "Bezal Shard", "rarity": "RARE"},
    "SHARD_HERON": {"name": "Heron Shard", "rarity": "RARE"},
    "SHARD_FLARE": {"name": "Flare Shard", "rarity": "RARE"},
    "SHARD_KING_COBRA": {"name": "King Cobra Shard", "rarity": "RARE"},
    "SHARD_VERDANT": {"name": "Verdant Shard", "rarity": "RARE"},
    "SHARD_SHINYFISH": {"name": "Shinyfish Shard", "rarity": "RARE"},
    "SHARD_ENT": {"name": "Ent Shard", "rarity": "RARE"},
    "SHARD_AERO": {"name": "Aero Shard", "rarity": "RARE"},
    "SHARD_HARPY": {"name": "Harpy Shard", "rarity": "RARE"},
    "SHARD_ALLIGATOR": {"name": "Alligator Shard", "rarity": "RARE"},
    "SHARD_SEA_SERPENT": {"name": "Sea Serpent Shard", "rarity": "RARE"},
    "SHARD_PRAYING_MANTIS": {"name": "Praying Mantis Shard", "rarity": "RARE"},
    "SHARD_DROWNED": {"name": "Drowned Shard", "rarity": "RARE"},
    "SHARD_HIDEONDRA": {"name": "Hideondra Shard", "rarity": "RARE"},
    "SHARD_IGUANA": {"name": "Iguana Shard", "rarity": "RARE"},
    "SHARD_TIDE": {"name": "Tide Shard", "rarity": "RARE"},
    "SHARD_HIDEONLEAF": {"name": "Hideonleaf Shard", "rarity": "RARE"},
    "SHARD_BLIZZARD": {"name": "Blizzard Shard", "rarity": "RARE"},
    "SHARD_EEL": {"name": "Eel Shard", "rarity": "RARE"},
    "SHARD_FENLORD": {"name": "Fenlord Shard", "rarity": "RARE"},
    "SHARD_HIDEONBOX": {"name": "Hideonbox Shard", "rarity": "RARE"},
    "SHARD_HIDEONSACK": {"name": "Hideonsack Shard", "rarity": "RARE"},
    "SHARD_BARBARIAN_DUKE_X": {"name": "Barbarian Duke X Shard", "rarity": "RARE"},
    "SHARD_WYVERN": {"name": "Wyvern Shard", "rarity": "RARE"},
    "SHARD_RAIN_SLIME": {"name": "Rain Slime Shard", "rarity": "RARE"},
    "SHARD_MATCHO": {"name": "Matcho Shard", "rarity": "RARE"},
    "SHARD_GLACITE_WALKER": {"name": "Glacite Walker Shard", "rarity": "RARE"},
    "SHARD_KADA_KNIGHT": {"name": "Kada Knight Shard", "rarity": "RARE"},
    "SHARD_SEA_EMPEROR": {"name": "Sea Emperor Shard", "rarity": "RARE"},
    "SHARD_FLASH": {"name": "Flash Shard", "rarity": "RARE"},
    "SHARD_MORAY_EEL": {"name": "Moray Eel Shard", "rarity": "RARE"},
    "SHARD_CASCADE": {"name": "Cascade Shard", "rarity": "RARE"},
    "SHARD_HELLWISP": {"name": "Hellwisp Shard", "rarity": "RARE"},
    "SHARD_MUDWORM": {"name": "Mudworm Shard", "rarity": "RARE"},
    "SHARD_TOAD": {"name": "Toad Shard", "rarity": "RARE"},
    "SHARD_MOSSYBIT": {"name": "Mossybit Shard", "rarity": "RARE"},
    "SHARD_MOCHIBEAR": {"name": "Mochibear Shard", "rarity": "RARE"},
    "SHARD_SPIKE": {"name": "Spike Shard", "rarity": "RARE"},
    "SHARD_FIRE_EEL": {"name": "Fire Eel Shard", "rarity": "RARE"},
    "SHARD_VORACIOUS_SPIDER": {"name": "Voracious Spider Shard", "rarity": "RARE"},
    "SHARD_MIMIC": {"name": "Mimic Shard", "rarity": "RARE"},
    "SHARD_MIST": {"name": "Mist Shard", "rarity": "RARE"},
    "SHARD_TORTOISE": {"name": "Tortoise Shard", "rarity": "RARE"},
    "SHARD_SHELLWISE": {"name": "Shellwise Shard", "rarity": "RARE"},
    "SHARD_STAR_SENTRY": {"name": "Star Sentry Shard", "rarity": "RARE"},
    "SHARD_LUMISQUID": {"name": "Lumisquid Shard", "rarity": "RARE"},
    "SHARD_CHAMELEON": {"name": "Chameleon Shard", "rarity": "RARE"},
    "SHARD_LIZARD_KING": {"name": "Lizard King Shard", "rarity": "RARE"},
    "SHARD_SOUL_OF_THE_ALPHA": {"name": "Soul Of The Alpha Shard", "rarity": "RARE"},
    "SHARD_PHANPYRE": {"name": "Phanpyre Shard", "rarity": "RARE"},
    "SHARD_ANANKE": {"name": "Ananke Shard", "rarity": "RARE"},
    "SHARD_THYST": {"name": "Thyst Shard", "rarity": "RARE"},
    "SHARD_CAIMAN": {"name": "Caiman Shard", "rarity": "RARE"},
    "SHARD_CONDOR": {"name": "Condor Shard", "rarity": "RARE"},
    "SHARD_VIPER": {"name": "Viper Shard", "rarity": "RARE"},
    "SHARD_AZURE": {"name": "Azure Shard", "rarity": "RARE"},
    "SHARD_ENDSTONE_PROTECTOR": {"name": "Endstone Protector Shard", "rarity": "RARE"},
    "SHARD_YOG": {"name": "Yog Shard", "rarity": "RARE"},
    "SHARD_CROW": {"name": "Crow Shard", "rarity": "RARE"},
    "SHARD_CHILL": {"name": "Chill Shard", "rarity": "RARE"},
    "SHARD_BOLT": {"name": "Bolt Shard", "rarity": "RARE"},
    "SHARD_CORALOT": {"name": "Coralot Shard", "rarity": "RARE"},
    "SHARD_QUARTZFANG": {"name": "Quartzfang Shard", "rarity": "RARE"},
    "SHARD_HIDEONCAVE": {"name": "Hideoncave Shard", "rarity": "RARE"},
    "SHARD_CINDER_BAT": {"name": "Cinder Bat Shard", "rarity": "RARE"},
    "SHARD_WATER_HYDRA": {"name": "Water Hydra Shard", "rarity": "RARE"},
    "SHARD_DREADWING": {"name": "Dreadwing Shard", "rarity": "RARE"},
    "SHARD_PIRANHA": {"name": "Piranha Shard", "rarity": "RARE"},
    "SHARD_LUNAR_MOTH": {"name": "Lunar Moth Shard", "rarity": "RARE"},
    "SHARD_LEATHERBACK": {"name": "Leatherback Shard", "rarity": "RARE"},
    "SHARD_NEWT": {"name": "Newt Shard", "rarity": "RARE"},
    "SHARD_HIDEONGEON": {"name": "Hideongeon Shard", "rarity": "RARE"},
    "SHARD_SUN_FISH": {"name": "Sun Fish Shard", "rarity": "RARE"},
    "SHARD_DRAGONFLY": {"name": "Dragonfly Shard", "rarity": "RARE"},
    "SHARD_POWER_DRAGON": {"name": "Power Dragon Shard", "rarity": "RARE"},
    "SHARD_CROCODILE": {"name": "Crocodile Shard", "rarity": "RARE"},
    "SHARD_CUBOA": {"name": "Cuboa Shard", "rarity": "RARE"},
    "SHARD_SALAMANDER": {"name": "Salamander Shard", "rarity": "RARE"},
    "SHARD_SPARROW": {"name": "Sparrow Shard", "rarity": "RARE"},
    "SHARD_BRUISER": {"name": "Bruiser Shard", "rarity": "RARE"},
    "SHARD_PHANFLARE": {"name": "Phanflare Shard", "rarity": "RARE"},
    "SHARD_DRACONIC": {"name": "Draconic Shard", "rarity": "RARE"},
    "SHARD_GALAXY_FISH": {"name": "Galaxy Fish Shard", "rarity": "RARE"},
    "SHARD_BAMBLOOM": {"name": "Bambloom Shard", "rarity": "RARE"},
    "SHARD_TERMITE": {"name": "Termite Shard", "rarity": "RARE"},
    "SHARD_REVENANT": {"name": "Revenant Shard", "rarity": "RARE"},
    "SHARD_CRYO": {"name": "Cryo Shard", "rarity": "RARE"},
    "SHARD_INVISIBUG": {"name": "Invisibug Shard", "rarity": "RARE"},
    "SHARD_BULLFROG": {"name": "Bullfrog Shard", "rarity": "RARE"},
    "SHARD_TENEBRIS": {"name": "Tenebris Shard", "rarity": "RARE"},
    "SHARD_STRIDER_SURFER": {"name": "Strider Surfer Shard", "rarity": "RARE"},
    "SHARD_ABYSSAL_LANTERN": {"name": "Abyssal Lantern Shard", "rarity": "RARE"},
    "SHARD_BIRRIES": {"name": "Birries Shard", "rarity": "RARE"},
    "SHARD_DAEMON": {"name": "Daemon Shard", "rarity": "RARE"},
    "SHARD_INFERNO_KOI": {"name": "Inferno Koi Shard", "rarity": "RARE"},
    "SHARD_CROPEETLE": {"name": "Cropeetle Shard", "rarity": "RARE"},
    "SHARD_SEA_ARCHER": {"name": "Sea Archer Shard", "rarity": "RARE"},
    "SHARD_COD": {"name": "Cod Shard", "rarity": "RARE"},
    "SHARD_XYZ": {"name": "Xyz Shard", "rarity": "RARE"},
    "SHARD_LORD_JAWBUS": {"name": "Lord Jawbus Shard", "rarity": "RARE"},
    "SHARD_SYCOPHANT": {"name": "Sycophant Shard", "rarity": "RARE"},
    "SHARD_SEAGULL": {"name": "Seagull Shard", "rarity": "RARE"},
    "SHARD_FLAMING_SPIDER": {"name": "Flaming Spider Shard", "rarity": "RARE"},
    "SHARD_GROVE": {"name": "Grove Shard", "rarity": "RARE"},
    "SHARD_LAPIS_ZOMBIE": {"name": "Lapis Zombie Shard", "rarity": "RARE"},
    "SHARD_BURNINGSOUL": {"name": "Burningsoul Shard", "rarity": "RARE"},
    "SHARD_ARACHNE": {"name": "Arachne Shard", "rarity": "RARE"},
    "SHARD_BAMBULEAF": {"name": "Bambuleaf Shard", "rarity": "RARE"},
    "SHARD_ETHERDRAKE": {"name": "Etherdrake Shard", "rarity": "RARE"},
    "SHARD_JORMUNG": {"name": "Jormung Shard", "rarity": "RARE"},
    "SHARD_NAGA": {"name": "Naga Shard", "rarity": "RARE"},
    "SHARD_MOLTENFISH": {"name": "Moltenfish Shard", "rarity": "RARE"},
    "SHARD_FUNGLOOM": {"name": "Fungloom Shard", "rarity": "RARE"},
    "SHARD_CRETAN_BULL": {"name": "Cretan Bull Shard", "rarity": "RARE"},
    "SHARD_SEER": {"name": "Seer Shard", "rarity": "RARE"},
    "SHARD_FIREFLY": {"name": "Firefly Shard", "rarity": "RARE"},
    "SHARD_LADYBUG": {"name": "Ladybug Shard", "rarity": "RARE"},
    "SHARD_SILENTDEPTH": {"name": "Silentdepth Shard", "rarity": "RARE"},
    "SHARD_SCARF": {"name": "Scarf Shard", "rarity": "RARE"},
    "SHARD_TERRA": {"name": "Terra Shard", "rarity": "RARE"},
    "SHARD_TANK_ZOMBIE": {"name": "Tank Zombie Shard", "rarity": "RARE"},
    "SHARD_LAPIS_SKELETON": {"name": "Lapis Skeleton Shard", "rarity": "RARE"},
    "SHARD_PANDARAI": {"name": "Pandarai Shard", "rarity": "RARE"},
    "SHARD_MOLTHORN": {"name": "Molthorn Shard", "rarity": "RARE"},
    "SHARD_LAPIS_CREEPER": {"name": "Lapis Creeper Shard", "rarity": "RARE"},
    "SHARD_STARBORN": {"name": "Starborn Shard", "rarity": "RARE"},
    "SHARD_JOYDIVE": {"name": "Joydive Shard", "rarity": "RARE"},
    "SHARD_SYLVAN": {"name": "Sylvan Shard", "rarity": "RARE"},
    "SHARD_ZOMBIE_SOLDIER": {"name": "Zombie Soldier Shard", "rarity": "RARE"},
    "SHARD_TADGANG": {"name": "Tadgang Shard", "rarity": "RARE"},
    "SHARD_GOLDFIN": {"name": "Goldfin Shard", "rarity": "RARE"},
    "SHARD_TITANOBOA": {"name": "Titanoboa Shard", "rarity": "RARE"},
    "SHARD_MINER_ZOMBIE": {"name": "Miner Zombie Shard", "rarity": "RARE"},
    "SHARD_BEACONMITE": {"name": "Beaconmite Shard", "rarity": "RARE"},
    "SHARD_APEX_DRAGON": {"name": "Apex Dragon Shard", "rarity": "RARE"},
    "SHARD_TAURUS": {"name": "Taurus Shard", "rarity": "RARE"},
    "SHARD_RANA": {"name": "Rana Shard", "rarity": "RARE"},
    "SHARD_CAVERNSHADE": {"name": "Cavernshade Shard", "rarity": "RARE"},
    "SHARD_BRAMBLE": {"name": "Bramble Shard", "rarity": "RARE"},
    "SHARD_KRAKEN": {"name": "Kraken Shard", "rarity": "RARE"},
    "SHARD_ZEALOT": {"name": "Zealot Shard", "rarity": "RARE"},
    "SHARD_WITHER": {"name": "Wither Shard", "rarity": "RARE"},
    "SHARD_MAGMA_SLUG": {"name": "Magma Slug Shard", "rarity": "RARE"},
    "SHARD_QUAKE": {"name": "Quake Shard", "rarity": "RARE"},
    "SHARD_HIDEONGIFT": {"name": "Hideongift Shard", "rarity": "RARE"},
    "SHARD_KIWI": {"name": "Kiwi Shard", "rarity": "RARE"},
    "SHARD_SNOWFIN": {"name": "Snowfin Shard", "rarity": "RARE"},
    "SHARD_MINOTAUR": {"name": "Minotaur Shard", "rarity": "RARE"},
    "SHARD_GHOST": {"name": "Ghost Shard", "rarity": "RARE"},
    "SHARD_TOUCAN": {"name": "Toucan Shard", "rarity": "RARE"},
    "SHARD_STALAGMIGHT": {"name": "Stalagmight Shard", "rarity": "RARE"},
    "SHARD_KOMODO_DRAGON": {"name": "Komodo Dragon Shard", "rarity": "RARE"},
    "SHARD_FALCON": {"name": "Falcon Shard", "rarity": "RARE"},
    "SHARD_HIDEONRING": {"name": "Hideonring Shard", "rarity": "RARE"},
    "SHARD_LEVIATHAN": {"name": "Leviathan Shard", "rarity": "RARE"},
}

def decode_inventory_data(b64_data: str) -> List[str]:
    """
    Decodes Hypixel inventory data (base64 -> gzip -> NBT) and returns a list of item IDs.
    """
    if not b64_data or not NBT_AVAILABLE:
        return []
    
    try:
        decoded = base64.b64decode(b64_data)
        try:
            decompressed = gzip.decompress(decoded)
        except gzip.BadGzipFile:
            decompressed = decoded
            
        nbt_file = nbtlib.File.from_fileobj(io.BytesIO(decompressed))
        
        item_ids = []
        root = nbt_file.root
        
        # Handle standard inventory structure
        items = []
        if "i" in root:
            items = root["i"]
        elif "inv_contents" in root:
             items = root["inv_contents"]
             
        # Iterate over items
        for item in items:
            if not item: 
                continue
                
            try:
                if "tag" in item and "ExtraAttributes" in item["tag"]:
                    extra = item["tag"]["ExtraAttributes"]
                    if "id" in extra:
                        item_ids.append(str(extra["id"]))
            except KeyError:
                continue
                        
        return item_ids

    except Exception as e:
        LOGGER.error(f"Failed to decode inventory data: {e}")
        return []

def extract_player_shards(member_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract shard hunting statistics from player profile data.
    Also scans inventory for owned shards.
    """
    # Get shard hunting stats from player_stats
    player_stats = member_data.get("player_stats", {})
    unique_shards = int(player_stats.get("unique_shards", 0))
    shard_combat_hunts = int(player_stats.get("shard_combat_hunts", 0))
    shard_fishing_hunts = int(player_stats.get("shard_fishing_hunts", 0))
    shard_forest_hunts = int(player_stats.get("shard_forest_hunts", 0))
    shard_trap_hunts = int(player_stats.get("shard_trap_hunts", 0))
    shard_salt_hunts = int(player_stats.get("shard_salt_hunts", 0))
    
    # Get active effects for shard charm
    active_effects = member_data.get("active_effects", [])
    shard_charm_level = 0
    for effect in active_effects:
        if effect.get("effect") == "shard_charm":
            shard_charm_level = int(effect.get("level", 0))
            break

    total_hunts = (
        shard_combat_hunts + 
        shard_fishing_hunts + 
        shard_forest_hunts + 
        shard_trap_hunts + 
        shard_salt_hunts
    )
    
    # Scan inventories for owned shards
    owned_shards = set()
    
    def process_content(content: Any):
        if isinstance(content, dict) and "data" in content:
            ids = decode_inventory_data(content["data"])
            for item_id in ids:
                if item_id in SHARD_DATA:
                    owned_shards.add(item_id)
        elif isinstance(content, str):
             ids = decode_inventory_data(content)
             for item_id in ids:
                if item_id in SHARD_DATA:
                    owned_shards.add(item_id)

    if "inventory" in member_data:
        inv = member_data["inventory"]
        process_content(inv.get("inv_contents"))
        process_content(inv.get("ender_chest_contents"))
        process_content(inv.get("inv_armor"))
        process_content(inv.get("equipment_contents"))
        process_content(inv.get("wardrobe_contents"))
        process_content(inv.get("personal_vault_contents"))
        
        if "backpack_contents" in inv:
            bp = inv["backpack_contents"]
            if isinstance(bp, dict):
                for key, val in bp.items():
                    process_content(val)
    
    # Also check top level just in case
    process_content(member_data.get("inv_contents"))
    process_content(member_data.get("ender_chest_contents"))
    process_content(member_data.get("backpack_contents"))

    # Construct result
    shards_list = []
    for shard_id, data in SHARD_DATA.items():
        is_owned = shard_id in owned_shards
        shards_list.append({
            "id": shard_id,
            "name": data["name"],
            "rarity": data["rarity"],
            "owned": is_owned
        })
        
    return {
        "stats": {
            "unique_shards": unique_shards,
            "shard_charm_level": shard_charm_level,
            "total_hunts": total_hunts,
            "hunts_by_category": {
                "combat": shard_combat_hunts,
                "fishing": shard_fishing_hunts,
                "forest": shard_forest_hunts,
                "trap": shard_trap_hunts,
                "salt": shard_salt_hunts,
            }
        },
        "shards": shards_list,
        "total_owned": len(owned_shards),
        "total_shards": len(SHARD_DATA)
    }
