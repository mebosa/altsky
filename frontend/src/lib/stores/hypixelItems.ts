import { writable, derived, get } from 'svelte/store';

// Hypixel item data from public API
export type HypixelItem = {
  id: string;
  name: string;
  material?: string;
  durability?: number;
  skin?: { value: string };
  category?: string;
  tier?: string;
};

// Store for items map
const itemsMapStore = writable<Map<string, HypixelItem>>(new Map());

// Loading state
export const itemsLoading = writable(false);
export const itemsLoaded = writable(false);

// Texture caches (loaded from backend)
const furfskyCacheStore = writable<Map<string, string | null>>(new Map());
export const furfskyCacheLoaded = writable(false);
const furfskyCacheLoading = writable(false);

const vanillaCacheStore = writable<Map<string, string | null>>(new Map());
export const vanillaCacheLoaded = writable(false);
const vanillaCacheLoading = writable(false);

// Material to vanilla texture path mapping
const MATERIAL_TO_TEXTURE: Record<string, string> = {
  // Armor
  LEATHER_HELMET: 'item/leather_helmet',
  LEATHER_CHESTPLATE: 'item/leather_chestplate',
  LEATHER_LEGGINGS: 'item/leather_leggings',
  LEATHER_BOOTS: 'item/leather_boots',
  IRON_HELMET: 'item/iron_helmet',
  IRON_CHESTPLATE: 'item/iron_chestplate',
  IRON_LEGGINGS: 'item/iron_leggings',
  IRON_BOOTS: 'item/iron_boots',
  GOLD_HELMET: 'item/golden_helmet',
  GOLD_CHESTPLATE: 'item/golden_chestplate',
  GOLD_LEGGINGS: 'item/golden_leggings',
  GOLD_BOOTS: 'item/golden_boots',
  DIAMOND_HELMET: 'item/diamond_helmet',
  DIAMOND_CHESTPLATE: 'item/diamond_chestplate',
  DIAMOND_LEGGINGS: 'item/diamond_leggings',
  DIAMOND_BOOTS: 'item/diamond_boots',
  CHAINMAIL_HELMET: 'item/chainmail_helmet',
  CHAINMAIL_CHESTPLATE: 'item/chainmail_chestplate',
  CHAINMAIL_LEGGINGS: 'item/chainmail_leggings',
  CHAINMAIL_BOOTS: 'item/chainmail_boots',
  // Weapons
  WOOD_SWORD: 'item/wooden_sword',
  STONE_SWORD: 'item/stone_sword',
  IRON_SWORD: 'item/iron_sword',
  GOLD_SWORD: 'item/golden_sword',
  DIAMOND_SWORD: 'item/diamond_sword',
  BOW: 'item/bow',
  // Tools
  WOOD_PICKAXE: 'item/wooden_pickaxe',
  STONE_PICKAXE: 'item/stone_pickaxe',
  IRON_PICKAXE: 'item/iron_pickaxe',
  GOLD_PICKAXE: 'item/golden_pickaxe',
  DIAMOND_PICKAXE: 'item/diamond_pickaxe',
  WOOD_AXE: 'item/wooden_axe',
  STONE_AXE: 'item/stone_axe',
  IRON_AXE: 'item/iron_axe',
  GOLD_AXE: 'item/golden_axe',
  DIAMOND_AXE: 'item/diamond_axe',
  WOOD_HOE: 'item/wooden_hoe',
  STONE_HOE: 'item/stone_hoe',
  IRON_HOE: 'item/iron_hoe',
  GOLD_HOE: 'item/golden_hoe',
  DIAMOND_HOE: 'item/diamond_hoe',
  WOOD_SPADE: 'item/wooden_shovel',
  STONE_SPADE: 'item/stone_shovel',
  IRON_SPADE: 'item/iron_shovel',
  GOLD_SPADE: 'item/golden_shovel',
  DIAMOND_SPADE: 'item/diamond_shovel',
  // Misc items
  STICK: 'item/stick',
  BLAZE_ROD: 'item/blaze_rod',
  BONE: 'item/bone',
  GOLD_INGOT: 'item/gold_ingot',
  IRON_INGOT: 'item/iron_ingot',
  DIAMOND: 'item/diamond',
  EMERALD: 'item/emerald',
  PRISMARINE_SHARD: 'item/prismarine_shard',
  PRISMARINE_CRYSTALS: 'item/prismarine_crystals',
  GHAST_TEAR: 'item/ghast_tear',
  MAGMA_CREAM: 'item/magma_cream',
  FEATHER: 'item/feather',
  FISHING_ROD: 'item/fishing_rod',
  SHEARS: 'item/shears',
  SKULL_ITEM: 'item/player_head',
  // Blocks
  CACTUS: 'block/cactus_side',
  PUMPKIN: 'block/pumpkin_side',
  MELON_BLOCK: 'block/melon_side',
  SPONGE: 'block/sponge',
  WOOL: 'block/white_wool',
  GOLD_BLOCK: 'block/gold_block',
  IRON_BLOCK: 'block/iron_block',
  DIAMOND_BLOCK: 'block/diamond_block',
  EMERALD_BLOCK: 'block/emerald_block',
  LAPIS_BLOCK: 'block/lapis_block',
  REDSTONE_BLOCK: 'block/redstone_block',
  COAL_BLOCK: 'block/coal_block',
  OBSIDIAN: 'block/obsidian',
  GLOWSTONE: 'block/glowstone',
  NETHERRACK: 'block/netherrack',
  END_STONE: 'block/end_stone',
  QUARTZ_BLOCK: 'block/quartz_block_side',
  PRISMARINE: 'block/prismarine',
  
  // Collection Items - Farming
  WHEAT: 'item/wheat',
  BREAD: 'item/bread',
  CARROT_ITEM: 'item/carrot',
  POTATO_ITEM: 'item/potato',
  MELON: 'item/melon_slice',
  SEEDS: 'item/wheat_seeds',
  RED_MUSHROOM: 'block/red_mushroom',
  BROWN_MUSHROOM: 'block/brown_mushroom',
  MUSHROOM_COLLECTION: 'block/red_mushroom',
  'INK_SACK:3': 'item/cocoa_beans',
  SUGAR_CANE: 'item/sugar_cane',
  LEATHER: 'item/leather',
  PORK: 'item/porkchop',
  RAW_CHICKEN: 'item/chicken',
  MUTTON: 'item/mutton',
  RABBIT: 'item/rabbit',
  NETHER_STALK: 'item/nether_wart',
  
  // Collection Items - Mining
  COBBLESTONE: 'block/cobblestone',
  COAL: 'item/coal',
  'INK_SACK:4': 'item/lapis_lazuli',
  REDSTONE: 'item/redstone',
  QUARTZ: 'item/quartz',
  GLOWSTONE_DUST: 'item/glowstone_dust',
  GRAVEL: 'block/gravel',
  ICE: 'block/ice',
  SAND: 'block/sand',
  'SAND:1': 'block/red_sand',
  ENDER_STONE: 'block/end_stone',
  MITHRIL_ORE: 'item/prismarine_crystals',
  HARD_STONE: 'block/stone',
  GEMSTONE_COLLECTION: 'item/emerald',
  MYCEL: 'block/mycelium_side',
  
  // Missing Items
  ENCHANTED_JUNGLE_LOG: 'block/jungle_log',
  NURSE_SHARK_TOOTH: 'item/ghast_tear',
  ENCHANTED_PAPER: 'item/paper',
  SULPHURIC_COAL: 'item/coal',
  HALF_EATEN_MUSHROOM: 'block/brown_mushroom',
  SHARD_ABYSSAL_LANTERNFISH: '/items/shards/abyssal_lanternfish_shard.png',
  SHARD_AERO: '/items/shards/aero_shard.png',
  SHARD_ALLIGATOR: '/items/shards/alligator_shard.png',
  SHARD_ANANKE: '/items/shards/ananke_shard.png',
  SHARD_APEX_DRAGON: '/items/shards/apex_dragon_shard.png',
  SHARD_ARACHNE: '/items/shards/arachne_shard.png',
  SHARD_AZURE: '/items/shards/azure_shard.png',
  SHARD_BAL: '/items/shards/bal_shard.png',
  SHARD_BAMBLOOM: '/items/shards/bambloom_shard.png',
  SHARD_BAMBULEAF: '/items/shards/bambuleaf_shard.png',
  SHARD_BARBARIAN_DUKE_X: '/items/shards/barbarian_duke_x_shard.png',
  SHARD_BASILISK: '/items/shards/basilisk_shard.png',
  SHARD_BEACONMITE: '/items/shards/beaconmite_shard.png',
  SHARD_BEZAL: '/items/shards/bezal_shard.png',
  SHARD_BIRRIES: '/items/shards/birries_shard.png',
  SHARD_BITBUG: '/items/shards/bitbug_shard.png',
  SHARD_BLIZZARD: '/items/shards/blizzard_shard.png',
  SHARD_BOGGED: '/items/shards/bogged_shard.png',
  SHARD_BOLT: '/items/shards/bolt_shard.png',
  SHARD_BOREAL_OWL: '/items/shards/boreal_owl_shard.png',
  SHARD_BRAMBLE: '/items/shards/bramble_shard.png',
  SHARD_BRUISER: '/items/shards/bruiser_shard.png',
  SHARD_BULLFROG: '/items/shards/bullfrog_shard.png',
  SHARD_BURNINGSOUL: '/items/shards/burningsoul_shard.png',
  SHARD_CAIMAN: '/items/shards/caiman_shard.png',
  SHARD_CARROT_KING: '/items/shards/carrot_king_shard.png',
  SHARD_CASCADE: '/items/shards/cascade_shard.png',
  SHARD_CAVERNSHADE: '/items/shards/cavernshade_shard.png',
  SHARD_CHAMELEON: '/items/shards/chameleon_shard.png',
  SHARD_CHILL: '/items/shards/chill_shard.png',
  SHARD_CINDERBAT: '/items/shards/cinderbat_shard.png',
  SHARD_COD: '/items/shards/cod_shard.png',
  SHARD_CONDOR: '/items/shards/condor_shard.png',
  SHARD_CORALOT: '/items/shards/coralot_shard.png',
  SHARD_CRETAN_BULL: '/items/shards/cretan_bull_shard.png',
  SHARD_CROCODILE: '/items/shards/crocodile_shard.png',
  SHARD_CROPEETLE: '/items/shards/cropeetle_shard.png',
  SHARD_CROW: '/items/shards/crow_shard.png',
  SHARD_CRYO: '/items/shards/cryo_shard.png',
  SHARD_CUBOA: '/items/shards/cuboa_shard.png',
  SHARD_DAEMON: '/items/shards/daemon_shard.png',
  SHARD_DODO: '/items/shards/dodo_shard.png',
  SHARD_DRACONIC: '/items/shards/draconic_shard.png',
  SHARD_DRAGONFLY: '/items/shards/dragonfly_shard.png',
  SHARD_DREADWING: '/items/shards/dreadwing_shard.png',
  SHARD_DROWNED: '/items/shards/drowned_shard.png',
  SHARD_EEL: '/items/shards/eel_shard.png',
  SHARD_END_STONE_PROTECTOR: '/items/shards/end_stone_protector_shard.png',
  SHARD_ENT: '/items/shards/ent_shard.png',
  SHARD_ETHERDRAKE: '/items/shards/etherdrake_shard.png',
  SHARD_FALCON: '/items/shards/falcon_shard.png',
  SHARD_FENLORD: '/items/shards/fenlord_shard.png',
  SHARD_FIREFLY: '/items/shards/firefly_shard.png',
  SHARD_FIRE_EEL: '/items/shards/fire_eel_shard.png',
  SHARD_FLAMING_SPIDER: '/items/shards/flaming_spider_shard.png',
  SHARD_FLARE: '/items/shards/flare_shard.png',
  SHARD_FLASH: '/items/shards/flash_shard.png',
  SHARD_FUNGLOOM: '/items/shards/fungloom_shard.png',
  SHARD_GALAXY_FISH: '/items/shards/galaxy_fish_shard.png',
  SHARD_GECKO: '/items/shards/gecko_shard.png',
  SHARD_GHOST: '/items/shards/ghost_shard.png',
  SHARD_GLACITE_WALKER: '/items/shards/glacite_walker_shard.png',
  SHARD_GOLDEN_GHOUL: '/items/shards/golden_ghoul_shard.png',
  SHARD_GOLDFIN: '/items/shards/goldfin_shard.png',
  SHARD_GROVE: '/items/shards/grove_shard.png',
  SHARD_HARPY: '/items/shards/harpy_shard.png',
  SHARD_HELLWISP: '/items/shards/hellwisp_shard.png',
  SHARD_HERON: '/items/shards/heron_shard.png',
  SHARD_HIDEONBOX: '/items/shards/hideonbox_shard.png',
  SHARD_HIDEONCAVE: '/items/shards/hideoncave_shard.png',
  SHARD_HIDEONDRA: '/items/shards/hideondra_shard.png',
  SHARD_HIDEONGEON: '/items/shards/hideongeon_shard.png',
  SHARD_HIDEONGIFT: '/items/shards/hideongift_shard.png',
  SHARD_HIDEONLEAF: '/items/shards/hideonleaf_shard.png',
  SHARD_HIDEONRING: '/items/shards/hideonring_shard.png',
  SHARD_HIDEONSACK: '/items/shards/hideonsack_shard.png',
  SHARD_HUMMINGBIRD: '/items/shards/hummingbird_shard.png',
  SHARD_IGUANA: '/items/shards/iguana_shard.png',
  SHARD_INFERNO_KOI: '/items/shards/inferno_koi_shard.png',
  SHARD_INVISIBUG: '/items/shards/invisibug_shard.png',
  SHARD_JORMUNG: '/items/shards/jormung_shard.png',
  SHARD_JOYDIVE: '/items/shards/joydive_shard.png',
  SHARD_KADA_KNIGHT: '/items/shards/kada_knight_shard.png',
  SHARD_KING_COBRA: '/items/shards/king_cobra_shard.png',
  SHARD_KING_MINOS: '/items/shards/king_minos_shard.png',
  SHARD_KIWI: '/items/shards/kiwi_shard.png',
  SHARD_KOMODO_DRAGON: '/items/shards/komodo_dragon_shard.png',
  SHARD_KRAKEN: '/items/shards/kraken_shard.png',
  SHARD_LADYBUG: '/items/shards/ladybug_shard.png',
  SHARD_LAPIS_CREEPER: '/items/shards/lapis_creeper_shard.png',
  SHARD_LAPIS_SKELETON: '/items/shards/lapis_skeleton_shard.png',
  SHARD_LAPIS_ZOMBIE: '/items/shards/lapis_zombie_shard.png',
  SHARD_LAVA_FLAME: '/items/shards/lava_flame_shard.png',
  SHARD_LEATHERBACK: '/items/shards/leatherback_shard.png',
  SHARD_LEVIATHAN: '/items/shards/leviathan_shard.png',
  SHARD_LIZARD_KING: '/items/shards/lizard_king_shard.png',
  SHARD_LOCH_EMPEROR: '/items/shards/loch_emperor_shard.png',
  SHARD_LORD_JAWBUS: '/items/shards/lord_jawbus_shard.png',
  SHARD_LUMISQUID: '/items/shards/lumisquid_shard.png',
  SHARD_LUNAR_MOTH: '/items/shards/lunar_moth_shard.png',
  SHARD_MAGMA_SLUG: '/items/shards/magma_slug_shard.png',
  SHARD_MATCHO: '/items/shards/matcho_shard.png',
  SHARD_MEGALITH: '/items/shards/megalith_shard.png',
  SHARD_MIMIC: '/items/shards/mimic_shard.png',
  SHARD_MINER_ZOMBIE: '/items/shards/miner_zombie_shard.png',
  SHARD_MIST: '/items/shards/mist_shard.png',
  SHARD_MOCHIBEAR: '/items/shards/mochibear_shard.png',
  SHARD_MOLTENFISH: '/items/shards/moltenfish_shard.png',
  SHARD_MOLTHORN: '/items/shards/molthorn_shard.png',
  SHARD_MORAY_EEL: '/items/shards/moray_eel_shard.png',
  SHARD_MOSSYBIT: '/items/shards/mossybit_shard.png',
  SHARD_MUDWORM: '/items/shards/mudworm_shard.png',
  SHARD_NEWT: '/items/shards/newt_shard.png',
  SHARD_NIGHT_SQUID: '/items/shards/night_squid_shard.png',
  SHARD_OBSIDIAN_DEFENDER: '/items/shards/obsidian_defender_shard.png',
  SHARD_PANDARAI: '/items/shards/pandarai_shard.png',
  SHARD_PEST: '/items/shards/pest_shard.png',
  SHARD_PHANFLARE: '/items/shards/phanflare_shard.png',
  SHARD_PHANPYRE: '/items/shards/phanpyre_shard.png',
  SHARD_PIRANHA: '/items/shards/piranha_shard.png',
  SHARD_POWER_DRAGON: '/items/shards/power_dragon_shard.png',
  SHARD_PRAYING_MANTIS: '/items/shards/praying_mantis_shard.png',
  SHARD_PRINCE: '/items/shards/prince_shard.png',
  SHARD_PYTHON: '/items/shards/python_shard.png',
  SHARD_QUAKE: '/items/shards/quake_shard.png',
  SHARD_QUARTZFANG: '/items/shards/quartzfang_shard.png',
  SHARD_RAIN_SLIME: '/items/shards/rain_slime_shard.png',
  SHARD_RANA: '/items/shards/rana_shard.png',
  SHARD_REVENANT: '/items/shards/revenant_shard.png',
  SHARD_SALAMANDER: '/items/shards/salamander_shard.png',
  SHARD_SALMON: '/items/shards/salmon_shard.png',
  SHARD_SCARF: '/items/shards/scarf_shard.png',
  SHARD_SEAGULL: '/items/shards/seagull_shard.png',
  SHARD_SEA_SERPENT: '/items/shards/sea_serpent_shard.png',
  SHARD_SEER: '/items/shards/seer_shard.png',
  SHARD_SHELLWISE: '/items/shards/shellwise_shard.png',
  SHARD_SHINYFISH: '/items/shards/shinyfish_shard.png',
  SHARD_SILENTDEPTH: '/items/shards/silentdepth_shard.png',
  SHARD_SKELETOR: '/items/shards/skeletor_shard.png',
  SHARD_SNOWFIN: '/items/shards/snowfin_shard.png',
  SHARD_SOUL_OF_THE_ALPHA: '/items/shards/soul_of_the_alpha_shard.png',
  SHARD_SPARROW: '/items/shards/sparrow_shard.png',
  SHARD_SPHINX: '/items/shards/sphinx_shard.png',
  SHARD_SPIKE: '/items/shards/spike_shard.png',
  SHARD_STALAGMIGHT: '/items/shards/stalagmight_shard.png',
  SHARD_STARBORN: '/items/shards/starborn_shard.png',
  SHARD_STAR_SENTRY: '/items/shards/star_sentry_shard.png',
  SHARD_STRIDERSURFER: '/items/shards/stridersurfer_shard.png',
  SHARD_SUN_FISH: '/items/shards/sun_fish_shard.png',
  SHARD_SYCOPHANT: '/items/shards/sycophant_shard.png',
  SHARD_SYLVAN: '/items/shards/sylvan_shard.png',
  SHARD_TADGANG: '/items/shards/tadgang_shard.png',
  SHARD_TANK_ZOMBIE: '/items/shards/tank_zombie_shard.png',
  SHARD_TAURUS: '/items/shards/taurus_shard.png',
  SHARD_TEMPEST: '/items/shards/tempest_shard.png',
  SHARD_TENEBRIS: '/items/shards/tenebris_shard.png',
  SHARD_TERMITE: '/items/shards/termite_shard.png',
  SHARD_TERRA: '/items/shards/terra_shard.png',
  SHARD_THORN: '/items/shards/thorn_shard.png',
  SHARD_THYST: '/items/shards/thyst_shard.png',
  SHARD_TIAMAT: '/items/shards/tiamat_shard.png',
  SHARD_TIDE: '/items/shards/tide_shard.png',
  SHARD_TITANOBOA: '/items/shards/titanoboa_shard.png',
  SHARD_TOAD: '/items/shards/toad_shard.png',
  SHARD_TORTOISE: '/items/shards/tortoise_shard.png',
  SHARD_TOUCAN: '/items/shards/toucan_shard.png',
  SHARD_TROGLOBYTE: '/items/shards/troglobyte_shard.png',
  SHARD_VERDANT: '/items/shards/verdant_shard.png',
  SHARD_VIPER: '/items/shards/viper_shard.png',
  SHARD_VORACIOUS_SPIDER: '/items/shards/voracious_spider_shard.png',
  SHARD_WARTYBUG: '/items/shards/wartybug_shard.png',
  SHARD_WATER_HYDRA: '/items/shards/water_hydra_shard.png',
  SHARD_WITHER: '/items/shards/wither_shard.png',
  SHARD_WITHER_SPECTER: '/items/shards/wither_specter_shard.png',
  SHARD_WYVERN: '/items/shards/wyvern_shard.png',
  SHARD_XYZ: '/items/shards/xyz_shard.png',
  SHARD_YOG: '/items/shards/yog_shard.png',
  SHARD_ZEALOT: '/items/shards/zealot_shard.png',
  SHARD_ZOMBIE_SOLDIER: '/items/shards/zombie_soldier_shard.png',
  ENCHANTMENT_ULTIMATE_COMBO_5: 'item/enchanted_book',
  BEZOS: 'item/stone_button',
  X: 'item/barrier',
  GENERATOR_UPGRADE_STONE_FISHING_12: 'block/sea_lantern',
  RED_SAND: 'block/red_sand',
  SULPHUR_ORE: 'item/gunpowder',
  SNOW_BALL: 'item/snowball',
  
  // Collection Items - Combat
  ROTTEN_FLESH: 'item/rotten_flesh',
  STRING: 'item/string',
  SPIDER_EYE: 'item/spider_eye',
  SULPHUR: 'item/gunpowder',
  GUNPOWDER: 'item/gunpowder',
  ENDER_PEARL: 'item/ender_pearl',
  SLIME_BALL: 'item/slime_ball',
  
  // Collection Items - Foraging
  LOG: 'block/oak_log',
  'LOG:1': 'block/spruce_log',
  'LOG:2': 'block/birch_log',
  'LOG_2:1': 'block/dark_oak_log',
  LOG_2: 'block/acacia_log',
  'LOG:3': 'block/jungle_log',
  
  // Collection Items - Fishing
  RAW_FISH: 'item/cod',
  'RAW_FISH:1': 'item/salmon',
  'RAW_FISH:2': 'item/tropical_fish',
  'RAW_FISH:3': 'item/pufferfish',
  CLAY_BALL: 'item/clay_ball',
  WATER_LILY: 'block/lily_pad',
  INK_SACK: 'item/ink_sac',
  
  // Rift items
  AGARICUS_CAP: 'block/red_mushroom',
  CADUCOUS_STEM: 'item/stick',
  WILTED_BERBERIS: 'block/dead_bush',
  HALF_EATEN_CARROT: 'item/carrot',
  HEMOVIBE: 'item/redstone',
};

const VANILLA_TEXTURE_BASE = 'https://mcasset.cloud/1.20.4/assets/minecraft/textures';

// Load items from Hypixel API
export async function loadHypixelItems(): Promise<void> {
  if (get(itemsLoaded) || get(itemsLoading)) return;
  
  itemsLoading.set(true);
  
  try {
    const response = await fetch('https://api.hypixel.net/resources/skyblock/items');
    if (!response.ok) throw new Error('Failed to fetch items');
    
    const data = await response.json();
    const items = data.items as HypixelItem[];
    
    const map = new Map<string, HypixelItem>();
    for (const item of items) {
      if (item.id) {
        map.set(item.id, item);
      }
    }
    
    itemsMapStore.set(map);
    itemsLoaded.set(true);
  } catch (error) {
    console.error('Failed to load Hypixel items:', error);
  } finally {
    itemsLoading.set(false);
  }
}

// Load textures for a list of item IDs from backend (supports both packs)
export async function loadItemTextures(
  itemIds: string[],
  pack: 'vanilla' | 'furfsky' = 'furfsky'
): Promise<void> {
  const cacheStore = pack === 'furfsky' ? furfskyCacheStore : vanillaCacheStore;
  const loadingStore = pack === 'furfsky' ? furfskyCacheLoading : vanillaCacheLoading;
  const loadedStore = pack === 'furfsky' ? furfskyCacheLoaded : vanillaCacheLoaded;

  if (get(loadingStore) || itemIds.length === 0) return;

  // Filter out already cached items
  const currentCache = get(cacheStore);
  const uncachedIds = itemIds.filter((id) => !currentCache.has(id));

  if (uncachedIds.length === 0) {
    loadedStore.set(true);
    return;
  }

  loadingStore.set(true);

  try {
    const response = await fetch('/api/textures/batch', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ item_ids: uncachedIds, pack })
    });

    if (!response.ok) throw new Error(`Failed to fetch ${pack} textures`);

    const data = await response.json();
    const textures = data.textures as Record<string, string | null>;

    // Update cache
    const newCache = new Map(currentCache);
    for (const [id, url] of Object.entries(textures)) {
      newCache.set(id, url);
    }
    cacheStore.set(newCache);
    loadedStore.set(true);
  } catch (error) {
    console.error(`Failed to load ${pack} textures:`, error);
  } finally {
    loadingStore.set(false);
  }
}

// Legacy alias for backward compatibility
export async function loadFurfskytextures(itemIds: string[]): Promise<void> {
  return loadItemTextures(itemIds, 'furfsky');
}

// Get furfsky texture URL from cache
export function getFurfskyCachedTexture(itemId: string): string | null | undefined {
  return get(furfskyCacheStore).get(itemId);
}

// Get texture URL from cache (supports both packs)
export function getCachedTexture(
  itemId: string,
  pack: 'vanilla' | 'furfsky' = 'furfsky'
): string | null | undefined {
  const cacheStore = pack === 'furfsky' ? furfskyCacheStore : vanillaCacheStore;
  return get(cacheStore).get(itemId);
}

// Get item by ID
export function getItem(itemId: string): HypixelItem | undefined {
  return get(itemsMapStore).get(itemId);
}

// Extract skin texture ID from base64 encoded skin value
function extractSkinTextureId(skinValue: string): string | null {
  try {
    const decoded = JSON.parse(atob(skinValue));
    const url = decoded?.textures?.SKIN?.url;
    if (url) {
      // Extract texture ID from URL like http://textures.minecraft.net/texture/ABC123
      const match = url.match(/\/texture\/([a-f0-9]+)/i);
      return match ? match[1] : null;
    }
  } catch {
    // Ignore decode errors
  }
  return null;
}

// Get texture URL for an item with pack support
export function getItemTextureUrl(itemId: string, pack: 'vanilla' | 'furfsky' = 'vanilla'): string | null {
  // Always check the backend cache first (supports NEU textures, etc.)
  const cacheStore = pack === 'furfsky' ? furfskyCacheStore : vanillaCacheStore;
  const cachedUrl = get(cacheStore).get(itemId);
  // If cached (even if null), use the cached value
  if (cachedUrl !== undefined) {
    if (cachedUrl) return cachedUrl;
    // Fall through to local resolution if backend returned null
  }
  
  // First, try direct lookup in MATERIAL_TO_TEXTURE (for collection items etc.)
  const directTexturePath = MATERIAL_TO_TEXTURE[itemId];
  if (directTexturePath) {
    if (directTexturePath.startsWith('/')) {
      return directTexturePath;
    }
    return `${VANILLA_TEXTURE_BASE}/${directTexturePath}.png`;
  }
  
  const map = get(itemsMapStore);
  
  // Try exact match first
  let item = map.get(itemId);
  let resolvedId = itemId;
  
  // For armor sets (like CACTUS), try to find the helmet variant
  if (!item && !itemId.includes('_HELMET') && !itemId.includes('_CHESTPLATE') && 
      !itemId.includes('_LEGGINGS') && !itemId.includes('_BOOTS')) {
    // Try armor helmet first (most iconic piece)
    const variants = [`${itemId}_HELMET`, `${itemId}_CHESTPLATE`, `${itemId}_BOOTS`, `${itemId}_LEGGINGS`];
    for (const variant of variants) {
      if (map.get(variant)) {
        item = map.get(variant);
        resolvedId = variant;
        break;
      }
    }
    
    // Also check cache for resolved variant
    const variantCachedUrl = get(cacheStore).get(resolvedId);
    if (variantCachedUrl !== undefined && variantCachedUrl) {
      return variantCachedUrl;
    }
  }
  
  if (!item) return null;
  
  // Check if has custom skin (skull texture) - use mc-heads for 3D render
  if (item.skin?.value) {
    const textureId = extractSkinTextureId(item.skin.value);
    if (textureId) {
      // Use mc-heads.net for 3D head rendering
      return `https://mc-heads.net/head/${textureId}/64`;
    }
  }
  
  // Try to get texture from material
  const material = item.material;
  if (material) {
    // Handle durability for colored items
    const baseMaterial = material.split(':')[0];
    const texturePath = MATERIAL_TO_TEXTURE[baseMaterial];
    if (texturePath) {
      return `${VANILLA_TEXTURE_BASE}/${texturePath}.png`;
    }
  }
  
  return null;
}

// Legacy function for backward compatibility
export function getVanillaTextureUrl(itemId: string): string | null {
  return getItemTextureUrl(itemId, 'vanilla');
}

// Derived store for convenient access
export const hypixelItems = derived(itemsMapStore, ($map) => $map);
