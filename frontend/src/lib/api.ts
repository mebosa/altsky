// src/lib/api.ts
const STORAGE_KEY = 'altsky_api_base_pref';
const ORIGIN_TOKEN = '__origin__';
const PARAM_KEYS = ['api_base', 'api', 'backend'];
const LOOPBACK_HOSTS = new Set(['localhost', '127.0.0.1', '::1', '[::1]']);

type BasePreference = {
  rawBase: string;
  persist: boolean;
  clearStorage?: boolean;
};

let cachedBrowserBase: string | undefined;

function stripTrailingSlash(value: string) {
  return value.replace(/\/+$/, '');
}

function isLoopbackHost(host: string) {
  return LOOPBACK_HOSTS.has(host.toLowerCase());
}

function toURL(value: string, origin?: string) {
  try {
    return new URL(value);
  } catch {
    if (origin) {
      try {
        return new URL(value, origin);
      } catch {
        return null;
      }
    }
    return null;
  }
}

function adaptBaseForBrowser(resolvedBase: string, origin: string) {
  if (!resolvedBase) return resolvedBase;
  const originUrl = toURL(origin);
  const target = toURL(resolvedBase, origin);
  if (!originUrl || !target) return resolvedBase;
  if (isLoopbackHost(target.hostname) && !isLoopbackHost(originUrl.hostname)) {
    return stripTrailingSlash(origin);
  }
  return resolvedBase;
}

function sanitizeRawBase(value: string) {
  let trimmed = value.trim();
  if (trimmed.startsWith('//')) {
    trimmed = `https:${trimmed}`;
  }
  if (
    !/^https?:\/\//i.test(trimmed) &&
    !trimmed.startsWith('/') &&
    /^[\w.-]+(:\d+)?(\/.*)?$/.test(trimmed)
  ) {
    trimmed = `https://${trimmed}`;
  }
  return stripTrailingSlash(trimmed);
}

function normalizeConfiguredBase(value: string) {
  const trimmed = value.trim();
  const lower = trimmed.toLowerCase();
  if (!trimmed || lower === 'origin' || lower === 'same' || lower === 'here') {
    return ORIGIN_TOKEN;
  }
  if (lower === 'local') {
    return sanitizeRawBase('http://localhost:8000');
  }
  return sanitizeRawBase(trimmed);
}

function materializeRawBase(rawBase: string, origin?: string) {
  if (rawBase === ORIGIN_TOKEN) {
    return origin ? stripTrailingSlash(origin) : '';
  }
  if (rawBase.startsWith('/')) {
    return origin ? `${stripTrailingSlash(origin)}${rawBase}` : rawBase;
  }
  return rawBase;
}

function readStoredRawBase() {
  if (typeof window === 'undefined') return undefined;
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (raw === null) return undefined;
    return raw;
  } catch {
    return undefined;
  }
}

function storeRawBase(rawBase: string) {
  if (typeof window === 'undefined') return;
  try {
    window.localStorage.setItem(STORAGE_KEY, rawBase);
  } catch {
    // ignore storage failures
  }
}

function clearStoredRawBase() {
  if (typeof window === 'undefined') return;
  try {
    window.localStorage.removeItem(STORAGE_KEY);
  } catch {
    // ignore storage failures
  }
}

function readPreferenceFromUrl(url: URL): BasePreference | null {
  for (const key of PARAM_KEYS) {
    if (!url.searchParams.has(key)) continue;
    const value = url.searchParams.get(key);
    if (value === null) {
      return { rawBase: ORIGIN_TOKEN, persist: true };
    }
    const trimmed = value.trim();
    const lower = trimmed.toLowerCase();
    if (lower === 'clear' || lower === 'reset' || lower === 'default') {
      return { rawBase: ORIGIN_TOKEN, persist: false, clearStorage: true };
    }
    return { rawBase: normalizeConfiguredBase(trimmed), persist: true };
  }
  return null;
}

function resolveBrowserBase() {
  if (cachedBrowserBase !== undefined) return cachedBrowserBase;

  if (typeof window === 'undefined') return '';

  const currentUrl = new URL(window.location.href);
  const pref = readPreferenceFromUrl(currentUrl);
  if (pref) {
    if (pref.clearStorage) {
      clearStoredRawBase();
    } else if (pref.persist) {
      storeRawBase(pref.rawBase);
    }
    const resolvedPref = materializeRawBase(pref.rawBase, window.location.origin);
    const adapted = adaptBaseForBrowser(resolvedPref, window.location.origin);
    cachedBrowserBase = adapted;
    return adapted;
  }

  const stored = readStoredRawBase();
  if (stored !== undefined) {
    const resolvedStored = materializeRawBase(stored, window.location.origin);
    const adapted = adaptBaseForBrowser(resolvedStored, window.location.origin);
    cachedBrowserBase = adapted;
    return adapted;
  }

  const fallback = materializeRawBase(ORIGIN_TOKEN, window.location.origin);
  const adaptedFallback = adaptBaseForBrowser(fallback, window.location.origin);
  cachedBrowserBase = adaptedFallback;
  return adaptedFallback;
}

export function resolveApiBase(context?: { url?: URL }) {
  const envRaw = import.meta.env.VITE_API_BASE;
  if (envRaw !== undefined) {
    const rawBase = normalizeConfiguredBase(String(envRaw));
    const origin = context?.url?.origin ?? (typeof window !== 'undefined' ? window.location.origin : undefined);
    let resolved = materializeRawBase(rawBase, origin);
    if (typeof window !== 'undefined' && origin) {
      resolved = adaptBaseForBrowser(resolved, window.location.origin);
    }
    return resolved;
  }

  if (context?.url) {
    const pref = readPreferenceFromUrl(context.url);
    if (pref) {
      return materializeRawBase(pref.rawBase, context.url.origin);
    }
    return stripTrailingSlash(context.url.origin);
  }

  if (typeof window !== 'undefined') {
    return resolveBrowserBase();
  }

  if (import.meta.env.DEV) {
    return 'http://localhost:8000';
  }

  return '';
}

export function setApiBasePreference(base: string | null, persist = true) {
  if (typeof window === 'undefined') return;
  const rawBase = base !== null && base.trim() ? normalizeConfiguredBase(base) : ORIGIN_TOKEN;
  if (persist) {
    storeRawBase(rawBase);
  } else {
    clearStoredRawBase();
  }
  const resolved = materializeRawBase(rawBase, window.location.origin);
  cachedBrowserBase = adaptBaseForBrowser(resolved, window.location.origin);
}

type GetOpts = {
  query?: Record<string, string | number | boolean | undefined | null>;
  signal?: AbortSignal;
};

function buildQuery(q?: GetOpts['query']) {
  if (!q) return '';
  const usp = new URLSearchParams();
  for (const [k, v] of Object.entries(q)) {
    if (v === undefined || v === null) continue;
    usp.set(k, String(v));
  }
  const s = usp.toString();
  return s ? `?${s}` : '';
}

export async function get<T>(path: string, opts: GetOpts = {}): Promise<T> {
  try {
    const base = resolveApiBase();
    const url = `${base}${path}${buildQuery(opts.query)}`;
    const r = await fetch(url, { 
      signal: opts.signal,
      headers: {
        'Accept': 'application/json'
      }
    });
    
    const data = await r.json();
    
    if (!r.ok) {
      throw new Error(data.error || `HTTP error! status: ${r.status}`);
    }
    
    return data;
  } catch (error) {
    console.error('API request failed:', error);
    throw error;
  }
}
