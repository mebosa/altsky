import type { PageLoad } from './$types';

export const load: PageLoad = async ({ params, fetch }) => {
  const productId = params.product_id;
  const query = new URLSearchParams({
    product_id: productId,
    window_seconds: String(6 * 60 * 60),
    max_points: String(360),
    backfill: '1'
  });

  const res = await fetch(`/api/bazaar/history?${query.toString()}`);
  let history: any;
  try {
    history = await res.json();
  } catch {
    history = { error: 'invalid_response' };
  }

  if (!res.ok && history && !history.error) {
    history = { error: 'http_error', detail: `HTTP ${res.status}` };
  }

  return {
    productId,
    history
  };
};
