export const TABS = [
  { id: 'summary', label: 'Overview' },
  { id: 'skills', label: 'Skills' },
  { id: 'stats', label: 'Stats' },
  { id: 'slayer', label: 'Slayer' },
  { id: 'dungeons', label: 'Dungeons' },
  { id: 'accessories', label: 'Accessories' },
  { id: 'wardrobe', label: 'Wardrobe' }
] as const;

export type TabId = (typeof TABS)[number]['id'];
