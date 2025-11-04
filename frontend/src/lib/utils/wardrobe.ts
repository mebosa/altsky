import type { WardrobeItem } from '../types/wardrobe';

export function buildWardrobeColumns(items: (WardrobeItem | null)[]) {
  const columns: (WardrobeItem | null)[][] = [];
  let currentColumn: (WardrobeItem | null)[] = [];

  for (const item of items) {
    currentColumn.push(item);
    if (currentColumn.length === 4) {
      columns.push(currentColumn);
      currentColumn = [];
    }
  }

  if (currentColumn.length > 0) {
    columns.push(currentColumn);
  }

  return columns;
}

export function toEquippedItems(index: number | null, items: (WardrobeItem | null)[]) {
  if (index === null || !items.length) return [];
  const startIndex = index * 4;
  return items.slice(startIndex, startIndex + 4).filter((item): item is WardrobeItem => item !== null);
}

export function deriveSetLabel(items: WardrobeItem[]) {
  if (!items.length) return '';
  const firstItem = items[0];
  if (!firstItem) return '';
  
  const baseNameMatch = firstItem.name.match(/^(\w+)/);
  if (!baseNameMatch) return '';
  
  const baseName = baseNameMatch[1];
  return items.every(item => item.name.startsWith(baseName)) ? baseName : '';
}

export function aggregateSetStats(items: WardrobeItem[]) {
  const stats = new Map<string, number>();
  
  for (const item of items) {
    // Add stat parsing logic here
  }
  
  return Array.from(stats.entries()).map(([label, value]) => ({
    label,
    display: formatStat(label, value)
  }));
}

export function gatherSetBonusLines(items: WardrobeItem[]) {
  const bonuses: string[] = [];
  // Add bonus parsing logic here
  return bonuses;
}

function formatStat(label: string, value: number) {
  // Add stat formatting logic here
  return `${value}`;
}