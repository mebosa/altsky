<script lang="ts">

  interface HistoryPoint {
    ts: string;
    buy_price: number;
    sell_price: number;
  }

  interface Quality {
    confidence_label?: string;
    confidence_score?: number;
    liquidity_score?: number;
    spread_percent?: number;
    notes?: string[];
  }

  interface HistoryResponse {
    success: boolean;
    product_id: string;
    name: string;
    current: {
      buy_price: number;
      sell_price: number;
      buy_volume: number;
      sell_volume: number;
      buy_orders: number;
      sell_orders: number;
      quality: Quality;
    };
    points: HistoryPoint[];
    last_updated: string;
  }

  export let data: {
    productId: string;
    history: HistoryResponse | { error: string; detail?: string };
  };

  $: history = (data?.history && 'success' in data.history && data.history.success) ? (data.history as HistoryResponse) : null;
  $: error = history ? '' : (data?.history as any)?.detail || (data?.history as any)?.error || '';
  $: lastUpdated = history
    ? new Date(history.last_updated).toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      })
    : '';

  function formatNumber(num: number): string {
    if (num >= 1_000_000_000) return (num / 1_000_000_000).toFixed(2) + 'B';
    if (num >= 1_000_000) return (num / 1_000_000).toFixed(2) + 'M';
    if (num >= 1_000) return (num / 1_000).toFixed(2) + 'K';
    return num.toLocaleString('en-US');
  }

  function formatCoins(num: number): string {
    return num.toLocaleString('en-US', { minimumFractionDigits: 1, maximumFractionDigits: 1 });
  }

  function buildPath(points: HistoryPoint[], key: 'buy_price' | 'sell_price', w = 960, h = 260): string {
    if (!points.length) return '';
    const ys = points.map((p) => p[key]);
    const allYs = points.flatMap((p) => [p.buy_price, p.sell_price]);
    const minY = Math.min(...allYs);
    const maxY = Math.max(...allYs);
    const pad = Math.max(1e-9, (maxY - minY) * 0.08);
    const y0 = minY - pad;
    const y1 = maxY + pad;

    const toX = (i: number) => (points.length <= 1 ? w / 2 : (i / (points.length - 1)) * w);
    const toY = (v: number) => {
      const t = (v - y0) / (y1 - y0);
      return h - t * h;
    };

    let d = '';
    for (let i = 0; i < points.length; i++) {
      const x = toX(i);
      const y = toY(ys[i]);
      d += i === 0 ? `M ${x.toFixed(2)} ${y.toFixed(2)}` : ` L ${x.toFixed(2)} ${y.toFixed(2)}`;
    }
    return d;
  }
</script>

<svelte:head>
  <title>Bazaar Item · AltSky</title>
  <meta name="description" content="Hypixel SkyBlock Bazaar item details" />
</svelte:head>

<div class="wrap">
  <div class="header">
    <div class="header-main">
      <a href="/bazaar" class="back-link">← Back</a>
      <div class="title-section">
        <h1>{history?.name ?? data.productId}</h1>
        <p class="muted">Buy/Sell overlay history (cache-based)</p>
      </div>
    </div>
    {#if lastUpdated}
      <span class="badge">Updated: {lastUpdated}</span>
    {/if}
  </div>

  {#if error}
    <div class="error-message">{error}</div>
  {/if}

  {#if history}
    <div class="panel">
      <div class="stats">
        <div class="stat">
          <div class="stat-label">Buy (Instant)</div>
          <div class="stat-value">{formatCoins(history.current.buy_price)}</div>
        </div>
        <div class="stat">
          <div class="stat-label">Sell (Instant)</div>
          <div class="stat-value">{formatCoins(history.current.sell_price)}</div>
        </div>
        <div class="stat">
          <div class="stat-label">Quality</div>
          <div class="stat-value">
            {history.current.quality?.confidence_label ?? '—'}
            {#if typeof history.current.quality?.confidence_score === 'number'}
              <span class="stat-sub">({history.current.quality.confidence_score.toFixed(2)})</span>
            {/if}
          </div>
        </div>
        <div class="stat">
          <div class="stat-label">Min Volume</div>
          <div class="stat-value">{formatNumber(Math.min(history.current.buy_volume, history.current.sell_volume))}</div>
        </div>
      </div>

      <div class="chart-wrap" aria-label="Buy and sell price history chart">
        <svg viewBox="0 0 960 260" preserveAspectRatio="none" class="chart">
          <path d={buildPath(history.points, 'buy_price')} class="line buy" />
          <path d={buildPath(history.points, 'sell_price')} class="line sell" />
        </svg>
        <div class="legend">
          <span class="legend-item"><span class="dot buy"></span> Buy</span>
          <span class="legend-item"><span class="dot sell"></span> Sell</span>
        </div>
      </div>

      <div class="panel-note">
        This history is cached in the server cache and grows as endpoints are called.
      </div>
    </div>
  {:else}
    <div class="panel empty-panel">
      <p>No history available yet.</p>
    </div>
  {/if}
</div>

<style>
  .wrap {
    max-width: 1200px;
    margin: 40px auto 64px;
    padding: 0 18px;
    display: flex;
    flex-direction: column;
    gap: 20px;
    color: var(--theme-text-primary);
  }

  .header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 16px;
    flex-wrap: wrap;
  }

  .header-main {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .back-link {
    color: var(--theme-accent);
    text-decoration: none;
    font-size: 14px;
    font-weight: 500;
    transition: opacity 0.2s;
  }

  .back-link:hover {
    opacity: 0.8;
  }

  .title-section {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  h1 {
    font-size: clamp(28px, 5vw, 36px);
    margin: 0;
    letter-spacing: -0.02em;
    color: var(--theme-text-primary);
  }

  .muted {
    color: var(--theme-text-soft);
    margin: 0;
    font-size: 14px;
  }

  .badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 8px 12px;
    border-radius: 10px;
    border: 1px solid color-mix(in srgb, var(--theme-accent) 40%, #ffffff 10%);
    color: var(--theme-text-primary);
    background: color-mix(in srgb, var(--theme-accent-alpha-22) 60%, transparent);
    font-size: 12px;
    font-weight: 500;
  }

  .panel {
    border: 1px solid color-mix(in srgb, var(--theme-surface-border) 80%, transparent);
    border-radius: 16px;
    background: color-mix(in srgb, var(--theme-surface) 96%, transparent);
    padding: 18px;
    box-shadow: var(--neu-elevated), inset 4px 4px 10px rgba(0, 0, 0, 0.25);
  }

  .stats {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 12px;
    margin-bottom: 16px;
  }

  @media (max-width: 900px) {
    .stats {
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }
  }

  .stat {
    border: 1px solid color-mix(in srgb, var(--theme-surface-border) 70%, transparent);
    border-radius: 14px;
    padding: 12px;
    background: color-mix(in srgb, var(--theme-surface) 92%, transparent);
  }

  .stat-label {
    color: var(--theme-text-soft);
    font-size: 12px;
    margin-bottom: 6px;
  }

  .stat-value {
    font-size: 16px;
    font-weight: 700;
  }

  .stat-sub {
    margin-left: 6px;
    color: var(--theme-text-soft);
    font-weight: 600;
    font-size: 12px;
  }

  .chart-wrap {
    border: 1px solid color-mix(in srgb, var(--theme-surface-border) 70%, transparent);
    border-radius: 14px;
    padding: 12px;
    background: color-mix(in srgb, var(--theme-surface) 92%, transparent);
  }

  .chart {
    width: 100%;
    height: 260px;
    display: block;
  }

  .line {
    fill: none;
    stroke-width: 2.2;
    vector-effect: non-scaling-stroke;
  }

  .line.buy {
    stroke: var(--theme-accent);
  }

  .line.sell {
    stroke: color-mix(in srgb, var(--theme-text-primary) 70%, var(--theme-accent) 30%);
    opacity: 0.9;
  }

  .legend {
    display: flex;
    gap: 14px;
    margin-top: 10px;
    color: var(--theme-text-soft);
    font-size: 12px;
  }

  .legend-item {
    display: inline-flex;
    align-items: center;
    gap: 8px;
  }

  .dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    display: inline-block;
  }

  .dot.buy {
    background: var(--theme-accent);
  }

  .dot.sell {
    background: color-mix(in srgb, var(--theme-text-primary) 70%, var(--theme-accent) 30%);
  }

  .panel-note {
    margin-top: 12px;
    color: var(--theme-text-soft);
    font-size: 12px;
  }

  .error-message {
    border: 1px solid color-mix(in srgb, #ff6b6b 55%, transparent);
    background: color-mix(in srgb, #ff6b6b 10%, transparent);
    border-radius: 14px;
    padding: 12px 14px;
    color: var(--theme-text-primary);
  }

  .empty-panel {
    text-align: center;
  }
</style>
