import base64
import binascii
import json
import logging
import os
import zipfile
import threading
import queue
from functools import lru_cache
from io import BytesIO
from typing import Dict, Iterable, Iterator, Literal, Optional, Set, Tuple

import requests

try:
    from PIL import Image  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover - optional dependency
    Image = None

LOGGER = logging.getLogger(__name__)
ITEMS_URL = "https://api.hypixel.net/resources/skyblock/items"
ASSET_BASE = (
    "https://raw.githubusercontent.com/InventivetalentDev/minecraft-assets/1.20.1"
    "/assets/minecraft/textures"
)
FURFSKY_TEXTURES_PATH = os.path.join(os.path.dirname(__file__), "furfsky_textures")
FURFSKY_TEXTURES_ZIP = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "furfsky.zip")
)
NEU_ICON_BASE_URL = (
    "https://raw.githubusercontent.com/Moulberry/NotEnoughUpdates-REPO/master/items"
)
NEU_TEXTURE_CACHE = os.path.join(os.path.dirname(__file__), "texture_cache")
VANILLA_TEXTURES_LIST = os.path.join(os.path.dirname(__file__), "vanilla_textures.json")

# Load valid vanilla textures
_VALID_VANILLA_TEXTURES: Set[str] = set()
if os.path.exists(VANILLA_TEXTURES_LIST):
    try:
        with open(VANILLA_TEXTURES_LIST, "r", encoding="utf-8") as f:
            _VALID_VANILLA_TEXTURES = set(json.load(f))
        LOGGER.info("Loaded %d valid vanilla textures", len(_VALID_VANILLA_TEXTURES))
    except Exception as e:
        LOGGER.warning("Failed to load vanilla textures list: %s", e)

# Dynamic texture cache for items discovered from player inventories
DYNAMIC_TEXTURE_CACHE_FILE = os.path.join(
    os.path.dirname(__file__), "dynamic_texture_cache.json"
)
_dynamic_texture_cache: Dict[str, str] = {}
_dynamic_cache_loaded = False


def _load_dynamic_cache() -> None:
    """Load dynamic texture cache from disk."""
    global _dynamic_texture_cache, _dynamic_cache_loaded
    if _dynamic_cache_loaded:
        return
    _dynamic_cache_loaded = True
    if os.path.exists(DYNAMIC_TEXTURE_CACHE_FILE):
        try:
            with open(DYNAMIC_TEXTURE_CACHE_FILE, "r", encoding="utf-8") as f:
                _dynamic_texture_cache = json.load(f)
            LOGGER.info("Loaded %d items from dynamic texture cache", len(_dynamic_texture_cache))
        except Exception as e:
            LOGGER.warning("Failed to load dynamic texture cache: %s", e)


def _save_dynamic_cache() -> None:
    """Save dynamic texture cache to disk."""
    try:
        with open(DYNAMIC_TEXTURE_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(_dynamic_texture_cache, f)
    except Exception as e:
        LOGGER.warning("Failed to save dynamic texture cache: %s", e)


def cache_item_texture(item_id: str, texture_url: str) -> None:
    """Cache a discovered item texture (e.g., from player inventory)."""
    _load_dynamic_cache()
    if item_id and texture_url and item_id not in _dynamic_texture_cache:
        _dynamic_texture_cache[item_id] = texture_url
        _save_dynamic_cache()
        LOGGER.debug("Cached texture for %s: %s", item_id, texture_url[:60])
        # Note: LRU cache will be cleared lazily when resolve_item_icon_for_pack is called


def _clear_icon_lru_cache() -> None:
    """Clear the LRU cache for resolve_item_icon_for_pack. Call after adding to dynamic cache."""
    try:
        resolve_item_icon_for_pack.cache_clear()
    except Exception:
        pass  # Function not yet defined or no cache


def get_cached_item_texture(item_id: str) -> Optional[str]:
    """Get a cached item texture URL."""
    _load_dynamic_cache()
    return _dynamic_texture_cache.get(item_id)


SESSION = requests.Session()
_ASSET_CACHE: Dict[str, Optional[str]] = {}
_TALL_TEXTURE_NOTICE_EMITTED = False
_NEU_ICON_MISSING: Set[str] = set()

# Background download worker for NEU textures
_DOWNLOAD_QUEUE = queue.Queue()
_PENDING_DOWNLOADS = set()
_DOWNLOAD_LOCK = threading.Lock()

def _neu_download_worker():
    while True:
        neu_key, local_path = _DOWNLOAD_QUEUE.get()
        url = f"{NEU_ICON_BASE_URL}/{neu_key}.png"
        try:
            response = SESSION.get(url, timeout=10)
            if response.status_code == 200 and response.content:
                # Write to temp file and rename to be atomic
                tmp_path = local_path + ".tmp"
                with open(tmp_path, "wb") as handle:
                    handle.write(response.content)
                if os.path.exists(tmp_path):
                    os.replace(tmp_path, local_path)
            else:
                _NEU_ICON_MISSING.add(neu_key)
        except Exception as e:
            LOGGER.debug(f"Failed to download NEU texture {neu_key}: {e}")
        finally:
            with _DOWNLOAD_LOCK:
                _PENDING_DOWNLOADS.discard(neu_key)
            _DOWNLOAD_QUEUE.task_done()

# Start worker thread
_WORKER_THREAD = threading.Thread(target=_neu_download_worker, daemon=True)
_WORKER_THREAD.start()

TexturePack = Literal["furfsky", "vanilla"]
TEXTURE_PACKS: Tuple[TexturePack, ...] = ("furfsky", "vanilla")

LEGACY_DYE_COLORS = [
    "white",
    "orange",
    "magenta",
    "light_blue",
    "yellow",
    "lime",
    "pink",
    "gray",
    "light_gray",
    "cyan",
    "purple",
    "blue",
    "brown",
    "green",
    "red",
    "black",
]

LEGACY_ID_ALIASES = {
    1: "stone",
    2: "grass_block",
    3: "dirt",
    4: "cobblestone",
    5: "oak_planks",
    6: "oak_sapling",
    7: "bedrock",
    8: "water",
    9: "water",
    10: "lava",
    11: "lava",
    12: "sand",
    13: "gravel",
    14: "gold_ore",
    15: "iron_ore",
    16: "coal_ore",
    17: "oak_log",
    18: "oak_leaves",
    19: "sponge",
    20: "glass",
    21: "lapis_ore",
    22: "lapis_block",
    23: "dispenser",
    24: "sandstone",
    25: "note_block",
    26: "bed",
    27: "powered_rail",
    28: "detector_rail",
    29: "sticky_piston",
    30: "cobweb",
    31: "grass",
    32: "dead_bush",
    33: "piston",
    34: "piston_head",
    35: "wool",
    37: "dandelion",
    38: "poppy",
    39: "brown_mushroom",
    40: "red_mushroom",
    41: "gold_block",
    42: "iron_block",
    43: "smooth_stone_slab",
    44: "stone_slab",
    45: "bricks",
    46: "tnt",
    47: "bookshelf",
    48: "mossy_cobblestone",
    49: "obsidian",
    50: "torch",
    51: "fire",
    52: "spawner",
    53: "oak_stairs",
    54: "chest",
    55: "redstone_wire",
    56: "diamond_ore",
    57: "diamond_block",
    58: "crafting_table",
    59: "wheat",
    60: "farmland",
    61: "furnace",
    62: "furnace",
    63: "oak_sign",
    64: "oak_door",
    65: "ladder",
    66: "rail",
    67: "cobblestone_stairs",
    68: "oak_wall_sign",
    69: "lever",
    70: "stone_pressure_plate",
    71: "iron_door",
    72: "oak_pressure_plate",
    73: "redstone_ore",
    74: "redstone_ore",
    75: "redstone_torch",
    76: "redstone_torch",
    77: "stone_button",
    78: "snow",
    79: "ice",
    80: "snow_block",
    81: "cactus",
    82: "clay",
    83: "sugar_cane",
    84: "jukebox",
    85: "oak_fence",
    86: "pumpkin",
    87: "netherrack",
    88: "soul_sand",
    89: "glowstone",
    90: "nether_portal",
    91: "jack_o_lantern",
    92: "cake",
    93: "repeater",
    94: "repeater",
    95: "stained_glass",
    96: "oak_trapdoor",
    97: "infested_stone",
    98: "stone_bricks",
    99: "brown_mushroom_block",
    100: "red_mushroom_block",
    101: "iron_bars",
    102: "glass_pane",
    103: "melon",
    104: "pumpkin_stem",
    105: "melon_stem",
    106: "vine",
    107: "oak_fence_gate",
    108: "brick_stairs",
    109: "stone_brick_stairs",
    110: "mycelium",
    111: "lily_pad",
    112: "nether_bricks",
    113: "nether_brick_fence",
    114: "nether_brick_stairs",
    115: "nether_wart",
    116: "enchanting_table",
    117: "brewing_stand",
    118: "cauldron",
    119: "end_portal",
    120: "end_portal_frame",
    121: "end_stone",
    122: "dragon_egg",
    123: "redstone_lamp",
    124: "redstone_lamp",
    125: "oak_slab",
    126: "oak_slab",
    127: "cocoa",
    128: "sandstone_stairs",
    129: "emerald_ore",
    130: "ender_chest",
    131: "tripwire_hook",
    132: "tripwire",
    133: "emerald_block",
    134: "spruce_stairs",
    135: "birch_stairs",
    136: "jungle_stairs",
    137: "command_block",
    138: "beacon",
    139: "cobblestone_wall",
    140: "flower_pot",
    141: "carrots",
    142: "potatoes",
    143: "oak_button",
    144: "skeleton_skull",
    145: "anvil",
    146: "trapped_chest",
    147: "light_weighted_pressure_plate",
    148: "heavy_weighted_pressure_plate",
    149: "comparator",
    150: "comparator",
    151: "daylight_detector",
    152: "redstone_block",
    153: "nether_quartz_ore",
    154: "hopper",
    155: "quartz_block",
    156: "quartz_stairs",
    157: "activator_rail",
    158: "dropper",
    159: "stained_clay",
    160: "stained_glass_pane",
    161: "acacia_leaves",
    162: "acacia_log",
    163: "acacia_stairs",
    164: "dark_oak_stairs",
    165: "slime_block",
    166: "barrier",
    167: "iron_trapdoor",
    168: "prismarine",
    169: "sea_lantern",
    170: "hay_block",
    171: "carpet",
    172: "terracotta",
    173: "coal_block",
    174: "packed_ice",
    175: "sunflower",
    176: "banner",
    177: "banner",
    178: "daylight_detector",
    179: "red_sandstone",
    180: "red_sandstone_stairs",
    181: "red_sandstone_slab",
    182: "red_sandstone_slab",
    183: "spruce_fence_gate",
    184: "birch_fence_gate",
    185: "jungle_fence_gate",
    186: "dark_oak_fence_gate",
    187: "acacia_fence_gate",
    188: "spruce_fence",
    189: "birch_fence",
    190: "jungle_fence",
    191: "dark_oak_fence",
    192: "acacia_fence",
    193: "spruce_door",
    194: "birch_door",
    195: "jungle_door",
    196: "acacia_door",
    197: "dark_oak_door",
    198: "end_rod",
    199: "chorus_plant",
    200: "chorus_flower",
    201: "purpur_block",
    202: "purpur_pillar",
    203: "purpur_stairs",
    204: "purpur_slab",
    205: "purpur_slab",
    206: "end_stone_bricks",
    207: "beetroots",
    208: "grass_path",
    209: "end_gateway",
    210: "repeating_command_block",
    211: "chain_command_block",
    212: "frosted_ice",
    213: "magma_block",
    214: "nether_wart_block",
    215: "red_nether_bricks",
    216: "bone_block",
    217: "structure_void",
    218: "observer",
    219: "white_shulker_box",
    220: "orange_shulker_box",
    221: "magenta_shulker_box",
    222: "light_blue_shulker_box",
    223: "yellow_shulker_box",
    224: "lime_shulker_box",
    225: "pink_shulker_box",
    226: "gray_shulker_box",
    227: "light_gray_shulker_box",
    228: "cyan_shulker_box",
    229: "purple_shulker_box",
    230: "blue_shulker_box",
    231: "brown_shulker_box",
    232: "green_shulker_box",
    233: "red_shulker_box",
    234: "black_shulker_box",
    235: "white_glazed_terracotta",
    236: "concrete",
    237: "concrete_powder",
    256: "iron_shovel",
    257: "iron_pickaxe",
    258: "iron_axe",
    259: "flint_and_steel",
    260: "apple",
    261: "bow",
    262: "arrow",
    263: "coal",
    264: "diamond",
    265: "iron_ingot",
    266: "gold_ingot",
    267: "iron_sword",
    268: "wooden_sword",
    269: "wooden_shovel",
    270: "wooden_pickaxe",
    271: "wooden_axe",
    272: "stone_sword",
    273: "stone_shovel",
    274: "stone_pickaxe",
    275: "stone_axe",
    276: "diamond_sword",
    277: "diamond_shovel",
    278: "diamond_pickaxe",
    279: "diamond_axe",
    280: "stick",
    281: "bowl",
    282: "mushroom_stew",
    283: "golden_sword",
    284: "golden_shovel",
    285: "golden_pickaxe",
    286: "golden_axe",
    287: "string",
    288: "feather",
    289: "gunpowder",
    290: "wooden_hoe",
    291: "stone_hoe",
    292: "iron_hoe",
    293: "diamond_hoe",
    294: "golden_hoe",
    295: "wheat_seeds",
    296: "wheat",
    297: "bread",
    298: "leather_helmet",
    299: "leather_chestplate",
    300: "leather_leggings",
    301: "leather_boots",
    302: "chainmail_helmet",
    303: "chainmail_chestplate",
    304: "chainmail_leggings",
    305: "chainmail_boots",
    306: "iron_helmet",
    307: "iron_chestplate",
    308: "iron_leggings",
    309: "iron_boots",
    310: "diamond_helmet",
    311: "diamond_chestplate",
    312: "diamond_leggings",
    313: "diamond_boots",
    314: "golden_helmet",
    315: "golden_chestplate",
    316: "golden_leggings",
    317: "golden_boots",
    318: "flint",
    319: "porkchop",
    320: "cooked_porkchop",
    321: "painting",
    322: "golden_apple",
    323: "sign",
    324: "wooden_door",
    325: "bucket",
    326: "water_bucket",
    327: "lava_bucket",
    328: "minecart",
    329: "saddle",
    330: "iron_door",
    331: "redstone",
    332: "snowball",
    333: "oak_boat",
    334: "leather",
    335: "milk_bucket",
    336: "brick",
    337: "clay_ball",
    338: "reeds",
    339: "paper",
    340: "book",
    341: "slime_ball",
    342: "chest_minecart",
    343: "furnace_minecart",
    344: "egg",
    345: "compass",
    346: "fishing_rod",
    347: "clock",
    348: "glowstone_dust",
    349: "fish",
    350: "cooked_fish",
    351: "dye",
    352: "bone",
    353: "sugar",
    354: "cake",
    355: "bed",
    356: "repeater",
    357: "cookie",
    358: "filled_map",
    359: "shears",
    360: "melon",
    361: "pumpkin_seeds",
    362: "melon_seeds",
    363: "beef",
    364: "cooked_beef",
    365: "chicken",
    366: "cooked_chicken",
    367: "rotten_flesh",
    368: "ender_pearl",
    369: "blaze_rod",
    370: "ghast_tear",
    371: "gold_nugget",
    372: "nether_wart",
    373: "potion",
    374: "glass_bottle",
    375: "spider_eye",
    376: "fermented_spider_eye",
    377: "blaze_powder",
    378: "magma_cream",
    379: "brewing_stand",
    380: "cauldron",
    381: "ender_eye",
    382: "speckled_melon",
    383: "spawn_egg",
    384: "experience_bottle",
    385: "fire_charge",
    386: "writable_book",
    387: "written_book",
    388: "emerald",
    389: "item_frame",
    390: "flower_pot",
    391: "carrot",
    392: "potato",
    393: "baked_potato",
    394: "poisonous_potato",
    395: "map",
    396: "golden_carrot",
    397: "skull",
    398: "carrot_on_a_stick",
    399: "nether_star",
    400: "pumpkin_pie",
    401: "firework_rocket",
    402: "firework_star",
    403: "enchanted_book",
    404: "comparator",
    405: "nether_brick",
    406: "quartz",
    407: "tnt_minecart",
    408: "hopper_minecart",
    409: "prismarine_shard",
    410: "prismarine_crystals",
    411: "rabbit",
    412: "cooked_rabbit",
    413: "rabbit_stew",
    414: "rabbit_foot",
    415: "rabbit_hide",
    416: "armor_stand",
    417: "iron_horse_armor",
    418: "golden_horse_armor",
    419: "diamond_horse_armor",
    420: "lead",
    421: "name_tag",
    422: "command_block_minecart",
    423: "mutton",
    424: "cooked_mutton",
    425: "banner",
    426: "end_crystal",
    427: "spruce_door",
    428: "birch_door",
    429: "jungle_door",
    430: "acacia_door",
    431: "dark_oak_door",
    432: "chorus_fruit",
    433: "popped_chorus_fruit",
    434: "beetroot",
    435: "beetroot_seeds",
    436: "beetroot_soup",
    437: "dragon_breath",
    438: "splash_potion",
    439: "spectral_arrow",
    440: "tipped_arrow",
    441: "lingering_potion",
    442: "shield",
    443: "elytra",
    444: "spruce_boat",
    445: "birch_boat",
    446: "jungle_boat",
    447: "acacia_boat",
    448: "dark_oak_boat",
    449: "totem_of_undying",
    450: "shulker_shell",
    452: "iron_nugget",
    453: "knowledge_book",
}

# Skip HEAD validation for common vanilla armor textures
# These are standard Minecraft items that should always exist
COMMON_VANILLA_ITEMS = {
    'item/leather_helmet.png',
    'item/leather_chestplate.png', 
    'item/leather_leggings.png',
    'item/leather_boots.png',
    'item/iron_helmet.png',
    'item/iron_chestplate.png',
    'item/iron_leggings.png',
    'item/iron_boots.png',
    'item/diamond_helmet.png',
    'item/diamond_chestplate.png',
    'item/diamond_leggings.png',
    'item/diamond_boots.png',
    'item/golden_helmet.png',
    'item/golden_chestplate.png',
    'item/golden_leggings.png',
    'item/golden_boots.png',
    'item/chainmail_helmet.png',
    'item/chainmail_chestplate.png',
    'item/chainmail_leggings.png',
    'item/chainmail_boots.png',
    'item/bow.png',
    'item/arrow.png',
    'item/iron_sword.png',
    'item/diamond_sword.png',
    'item/golden_sword.png',
    'item/stone_sword.png',
    'item/wooden_sword.png',
    'item/stick.png',
    'item/blaze_rod.png',
    'item/ender_pearl.png',
    'item/bone.png',
    'item/rotten_flesh.png',
    'item/gunpowder.png',
    'item/spider_eye.png',
    'item/ghast_tear.png',
    'item/magma_cream.png',
    'item/potion.png',
    'item/glass_bottle.png',
    'item/paper.png',
    'item/book.png',
    'item/map.png',
    'item/compass.png',
    'item/clock.png',
    'item/shears.png',
    'item/bucket.png',
    'item/water_bucket.png',
    'item/lava_bucket.png',
    'item/milk_bucket.png',
    'item/minecart.png',
    'item/chest_minecart.png',
    'item/tnt_minecart.png',
    'item/hopper_minecart.png',
    'item/boat.png',
    'item/elytra.png',
    'item/shulker_shell.png',
    'item/totem_of_undying.png',
    'item/trident.png',
    'item/shield.png',
    'item/crossbow.png',
    'item/skeleton_skull.png',
    'item/wither_skeleton_skull.png',
    'item/zombie_head.png',
    'item/creeper_head.png',
    'item/dragon_head.png',
    'item/barrier.png',
    'block/stone.png',
    'block/dirt.png',
    'block/grass_block.png',
    'block/cobblestone.png',
    'block/oak_planks.png',
    'block/bedrock.png',
    'block/sand.png',
    'block/gravel.png',
    'block/gold_ore.png',
    'block/iron_ore.png',
    'block/coal_ore.png',
    'block/oak_log.png',
    'block/oak_leaves.png',
    'block/sponge.png',
    'block/glass.png',
    'block/lapis_ore.png',
    'block/lapis_block.png',
    'block/dispenser.png',
    'block/sandstone.png',
    'block/note_block.png',
    'block/wool.png',
    'block/gold_block.png',
    'block/iron_block.png',
    'block/bricks.png',
    'block/tnt.png',
    'block/bookshelf.png',
    'block/mossy_cobblestone.png',
    'block/obsidian.png',
    'block/torch.png',
    'block/spawner.png',
    'block/chest.png',
    'block/diamond_ore.png',
    'block/diamond_block.png',
    'block/crafting_table.png',
    'block/furnace.png',
    'block/redstone_ore.png',
    'block/ice.png',
    'block/snow_block.png',
    'block/clay.png',
    'block/jukebox.png',
    'block/pumpkin.png',
    'block/netherrack.png',
    'block/soul_sand.png',
    'block/glowstone.png',
    'block/jack_o_lantern.png',
    'block/stained_glass.png',
    'block/stone_bricks.png',
    'block/melon.png',
    'block/end_stone.png',
    'block/redstone_lamp.png',
    'block/emerald_ore.png',
    'block/emerald_block.png',
    'block/command_block.png',
    'block/redstone_block.png',
    'block/quartz_block.png',
    'block/dropper.png',
    'block/stained_glass_pane.png',
    'block/slime_block.png',
    'block/hay_block.png',
    'block/coal_block.png',
    'block/packed_ice.png',
    'block/concrete.png',
    'block/concrete_powder.png',
}

COLOR_TEMPLATE_MAP = {
    "carpet": ["block/{color}_carpet.png"],
    "concrete": ["block/{color}_concrete.png"],
    "concrete_powder": ["block/{color}_concrete_powder.png"],
    "glazed_terracotta": ["block/{color}_glazed_terracotta.png"],
    "shulker_box": ["block/{color}_shulker_box.png"],
    "stained_clay": ["block/{color}_terracotta.png"],
    "stained_glass": ["block/{color}_stained_glass.png"],
    "stained_glass_pane": ["block/{color}_stained_glass_pane.png"],
    "stained_hardened_clay": ["block/{color}_terracotta.png"],
    "terracotta": ["block/{color}_terracotta.png"],
    "wool": ["block/{color}_wool.png"],
    "ink_sack": ["item/{color}_dye.png"],
}

MATERIAL_ALIASES = {
    "gold_helmet": "golden_helmet",
    "gold_chestplate": "golden_chestplate",
    "gold_leggings": "golden_leggings",
    "gold_boots": "golden_boots",
    "gold_sword": "golden_sword",
    "gold_horse_armor": "golden_horse_armor",
    "golden_apple": "golden_apple",
}

FURFSKY_ICON_ALIASES: Dict[str, str] = {
    "ranchers_boots": "rancher_boots.png",
    "melon_helmet": "melon.png",
}


def _furfsky_zip_path() -> Optional[str]:
    if os.path.exists(FURFSKY_TEXTURES_ZIP):
        return FURFSKY_TEXTURES_ZIP
    return None


@lru_cache(maxsize=1)
def _furfsky_zip_index() -> Dict[str, str]:
    zip_path = _furfsky_zip_path()
    if not zip_path:
        return {}

    def _entry_score(path: str) -> int:
        lowered = path.lower()
        score = 0
        if "/icons/" in lowered:
            score += 10
        if "/model/" in lowered or "/models/" in lowered:
            score -= 5
        if lowered.endswith("_icon.png"):
            score += 5
        if "/items/" in lowered:
            score += 2
        return score

    try:
        with zipfile.ZipFile(zip_path, "r") as zip_file:
            mapping: Dict[str, str] = {}
            scores: Dict[str, int] = {}
            for entry in zip_file.infolist():
                if entry.is_dir():
                    continue
                if not entry.filename.lower().endswith(".png"):
                    continue
                name = os.path.basename(entry.filename)
                score = _entry_score(entry.filename)
                if name not in mapping or score > scores.get(name, -999):
                    mapping[name] = entry.filename
                    scores[name] = score
    except zipfile.BadZipFile as exc:
        LOGGER.warning("Failed to index FurSky texture pack: %s", exc)
        return {}

    return mapping


def furfsky_texture_exists(filename: str) -> bool:
    if not filename:
        return False

    local_path = os.path.join(FURFSKY_TEXTURES_PATH, filename)
    if os.path.exists(local_path):
        return True

    return filename in _furfsky_zip_index()


@lru_cache(maxsize=256)
def load_furfsky_texture(filename: str) -> Optional[bytes]:
    if not filename:
        return None

    try:
        for root in (FURFSKY_TEXTURES_PATH, NEU_TEXTURE_CACHE):
            if not root:
                continue
            local_path = os.path.join(root, filename)
            if os.path.exists(local_path):
                with open(local_path, "rb") as handle:
                    payload = handle.read()
                return _normalize_texture_payload(payload)

        mapping = _furfsky_zip_index()
        relative = mapping.get(filename)
        zip_path = _furfsky_zip_path()
        if not relative or not zip_path:
            return None

        with zipfile.ZipFile(zip_path, "r") as zip_file:
            payload = zip_file.read(relative)
        return _normalize_texture_payload(payload)
    except (KeyError, OSError, zipfile.BadZipFile) as exc:
        LOGGER.warning("Failed to extract %s from FurSky zip: %s", filename, exc)
    except Exception:  # pragma: no cover - defensive
        LOGGER.exception("Unexpected error while loading FurSky texture %s", filename)

    return None


def _normalize_texture_payload(payload: bytes) -> bytes:
    if not payload or Image is None:
        return payload

    global _TALL_TEXTURE_NOTICE_EMITTED
    try:
        with Image.open(BytesIO(payload)) as image:
            width, height = image.size
            if (
                width <= 0
                or height <= 0
                or height <= width
                or height % width != 0
                or height < width * 2
            ):
                return payload

            frame_height = width
            cropped = image.crop((0, 0, width, frame_height))
            buffer = BytesIO()
            cropped.save(buffer, format="PNG")
            if not _TALL_TEXTURE_NOTICE_EMITTED:
                LOGGER.debug(
                    "Trimmed tall FurSky texture to the first frame (w=%s h=%s)",
                    width,
                    height,
                )
                _TALL_TEXTURE_NOTICE_EMITTED = True
            return buffer.getvalue()
    except Exception:
        LOGGER.debug("Failed to normalize FurSky texture payload", exc_info=True)
        return payload


def _normalize_identifier(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    normalized = str(value).lower()
    normalized = normalized.replace("minecraft:", "")
    for ch in (" ", "-", ":", ".", "'"):
        normalized = normalized.replace(ch, "_")
    while "__" in normalized:
        normalized = normalized.replace("__", "_")
    normalized = normalized.strip("_")
    return normalized or None


def _furfsky_icon_candidates(value: Optional[str]) -> Iterator[str]:
    normalized = _normalize_identifier(value)
    if not normalized:
        return

    yield f"{normalized}.png"

    # Some icons are stored without trailing suffixes; try a few variants.
    suffix_map = {
        "_helmet": ("_head", "_cap"),
        "_chestplate": ("_chest",),
        "_leggings": ("_legs", "_pant"),
        "_boots": ("_feet",),
    }
    for suffix, variants in suffix_map.items():
        if normalized.endswith(suffix):
            stem = normalized[: -len(suffix)]
            for variant in variants:
                yield f"{stem}{variant}.png"


def _furfsky_icon_override(*values: Optional[str]) -> Optional[str]:
    for value in values:
        normalized = _normalize_identifier(value)
        if normalized:
            alias_candidate = FURFSKY_ICON_ALIASES.get(normalized)
            if alias_candidate and furfsky_texture_exists(alias_candidate):
                return f"/api/static/{alias_candidate}"

        for candidate in _furfsky_icon_candidates(value):
            if furfsky_texture_exists(candidate):
                return f"/api/static/{candidate}"
        neu_texture = _ensure_neu_texture(value)
        if neu_texture:
            return f"/api/static/{neu_texture}"
    return None


def _ensure_neu_texture(identifier: Optional[str]) -> Optional[str]:
    normalized = _normalize_identifier(identifier)
    if not normalized:
        return None

    neu_key = normalized.upper()
    if neu_key in _NEU_ICON_MISSING:
        return None

    filename = f"neu_{neu_key}.png"
    os.makedirs(NEU_TEXTURE_CACHE, exist_ok=True)
    local_path = os.path.join(NEU_TEXTURE_CACHE, filename)
    
    if os.path.exists(local_path):
        return filename

    # Check if already pending
    with _DOWNLOAD_LOCK:
        if neu_key in _PENDING_DOWNLOADS:
            return None
        _PENDING_DOWNLOADS.add(neu_key)
    
    # Queue for background download
    _DOWNLOAD_QUEUE.put((neu_key, local_path))
    
    # Return None immediately so we don't block
    return None


@lru_cache(maxsize=1)
def _load_item_resource_map() -> Dict[str, Dict[str, object]]:
    try:
        response = SESSION.get(ITEMS_URL, timeout=10)
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException as exc:  # pragma: no cover - network failure
        LOGGER.warning("Failed to load Hypixel item resources: %s", exc)
        return {}

    items = payload.get("items") or []
    mapping = {}
    for item in items:
        item_id = item.get("id")
        if item_id:
            mapping[item_id] = item
    return mapping


def get_item_resource(item_id: Optional[str]) -> Optional[Dict[str, object]]:
    if not item_id:
        return None
    mapping = _load_item_resource_map()
    return mapping.get(item_id)


def decode_texture_value(value: Optional[str], prefer_raw_skin: bool = False) -> Optional[str]:
    """
    Decodes a base64 texture value or handles a texture hash/url.
    Returns a URL to the image (mc-heads, crafatar, or direct).
    If prefer_raw_skin is True, returns the raw textures.minecraft.net URL if available.
    """
    if not value:
        return None

    # If it's already a URL, convert to mc-heads if it's a raw texture URL
    if value.startswith("http"):
        value = value.replace("http://", "https://")
        if not prefer_raw_skin and value.startswith("https://textures.minecraft.net/texture/"):
            texture_hash = value.rsplit("/", 1)[-1]
            if texture_hash:
                return f"https://mc-heads.net/head/{texture_hash}"
        return value

    # Check if it's a plain texture hash (64 character hex string)
    if len(value) == 64 and all(c in '0123456789abcdefABCDEF' for c in value):
        if prefer_raw_skin:
            return f"https://textures.minecraft.net/texture/{value}"
        return f"https://mc-heads.net/head/{value}"

    try:
        # Fix padding if necessary
        value_padded = value + "=" * (-len(value) % 4)
        decoded_bytes = base64.b64decode(value_padded)
        decoded_str = decoded_bytes.decode("utf-8")
        payload = json.loads(decoded_str)
    except (binascii.Error, ValueError, TypeError, json.JSONDecodeError, UnicodeDecodeError):
        return None

    textures = payload.get("textures")
    if isinstance(textures, dict):
        skin = textures.get("SKIN")
        if isinstance(skin, dict):
            url = skin.get("url")
            if isinstance(url, str) and url:
                url = url.replace("http://", "https://")
                if not prefer_raw_skin and url.startswith("https://textures.minecraft.net/texture/"):
                    texture_hash = url.rsplit("/", 1)[-1]
                    if texture_hash:
                        # Use mc-heads for better caching/performance on heads
                        return f"https://mc-heads.net/head/{texture_hash}"
                return url

    if not prefer_raw_skin:
        profile_id = payload.get("profileId")
        if isinstance(profile_id, str):
            stripped = profile_id.replace("-", "")
            if len(stripped) == 32:
                return f"https://crafatar.com/renders/head/{stripped}?overlay&scale=6"

    return None


def _decode_skin_url(skin: Optional[Dict[str, str]]) -> Optional[str]:
    if not skin:
        return None
    value = skin.get("value")
    return decode_texture_value(value)


def _cached_asset_path(candidate: str) -> Optional[str]:
    """
    Return a local proxy URL for vanilla textures instead of direct GitHub links.
    This avoids CORS issues and improves reliability.
    """
    if candidate in _ASSET_CACHE:
        return _ASSET_CACHE[candidate]

    # Use local proxy path for all vanilla textures
    proxy_url = f"/api/vanilla/{candidate}"
    
    # Fast path: Check against pre-loaded list
    if candidate in _VALID_VANILLA_TEXTURES or candidate in COMMON_VANILLA_ITEMS:
        _ASSET_CACHE[candidate] = proxy_url
        return proxy_url
    
    # If not in our valid list, assume it doesn't exist to avoid slow network checks
    # This is a trade-off: we might miss some obscure textures, but we gain massive performance
    _ASSET_CACHE[candidate] = None
    return None


def _color_from_damage(durability: Optional[int]) -> Optional[str]:
    if durability is None:
        return None
    try:
        idx = int(durability) & 15
    except (TypeError, ValueError):
        return None
    if 0 <= idx < len(LEGACY_DYE_COLORS):
        return LEGACY_DYE_COLORS[idx]
    return None


def _build_material_candidates(
    name: str,
    durability: Optional[int] = None,
    include_generic_fallback: bool = True,
) -> Iterable[str]:
    normalized = name.lower().replace("minecraft:", "").replace(":", "_")
    normalized = MATERIAL_ALIASES.get(normalized, normalized)
    normalized = normalized.replace(".", "_")

    parts = normalized.split()
    if len(parts) > 1:
        normalized = "_".join(parts)

    base = normalized

    color = _color_from_damage(durability)
    if color:
        color_key = base
        if color_key.endswith("_pane"):
            color_key = color_key  # already handled by map
        if color_key in COLOR_TEMPLATE_MAP:
            for template in COLOR_TEMPLATE_MAP[color_key]:
                yield template.format(color=color)
        elif color_key.endswith("_shulker_box"):
            yield f"block/{color}_shulker_box.png"

    # Try item texture first
    candidates = [f"item/{base}.png"]

    # Try block textures with various suffixes
    candidates.extend([
        f"block/{base}.png",
        f"block/{base}_side.png",
        f"block/{base}_top.png",
        f"block/{base}_front.png",
    ])

    if base == "skull":
        # Handle skull types
        skull_types = {
            0: "skeleton_skull",
            1: "wither_skeleton_skull",
            2: "zombie_head",
            3: "player_head",
            4: "creeper_head",
            5: "dragon_head"
        }
        skull_name = skull_types.get(durability or 0, "skeleton_skull")
        if skull_name == "player_head":
             # Player head doesn't have a static texture usually, but we can try steve
             yield "item/player_head.png" # Might not exist
             yield "item/steve.png" # Custom fallback?
             # Fallback to skeleton skull if nothing else
             yield "item/skeleton_skull.png"
        else:
             yield f"item/{skull_name}.png"
             yield f"block/{skull_name}.png"

    if base.endswith("_block"):
        trimmed = base[:-6]
        candidates.extend(
            [
                f"block/{trimmed}.png",
                f"block/{trimmed}_side.png",
                f"block/{trimmed}_top.png",
            ]
        )
    if base.endswith("_ore"):
        trimmed = base[:-4]
        candidates.extend(
            [
                f"block/{base}.png",
                f"block/{trimmed}_ore.png",
            ]
        )
    if base.endswith("_helmet"):
        candidates.append("item/iron_helmet.png")
    if base.endswith("_chestplate"):
        candidates.append("item/iron_chestplate.png")
    if base.endswith("_leggings"):
        candidates.append("item/iron_leggings.png")
    if base.endswith("_boots"):
        candidates.append("item/iron_boots.png")

    if "_" in base:
        tail = base.split("_")[-1]
        candidates.extend([
            f"item/{tail}.png",
            f"block/{tail}.png",
        ])

    # Do NOT use stone as fallback - it's confusing
    # Better to show nothing than a misleading stone texture

    seen = set()
    for candidate in candidates:
        if candidate not in seen:
            seen.add(candidate)
            yield candidate


def _local_asset_path(candidate: str) -> Optional[str]:
    filename = os.path.basename(candidate)
    if furfsky_texture_exists(filename):
        return f"/api/static/{filename}"
    return None


def _material_texture(
    name: Optional[str],
    durability: Optional[int] = None,
    pack: TexturePack = "furfsky",
    include_generic_fallback: bool = True,
) -> Optional[str]:
    if not name:
        return None
    normalized = name
    if isinstance(name, bytes):
        try:
            normalized = name.decode("utf-8")
        except UnicodeDecodeError:
            normalized = str(name)
    try:
        numeric = int(normalized)
    except (TypeError, ValueError):
        numeric = None
    else:
        normalized = LEGACY_ID_ALIASES.get(numeric, str(normalized))

    normalized = MATERIAL_ALIASES.get(str(normalized).lower(), str(normalized))

    normalized_pack = "vanilla" if str(pack).lower() == "vanilla" else "furfsky"

    for candidate in _build_material_candidates(
        str(normalized),
        durability,
        include_generic_fallback=include_generic_fallback,
    ):
        if normalized_pack == "furfsky":
            local_path = _local_asset_path(candidate)
            if local_path:
                return local_path

        url = _cached_asset_path(candidate)
        if url:
            return url
    return None


def _normalize_pack(pack: str) -> TexturePack:
    return "vanilla" if str(pack).lower() == "vanilla" else "furfsky"


@lru_cache(maxsize=2048)
def resolve_item_icon_for_pack(
    item_id: Optional[str],
    mc_id: Optional[str],
    damage: Optional[int] = None,
    pack: TexturePack = "furfsky",
) -> Optional[str]:
    """
    Resolve an icon URL for the requested texture pack.
    Preference order:
        0. Dynamic cache (discovered from player inventories)
        1. Hypixel custom skin texture
        2. Pack-specific overrides (FurSky only)
        3. Vanilla material texture, using Hypixel material hints/durability
        4. Vanilla material texture derived from the raw mc_id/damage combo
    """
    normalized_pack = _normalize_pack(pack)
    
    # Check dynamic cache first (for items not in Hypixel API)
    if item_id:
        cached_url = get_cached_item_texture(item_id)
        if cached_url:
            return cached_url
    
    resource_map = _load_item_resource_map()
    icon_url: Optional[str] = None

    entry = resource_map.get(item_id) if item_id else None
    entry_durability: Optional[int] = None
    entry_material = None
    entry_internal = None
    entry_category = None

    if entry:
        icon_url = _decode_skin_url(entry.get("skin"))  # type: ignore[arg-type]
        entry_material = entry.get("material")
        entry_durability = entry.get("durability")
        entry_internal = entry.get("internalname")
        entry_category = entry.get("category")

    # FurSky: try override on internal name first
    if normalized_pack == "furfsky" and icon_url:
        return icon_url

    if normalized_pack == "furfsky":
        override = _furfsky_icon_override(item_id, entry_internal if entry_internal else None)
        if override:
            return override

    if icon_url:
        return icon_url

    skip_generic_fallback = str(entry_category).upper() == "ACCESSORY"
    icon_url = _material_texture(
        entry_material,
        entry_durability,
        pack=normalized_pack,
        include_generic_fallback=not skip_generic_fallback,
    )
    if icon_url:
        return icon_url

    if not mc_id:
        return None

    effective_durability = damage if damage is not None else entry_durability
    if normalized_pack == "furfsky":
        override = _furfsky_icon_override(mc_id)
        if override:
            return override

    return _material_texture(
        mc_id,
        effective_durability,
        pack=normalized_pack,
        include_generic_fallback=not skip_generic_fallback,
    )


def resolve_item_icon_variants(
    item_id: Optional[str],
    mc_id: Optional[str],
    damage: Optional[int] = None,
) -> Dict[TexturePack, Optional[str]]:
    variants: Dict[TexturePack, Optional[str]] = {}
    for pack in TEXTURE_PACKS:
        variants[pack] = resolve_item_icon_for_pack(item_id, mc_id, damage, pack=pack)
    return variants


def resolve_item_icon(
    item_id: Optional[str],
    mc_id: Optional[str],
    damage: Optional[int] = None,
) -> Optional[str]:
    return resolve_item_icon_for_pack(item_id, mc_id, damage, pack="furfsky")
