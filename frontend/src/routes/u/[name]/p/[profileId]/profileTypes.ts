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

export type WardrobeItem = {
  slot: number;
  id: string;
  mc_id: string;
  name: string;
  count: number;
  rarity?: string | null;
  lore: string[];
  icon_url?: string | null;
  leather_color?: string | null;
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
  slayer: Record<string, { level: number; xp: number }> & { total_xp: number };
  dungeons: {
    catacombs: { level: number; xp: number };
    classes: Record<string, { level: number; xp: number }>;
  };
  stats: Record<string, number>;
  currencies: {
    purse: number;
    bank: number;
    total_coins: number;
    motes: number;
    essence_total: number;
    essence: Record<string, number>;
  };
  wardrobe: {
    equipped_slot: number | null;
    items: (WardrobeItem | null)[];
    slots: number;
  };
};

export type AggregatedStat = {
  label: string;
  value: number;
  suffix: '' | '%';
  display: string;
};
