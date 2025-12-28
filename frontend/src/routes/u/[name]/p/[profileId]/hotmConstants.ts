// HOTM Tree Constants
// Based on Hypixel SkyBlock HOTM structure

export const HOTM_TIERS = 10;
export const HOTM_GRID_COLS = 7;
export const HOTM_GRID_ROWS = 10;

// HOTM XP requirements for each tier
export const HOTM_XP_REQUIREMENTS: Record<number, number> = {
  1: 0,
  2: 3000,
  3: 12000,
  4: 37000,
  5: 97000,
  6: 197000,
  7: 347000,
  8: 557000,
  9: 847000,
  10: 1247000
};

// Tokens earned per tier
export const TOKENS_PER_TIER: Record<number, number> = {
  1: 1,
  2: 2,
  3: 2,
  4: 2,
  5: 2,
  6: 2,
  7: 3,
  8: 2,
  9: 2,
  10: 2
};

export type PowderType = 'mithril' | 'gemstone' | 'glacite' | null;

export interface HOTMPerk {
  id: string;
  name: string;
  position: number;  // 1-70 position in 7x10 grid
  maxLevel: number;
  tier: number;  // Required HOTM tier
  powderType: PowderType;
  isAbility?: boolean;
  isSpecial?: boolean;
  description: (level: number) => string;
  effect: (level: number) => string;
}

// Grid position mapping (row, col) from 1-based position
export function positionToGrid(position: number): { row: number; col: number } {
  const row = Math.floor((position - 1) / HOTM_GRID_COLS);
  const col = (position - 1) % HOTM_GRID_COLS;
  return { row, col };
}

// Color scheme for different perk states
export const PERK_COLORS = {
  locked: { bg: '#3d3d3d', border: '#1a1a1a', text: '#666' },
  unlocked: { bg: '#2d4a2d', border: '#4ade80', text: '#4ade80' },
  maxed: { bg: '#4a2d4a', border: '#c084fc', text: '#c084fc' },
  ability: { bg: '#2d3a4a', border: '#60a5fa', text: '#60a5fa' },
  special: { bg: '#4a3d2d', border: '#fbbf24', text: '#fbbf24' }
};

// Powder colors
export const POWDER_COLORS: Record<string, string> = {
  mithril: '#2ecc71',
  gemstone: '#d946ef',
  glacite: '#67e8f9'
};

// All HOTM perks with their positions and details
// Positions follow a 7-column grid, 10 rows (Tier 10 at top, Tier 1 at bottom)
export const HOTM_PERKS: Record<string, HOTMPerk> = {
  // ===== TIER 10 (Row 1, positions 1-7) =====
  gemstone_infusion: {
    id: 'gemstone_infusion',
    name: 'Gemstone Infusion',
    position: 1,
    maxLevel: 1,
    tier: 10,
    powderType: null,
    isAbility: true,
    description: () => 'Pickaxe Ability',
    effect: (level) => `Increases Gemstone effectiveness by 100% for ${15 + level * 5}s`
  },
  crystalline: {
    id: 'crystalline',
    name: 'Crystalline',
    position: 2,
    maxLevel: 50,
    tier: 10,
    powderType: 'glacite',
    description: (level) => `+${level * 0.5}% chance for double Gemstone powder`,
    effect: (level) => `${(level * 0.5).toFixed(1)}% Double Powder`
  },
  gifts_from_the_departed: {
    id: 'gifts_from_the_departed',
    name: 'Gifts from the Departed',
    position: 3,
    maxLevel: 100,
    tier: 10,
    powderType: 'glacite',
    description: (level) => `+${(level * 0.2).toFixed(1)}% extra loot from Frozen Corpses`,
    effect: (level) => `${(level * 0.2).toFixed(1)}% Extra Loot`
  },
  mining_master: {
    id: 'mining_master',
    name: 'Mining Master',
    position: 4,
    maxLevel: 10,
    tier: 10,
    powderType: 'glacite',
    description: (level) => `+${(level * 0.1).toFixed(1)} Pristine`,
    effect: (level) => `+${(level * 0.1).toFixed(1)} Pristine`
  },
  hungry_for_more: {
    id: 'hungry_for_more',
    name: "Dead Man's Chest",
    position: 5,
    maxLevel: 50,
    tier: 10,
    powderType: 'glacite',
    description: (level) => `+${level}% extra Frozen Corpse spawns`,
    effect: (level) => `+${level}% Corpse Chance`
  },
  vanguard_seeker: {
    id: 'vanguard_seeker',
    name: 'Vanguard Seeker',
    position: 6,
    maxLevel: 50,
    tier: 10,
    powderType: 'glacite',
    description: (level) => `+${level}% Vanguard Corpse chance`,
    effect: (level) => `+${level}% Vanguard`
  },
  sheer_force: {
    id: 'sheer_force',
    name: 'Sheer Force',
    position: 7,
    maxLevel: 1,
    tier: 10,
    powderType: null,
    isAbility: true,
    description: () => 'Pickaxe Ability',
    effect: () => 'Mines all Hard Stone in a 4 block radius'
  },
  
  // ===== TIER 9 (Row 2, positions 8-14) =====
  metal_head: {
    id: 'metal_head',
    name: 'Metal Head',
    position: 11,
    maxLevel: 20,
    tier: 9,
    powderType: 'glacite',
    description: (level) => `+${level * 5} Dwarven Metal Fortune`,
    effect: (level) => `+${level * 5} ☘ Fortune`
  },
  rags_to_riches: {
    id: 'rags_to_riches',
    name: 'Rags to Riches',
    position: 13,
    maxLevel: 50,
    tier: 9,
    powderType: 'glacite',
    description: (level) => `+${level * 4} Mining Fortune in Mineshafts`,
    effect: (level) => `+${level * 4} ☘ Fortune`
  },
  eager_adventurer: {
    id: 'eager_adventurer',
    name: 'Eager Adventurer',
    position: 15,
    maxLevel: 100,
    tier: 9,
    powderType: 'glacite',
    description: (level) => `+${level * 4} Mining Speed in Mineshafts`,
    effect: (level) => `+${level * 4} ⸕ Speed`
  },
  
  // ===== TIER 8 (Row 3, positions 15-21) =====
  miners_blessing: {
    id: 'miners_blessing',
    name: "Miner's Blessing",
    position: 19,
    maxLevel: 1,
    tier: 8,
    powderType: null,
    isSpecial: true,
    description: () => '+30 Magic Find on Mining Islands',
    effect: () => '+30 ✯ Magic Find'
  },
  no_stone_unturned: {
    id: 'no_stone_unturned',
    name: 'No Stone Unturned',
    position: 20,
    maxLevel: 50,
    tier: 8,
    powderType: 'glacite',
    description: (level) => `+${(level * 0.5).toFixed(1)}% Suspicious Scrap chance`,
    effect: (level) => `+${(level * 0.5).toFixed(1)}% Scrap`
  },
  strong_arm: {
    id: 'strong_arm',
    name: 'Strong Arm',
    position: 21,
    maxLevel: 100,
    tier: 8,
    powderType: 'glacite',
    description: (level) => `+${level * 5} Mining Speed on Dwarven Metals`,
    effect: (level) => `+${level * 5} ⸕ Speed`
  },
  steady_hand: {
    id: 'steady_hand',
    name: 'Steady Hand',
    position: 22,
    maxLevel: 100,
    tier: 8,
    powderType: 'glacite',
    description: (level) => `+${(level * 0.1).toFixed(1)} Gemstone Spread in Mineshafts`,
    effect: (level) => `+${(level * 0.1).toFixed(1)} Spread`
  },
  warm_hearted: {
    id: 'warm_hearted',
    name: 'Warm Hearted',
    position: 23,
    maxLevel: 50,
    tier: 8,
    powderType: 'glacite',
    description: (level) => `+${(level * 0.4).toFixed(1)} Cold Resistance`,
    effect: (level) => `+${(level * 0.4).toFixed(1)} ❄ Resist`
  },
  surveyor: {
    id: 'surveyor',
    name: 'Surveyor',
    position: 24,
    maxLevel: 20,
    tier: 8,
    powderType: 'glacite',
    description: (level) => `+${(level * 0.75).toFixed(1)}% Mineshaft chance`,
    effect: (level) => `+${(level * 0.75).toFixed(2)}% Mineshaft`
  },
  mineshaft_mayhem: {
    id: 'mineshaft_mayhem',
    name: 'Mineshaft Mayhem',
    position: 25,
    maxLevel: 1,
    tier: 8,
    powderType: null,
    isSpecial: true,
    description: () => 'Random buffs when entering Mineshafts',
    effect: () => 'Random Mineshaft Buffs'
  },
  
  // ===== TIER 7 (Row 4, positions 22-28) =====
  mining_speed_2: {
    id: 'mining_speed_2',
    name: 'Speedy Mineman',
    position: 29,
    maxLevel: 50,
    tier: 7,
    powderType: 'gemstone',
    description: (level) => `+${level * 40} Mining Speed`,
    effect: (level) => `+${level * 40} ⸕ Speed`
  },
  powder_buff: {
    id: 'powder_buff',
    name: 'Powder Buff',
    position: 31,
    maxLevel: 50,
    tier: 7,
    powderType: 'gemstone',
    description: (level) => `+${level}% more Powder from all sources`,
    effect: (level) => `+${level}% Powder`
  },
  mining_fortune_2: {
    id: 'mining_fortune_2',
    name: 'Fortunate Mineman',
    position: 33,
    maxLevel: 50,
    tier: 7,
    powderType: 'gemstone',
    description: (level) => `+${level * 3} Mining Fortune`,
    effect: (level) => `+${level * 3} ☘ Fortune`
  },
  
  // ===== TIER 6 (Row 5, positions 29-35) =====
  anomalous_desire: {
    id: 'anomalous_desire',
    name: 'Tunnel Vision',
    position: 36,
    maxLevel: 1,
    tier: 6,
    powderType: null,
    isAbility: true,
    description: () => 'Pickaxe Ability',
    effect: () => '+30-50% rare occurrence chance for 30s'
  },
  blockhead: {
    id: 'blockhead',
    name: 'Blockhead',
    position: 38,
    maxLevel: 20,
    tier: 6,
    powderType: 'gemstone',
    description: (level) => `+${level * 5} Block Fortune`,
    effect: (level) => `+${level * 5} ☘ Fortune`
  },
  subterranean_fisher: {
    id: 'subterranean_fisher',
    name: 'Subterranean Fisher',
    position: 39,
    maxLevel: 40,
    tier: 6,
    powderType: 'gemstone',
    description: (level) => `+${level} Sea Creature Chance in lava`,
    effect: (level) => `+${level} α SC Chance`
  },
  keep_it_cool: {
    id: 'keep_it_cool',
    name: 'Keep It Cool',
    position: 40,
    maxLevel: 50,
    tier: 6,
    powderType: 'gemstone',
    description: (level) => `+${(level * 0.4).toFixed(1)} Heat Resistance`,
    effect: (level) => `+${(level * 0.4).toFixed(1)} ♨ Resist`
  },
  lonesome_miner: {
    id: 'lonesome_miner',
    name: 'Lonesome Miner',
    position: 41,
    maxLevel: 45,
    tier: 6,
    powderType: 'gemstone',
    description: (level) => `+${(5 + (level - 1) * 0.5).toFixed(1)}% combat stats on Mining Islands`,
    effect: (level) => `+${(5 + (level - 1) * 0.5).toFixed(1)}% Stats`
  },
  great_explorer: {
    id: 'great_explorer',
    name: 'Great Explorer',
    position: 42,
    maxLevel: 20,
    tier: 6,
    powderType: 'gemstone',
    description: (level) => `+${20 + (level - 1) * 4}% treasure chest chance`,
    effect: (level) => `+${20 + (level - 1) * 4}% Chest`
  },
  maniac_miner: {
    id: 'maniac_miner',
    name: 'Maniac Miner',
    position: 43,
    maxLevel: 1,
    tier: 6,
    powderType: null,
    isAbility: true,
    description: () => 'Pickaxe Ability',
    effect: () => 'Speed increases as you mine, up to +1000'
  },
  
  // ===== TIER 5 (Row 6, positions 36-42) =====
  daily_grind: {
    id: 'daily_grind',
    name: 'Daily Grind',
    position: 47,
    maxLevel: 1,
    tier: 5,
    powderType: null,
    description: () => 'First commission grants +500 Powder × HOTM level',
    effect: () => '+500 × HOTM Powder'
  },
  special_0: {
    id: 'special_0',
    name: 'Peak of the Mountain',
    position: 49,
    maxLevel: 10,
    tier: 5,
    powderType: 'mithril',
    isSpecial: true,
    description: (level) => `Tier ${level} rewards`,
    effect: (level) => `Tier ${level}`
  },
  daily_powder: {
    id: 'daily_powder',
    name: 'Daily Powder',
    position: 51,
    maxLevel: 1,
    tier: 5,
    powderType: null,
    description: () => 'First ore mined grants +500 × HOTM level powder',
    effect: () => '+500 × HOTM Powder'
  },
  
  // ===== TIER 4 (Row 7, positions 43-49) =====
  daily_effect: {
    id: 'daily_effect',
    name: 'Sky Mall',
    position: 55,
    maxLevel: 1,
    tier: 4,
    powderType: null,
    isSpecial: true,
    description: () => 'Random buff each SkyBlock day',
    effect: () => 'Daily Random Buff'
  },
  old_school: {
    id: 'old_school',
    name: 'Old-School',
    position: 56,
    maxLevel: 20,
    tier: 4,
    powderType: 'gemstone',
    description: (level) => `+${level * 5} Ore Fortune`,
    effect: (level) => `+${level * 5} ☘ Fortune`
  },
  professional: {
    id: 'professional',
    name: 'Professional',
    position: 57,
    maxLevel: 140,
    tier: 4,
    powderType: 'gemstone',
    description: (level) => `+${50 + level * 5} Mining Speed on Gemstones`,
    effect: (level) => `+${50 + level * 5} ⸕ Speed`
  },
  mole: {
    id: 'mole',
    name: 'Mole',
    position: 58,
    maxLevel: 200,
    tier: 4,
    powderType: 'gemstone',
    description: (level) => `+${(50 + (level - 1) * (350/199)).toFixed(1)} Mining Spread`,
    effect: (level) => `+${(50 + (level - 1) * (350/199)).toFixed(0)} Spread`
  },
  fortunate: {
    id: 'fortunate',
    name: 'Gem Lover',
    position: 59,
    maxLevel: 20,
    tier: 4,
    powderType: 'gemstone',
    description: (level) => `+${20 + level * 4} Gemstone Fortune`,
    effect: (level) => `+${20 + level * 4} ☘ Fortune`
  },
  mining_experience: {
    id: 'mining_experience',
    name: 'Seasoned Mineman',
    position: 60,
    maxLevel: 100,
    tier: 4,
    powderType: 'gemstone',
    description: (level) => `+${(5 + level * 0.1).toFixed(1)} Mining Wisdom`,
    effect: (level) => `+${(5 + level * 0.1).toFixed(1)} ☯ Wisdom`
  },
  front_loaded: {
    id: 'front_loaded',
    name: 'Front Loaded',
    position: 61,
    maxLevel: 1,
    tier: 4,
    powderType: null,
    isSpecial: true,
    description: () => 'Buffs for first 2,500 gemstones daily',
    effect: () => '3x Powder, +150 Fortune, +250 Speed'
  },
  
  // ===== TIER 3 (Row 8, positions 50-56) =====
  random_event: {
    id: 'random_event',
    name: 'Luck of the Cave',
    position: 65,
    maxLevel: 45,
    tier: 3,
    powderType: 'mithril',
    description: (level) => `+${5 + level}% rare occurrences chance`,
    effect: (level) => `+${5 + level}% Rare Events`
  },
  efficient_miner: {
    id: 'efficient_miner',
    name: 'Efficient Miner',
    position: 67,
    maxLevel: 100,
    tier: 3,
    powderType: 'mithril',
    description: (level) => `+${level * 3} Mining Spread`,
    effect: (level) => `+${level * 3} Spread`
  },
  forge_time: {
    id: 'forge_time',
    name: 'Quick Forge',
    position: 69,
    maxLevel: 20,
    tier: 3,
    powderType: 'mithril',
    description: (level) => `-${(10 + level * 0.5).toFixed(1)}% Forge time`,
    effect: (level) => `-${(10 + level * 0.5).toFixed(1)}% Time`
  },
  
  // ===== TIER 2 (Row 9, positions 57-63) =====
  mining_speed_boost: {
    id: 'mining_speed_boost',
    name: 'Mining Speed Boost',
    position: 74,
    maxLevel: 1,
    tier: 2,
    powderType: null,
    isAbility: true,
    description: () => 'Pickaxe Ability',
    effect: () => '+200-300% Mining Speed for 10-20s'
  },
  precision_mining: {
    id: 'precision_mining',
    name: 'Precision Mining',
    position: 75,
    maxLevel: 1,
    tier: 2,
    powderType: null,
    description: () => '+30% Mining Speed when aiming at particle target',
    effect: () => '+30% Targeted Speed'
  },
  mining_fortune: {
    id: 'mining_fortune',
    name: 'Mining Fortune',
    position: 76,
    maxLevel: 50,
    tier: 2,
    powderType: 'mithril',
    description: (level) => `+${level * 2} Mining Fortune`,
    effect: (level) => `+${level * 2} ☘ Fortune`
  },
  titanium_insanium: {
    id: 'titanium_insanium',
    name: 'Titanium Insanium',
    position: 77,
    maxLevel: 50,
    tier: 2,
    powderType: 'mithril',
    description: (level) => `+${(level * 2).toFixed(0)}% Titanium ore chance`,
    effect: (level) => `+${(level * 2).toFixed(0)}% Titanium`
  },
  pickobulus: {
    id: 'pickobulus',
    name: 'Pickobulus',
    position: 78,
    maxLevel: 1,
    tier: 2,
    powderType: null,
    isAbility: true,
    description: () => 'Pickaxe Ability',
    effect: () => 'Explosive mining in 3 block radius'
  },
  
  // ===== TIER 1 (Row 10, positions 64-70) =====
  mining_speed: {
    id: 'mining_speed',
    name: 'Mining Speed',
    position: 85,
    maxLevel: 50,
    tier: 1,
    powderType: 'mithril',
    description: (level) => `+${level * 20} Mining Speed`,
    effect: (level) => `+${level * 20} ⸕ Speed`
  }
};

// Get total tokens available up to a tier
export function getTotalTokens(tier: number): number {
  let total = 0;
  for (let t = 1; t <= tier; t++) {
    total += TOKENS_PER_TIER[t] || 0;
  }
  return total;
}

// Get HOTM XP progress info
export function getHOTMProgress(tier: number, experience: number): { current: number; next: number; progress: number } {
  const currentReq = HOTM_XP_REQUIREMENTS[tier] || 0;
  const nextTier = tier + 1;
  const nextReq = HOTM_XP_REQUIREMENTS[nextTier];
  
  if (!nextReq || tier >= HOTM_TIERS) {
    return { current: experience - currentReq, next: 0, progress: 100 };
  }
  
  const tierXP = nextReq - currentReq;
  const earnedInTier = experience - currentReq;
  const progress = Math.min(100, (earnedInTier / tierXP) * 100);
  
  return { current: earnedInTier, next: tierXP, progress };
}

// Crystal Hollows crystals
export const CRYSTALS = {
  jade: { name: 'Jade', color: '#55FF55' },
  amber: { name: 'Amber', color: '#FFAA00' },
  topaz: { name: 'Topaz', color: '#FFFF55' },
  sapphire: { name: 'Sapphire', color: '#5555FF' },
  amethyst: { name: 'Amethyst', color: '#AA00AA' },
  jasper: { name: 'Jasper', color: '#FF55FF' },
  ruby: { name: 'Ruby', color: '#FF5555' }
};

// Get perk status
export function getPerkStatus(perk: HOTMPerk, level: number, hotmTier: number): 'locked' | 'unlocked' | 'maxed' | 'ability' | 'special' {
  if (hotmTier < perk.tier) return 'locked';
  if (level === 0) return 'locked';
  if (perk.isAbility) return 'ability';
  if (perk.isSpecial) return 'special';
  if (level >= perk.maxLevel) return 'maxed';
  return 'unlocked';
}

// Format large numbers
export function formatPowder(num: number): string {
  if (num >= 1_000_000_000) return `${(num / 1_000_000_000).toFixed(1)}B`;
  if (num >= 1_000_000) return `${(num / 1_000_000).toFixed(1)}M`;
  if (num >= 1_000) return `${(num / 1_000).toFixed(1)}K`;
  return num.toLocaleString();
}
