import type { SkillStat } from './skills';
import type { WardrobeItem } from './wardrobe';
import type { AccessorySummary } from './accessories';

export type Player = {
  name: string;
  uuid: string;
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
  accessories: AccessorySummary;
};
