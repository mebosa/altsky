import type { TexturePack } from '$lib/stores/texturePack';

export type Player = {
  name: string;
  uuid: string;
};

export type SkillStat = {
  level: number;
  progress: number;
  xp: number;
  current: number;
  to_next: number;
};

export type SlayerKills = {
  total: number;
  tiers: Record<string, number>;
};

export type SlayerBoss = {
  level: number;
  xp: number;
  kills?: SlayerKills;
};

export type WardrobeItem = {
  slot: number;
  id: string;
  mc_id: string;
  name: string;
  count: number;
  rarity?: string | null;
  lore: string[];
  lore_colored?: string[];
  icon_url?: string | null;
  icon_variants?: Partial<Record<TexturePack, string>>;
  leather_color?: string | null;
  skin_url?: string | null;
  recombobulated?: boolean;
};

export type AccessoryItem = {
  slot: number;
  id: string;
  mc_id: string;
  name: string;
  count: number;
  rarity?: string | null;
  lore: string[];
  lore_colored?: string[];
  icon_url?: string | null;
  icon_variants?: Partial<Record<TexturePack, string>>;
  leather_color?: string | null;
  modifier?: string | null;
  enrichment?: string | null;
  recombobulated?: boolean;
};

export type MissingAccessory = {
  id: string;
  name: string;
  tier?: string | null;
  mc_id?: string | null;
  damage?: number | null;
  icon_url?: string | null;
  icon_variants?: Partial<Record<TexturePack, string>>;
};

export type DungeonFloor = {
  name: string;
  completions: number;
  attempts: number;
  fastest_time: number;
  best_score: number;
};

export type ProfileSummaryResponse = {
  ok: boolean;
  last_updated?: string | number;
  profile: {
    profile_id: string;
    cute_name?: string | null;
    game_mode?: string | null;
    member_count: number;
    last_save?: number | null;
    last_save_iso?: string | null;
  };
  skyblock_level: {
    level: number;
    progress: number;
    experience: number;
  };
  skills: Record<string, SkillStat> & { average_level: number };
  slayer: Record<string, SlayerBoss> & { total_xp: number };
  minions: {
    categories: Record<string, {
      minions: {
        id: string;
        name: string;
        tiers: number[];
        tier: number;
        maxTier: number;
        unlockedTiers: number;
        isMaxed: boolean;
        texture: string;
        nextTierCost: {
          craftOnly: boolean;
          bazaarCost: number | null;
        } | null;
      }[];
      totalMinions: number;
      maxedMinions: number;
      unlockedTiers: number;
      unlockableTiers: number;
    }>;
    totalMinions: number;
    maxedMinions: number;
    unlockedTiers: number;
    unlockableTiers: number;
    slots: {
      current: number;
      next_threshold: number | null;
      tiers_until_next: number | null;
    };
  };
  dungeons: {
    catacombs: {
      level: number;
      xp: number;
      progress: number;
      current: number;
      to_next: number;
      overflow: number;
      floors: Record<string, DungeonFloor>;
    };
    master_catacombs: {
      floors: Record<string, DungeonFloor>;
    };
    classes: Record<
      string,
      {
        level: number;
        xp: number;
        progress: number;
        current: number;
        to_next: number;
        overflow: number;
      }
    >;
  };
  stats: Record<string, number>;
  computed_stats?: {
    stats: Record<string, number>;
    breakdown: Record<string, {
      total: number;
      base: number;
      bonuses: { source: string; value: number }[];
    }>;
  };
  stat_breakdown?: Record<string, {
    total: number;
    base: number;
    bonuses: { source: string; value: number }[];
  }>;
  currencies: {
    purse: number;
    bank: {
      coop: number;
      personal: number;
      total: number;
    };
    total_coins: number;
    motes: number;
    essence_total: number;
    essence: Record<string, number>;
  };
  wardrobe: {
    equipped_slot: number | null;
    items: (WardrobeItem | null)[];
    slots: number;
    equipped_items?: (WardrobeItem | null)[];
  };
  accessories: AccessorySummary;
  weapon_candidates?: {
    slot: number;
    id: string;
    name?: string | null;
    rarity?: string | null;
  }[];
  weapon_selected_slot?: number | null;
  weapon_catalog?: {
    id: string;
    name?: string | null;
  }[];
  weapon_selected_id?: string | null;
  museum?: MuseumData | null;
  collections?: CollectionsData | null;
  inventory?: InventoryData | null;
  networth?: NetworthData | null;
  shards?: ShardsData | null;
  hotm?: HOTMData | null;
};

// ===== Networth Types =====

export type NetworthCategory = {
  name: string;
  total: number;
  item_count: number;
};

export type NetworthData = {
  total: number;
  unsoulbound: number;
  purse: number;
  bank: number;
  categories: Record<string, NetworthCategory>;
};

export type AggregatedStat = {
  label: string;
  value: number;
  suffix: '' | '%';
  display: string;
};

export type AccessorySummary = {
  items: AccessoryItem[];
  slots: number;
  unique_count: number;
  rarity_counts: Record<string, number>;
  selected_power?: string | null;
  selected_power_label?: string | null;
  magical_power: number;
  magical_power_max?: number;
  highest_magical_power: number;
  tuning: Record<string, number>;
  unlocked_powers: string[];
  power_stones: Record<string, number>;
  missing?: MissingAccessory[];
  missing_total?: number;
  missing_count?: number;
  missing_recommendations?: (MissingAccessory & {
    category?: 'new' | 'upgrade' | 'replace';
    price?: number;
    price_per_mp?: number | null;
    mp_per_coin?: number | null;
    magical_power?: number;
    upgrade_from?: string | null;
    upgrade_sell_price?: number | null;
    upgrade_buy_price?: number | null;
    upgrade_net_cost?: number | null;
    upgrade_mp_gain?: number | null;
  })[];
};

// ===== Museum Types =====

export type MuseumItem = {
  id: string;
  name: string;
  donated_time?: number | null;
  borrowing: boolean;
  rarity?: string | null;
  category?: string;
  mc_id?: string | null;
  damage?: number | null;
  icon_url?: string | null;
  icon_variants?: {
    vanilla?: string | null;
    furfsky?: string | null;
  };
};

export type MuseumMissingItem = {
  id: string;
  name: string;
  category: 'weapons' | 'armor' | 'rarities';
  price?: number | null;
  price_formatted?: string | null;
  icon_url?: string | null;
  icon_variants?: {
    vanilla?: string | null;
    furfsky?: string | null;
  };
};

export type MuseumCategoryProgress = {
  total: number;
  donated: number;
  missing: MuseumMissingItem[];
};

export type MuseumMissing = {
  total_museum_items: number;
  total_donated: number;
  total_missing: number;
  progress_percent: number;
  weapons: MuseumCategoryProgress;
  armor: MuseumCategoryProgress;
  rarities: MuseumCategoryProgress;
  all_missing: MuseumMissingItem[];
  cheapest: MuseumMissingItem[];
};

export type MuseumCategory = {
  name: string;
  items: MuseumItem[];
  donated_count: number;
  total_count: number;
  progress: number;
};

export type MuseumData = {
  available: boolean;
  value: number;
  calculated_value?: number;
  appraisal: boolean;
  total_donated: number;
  regular_items: number;
  special_items: number;
  items: MuseumItem[];
  special: MuseumItem[];
  missing?: MuseumMissing | null;
  categories?: {
    weapons?: MuseumCategory;
    armor?: MuseumCategory;
    rarities?: MuseumCategory;
  };
};

// ===== Collection Types =====

export type CollectionItem = {
  id: string;
  name: string;
  amount: number;
  amountFormatted: string;
  tier: number;
  maxTier: number;
  isMaxed: boolean;
  progress: number;
  nextTierReq: number | null;
  nextTierReqFormatted: string | null;
  texture: string;
};

export type CollectionCategory = {
  name: string;
  icon: string;
  color: string;
  collections: CollectionItem[];
  totalCollections: number;
  maxedCollections: number;
  totalTiers: number;
  unlockedTiers: number;
};

export type CollectionsData = {
  categories: Record<string, CollectionCategory>;
  totalCollections: number;
  maxedCollections: number;
  totalTiers: number;
  unlockedTiers: number;
};

// ===== Inventory Types =====

/** Reuse WardrobeItem structure for inventory items */
export type InventoryItem = WardrobeItem;

export type BackpackData = {
  slot: number;
  icon: InventoryItem | null;
  contents: (InventoryItem | null)[];
  size: number;
};

export type InventoryData = {
  /** Player inventory - 36 slots (0-8 hotbar, 9-35 main) */
  player_inventory: (InventoryItem | null)[];
  /** Ender chest contents */
  ender_chest: (InventoryItem | null)[];
  /** Currently equipped equipment */
  equipment: (InventoryItem | null)[];
  /** Backpack contents */
  backpacks: BackpackData[];
  /** Personal vault contents */
  personal_vault: (InventoryItem | null)[];
  /** Potion bag contents */
  potion_bag: (InventoryItem | null)[];
  /** Fishing bag contents */
  fishing_bag: (InventoryItem | null)[];
  /** Sacks bag contents */
  sacks_bag: (InventoryItem | null)[];
  /** Arrow quiver contents */
  quiver: (InventoryItem | null)[];
};

// ===== Shard Types =====

export type ShardItem = {
  id: string;
  name: string;
  rarity: string;
  owned: boolean;
};

export type ShardStats = {
  unique_shards: number;
  shard_charm_level: number;
  total_hunts: number;
  hunts_by_category: Record<string, number>;
};

export type ShardsData = {
  stats: ShardStats;
  shards: ShardItem[];
  total_owned: number;
  total_shards: number;
};

// ===== HOTM Types =====

export type HOTMPowder = {
  mithril: number;
  gemstone: number;
  glacite: number;
  mithril_total?: number;
  gemstone_total?: number;
  glacite_total?: number;
};

export type HOTMData = {
  tier: number;
  experience?: number;
  perks: Record<string, number>;
  powder: HOTMPowder;
  tokens_spent?: number;
  selected_ability?: string;
  crystals?: Record<string, { state: string; total_found?: number; total_placed?: number }>;
};
