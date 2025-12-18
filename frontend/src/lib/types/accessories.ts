import type { TexturePack } from '$lib/stores/texturePack';

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
};

export type AccessorySummary = {
  items: AccessoryItem[];
  slots: number;
  unique_count: number;
  rarity_counts: Record<string, number>;
  selected_power?: string | null;
  selected_power_label?: string | null;
  magical_power: number;
  highest_magical_power: number;
  tuning: Record<string, number>;
  unlocked_powers: string[];
  power_stones: Record<string, number>;
  missing?: MissingAccessory[];
  missing_total?: number;
  missing_count?: number;
};
