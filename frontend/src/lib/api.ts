// src/lib/api.ts
export const API_BASE = (import.meta.env.VITE_API_BASE ?? 'http://localhost:8000').replace(/\/$/,'');

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
  const url = `${API_BASE}${path}${buildQuery(opts.query)}`;
  const r = await fetch(url, { signal: opts.signal });
  if (!r.ok) throw new Error(`${r.status}`);
  return r.json();
}
