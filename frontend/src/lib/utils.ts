export function debounce<T extends (...args: any[]) => void>(fn: T, ms = 300) {
  let t: any;
  return (...args: Parameters<T>) => {
    clearTimeout(t);
    t = setTimeout(() => fn(...args), ms);
  };
}

export function timeAgo(ts?: string | number | Date) {
  if (!ts) return '';
  const d = new Date(ts);
  const sec = Math.max(0, Math.floor((Date.now() - d.getTime()) / 1000));
  if (sec < 60) return `${sec}초 전`;
  const min = Math.floor(sec / 60);
  if (min < 60) return `${min}분 전`;
  const hr = Math.floor(min / 60);
  if (hr < 24) return `${hr}시간 전`;
  const day = Math.floor(hr / 24);
  return `${day}일 전`;
}

export function saveRecent(name: string, limit = 8) {
  const key = 'altsky_recent';
  const list: string[] = JSON.parse(localStorage.getItem(key) || '[]');
  const n = name.trim();
  if (!n) return;
  const next = [n, ...list.filter(v => v.toLowerCase() !== n.toLowerCase())].slice(0, limit);
  localStorage.setItem(key, JSON.stringify(next));
  return next;
}
export function loadRecent(): string[] {
  try { return JSON.parse(localStorage.getItem('altsky_recent') || '[]'); }
  catch { return []; }
}
