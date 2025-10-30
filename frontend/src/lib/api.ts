export const API_BASE = (import.meta.env.VITE_API_BASE ?? 'http://localhost:8000').replace(/\/$/,'');
type Json = any;

export async function get<T = Json>(path: string, opts?: { query?: Record<string, string | number | boolean> }) {
  let url = `${API_BASE}${path}`;
  if (opts?.query) {
    const qs = new URLSearchParams();
    for (const [k,v] of Object.entries(opts.query)) qs.set(k, String(v));
    url += `?${qs.toString()}`;
  }
  const r = await fetch(url, { headers: { 'Accept': 'application/json' } });
  let body: any = null;
  try { body = await r.json(); } catch { /* ignore */ }

  if (!r.ok) {
    const msg = body?.error || body?.detail || `${r.status}`;
    throw new Error(String(msg));
  }
  return body as T;
}
