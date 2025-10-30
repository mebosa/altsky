export const API_BASE = (import.meta.env.VITE_API_BASE ?? "http://localhost:8000").replace(/\/$/,"");
export async function get<T>(path: string): Promise<T> {
  const url = `${API_BASE}${path}`;
  console.log("[AltSky] GET", url);
  const r = await fetch(url);
  if (!r.ok) throw new Error(String(r.status));
  return r.json();
}
