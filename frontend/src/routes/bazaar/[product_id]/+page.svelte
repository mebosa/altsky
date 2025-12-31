<script lang="ts">
  import { onMount } from 'svelte';
  import { texturePackStore } from '$lib/stores/texturePack';
  import {
    loadHypixelItems,
    getItemTextureUrl,
    itemsLoaded,
    loadItemTextures,
    furfskyCacheLoaded,
    vanillaCacheLoaded
  } from '$lib/stores/hypixelItems';

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

  $: itemsReady = $itemsLoaded;
  $: texturesCacheReady = $texturePackStore === 'furfsky' ? $furfskyCacheLoaded : $vanillaCacheLoaded;

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

  onMount(() => {
    loadHypixelItems();
  });

  // Preload this item's texture using the selected pack.
  $: if (data?.productId) {
    loadItemTextures([data.productId], $texturePackStore);
  }

  $: headerIcon = texturesCacheReady ? getItemTextureUrl(data.productId, $texturePackStore) : null;

  // Get fallback emoji for items without textures
  function getFallbackEmoji(productId: string): string {
    const id = productId.toUpperCase();
    if (id.startsWith('SHARD_')) return '💎';
    if (id.startsWith('ENCHANTMENT_') || id.startsWith('ENCHANTED_')) return '✨';
    if (id.includes('RUNE')) return '🔮';
    if (id.includes('ESSENCE')) return '⭐';
    if (id.includes('GEM') || id.includes('GEMSTONE')) return '💠';
    if (id.includes('FLOWER') || id.includes('ROSE')) return '🌸';
    if (id.includes('FISH') || id.includes('SHARK')) return '🐟';
    if (id.includes('POTION') || id.includes('BREW')) return '🧪';
    if (id.includes('BOOK')) return '📖';
    if (id.includes('FRAGMENT')) return '🔹';
    if (id.includes('CRYSTAL')) return '💎';
    if (id.includes('INK')) return '🖤';
    return '📦';
  }

  function formatNumber(num: number): string {
    if (num >= 1_000_000_000) return (num / 1_000_000_000).toFixed(2) + 'B';
    if (num >= 1_000_000) return (num / 1_000_000).toFixed(2) + 'M';
    if (num >= 1_000) return (num / 1_000).toFixed(2) + 'K';
    return num.toLocaleString('en-US');
  }

  function formatCoins(num: number): string {
    return num.toLocaleString('en-US', { minimumFractionDigits: 1, maximumFractionDigits: 1 });
  }

  function formatSignedCoins(num: number): string {
    const sign = num > 0 ? '+' : (num < 0 ? '−' : '');
    return sign + formatCoins(Math.abs(num));
  }

  function formatPercent(num: number): string {
    const sign = num > 0 ? '+' : (num < 0 ? '−' : '');
    return sign + Math.abs(num).toFixed(2) + '%';
  }

  type ChartSpec = {
    viewW: number;
    viewH: number;
    padL: number;
    padR: number;
    padT: number;
    padB: number;
    plotW: number;
    plotH: number;
    y0: number;
    y1: number;
    ticksY: { y: number; value: number }[];
    ticksX: { x: number; index: number; label: string }[];
    toX: (i: number) => number;
    toY: (v: number) => number;
  };

  function buildChartSpec(points: HistoryPoint[], viewW = 960, viewH = 260): ChartSpec {
    const padL = 66;
    const padR = 14;
    const padT = 10;
    const padB = 34;
    const plotW = Math.max(1, viewW - padL - padR);
    const plotH = Math.max(1, viewH - padT - padB);

    const allYs = points.flatMap((p) => [p.buy_price, p.sell_price]);
    const minY = allYs.length ? Math.min(...allYs) : 0;
    const maxY = allYs.length ? Math.max(...allYs) : 1;
    const span = Math.max(1e-9, maxY - minY);
    const pad = span * 0.08;
    const y0 = minY - pad;
    const y1 = maxY + pad;

    const toX = (i: number) => {
      if (points.length <= 1) return padL + plotW / 2;
      return padL + (i / (points.length - 1)) * plotW;
    };
    const toY = (v: number) => {
      const t = (v - y0) / (y1 - y0);
      return padT + plotH - t * plotH;
    };

    // Y ticks (5)
    const ticksY: { y: number; value: number }[] = [];
    for (let i = 0; i < 5; i++) {
      const t = i / 4;
      const value = y0 + (1 - t) * (y1 - y0);
      ticksY.push({ y: padT + t * plotH, value });
    }

    // X ticks (5)
    const ticksX: { x: number; index: number; label: string }[] = [];
    const fmt = new Intl.DateTimeFormat('en-US', { hour: '2-digit', minute: '2-digit' });
    for (let i = 0; i < 5; i++) {
      const t = i / 4;
      const index = points.length <= 1 ? 0 : Math.round(t * (points.length - 1));
      const ts = points[index]?.ts;
      const label = ts ? fmt.format(new Date(ts)) : '';
      ticksX.push({ x: toX(index), index, label });
    }

    return { viewW, viewH, padL, padR, padT, padB, plotW, plotH, y0, y1, ticksY, ticksX, toX, toY };
  }

  function buildPath(points: HistoryPoint[], key: 'buy_price' | 'sell_price', spec: ChartSpec): string {
    if (!points.length) return '';
    const ys = points.map((p) => p[key]);

    let d = '';
    for (let i = 0; i < points.length; i++) {
      const x = spec.toX(i);
      const y = spec.toY(ys[i]);
      d += i === 0 ? `M ${x.toFixed(2)} ${y.toFixed(2)}` : ` L ${x.toFixed(2)} ${y.toFixed(2)}`;
    }
    return d;
  }

  function mean(values: number[]): number {
    if (!values.length) return 0;
    return values.reduce((a, b) => a + b, 0) / values.length;
  }

  function stddev(values: number[]): number {
    if (values.length < 2) return 0;
    const m = mean(values);
    const v = values.reduce((acc, x) => acc + (x - m) * (x - m), 0) / (values.length - 1);
    return Math.sqrt(v);
  }

  function safePct(delta: number, base: number): number {
    if (!isFinite(base) || Math.abs(base) < 1e-12) return 0;
    return (delta / base) * 100;
  }

  function formatShortDateTime(ts: string): string {
    return new Date(ts).toLocaleString('en-US', {
      month: 'short',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  }

  $: points = history?.points ?? [];
  $: chartSpec = buildChartSpec(points);
  $: buySeries = points.map((p) => p.buy_price);
  $: sellSeries = points.map((p) => p.sell_price);
  $: first = points.length ? points[0] : null;
  $: last = points.length ? points[points.length - 1] : null;
  $: buyDelta = first && last ? (last.buy_price - first.buy_price) : 0;
  $: sellDelta = first && last ? (last.sell_price - first.sell_price) : 0;
  $: buyDeltaPct = first && last ? safePct(buyDelta, first.buy_price) : 0;
  $: sellDeltaPct = first && last ? safePct(sellDelta, first.sell_price) : 0;
  $: buyMin = buySeries.length ? Math.min(...buySeries) : 0;
  $: buyMax = buySeries.length ? Math.max(...buySeries) : 0;
  $: sellMin = sellSeries.length ? Math.min(...sellSeries) : 0;
  $: sellMax = sellSeries.length ? Math.max(...sellSeries) : 0;
  $: buyAvg = mean(buySeries);
  $: sellAvg = mean(sellSeries);
  $: buyStd = stddev(buySeries);
  $: sellStd = stddev(sellSeries);
  $: spreadNow = history ? (history.current.buy_price - history.current.sell_price) : 0;
  $: spreadPctNow = history
    ? (typeof history.current.quality?.spread_percent === 'number'
        ? history.current.quality.spread_percent
        : safePct(spreadNow, (history.current.buy_price + history.current.sell_price) / 2))
    : 0;

  let svgEl: SVGSVGElement | null = null;
  let hoverIndex: number | null = null;
  let hoverLeftPx = 0;
  let hoverTopPx = 0;

  function clamp(n: number, lo: number, hi: number): number {
    return Math.max(lo, Math.min(hi, n));
  }

  function onChartMove(ev: MouseEvent) {
    if (!svgEl || !points.length) {
      hoverIndex = null;
      return;
    }
    const rect = svgEl.getBoundingClientRect();
    const xPx = ev.clientX - rect.left;
    const yPx = ev.clientY - rect.top;
    const x = (xPx / rect.width) * chartSpec.viewW;
    const y = (yPx / rect.height) * chartSpec.viewH;

    // only react within plot area
    if (
      x < chartSpec.padL ||
      x > chartSpec.padL + chartSpec.plotW ||
      y < chartSpec.padT ||
      y > chartSpec.padT + chartSpec.plotH
    ) {
      hoverIndex = null;
      return;
    }

    const t = (x - chartSpec.padL) / chartSpec.plotW;
    const idx = points.length <= 1 ? 0 : Math.round(t * (points.length - 1));
    hoverIndex = clamp(idx, 0, points.length - 1);

    // tooltip positioning in px (keep inside chart box)
    hoverLeftPx = clamp(xPx + 12, 12, rect.width - 220);
    hoverTopPx = clamp(yPx - 10, 8, rect.height - 90);
  }

  function onChartLeave() {
    hoverIndex = null;
  }
</script>

<svelte:head>
  <title>{history?.name || data.productId} | Hypixel SkyBlock Bazaar · AltSky</title>
  <meta name="description" content={`Check current price, buy order, sell offer, and history for ${history?.name || data.productId} on Hypixel SkyBlock Bazaar. ${history?.name || data.productId} 바자 시세. ${history?.name || data.productId} 价格走势.`} />
</svelte:head>

<div class="wrap">
  <div class="header">
    <div class="header-main">
      <a href="/bazaar" class="back-link">← Back</a>
      <div class="title-section">
        <div class="title-row">
          {#if headerIcon}
            <img class="item-icon" src={headerIcon} alt="" loading="lazy" decoding="async" />
          {:else}
            <span class="item-icon placeholder" aria-hidden="true">{getFallbackEmoji(data.productId)}</span>
          {/if}
          <h1>{history?.name ?? data.productId}</h1>
        </div>
        <p class="muted">Buy/Sell overlay history</p>
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
          <div class="stat-label" title="Instant buy price (ask): the lowest sell offer price you pay when buying instantly.">Buy (Instant)</div>
          <div class="stat-value">{formatCoins(history.current.buy_price)}</div>
        </div>
        <div class="stat">
          <div class="stat-label" title="Instant sell price (bid): the highest buy order price you receive when selling instantly.">Sell (Instant)</div>
          <div class="stat-value">{formatCoins(history.current.sell_price)}</div>
        </div>
        <div class="stat">
          <div class="stat-label" title="Spread = Buy (ask) − Sell (bid). Large spreads can indicate poor liquidity or bad/buggy pricing.">Spread (Instant)</div>
          <div class="stat-value">{formatCoins(spreadNow)}</div>
        </div>
        <div class="stat">
          <div class="stat-label" title="Spread % from quality model when available; otherwise computed as spread / mid * 100.">Spread %</div>
          <div class="stat-value">{spreadPctNow.toFixed(2)}%</div>
        </div>
        <div class="stat">
          <div class="stat-label" title="Heuristic confidence label/score (no filtering). Use as a warning signal for outliers.">Quality</div>
          <div class="stat-value">
            {history.current.quality?.confidence_label ?? '—'}
            {#if typeof history.current.quality?.confidence_score === 'number'}
              <span class="stat-sub">({history.current.quality.confidence_score.toFixed(2)})</span>
            {/if}
          </div>
        </div>
        <div class="stat">
          <div class="stat-label" title="Liquidity score derived from volumes/orders and spread. Higher is generally safer.">Liquidity</div>
          <div class="stat-value">
            {#if typeof history.current.quality?.liquidity_score === 'number'}
              {history.current.quality.liquidity_score.toFixed(2)}
            {:else}
              —
            {/if}
          </div>
        </div>
        <div class="stat">
          <div class="stat-label" title="Min(buyVolume, sellVolume: 7d moving) from Hypixel quick_status. Rough activity proxy.">Min Volume</div>
          <div class="stat-value">{formatNumber(Math.min(history.current.buy_volume, history.current.sell_volume))}</div>
        </div>
        <div class="stat">
          <div class="stat-label" title="Number of stored history points returned for the selected window.">Samples</div>
          <div class="stat-value">{points.length.toLocaleString('en-US')}</div>
        </div>
      </div>

      <div class="chart-wrap" aria-label="Buy and sell price history chart">
        <svg
          bind:this={svgEl}
          viewBox="0 0 960 260"
          preserveAspectRatio="none"
          class="chart"
          role="img"
          aria-label="Price history chart with axes"
          on:mousemove={onChartMove}
          on:mouseleave={onChartLeave}
        >
          <!-- grid + axes -->
          {#each chartSpec.ticksY as t}
            <line x1={chartSpec.padL} y1={t.y} x2={chartSpec.padL + chartSpec.plotW} y2={t.y} class="grid" />
            <text x={chartSpec.padL - 10} y={t.y + 4} text-anchor="end" class="axis-text">{formatNumber(t.value)}</text>
          {/each}

          <line x1={chartSpec.padL} y1={chartSpec.padT} x2={chartSpec.padL} y2={chartSpec.padT + chartSpec.plotH} class="axis" />
          <line x1={chartSpec.padL} y1={chartSpec.padT + chartSpec.plotH} x2={chartSpec.padL + chartSpec.plotW} y2={chartSpec.padT + chartSpec.plotH} class="axis" />

          {#each chartSpec.ticksX as t}
            <line x1={t.x} y1={chartSpec.padT + chartSpec.plotH} x2={t.x} y2={chartSpec.padT + chartSpec.plotH + 6} class="tick" />
            <text x={t.x} y={chartSpec.padT + chartSpec.plotH + 22} text-anchor="middle" class="axis-text">{t.label}</text>
          {/each}

          <text x={chartSpec.padL} y={12} class="axis-title">Price (coins)</text>
          <text x={chartSpec.padL + chartSpec.plotW} y={252} text-anchor="end" class="axis-title">Time</text>

          <path d={buildPath(points, 'buy_price', chartSpec)} class="line buy" />
          <path d={buildPath(points, 'sell_price', chartSpec)} class="line sell" />

          {#if hoverIndex !== null}
            {@const p = points[hoverIndex]}
            {@const x = chartSpec.toX(hoverIndex)}
            {@const yBuy = chartSpec.toY(p.buy_price)}
            {@const ySell = chartSpec.toY(p.sell_price)}
            <line x1={x} y1={chartSpec.padT} x2={x} y2={chartSpec.padT + chartSpec.plotH} class="hover-line" />
            <circle cx={x} cy={yBuy} r="3.2" class="hover-dot buy" />
            <circle cx={x} cy={ySell} r="3.2" class="hover-dot sell" />
          {/if}
        </svg>

        {#if hoverIndex !== null}
          {@const p = points[hoverIndex]}
          <div class="chart-tooltip" style={`left:${hoverLeftPx}px; top:${hoverTopPx}px;`}>
            <div class="tt-title">{formatShortDateTime(p.ts)}</div>
            <div class="tt-row"><span class="tt-k">Buy (ask)</span><span class="tt-v">{formatCoins(p.buy_price)}</span></div>
            <div class="tt-row"><span class="tt-k">Sell (bid)</span><span class="tt-v">{formatCoins(p.sell_price)}</span></div>
            <div class="tt-row"><span class="tt-k">Spread</span><span class="tt-v">{formatCoins(p.buy_price - p.sell_price)}</span></div>
            <div class="tt-foot">Prices are top-of-book estimates (not guaranteed fills).</div>
          </div>
        {/if}

        <div class="legend">
          <span class="legend-item"><span class="dot buy"></span> Buy</span>
          <span class="legend-item"><span class="dot sell"></span> Sell</span>
        </div>
      </div>

      <div class="derived" aria-label="Derived metrics">
        <div class="derived-row">
          <div class="derived-item">
            <div class="derived-label" title="Time range covered by returned points.">Window</div>
            <div class="derived-value">
              {#if first && last}
                {formatShortDateTime(first.ts)} → {formatShortDateTime(last.ts)}
              {:else}
                —
              {/if}
            </div>
          </div>
          <div class="derived-item">
            <div class="derived-label" title="Change from first point to last point in the window.">Buy Change</div>
            <div class="derived-value">{formatSignedCoins(buyDelta)} ({formatPercent(buyDeltaPct)})</div>
          </div>
          <div class="derived-item">
            <div class="derived-label" title="Change from first point to last point in the window.">Sell Change</div>
            <div class="derived-value">{formatSignedCoins(sellDelta)} ({formatPercent(sellDeltaPct)})</div>
          </div>
          <div class="derived-item">
            <div class="derived-label" title="Min/mean/max of buy(ask) series within the window.">Buy Min/Avg/Max</div>
            <div class="derived-value">{formatCoins(buyMin)} / {formatCoins(buyAvg)} / {formatCoins(buyMax)}</div>
          </div>
          <div class="derived-item">
            <div class="derived-label" title="Min/mean/max of sell(bid) series within the window.">Sell Min/Avg/Max</div>
            <div class="derived-value">{formatCoins(sellMin)} / {formatCoins(sellAvg)} / {formatCoins(sellMax)}</div>
          </div>
          <div class="derived-item">
            <div class="derived-label" title="Sample standard deviation of buy(ask) series. Larger = more volatility.">Buy Volatility (Std Dev)</div>
            <div class="derived-value">{formatCoins(buyStd)}</div>
          </div>
          <div class="derived-item">
            <div class="derived-label" title="Sample standard deviation of sell(bid) series. Larger = more volatility.">Sell Volatility (Std Dev)</div>
            <div class="derived-value">{formatCoins(sellStd)}</div>
          </div>
          <div class="derived-item">
            <div class="derived-label" title="Quality model notes (reasons for lower confidence).">Notes</div>
            <div class="derived-value">
              {#if history.current.quality?.notes?.length}
                {history.current.quality.notes.join(', ')}
              {:else}
                —
              {/if}
            </div>
          </div>
        </div>
      </div>

      <div class="panel-note">
        History points are stored persistently in the server database (minute-rounded).
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

  .title-row {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .item-icon {
    width: 28px;
    height: 28px;
    border-radius: 8px;
    flex: 0 0 auto;
    image-rendering: pixelated;
    border: 1px solid color-mix(in srgb, var(--theme-surface-border) 65%, transparent);
    background: color-mix(in srgb, var(--theme-surface) 70%, transparent);
  }

  .item-icon.placeholder {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 18px;
    line-height: 1;
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
    position: relative;
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

  .axis {
    stroke: color-mix(in srgb, var(--theme-surface-border) 75%, transparent);
    stroke-width: 1;
    vector-effect: non-scaling-stroke;
  }

  .grid {
    stroke: color-mix(in srgb, var(--theme-surface-border) 55%, transparent);
    stroke-width: 1;
    opacity: 0.7;
    vector-effect: non-scaling-stroke;
  }

  .hover-line {
    stroke: color-mix(in srgb, var(--theme-accent) 45%, var(--theme-surface-border) 55%);
    stroke-width: 1;
    opacity: 0.9;
    vector-effect: non-scaling-stroke;
  }

  .hover-dot {
    stroke: color-mix(in srgb, var(--theme-surface) 40%, transparent);
    stroke-width: 1;
  }

  .hover-dot.buy {
    fill: var(--theme-accent);
  }

  .hover-dot.sell {
    fill: color-mix(in srgb, var(--theme-text-primary) 70%, var(--theme-accent) 30%);
  }

  .chart-tooltip {
    position: absolute;
    width: 220px;
    padding: 10px 10px;
    border-radius: 12px;
    border: 1px solid color-mix(in srgb, var(--theme-surface-border) 80%, transparent);
    background: color-mix(in srgb, var(--theme-surface) 96%, transparent);
    box-shadow: var(--neu-elevated);
    pointer-events: none;
    color: var(--theme-text-primary);
  }

  .tt-title {
    font-size: 12px;
    font-weight: 800;
    margin-bottom: 6px;
  }

  .tt-row {
    display: flex;
    justify-content: space-between;
    gap: 10px;
    font-size: 12px;
    margin: 2px 0;
  }

  .tt-k {
    color: var(--theme-text-soft);
    font-weight: 700;
  }

  .tt-v {
    font-weight: 800;
  }

  .tt-foot {
    margin-top: 6px;
    font-size: 11px;
    color: var(--theme-text-soft);
    line-height: 1.25;
  }

  .tick {
    stroke: color-mix(in srgb, var(--theme-surface-border) 70%, transparent);
    stroke-width: 1;
    vector-effect: non-scaling-stroke;
  }

  .axis-text {
    fill: var(--theme-text-soft);
    font-size: 10px;
  }

  .axis-title {
    fill: var(--theme-text-soft);
    font-size: 11px;
    font-weight: 600;
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

  .derived {
    margin-top: 14px;
    border: 1px solid color-mix(in srgb, var(--theme-surface-border) 70%, transparent);
    border-radius: 14px;
    padding: 12px;
    background: color-mix(in srgb, var(--theme-surface) 92%, transparent);
  }

  .derived-row {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 10px 14px;
  }

  @media (max-width: 900px) {
    .derived-row {
      grid-template-columns: 1fr;
    }
  }

  .derived-item {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .derived-label {
    color: var(--theme-text-soft);
    font-size: 12px;
  }

  .derived-value {
    color: var(--theme-text-primary);
    font-size: 13px;
    font-weight: 600;
    word-break: break-word;
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
