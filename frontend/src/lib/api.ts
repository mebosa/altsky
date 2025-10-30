export const API_BASE = (import.meta.env.VITE_API_BASE ?? 'http://localhost:8000').replace(/\/$/,'');
export async function get<T>(path: string): Promise<T> {
  const r = await fetch(${API_BASE});
  if (!r.ok) throw new Error(String(r.status));
  return r.json();
}
