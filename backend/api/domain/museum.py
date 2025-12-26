"""
Museum data processing for Hypixel SkyBlock profiles.

The Museum is a feature where players can donate items to earn SkyBlock XP.
Items are categorized into Weapons, Armor Sets, and Rarities (special items).
"""

from __future__ import annotations

import base64
import gzip
import io
import logging
import time
import requests
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Set

from ..http_client import session
from .nbt_parser import decode_inventory_data
from .item_textures import resolve_item_icon_variants
from .wardrobe import _parse_inventory_items
from .networth import calculate_item_value

LOGGER = logging.getLogger(__name__)

# Museum item categories based on Hypixel's museum structure
MUSEUM_CATEGORIES = {
    "weapons": "Weapons",
    "armor": "Armor Sets", 
    "rarities": "Rarities"
}

# Special items donated to museum (limited/unique items)
SPECIAL_CATEGORY = "special"

# ===== Museum Item Lists from SkyCrypt =====
# These are all donateable items to the museum

MUSEUM_WEAPONS = [
    "FANCY_SWORD", "UNDEAD_SWORD", "SPIDER_SWORD", "ROGUE_SWORD", "ASPECT_OF_THE_JERRY",
    "CLEAVER", "END_SWORD", "SQUIRE_SWORD", "CELESTE_WAND", "ARTISANAL_SHORTBOW",
    "PRISMARINE_BOW", "WITHER_BOW", "PRISMARINE_BLADE", "HUNTER_KNIFE", "UNDEAD_BOW",
    "CRYPT_DREADLORD_SWORD", "SNIPER_BOW", "RECLUSE_FANG", "STARLIGHT_WAND", "SUPER_CLEAVER",
    "TRIBAL_SPEAR", "HYPER_CLEAVER", "SUPER_UNDEAD_BOW", "ARACK", "FLAMING_SWORD",
    "DECENT_BOW", "VOIDWALKER_KATANA", "SAVANA_BOW", "ZOMBIE_SOLDIER_CUTLASS", "CONJURING_SWORD",
    "MERCENARY_AXE", "ENDER_BOW", "MACHINE_GUN_BOW", "TACTICIAN_SWORD", "CRYPT_BOW",
    "DEATH_BOW", "GIANT_CLEAVER", "ZOMBIE_COMMANDER_WHIP", "SHAMAN_SWORD", "ZOMBIE_KNIGHT_SWORD",
    "END_STONE_BOW", "SPIDER_QUEENS_STINGER", "SILVER_FANG", "REVENANT_SWORD", "ASPECT_OF_THE_END",
    "EDIBLE_MACE", "RAIDER_AXE", "SILENT_DEATH", "ZOMBIE_SWORD", "BLADE_OF_THE_VOLCANO",
    "GOLEM_SWORD", "STAFF_OF_THE_VOLCANO", "VENOMS_TOUCH", "DRAGON_SHORTBOW", "EMERALD_BLADE",
    "ORNATE_ZOMBIE_SWORD", "VOID_SWORD", "HURRICANE_BOW", "EARTH_SHARD", "GHOUL_BUSTER",
    "EXPLOSIVE_BOW", "END_STONE_SWORD", "SWORD_OF_BAD_HEALTH", "VOODOO_DOLL", "FROZEN_SCYTHE",
    "BONZO_STAFF", "VOIDEDGE_KATANA", "SOULS_REBOUND", "SLIME_BOW", "FIRE_FREEZE_STAFF",
    "LEAPING_SWORD", "STONE_BLADE", "FEL_SWORD", "FIRE_FURY_STAFF", "SCORPION_BOW",
    "SCORPION_FOIL", "SULPHUR_BOW", "SILK_EDGE_SWORD", "ASTRAEA", "HYPERION",
    "RUNIC_STAFF", "ASPECT_OF_THE_DRAGON", "FLORID_ZOMBIE_SWORD", "POOCH_SWORD", "SCYLLA",
    "HOLLOW_WAND", "VALKYRIE", "PHANTOM_ROD", "FIREDUST_DAGGER", "MAWDUST_DAGGER",
    "RAGNAROCK_AXE", "ASPECT_OF_THE_VOID", "PUMPKIN_LAUNCHER", "WAND_OF_STRENGTH", "INK_WAND",
    "VOODOO_DOLL_WILTED", "FLOWER_OF_TRUTH", "RUNAANS_BOW", "LIVID_DAGGER", "MIDAS_SWORD",
    "VORPAL_KATANA", "FIRE_VEIL_WAND", "SPIRIT_SWORD", "REAPER_SWORD", "SINSEEKER_SCYTHE",
    "WITHER_CLOAK", "JUJU_SHORTBOW", "YETI_SWORD", "SOUL_WHIP", "NECROMANCER_SWORD",
    "ALCHEMISTS_STAFF", "ICE_SPRAY_WAND", "SWORD_OF_REVELATIONS", "BONE_REAVER", "MOSQUITO_BOW",
    "LAST_BREATH", "REAPER_SCYTHE", "PIGMAN_SWORD", "ITEM_SPIRIT_BOW", "BOUQUET_OF_LIES",
    "GEMSTONE_GAUNTLET", "BONE_BOOMERANG", "FELTHORN_REAPER", "BAT_WAND", "SHADOW_FURY",
    "GLACIAL_SCYTHE", "BURSTMAW_DAGGER", "BURSTFIRE_DAGGER", "DAEDALUS_AXE", "ATOMSPLIT_KATANA",
    "AXE_OF_THE_SHREDDED", "GIANTS_SWORD", "MIDAS_STAFF", "TERMINATOR", "NECRON_BLADE",
    "HEARTMAW_DAGGER", "HEARTFIRE_DAGGER", "DARK_CLAYMORE",
]

MUSEUM_ARMOR = [
    "FARM_SUIT", "CELESTE", "SQUIRE", "ROSETTA", "MERCENARY", "LEAFLET", "ANGLER",
    "PUMPKIN", "MUSHROOM", "CACTUS", "HEAT", "ROTTEN", "STARLIGHT", "FAIRY",
    "MINER_OUTFIT", "MITHRIL", "LAPIS_ARMOR", "FISHERMAN", "TANK_MINER", "SALMON_NEW",
    "GOLEM_ARMOR", "GROWTH", "HEAVY", "FARM_ARMOR", "HARDENED_DIAMOND", "SKELETON_MASTER",
    "ZOMBIE_SOLDIER", "SUPER_HEAVY", "ARMOR_OF_YOG", "FLAME_BREAKER", "END",
    "SKELETON_GRUNT", "SKELETON_SOLDIER", "CHEAP_TUXEDO", "MELON", "PARTY", "SEYMOUR",
    "ARACHNE", "MONSTER_HUNTER", "MONSTER_RAIDER", "BOUNCY", "TITANIUM", "LOTUS",
    "GOBLIN", "MINERAL", "ZOMBIE", "GLACITE", "FANCY_TUXEDO", "CRIMSON_HUNTER",
    "SPEEDSTER", "SKELETOR", "GEMSTONE", "EMERALD_ARMOR", "REVENANT", "CROPIE",
    "ICHTHYIC", "RAMPART", "SPONGE", "SNOW_SUIT", "TARANTULA", "CRYSTAL",
    "SPEED_WITHER", "POWER_WITHER", "WISE_WITHER", "ELEGANT_TUXEDO", "TANK_WITHER",
    "ARMOR_OF_THE_PACK", "ZOMBIE_KNIGHT", "ADAPTIVE", "SPOOKY", "SHARK_SCALE",
    "GLOSSY_MINERAL", "WEREWOLF", "BAT_PERSON", "REAPER", "RABBIT", "VANQUISHED",
    "MASTIFF", "ZOMBIE_COMMANDER", "PERFECT_TIER_12", "FINAL_DESTINATION", "SQUASH",
    "BRONZE_HUNTER", "LAVA_SEA_CREATURE", "SHADOW_ASSASSIN", "SKELETON_LORD", "FINWAVE",
    "MOLTEN", "ZOMBIE_LORD", "REKINDLED_EMBER", "FROZEN_BLAZE", "WITHER", "SORROW",
    "HOLY_DRAGON", "WISE_DRAGON", "NUTCRACKER", "HOLLOW", "OLD_DRAGON", "UNSTABLE_DRAGON",
    "DIVER", "FERVOR", "TERROR", "YOUNG_DRAGON", "PROTECTOR_DRAGON", "CRIMSON",
    "PERFECT_TIER_13", "AURORA", "STRONG_DRAGON", "SILVER_HUNTER", "FERMENTO",
    "NECROMANCER_LORD", "BERSERKER", "THUNDER", "GILLSPLASH", "SUPERIOR_DRAGON",
    "SHIMMERING_LIGHT", "GOLD_HUNTER", "DIVAN", "MAGMA_LORD", "DIAMOND_HUNTER",
]

MUSEUM_RARITIES = [
    "SQUID_HAT", "FISH_HAT", "ZOMBIE_HAT", "PUFFERFISH_HAT", "CHICKEN_HEAD",
    "FLINT_SHOVEL", "DOJO_WHITE_BELT", "CREEPER_HAT", "ROOKIE_AXE", "COW_HEAD",
    "SPIDER_HAT", "ROOKIE_HOE", "SLIME_HAT", "SKELETON_HAT", "CLOWNFISH_HAT",
    "EFFICIENT_AXE", "PROMISING_SPADE", "BLOBFISH_HAT", "MAGMA_FISH_HAT", "PROMISING_AXE",
    "SNOW_CANNON", "SKYMART_VACUUM", "PRISMARINE_ROD", "SPONGE_ROD", "SCULPTORS_AXE",
    "ZOMBIE_PICKAXE", "ROOKIE_PICKAXE", "SAM_SCYTHE", "SWEET_AXE", "RUSTY_TITANIUM_PICKAXE",
    "SPRAYONATOR", "RADIANT_POWER_ORB", "SQUID_BOOTS", "JUNGLE_AXE", "WAND_OF_HEALING",
    "LAPIS_PICKAXE", "SALMON_MASK", "BASIC_GARDENING_AXE", "BANDAGED_MITHRIL_PICKAXE",
    "MITHRIL_PICKAXE", "BASIC_GARDENING_HOE", "ENDERMAN_MASK", "SKYMART_TURBO_VACUUM",
    "GARDEN_SCYTHE", "ZOMBIE_MASK", "PROMISING_PICKAXE", "DOJO_GREEN_BELT",
    "FRACTURED_MITHRIL_PICKAXE", "SPEEDSTER_ROD", "DOJO_YELLOW_BELT", "WAND_OF_MENDING",
    "WINTER_ROD", "MENDER_HELMET", "STONE_CHESTPLATE", "DOJO_BLUE_BELT", "CHALLENGE_ROD",
    "DARK_GOGGLES", "MUSIC_PANTS", "SHADOW_GOGGLES", "MENDER_FEDORA", "METAL_CHESTPLATE",
    "SNOW_BLASTER", "KALHUIKI_MASK", "JUNGLE_PICKAXE", "LUMINOUS_BRACELET",
    "ENCHANTED_JACK_O_LANTERN", "RABBIT_HAT", "FARMER_ROD", "SNOWMAN_MASK",
    "TITANIUM_PICKAXE", "SNIPER_HELMET", "PARROT_MASK", "CHUM_ROD", "FALLEN_STAR_HAT",
    "REFINED_MITHRIL_PICKAXE", "ZOMBIE_HEART", "ARMADILLO_MASK", "ADVANCED_GARDENING_HOE",
    "ADVANCED_GARDENING_AXE", "CHAMP_ROD", "SYNTHESIZER_V1", "STONK_PICKAXE",
    "DOJO_BROWN_BELT", "SNOW_HOWITZER", "THEORETICAL_HOE_WHEAT_1", "THEORETICAL_HOE_CANE_1",
    "THEORETICAL_HOE_POTATO_1", "THEORETICAL_HOE_WARTS_1", "THEORETICAL_HOE_CARROT_1",
    "FARMER_BOOTS", "WARNING_FLARE", "STARTER_LAVA_ROD", "WITCH_MASK", "SOUL_ESOWARD",
    "SKYMART_HYPER_VACUUM", "CRYSTALLIZED_HEART", "BALLOON_SNAKE", "ICE_ROD",
    "MANA_FLUX_POWER_ORB", "VAMPIRE_MASK", "WEIRD_TUBA", "REFINED_TITANIUM_PICKAXE",
    "BONZO_MASK", "GEMSTONE_DRILL_1", "PEST_VEST", "DRAGONFUSE_GLOVE", "BEE_MASK",
    "FUNGI_CUTTER", "MELON_DICER", "PELT_BELT", "TREECAPITATOR_AXE", "PUMPKIN_DICER",
    "FROG_MASK", "OBSIDIAN_CHESTPLATE", "WATER_HYDRA_HEAD", "RANCHERS_BOOTS",
    "CACTUS_KNIFE", "VAMPIRE_WITCH_MASK", "WAND_OF_RESTORATION", "COCO_CHOPPER",
    "MITHRIL_COAT", "DRAGONFADE_CLOAK", "THEORETICAL_HOE_WHEAT_2", "THEORETICAL_HOE_CANE_2",
    "THEORETICAL_HOE_POTATO_2", "THEORETICAL_HOE_WARTS_2", "THEORETICAL_HOE_CARROT_2",
    "GHOST_BOOTS", "GEMSTONE_DRILL_2", "LEGEND_ROD", "SYNTHESIZER_V2", "THORNS_BOOTS",
    "MELON_DICER_2", "PUMPKIN_DICER_2", "KRAMPUS_HELMET", "WEIRDER_TUBA",
    "GLOOMLOCK_GRIMOIRE", "RIFT_NECKLACE_OUTSIDE", "GOLD_LIVID_HEAD", "GOLD_BONZO_HEAD",
    "GOLD_THORN_HEAD", "GOLD_PROFESSOR_HEAD", "GOLD_SADAN_HEAD", "GOLD_NECRON_HEAD",
    "GOLD_SCARF_HEAD", "POLISHED_TOPAZ_ROD", "MITHRIL_DRILL_1", "MAGMA_ROD",
    "STEEL_CHESTPLATE", "SOULWEAVER_GLOVES", "INFINI_VACUUM", "BONE_NECKLACE",
    "JERRY_STAFF", "MENDER_CROWN", "WITHER_GOGGLES", "YETI_ROD", "REVIVED_HEART",
    "CROWN_OF_GREED", "GEMSTONE_DRILL_3", "THE_SHREDDER", "THEORETICAL_HOE_WHEAT_3",
    "THEORETICAL_HOE_CANE_3", "THEORETICAL_HOE_POTATO_3", "THEORETICAL_HOE_WARTS_3",
    "REINFORCED_CHISEL", "THEORETICAL_HOE_CARROT_3", "SUMMONING_RING", "ANCIENT_CLOAK",
    "DELIRIUM_NECKLACE", "GYROKINETIC_WAND", "DESTRUCTION_CLOAK", "MELON_DICER_3",
    "PUMPKIN_DICER_3", "AUGER_ROD", "INFINI_VACUUM_HOOVERIUS", "ROD_OF_THE_SEA",
    "REAPER_MASK", "WAND_OF_ATONEMENT", "MITHRIL_DRILL_2", "SCOVILLE_BELT",
    "ALERT_FLARE", "IMPLOSION_BELT", "INFERNO_ROD", "DWARVEN_HANDWARMERS",
    "SCOURGE_CLOAK", "OVERFLUX_POWER_ORB", "SPIRIT_MASK", "LAVA_SHELL_NECKLACE",
    "GLACITE_CHISEL", "TITANIUM_DRILL_1", "GEMSTONE_DRILL_4", "GAUNTLET_OF_CONTAGION",
    "CROWN_OF_AVARICE", "DIAMOND_PROFESSOR_HEAD", "DIAMOND_SADAN_HEAD", "DIAMOND_LIVID_HEAD",
    "DIAMOND_NECRON_HEAD", "DIAMOND_SCARF_HEAD", "DIAMOND_BONZO_HEAD", "DIAMOND_THORN_HEAD",
    "DEMONLORD_GAUNTLET", "DOJO_BLACK_BELT", "WARDEN_HELMET", "PRECURSOR_EYE",
    "TACTICAL_INSERTION", "SYNTHESIZER_V3", "FLAMING_FIST", "TITANIUM_DRILL_3",
    "TITANIUM_DRILL_2", "PLASMAFLUX_POWER_ORB", "PERFECT_CHISEL", "ZORROS_CAPE",
    "BLAZETEKK_HAM_RADIO", "ANNIHILATION_CLOAK", "HELLFIRE_ROD", "TITANIUM_DRILL_4",
    "SOS_FLARE", "DIVAN_PENDANT", "DIVAN_DRILL",
]

# Items that count as donating their child items (higher tier = child donated)
MUSEUM_CHILDREN = {
    "TITANIUM": "MITHRIL",
    "HEAT": "TANK_MINER",
    "MASTIFF": "GROWTH",
    "MINERAL": "HARDENED_DIAMOND",
    "ARMOR_OF_YOG": "FLAME_BREAKER",
    "FANCY_TUXEDO": "CHEAP_TUXEDO",
    "CROPIE": "MELON",
    "MONSTER_RAIDER": "MONSTER_HUNTER",
    "GLOSSY_MINERAL": "MINERAL",
    "REVENANT": "ZOMBIE",
    "ELEGANT_TUXEDO": "FANCY_TUXEDO",
    "VANQUISHED": "CRIMSON_HUNTER",
    "REAPER": "REVENANT",
    "SQUASH": "CROPIE",
    "FINWAVE": "ICHTHYIC",
    "SHARK_SCALE": "SPONGE",
    "NUTCRACKER": "SNOW_SUIT",
    "FROZEN_BLAZE": "BLAZE",
    "BAT_PERSON": "SPOOKY",
    "PERFECT_TIER_13": "PERFECT_TIER_12",
    "FERMENTO": "SQUASH",
    "SILVER_HUNTER": "BRONZE_HUNTER",
    "GILLSPLASH": "FINWAVE",
    "GOLD_HUNTER": "SILVER_HUNTER",
    "DIAMOND_HUNTER": "GOLD_HUNTER",
    # Weapons/tools with upgrade paths
    "SUPER_CLEAVER": "CLEAVER",
    "HYPER_CLEAVER": "SUPER_CLEAVER",
    "GIANT_CLEAVER": "HYPER_CLEAVER",
    "ASPECT_OF_THE_VOID": "ASPECT_OF_THE_END",
    "RECLUSE_FANG": "SPIDER_SWORD",
    "DEATH_BOW": "SUPER_UNDEAD_BOW",
    "SUPER_UNDEAD_BOW": "UNDEAD_BOW",
    "SILK_EDGE_SWORD": "LEAPING_SWORD",
    "FLORID_ZOMBIE_SWORD": "ORNATE_ZOMBIE_SWORD",
    "ORNATE_ZOMBIE_SWORD": "ZOMBIE_SWORD",
    "REVENANT_SWORD": "UNDEAD_SWORD",
    "REAPER_SWORD": "REVENANT_SWORD",
    "AXE_OF_THE_SHREDDED": "REAPER_SWORD",
    "POOCH_SWORD": "SHAMAN_SWORD",
    "BOUQUET_OF_LIES": "FLOWER_OF_TRUTH",
    "BONE_REAVER": "SPIRIT_SWORD",
    "FELTHORN_REAPER": "BONE_REAVER",
    "GLACIAL_SCYTHE": "FROZEN_SCYTHE",
    "VOODOO_DOLL_WILTED": "VOODOO_DOLL",
    # Katana line
    "VOIDEDGE_KATANA": "VOIDWALKER_KATANA",
    "VORPAL_KATANA": "VOIDEDGE_KATANA",
    "ATOMSPLIT_KATANA": "VORPAL_KATANA",
    # Necron blade line
    "ASTRAEA": "NECRON_BLADE",
    "HYPERION": "VALKYRIE",
    "SCYLLA": "ASTRAEA",
    "VALKYRIE": "SCYLLA",
    # Daggers
    "BURSTFIRE_DAGGER": "FIREDUST_DAGGER",
    "HEARTFIRE_DAGGER": "BURSTFIRE_DAGGER",
    "BURSTMAW_DAGGER": "MAWDUST_DAGGER",
    "HEARTMAW_DAGGER": "BURSTMAW_DAGGER",
}

# Armor set ID to helmet ID mapping
ARMOR_TO_HELMET = {
    "FARM_SUIT": "FARM_SUIT_HELMET",
    "CELESTE": "CELESTE_HELMET",
    "SQUIRE": "SQUIRE_HELMET",
    "ROSETTA": "ROSETTA_HELMET",
    "MERCENARY": "MERCENARY_HELMET",
    "LEAFLET": "LEAFLET_HELMET",
    "YOUNG_DRAGON": "YOUNG_DRAGON_HELMET",
    "OLD_DRAGON": "OLD_DRAGON_HELMET",
    "WISE_DRAGON": "WISE_DRAGON_HELMET",
    "STRONG_DRAGON": "STRONG_DRAGON_HELMET",
    "SUPERIOR_DRAGON": "SUPERIOR_DRAGON_HELMET",
    "HOLY_DRAGON": "HOLY_DRAGON_HELMET",
    "PROTECTOR_DRAGON": "PROTECTOR_DRAGON_HELMET",
    "UNSTABLE_DRAGON": "UNSTABLE_DRAGON_HELMET",
}

# ===== Price Cache =====
_BAZAAR_CACHE: Dict[str, Dict[str, float]] = {}
_BAZAAR_FETCHED_AT = 0.0
_BAZAAR_TTL_SECONDS = 5 * 60  # 5 minutes

_AUCTION_CACHE: Dict[str, float] = {}
_AUCTION_FETCHED_AT = 0.0
_AUCTION_TTL_SECONDS = 10 * 60  # 10 minutes


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


def _fetch_auction_prices() -> Dict[str, float]:
    """Fetch lowest BIN prices from Moulberry's API (aggregated auction data)"""
    global _AUCTION_CACHE, _AUCTION_FETCHED_AT
    
    now = time.time()
    if _AUCTION_CACHE and now - _AUCTION_FETCHED_AT < _AUCTION_TTL_SECONDS:
        return _AUCTION_CACHE
    
    try:
        # Use Moulberry's lowest bin API which is commonly used
        response = session.get('https://moulberry.codes/lowestbin.json', timeout=8)
        response.raise_for_status()
        data = response.json()
        
        _AUCTION_CACHE = {k: float(v) for k, v in data.items() if isinstance(v, (int, float))}
        _AUCTION_FETCHED_AT = now
        return _AUCTION_CACHE
        
    except requests.RequestException as exc:
        LOGGER.warning("Failed to fetch auction prices: %s", exc)
    except (ValueError, KeyError) as exc:
        LOGGER.warning("Failed to parse auction data: %s", exc)
    
    return _AUCTION_CACHE


def get_item_price(item_id: str) -> Optional[float]:
    """Get the lowest price for an item from bazaar or auction house"""
    # Try bazaar first
    bazaar = _fetch_bazaar_prices()
    if item_id in bazaar:
        return bazaar[item_id].get('buyPrice')
    
    # Try auction house
    auctions = _fetch_auction_prices()
    if item_id in auctions:
        return auctions[item_id]
    
    # For armor sets, try helmet variant
    if item_id in ARMOR_TO_HELMET:
        helmet_id = ARMOR_TO_HELMET[item_id]
        if helmet_id in auctions:
            # Multiply by 4 for full set estimate
            return auctions[helmet_id] * 4
    
    return None


@dataclass
class MuseumItem:
    """Represents a single donated museum item."""
    id: str
    name: str
    donated_time: Optional[int] = None
    borrowing: bool = False
    rarity: Optional[str] = None
    lore: List[str] = field(default_factory=list)
    texture: Optional[str] = None
    category: str = "unknown"
    mc_id: Optional[str] = None
    damage: Optional[int] = None
    icon_url: Optional[str] = None
    icon_variants: Optional[Dict[str, Optional[str]]] = None
    item_data: Optional[Dict[str, Any]] = None
    value: float = 0.0


@dataclass 
class MuseumArmorSet:
    """Represents a donated armor set."""
    id: str
    name: str
    pieces: List[MuseumItem] = field(default_factory=list)
    donated_time: Optional[int] = None
    borrowing: bool = False
    complete: bool = False


@dataclass
class MuseumCategory:
    """Represents a category of museum items (weapons, armor, rarities)."""
    name: str
    items: List[MuseumItem] = field(default_factory=list)
    donated_count: int = 0
    total_count: int = 0
    
    @property
    def progress(self) -> float:
        if self.total_count == 0:
            return 0.0
        return self.donated_count / self.total_count


@dataclass
class MuseumData:
    """Complete museum data for a player."""
    value: float = 0.0
    appraisal: bool = False
    weapons: MuseumCategory = field(default_factory=lambda: MuseumCategory(name="Weapons"))
    armor: MuseumCategory = field(default_factory=lambda: MuseumCategory(name="Armor Sets"))
    rarities: MuseumCategory = field(default_factory=lambda: MuseumCategory(name="Rarities"))
    special: List[MuseumItem] = field(default_factory=list)
    total_donated: int = 0
    total_items: int = 0
    
    @property
    def overall_progress(self) -> float:
        if self.total_items == 0:
            return 0.0
        return self.total_donated / self.total_items


def _decode_nbt_item(item_bytes: bytes) -> Optional[Dict[str, Any]]:
    """Decode a single NBT item from compressed bytes."""
    try:
        # Use base64 encoding for decode_inventory_data
        import base64
        b64_str = base64.b64encode(item_bytes).decode('utf-8')
        items = decode_inventory_data(b64_str)
        return items[0] if items else None
    except Exception as e:
        LOGGER.debug(f"Failed to decode NBT item: {e}")
        return None


def _extract_item_id(item_data: Dict[str, Any]) -> Optional[str]:
    """Extract the SkyBlock item ID from NBT data."""
    try:
        tag = item_data.get("tag", {})
        extra = tag.get("ExtraAttributes", {})
        return extra.get("id")
    except Exception:
        return None


def _extract_item_name(item_data: Dict[str, Any]) -> str:
    """Extract the display name from NBT data."""
    try:
        tag = item_data.get("tag", {})
        display = tag.get("display", {})
        name = display.get("Name", "")
        # Strip color codes
        if isinstance(name, str):
            import re
            return re.sub(r'§.', '', name)
        return str(name) if name else "Unknown Item"
    except Exception:
        return "Unknown Item"


def _extract_rarity(item_data: Dict[str, Any]) -> Optional[str]:
    """Extract item rarity from lore or NBT data."""
    try:
        tag = item_data.get("tag", {})
        extra = tag.get("ExtraAttributes", {})
        
        # Check for explicit rarity
        if "rarity" in extra:
            return str(extra["rarity"]).upper()
        
        # Try to parse from lore (last line usually has rarity)
        display = tag.get("display", {})
        lore = display.get("Lore", [])
        if lore:
            last_line = lore[-1] if isinstance(lore[-1], str) else ""
            rarities = ["COMMON", "UNCOMMON", "RARE", "EPIC", "LEGENDARY", 
                       "MYTHIC", "DIVINE", "SPECIAL", "VERY_SPECIAL"]
            for rarity in rarities:
                if rarity in last_line.upper():
                    return rarity
        return None
    except Exception:
        return None


def _extract_lore(item_data: Dict[str, Any]) -> List[str]:
    """Extract lore lines from NBT data."""
    try:
        tag = item_data.get("tag", {})
        display = tag.get("display", {})
        lore = display.get("Lore", [])
        return [str(line) for line in lore] if lore else []
    except Exception:
        return []


def _extract_mc_id(item_data: Dict[str, Any]) -> Optional[str]:
    """Extract Minecraft ID from NBT data."""
    try:
        return item_data.get("id")
    except Exception:
        return None


def _extract_damage(item_data: Dict[str, Any]) -> Optional[int]:
    """Extract damage/metadata value from NBT data."""
    try:
        damage = item_data.get("Damage") or item_data.get("damage")
        return int(damage) if damage is not None else None
    except Exception:
        return None


def _process_museum_items(
    raw_items: Any,
    category: str = "unknown",
    prices: Optional[Dict[str, float]] = None
) -> List[MuseumItem]:
    """Process raw museum item entries into MuseumItem objects."""
    items = []
    
    # Handle both dict and list formats
    if isinstance(raw_items, list):
        # List format: each item is a dict with item data
        for idx, item_entry in enumerate(raw_items):
            if not isinstance(item_entry, dict):
                continue
            
            # Try to extract item_id from the entry
            item_id = item_entry.get("id") or f"special_item_{idx}"
            donated_time = item_entry.get("donated_time")
            borrowing = item_entry.get("borrowing", False)
            
            items_data = item_entry.get("items", {})
            raw_data = items_data.get("data") if isinstance(items_data, dict) else None
            
            item_name = str(item_id).replace("_", " ").title()
            rarity = None
            lore = []
            mc_id = None
            damage = None
            item_data_parsed = None
            value = 0.0
            
            if raw_data:
                try:
                    # Use wardrobe's parser which is more robust and handles textures
                    parsed_list = _parse_inventory_items({'data': raw_data})
                    if parsed_list and len(parsed_list) > 0:
                        first_item = parsed_list[0]
                        if first_item:
                            item_name = first_item.get('name') or item_name
                            rarity = first_item.get('rarity')
                            lore = first_item.get('lore', [])
                            mc_id = first_item.get('mc_id')
                            item_data_parsed = first_item
                            
                            if prices:
                                value, _ = calculate_item_value(first_item, prices)
                except Exception as e:
                    LOGGER.debug(f"Failed to decode museum item {item_id}: {e}")
            
            # Resolve icon variants
            icon_variants = resolve_item_icon_variants(item_id, mc_id, damage)
            icon_url = icon_variants.get('furfsky') or icon_variants.get('vanilla')
            
            museum_item = MuseumItem(
                id=item_id,
                name=item_name,
                donated_time=donated_time,
                borrowing=borrowing,
                rarity=rarity,
                lore=lore,
                category=category,
                mc_id=mc_id,
                damage=damage,
                icon_url=icon_url,
                icon_variants=icon_variants,
                item_data=item_data_parsed,
                value=value
            )
            items.append(museum_item)
    elif isinstance(raw_items, dict):
        # Dict format: keyed by item_id
        for item_id, item_entry in raw_items.items():
            if not isinstance(item_entry, dict):
                continue
                
            donated_time = item_entry.get("donated_time")
            borrowing = item_entry.get("borrowing", False)
            
            # Decode the item data if present
            items_data = item_entry.get("items", {})
            raw_data = items_data.get("data") if isinstance(items_data, dict) else None
            
            item_name = item_id.replace("_", " ").title()
            rarity = None
            lore = []
            mc_id = None
            damage = None
            item_data_parsed = None
            value = 0.0
            
            if raw_data:
                try:
                    # Use wardrobe's parser
                    parsed_list = _parse_inventory_items({'data': raw_data})
                    if parsed_list and len(parsed_list) > 0:
                        first_item = parsed_list[0]
                        if first_item:
                            item_name = first_item.get('name') or item_name
                            rarity = first_item.get('rarity')
                            lore = first_item.get('lore', [])
                            mc_id = first_item.get('mc_id')
                            item_data_parsed = first_item
                            
                            if prices:
                                value, _ = calculate_item_value(first_item, prices)
                except Exception as e:
                    LOGGER.debug(f"Failed to decode museum item {item_id}: {e}")
            
            # Resolve icon variants
            icon_variants = resolve_item_icon_variants(item_id, mc_id, damage)
            icon_url = icon_variants.get('furfsky') or icon_variants.get('vanilla')
            
            museum_item = MuseumItem(
                id=item_id,
                name=item_name,
                donated_time=donated_time,
                borrowing=borrowing,
                rarity=rarity,
                lore=lore,
                category=category,
                mc_id=mc_id,
                damage=damage,
                icon_url=icon_url,
                icon_variants=icon_variants,
                item_data=item_data_parsed,
                value=value
            )
            items.append(museum_item)
    
    return items


def _process_special_items(raw_special: Dict[str, Any]) -> List[MuseumItem]:
    """Process special museum items (unique/limited items)."""
    return _process_museum_items(raw_special, category=SPECIAL_CATEGORY)


def parse_museum(
    museum_data: Optional[Dict[str, Any]],
    member_uuid: str
) -> Optional[Dict[str, Any]]:
    """
    Parse museum data from Hypixel API response.
    
    Args:
        museum_data: Raw museum API response containing member data
        member_uuid: The UUID of the player to get museum data for
        
    Returns:
        Processed museum data dictionary or None if not available
    """
    if not museum_data:
        return None
    
    # Museum API returns data keyed by member UUID
    member_museum = museum_data.get(member_uuid)
    if not member_museum:
        # Try without dashes
        clean_uuid = member_uuid.replace("-", "")
        member_museum = museum_data.get(clean_uuid)
    
    import logging
    LOGGER = logging.getLogger(__name__)
    LOGGER.warning(f"[MUSEUM] member_museum found: {member_museum is not None}, type: {type(member_museum) if member_museum else 'None'}")
    
    if not member_museum:
        return None
    
    # Extract value and appraisal status
    value = float(member_museum.get("value", 0))
    appraisal = member_museum.get("appraisal", False)
    
    # Process donated items
    raw_items = member_museum.get("items", {})
    raw_special = member_museum.get("special", {})
    
    # Categorize items
    weapons_items = []
    armor_items = []
    rarities_items = []
    
    all_items = _process_museum_items(raw_items, "items")
    special_items = _process_special_items(raw_special)
    
    # For now, all regular items go into a flat list
    # In a full implementation, you'd categorize based on MUSEUM constants
    
    total_donated = len(all_items)
    special_donated = len(special_items)
    
    return {
        "value": value,
        "appraisal": appraisal,
        "items": {
            "donated": [
                {
                    "id": item.id,
                    "name": item.name,
                    "donated_time": item.donated_time,
                    "borrowing": item.borrowing,
                    "rarity": item.rarity,
                    "category": item.category
                }
                for item in all_items
            ],
            "count": total_donated
        },
        "special": {
            "items": [
                {
                    "id": item.id,
                    "name": item.name,
                    "donated_time": item.donated_time,
                    "borrowing": item.borrowing,
                    "rarity": item.rarity
                }
                for item in special_items
            ],
            "count": special_donated
        },
        "summary": {
            "total_donated": total_donated + special_donated,
            "regular_items": total_donated,
            "special_items": special_donated,
            "museum_value": value,
            "has_appraisal": appraisal
        }
    }


def get_museum_summary(museum: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Get a summary of museum data for display.
    
    Args:
        museum: Processed museum data
        
    Returns:
        Summary dictionary for frontend display
    """
    if not museum:
        return {
            "available": False,
            "value": 0,
            "appraisal": False,
            "total_donated": 0,
            "categories": {}
        }
    
    return {
        "available": True,
        "value": museum.get("value", 0),
        "appraisal": museum.get("appraisal", False),
        "total_donated": museum.get("summary", {}).get("total_donated", 0),
        "regular_items": museum.get("items", {}).get("count", 0),
        "special_items": museum.get("special", {}).get("count", 0),
        "items": museum.get("items", {}).get("donated", []),
        "special": museum.get("special", {}).get("items", [])
    }


def _get_all_donated_items(donated_items: List[Dict[str, Any]]) -> Set[str]:
    """Get set of all donated item IDs including child items"""
    donated = set()
    
    for item in donated_items:
        item_id = item.get("id", "")
        donated.add(item_id)
        
        # If this item has children, mark them as donated too
        current = item_id
        while current in MUSEUM_CHILDREN:
            child = MUSEUM_CHILDREN[current]
            donated.add(child)
            current = child
    
    return donated


def get_missing_items(
    museum: Optional[Dict[str, Any]],
    include_prices: bool = True,
    sort_by_price: bool = True
) -> Dict[str, Any]:
    """
    Get missing museum items with prices, sorted by cheapest first.
    
    Args:
        museum: Processed museum data
        include_prices: Whether to fetch and include price data
        sort_by_price: Whether to sort by price (cheapest first)
        
    Returns:
        Dictionary with missing items by category
    """
    # Get donated items
    donated_items = []
    if museum:
        donated_items = museum.get("items", {}).get("donated", [])
    
    donated_set = _get_all_donated_items(donated_items)
    
    # Calculate totals
    all_museum_items = MUSEUM_WEAPONS + MUSEUM_ARMOR + MUSEUM_RARITIES
    total_items = len(all_museum_items)
    total_donated = len([i for i in all_museum_items if i in donated_set])
    
    # Find missing items by category
    missing_weapons = []
    missing_armor = []
    missing_rarities = []
    
    for item_id in MUSEUM_WEAPONS:
        if item_id not in donated_set:
            missing_weapons.append({
                "id": item_id,
                "name": item_id.replace("_", " ").title(),
                "category": "weapons"
            })
    
    for item_id in MUSEUM_ARMOR:
        if item_id not in donated_set:
            missing_armor.append({
                "id": item_id,
                "name": item_id.replace("_", " ").title(),
                "category": "armor"
            })
    
    for item_id in MUSEUM_RARITIES:
        if item_id not in donated_set:
            missing_rarities.append({
                "id": item_id,
                "name": item_id.replace("_", " ").title(),
                "category": "rarities"
            })
    
    # Add prices if requested
    if include_prices:
        # Prefetch prices
        _fetch_bazaar_prices()
        _fetch_auction_prices()
        
        for item in missing_weapons + missing_armor + missing_rarities:
            price = get_item_price(item["id"])
            item["price"] = price
            item["price_formatted"] = _format_price(price) if price else None
    
    # Sort by price if requested
    if sort_by_price:
        def sort_key(item):
            price = item.get("price")
            if price is None:
                return float('inf')  # Unknown prices go to end
            return price
        
        missing_weapons.sort(key=sort_key)
        missing_armor.sort(key=sort_key)
        missing_rarities.sort(key=sort_key)
    
    # Combine all missing items and sort
    all_missing = missing_weapons + missing_armor + missing_rarities
    if sort_by_price:
        all_missing.sort(key=lambda x: x.get("price") or float('inf'))
    
    return {
        "total_museum_items": total_items,
        "total_donated": total_donated,
        "total_missing": total_items - total_donated,
        "progress_percent": round((total_donated / total_items) * 100, 1) if total_items > 0 else 0,
        "weapons": {
            "total": len(MUSEUM_WEAPONS),
            "donated": len(MUSEUM_WEAPONS) - len(missing_weapons),
            "missing": missing_weapons
        },
        "armor": {
            "total": len(MUSEUM_ARMOR),
            "donated": len(MUSEUM_ARMOR) - len(missing_armor),
            "missing": missing_armor
        },
        "rarities": {
            "total": len(MUSEUM_RARITIES),
            "donated": len(MUSEUM_RARITIES) - len(missing_rarities),
            "missing": missing_rarities
        },
        "all_missing": all_missing[:100],  # Limit to top 100 cheapest
        "cheapest": all_missing[:20] if all_missing else []  # Top 20 cheapest for quick view
    }


def _format_price(price: float) -> str:
    """Format price with K/M/B suffix"""
    if price >= 1_000_000_000:
        return f"{price / 1_000_000_000:.1f}B"
    if price >= 1_000_000:
        return f"{price / 1_000_000:.1f}M"
    if price >= 1_000:
        return f"{price / 1_000:.1f}K"
    return f"{price:.0f}"


def get_cached_museum_summary(profile_id: str, museum_data: Dict[str, Any], force_refresh: bool = False) -> Optional[Dict[str, Any]]:
    cache_key = f"museum_summary:{profile_id}"
    if not force_refresh:
        cached = cache.get(cache_key)
        if cached:
            return cached
        
    summary = parse_museum(museum_data, profile_id)
    if summary:
        cache.set(cache_key, summary, timeout=300)
        
    return summary
