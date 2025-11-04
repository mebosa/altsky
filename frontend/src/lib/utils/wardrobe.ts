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

export function formatLeatherColor(color?: string | null) {
  if (!color) return null;
  let value = color.trim();
  if (!value) return null;
  if (/^#?[0-9a-fA-F]{6}$/.test(value)) {
    return value.startsWith('#') ? value : `#${value}`;
  }
  const parts = value.split(/[:;,]/).map((part) => part.trim()).filter(Boolean);
  if (parts.length === 3 && parts.every((part) => !Number.isNaN(Number(part)))) {
    const normalized = parts.map((part) => {
      const num = Number(part);
      if (!Number.isFinite(num)) return 0;
      return Math.max(0, Math.min(255, Math.round(num)));
    });
    return `rgb(${normalized.join(',')})`;
  }
  return null;
}

const RARITY_BACKGROUND_COLORS: Record<string, string> = {
  basic: 'rgba(148, 163, 184, 0.22)',
  common: 'rgba(113, 113, 122, 0.28)',
  uncommon: 'rgba(34, 197, 94, 0.28)',
  rare: 'rgba(59, 130, 246, 0.28)',
  epic: 'rgba(168, 85, 247, 0.28)',
  legendary: 'rgba(250, 204, 21, 0.32)',
  mythic: 'rgba(236, 72, 153, 0.32)',
  divine: 'rgba(129, 140, 248, 0.32)',
  supreme: 'rgba(14, 165, 233, 0.3)',
  special: 'rgba(239, 68, 68, 0.32)',
  very_special: 'rgba(239, 68, 68, 0.36)',
  ultimate: 'rgba(192, 132, 252, 0.32)',
  admin: 'rgba(248, 113, 113, 0.32)'
};

export function rarityToBackground(rarity?: string | null) {
  if (!rarity) return null;
  const normalized = rarity.trim().toLowerCase().replace(/\s+/g, '_');
  return RARITY_BACKGROUND_COLORS[normalized] ?? null;
}

export function buildStyleString(parts: (string | null | undefined)[]) {
  const filtered = parts.filter(
    (part): part is string => !!part && part.trim().length > 0
  );
  return filtered.length ? filtered.join(';') : undefined;
}

export function isFallbackIcon(url?: string | null) {
  if (!url) return false;
  const normalized = url.trim().toLowerCase();
  if (normalized.endsWith('diamond.png')) {
    return true;
  }
  return normalized.includes('diamond.png?');
}

const tintedIconCache = new Map<string, string>();
const tintedIconPromises = new Map<string, Promise<string>>();

function hasDOM() {
  return typeof document !== 'undefined';
}

async function loadImage(url: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.crossOrigin = 'anonymous';
    img.decoding = 'async';
    img.onload = () => resolve(img);
    img.onerror = (err) => reject(err);
    img.src = url;
  });
}

async function tintIcon(iconUrl: string, color: string): Promise<string> {
  if (!hasDOM()) {
    return iconUrl;
  }

  const img = await loadImage(iconUrl);
  const width = img.naturalWidth || img.width;
  const height = img.naturalHeight || img.height;

  if (!width || !height) {
    return iconUrl;
  }

  const canvas = document.createElement('canvas');
  canvas.width = width;
  canvas.height = height;
  const ctx = canvas.getContext('2d', { willReadFrequently: true });
  if (!ctx) {
    return iconUrl;
  }

  ctx.drawImage(img, 0, 0, width, height);
  try {
    const imageData = ctx.getImageData(0, 0, width, height);
    const data = imageData.data;
    for (let i = 0; i < data.length; i += 4) {
      const r = data[i];
      const g = data[i + 1];
      const b = data[i + 2];
      const luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b;
      data[i] = data[i + 1] = data[i + 2] = luminance;
    }
    ctx.putImageData(imageData, 0, 0);
  } catch (_err) {
    return iconUrl;
  }

  ctx.globalCompositeOperation = 'source-in';
  ctx.fillStyle = color;
  ctx.fillRect(0, 0, width, height);

  return canvas.toDataURL('image/png');
}

export function peekTintedIcon(iconUrl: string, color: string): string | undefined {
  const key = `${iconUrl}|${color}`;
  return tintedIconCache.get(key);
}

export function ensureTintedIcon(iconUrl: string, color: string): Promise<string> {
  const key = `${iconUrl}|${color}`;
  if (tintedIconCache.has(key)) {
    return Promise.resolve(tintedIconCache.get(key)!);
  }

  if (tintedIconPromises.has(key)) {
    return tintedIconPromises.get(key)!;
  }

  const promise = tintIcon(iconUrl, color)
    .catch(() => iconUrl)
    .then((result) => {
      tintedIconCache.set(key, result);
      return result;
    })
    .finally(() => {
      tintedIconPromises.delete(key);
    });

  tintedIconPromises.set(key, promise);
  return promise;
}

function formatStat(label: string, value: number) {
  // Add stat formatting logic here
  return `${value}`;
}
