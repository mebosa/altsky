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
  slayer: Record<
    string,
    {
      level: number;
      xp: number;
      kills?: { total: number; tiers: Record<string, number> };
    }
  > & { total_xp: number };
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
