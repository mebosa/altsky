import type { TexturePack } from '$lib/stores/texturePack';

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
};
