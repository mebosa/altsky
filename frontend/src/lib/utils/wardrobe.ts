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

type RGB = { r: number; g: number; b: number };

function parseColor(color: string): RGB | null {
  const trimmed = color.trim();
  if (/^#?[0-9a-f]{6}$/i.test(trimmed)) {
    const hex = trimmed.startsWith('#') ? trimmed.slice(1) : trimmed;
    return {
      r: parseInt(hex.slice(0, 2), 16),
      g: parseInt(hex.slice(2, 4), 16),
      b: parseInt(hex.slice(4, 6), 16)
    };
  }

  const rgbMatch = trimmed.match(
    /^rgb\s*\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*\)$/i
  );
  if (rgbMatch) {
    const [, r, g, b] = rgbMatch.map((value) => Number(value));
    if ([r, g, b].every((channel) => channel >= 0 && channel <= 255)) {
      return { r, g, b };
    }
  }

  return null;
}

async function tintIcon(iconUrl: string, color: string): Promise<string> {
  if (!hasDOM()) {
    return iconUrl;
  }

  const tint = parseColor(color);
  if (!tint) {
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
      if (data[i + 3] === 0) continue;
      data[i] = Math.min(255, Math.round((data[i] * tint.r) / 255));
      data[i + 1] = Math.min(255, Math.round((data[i + 1] * tint.g) / 255));
      data[i + 2] = Math.min(255, Math.round((data[i + 2] * tint.b) / 255));
    }
    ctx.putImageData(imageData, 0, 0);
  } catch (_err) {
    return iconUrl;
  }

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

export type LegacyStyle = {
  color?: string;
  bold?: boolean;
  italic?: boolean;
  underline?: boolean;
  strikethrough?: boolean;
  obfuscated?: boolean;
};

export type LegacySegment = LegacyStyle & {
  text: string;
};

const LEGACY_COLORS: Record<string, string> = {
  '0': '#000000',
  '1': '#0000AA',
  '2': '#00AA00',
  '3': '#00AAAA',
  '4': '#AA0000',
  '5': '#AA00AA',
  '6': '#FFAA00',
  '7': '#AAAAAA',
  '8': '#555555',
  '9': '#5555FF',
  a: '#55FF55',
  b: '#55FFFF',
  c: '#FF5555',
  d: '#FF55FF',
  e: '#FFFF55',
  f: '#FFFFFF'
};

const DEFAULT_SEGMENT_STYLE: LegacyStyle = {
  color: '#f5f5f5',
  bold: false,
  italic: false,
  underline: false,
  strikethrough: false,
  obfuscated: false
};

export function parseLegacyText(line: string): LegacySegment[] {
  const segments: LegacySegment[] = [];
  let buffer = '';
  let style: LegacyStyle = { ...DEFAULT_SEGMENT_STYLE };

  const pushSegment = () => {
    if (!buffer) return;
    segments.push({ ...style, text: buffer });
    buffer = '';
  };

  for (let i = 0; i < line.length; i += 1) {
    const char = line[i];
    if (char === '§' && i + 1 < line.length) {
      const code = line[i + 1].toLowerCase();
      i += 1;
      pushSegment();

      if (code === 'r') {
        style = { ...DEFAULT_SEGMENT_STYLE };
        continue;
      }
      if (LEGACY_COLORS[code]) {
        style = { ...DEFAULT_SEGMENT_STYLE, color: LEGACY_COLORS[code] };
        continue;
      }
      switch (code) {
        case 'k':
          style = { ...style, obfuscated: true };
          break;
        case 'l':
          style = { ...style, bold: true };
          break;
        case 'm':
          style = { ...style, strikethrough: true };
          break;
        case 'n':
          style = { ...style, underline: true };
          break;
        case 'o':
          style = { ...style, italic: true };
          break;
        default:
          break;
      }
      continue;
    }
    buffer += char;
  }

  pushSegment();
  return segments.filter((segment) => segment.text.length > 0);
}
