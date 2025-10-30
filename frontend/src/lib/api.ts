export const API_BASE = (import.meta.env.VITE_API_BASE ?? 'http://localhost:8000').replace(/\/$/,'');

async function handle(r: Response) {
  if (!r.ok) {
    const text = await r.text().catch(() => "");
    throw new Error(`${r.status} ${r.statusText}${text ? ` - ${text.slice(0,120)}` : ""}`);
  }
  return r.json();
}

export async function get<T>(path: string): Promise<T> {
  const url = `${API_BASE}${path}`;
  console.log('[AltSky] GET', url);
  const r = await fetch(url);
  return handle(r);
}
