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
  drops?: Record<string, number>;
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
  dungeons: {
    catacombs: {
      level: number;
      xp: number;
      progress: number;
      current: number;
      to_next: number;
      overflow: number;
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
