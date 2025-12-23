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

// Furfsky texture base URL
const FURFSKY_BASE = '/api/textures/furfsky';

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
};

const VANILLA_TEXTURE_BASE = 'https://raw.githubusercontent.com/InventivetalentDev/minecraft-assets/1.20.1/assets/minecraft/textures';

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
