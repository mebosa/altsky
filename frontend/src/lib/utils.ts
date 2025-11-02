export function debounce<T extends (...args: any[]) => void>(fn: T, ms = 300) {
  let handle: ReturnType<typeof setTimeout> | undefined;
  return (...args: Parameters<T>) => {
    if (handle) clearTimeout(handle);
    handle = setTimeout(() => fn(...args), ms);
  };
}

export function timeAgo(ts?: string | number | Date) {
  if (!ts) return '';
  const target = new Date(ts);
  const diff = Date.now() - target.getTime();
  if (Number.isNaN(diff)) return '';

  const sec = Math.max(0, Math.floor(diff / 1000));
  if (sec < 60) return `${sec}s ago`;

  const min = Math.floor(sec / 60);
  if (min < 60) return `${min}m ago`;

  const hr = Math.floor(min / 60);
  if (hr < 24) return `${hr}h ago`;

  const day = Math.floor(hr / 24);
  return `${day}d ago`;
}

import { browser } from '$app/environment'; // Used for SSR checks

const RECENT_KEY = 'altsky_recent'; // Key for recent searches

export function saveRecent(name: string) {
  if (typeof window !== 'undefined') {
    const recent = loadRecent();
    const newRecent = [name, ...recent.filter((n) => n !== name)].slice(0, 5);
    localStorage.setItem(RECENT_KEY, JSON.stringify(newRecent));
  }
}

export function loadRecent(): string[] {
  if (typeof window !== 'undefined') {
    const recent = localStorage.getItem(RECENT_KEY);
    return recent ? JSON.parse(recent) : [];
  }
  return [];
}

export function formatNumber(value: number, fraction = 0) {
  const opts: Intl.NumberFormatOptions = { maximumFractionDigits: fraction, minimumFractionDigits: fraction };
  return Number.isFinite(value) ? value.toLocaleString(undefined, opts) : '-';
}

export function formatLargeNumber(value: number) {
  if (!Number.isFinite(value)) return '-';
  const abs = Math.abs(value);
  if (abs >= 1_000_000_000) return `${(value / 1_000_000_000).toFixed(2)}B`;
  if (abs >= 1_000_000) return `${(value / 1_000_000).toFixed(2)}M`;
  if (abs >= 1_000) return `${(value / 1_000).toFixed(2)}K`;
  return value.toLocaleString();
}

export function formatPercent(value: number, fraction = 0) {
  if (!Number.isFinite(value)) return '-';
  return `${value.toFixed(fraction)}%`;
}
