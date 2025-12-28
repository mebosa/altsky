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
