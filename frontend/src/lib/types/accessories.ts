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
  mc_id?: string | null;
  damage?: number | null;
  icon_url?: string | null;
  icon_variants?: Partial<Record<TexturePack, string>>;
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
