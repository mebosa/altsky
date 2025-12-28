<script lang="ts">
  import { onMount } from 'svelte';
  import { get } from '$lib/api';

  interface FlipRecommendation {
    product_id: string;
    name: string;
    buy_price: number;
    sell_price: number;
    margin: number;
    margin_percent: number;
    buy_volume: number;
    sell_volume: number;
    buy_orders: number;
    sell_orders: number;
    potential_profit: number;
  }

  interface BazaarResponse {
    success: boolean;
    recommendations: FlipRecommendation[];
    last_updated: string;
    total_products: number;
  }

  let recommendations: FlipRecommendation[] = [];
  let isLoading = true;
  let error = '';
  let lastUpdated = '';
  let sortBy = 'margin_percent';
  let limit = 20;

  const sortOptions = [
    { value: 'margin_percent', label: 'Margin %' },
    { value: 'margin', label: 'Margin' },
    { value: 'profit', label: 'Profit' },
    { value: 'volume', label: 'Volume' },
  ];

  async function fetchFlips(refresh = false) {
    isLoading = true;
    error = '';
    
    try {
      const params: Record<string, string> = {
        limit: String(limit),
        sort: sortBy,
      };
      if (refresh) params.refresh = '1';
      
      const data = await get<BazaarResponse>('/api/bazaar/flips', { query: params });
      
      if (data.success) {
        recommendations = data.recommendations;
        lastUpdated = new Date(data.last_updated).toLocaleString();
      } else {
        error = 'Failed to fetch bazaar data';
      }
    } catch (err) {
      error = err instanceof Error ? err.message : 'Failed to fetch bazaar data';
    } finally {
      isLoading = false;
    }
  }

  function formatNumber(num: number): string {
    if (num >= 1_000_000_000) return (num / 1_000_000_000).toFixed(2) + 'B';
    if (num >= 1_000_000) return (num / 1_000_000).toFixed(2) + 'M';
    if (num >= 1_000) return (num / 1_000).toFixed(2) + 'K';
    return num.toLocaleString();
  }

  function formatCoins(num: number): string {
    return num.toLocaleString(undefined, { minimumFractionDigits: 1, maximumFractionDigits: 1 });
  }

  function handleSort(newSort: string) {
    sortBy = newSort;
    fetchFlips();
  }

  function handleRefresh() {
    fetchFlips(true);
  }

  onMount(() => {
    fetchFlips();
  });
</script>

<svelte:head>
  <title>Bazaar Flips · AltSky</title>
  <meta name="description" content="Hypixel SkyBlock Bazaar flip recommendations" />
</svelte:head>

<div class="wrap">
  <div class="header">
    <div class="header-main">
      <a href="/" class="back-link">← Back</a>
      <div class="title-section">
        <h1>Bazaar Flips</h1>
        <p class="muted">Real-time flip recommendations based on Hypixel Bazaar data</p>
      </div>
    </div>
    {#if lastUpdated}
      <span class="badge">Updated: {lastUpdated}</span>
    {/if}
  </div>

  <div class="controls panel">
    <div class="control-row">
      <div class="control-group">
        <span class="control-label">Sort by</span>
        <div class="chips">
          {#each sortOptions as option}
            <button
              type="button"
              class="chip"
              class:active={sortBy === option.value}
              on:click={() => handleSort(option.value)}
            >
              {option.label}
            </button>
          {/each}
        </div>
      </div>
      <button type="button" class="refresh-btn" on:click={handleRefresh} disabled={isLoading}>
        {isLoading ? 'Loading...' : 'Refresh'}
      </button>
    </div>
  </div>

  {#if error}
    <div class="error-message">
      {error}
    </div>
  {/if}

  {#if isLoading && recommendations.length === 0}
    <div class="panel loading-panel">
      <div class="loading-spinner"></div>
      <p>Loading bazaar data...</p>
    </div>
  {:else if recommendations.length === 0}
    <div class="panel empty-panel">
      <p>No flip recommendations available at the moment.</p>
    </div>
  {:else}
    <div class="table-container panel">
      <table class="flip-table">
        <thead>
          <tr>
            <th class="col-item">Item</th>
            <th class="col-price">Buy (Instant)</th>
            <th class="col-price">Sell (Instant)</th>
            <th class="col-margin">Margin</th>
            <th class="col-percent">Margin %</th>
            <th class="col-volume">Buy Vol</th>
            <th class="col-volume">Sell Vol</th>
          </tr>
        </thead>
        <tbody>
          {#each recommendations as item}
            <tr>
              <td class="col-item">
                <span class="item-name">{item.name}</span>
              </td>
              <td class="col-price buy-price">{formatCoins(item.buy_price)}</td>
              <td class="col-price sell-price">{formatCoins(item.sell_price)}</td>
              <td class="col-margin" class:positive={item.margin > 0} class:negative={item.margin < 0}>
                {formatCoins(item.margin)}
              </td>
              <td class="col-percent" class:positive={item.margin_percent > 0} class:negative={item.margin_percent < 0}>
                {item.margin_percent.toFixed(2)}%
              </td>
              <td class="col-volume">{formatNumber(item.buy_volume)}</td>
              <td class="col-volume">{formatNumber(item.sell_volume)}</td>
            </tr>
          {/each}
        </tbody>
      </table>
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
    backdrop-filter: blur(14px);
  }

  .controls {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .control-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    flex-wrap: wrap;
  }

  .control-group {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .control-label {
    font-size: 13px;
    font-weight: 600;
    color: var(--theme-text-soft);
  }

  .chips {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
  }

  .chip {
    padding: 6px 12px;
    border-radius: 10px;
    background: color-mix(in srgb, var(--theme-chip-bg) 95%, transparent);
    border: 1px solid color-mix(in srgb, var(--theme-chip-border) 90%, transparent);
    cursor: pointer;
    transition: background 0.2s ease, border 0.2s ease, transform 0.15s ease;
    color: var(--theme-chip-text);
    font-size: 13px;
    font-weight: 500;
  }

  .chip:hover {
    transform: translateY(-1px);
    background: color-mix(in srgb, var(--theme-accent-alpha-25) 70%, transparent);
    border-color: color-mix(in srgb, var(--theme-accent) 60%, #ffffff 10%);
  }

  .chip.active {
    background: color-mix(in srgb, var(--theme-accent) 90%, #ffffff 10%);
    border-color: var(--theme-accent);
    color: #0b1020;
  }

  .refresh-btn {
    padding: 10px 18px;
    border-radius: 10px;
    border: 1px solid color-mix(in srgb, var(--theme-accent) 70%, #ffffff 10%);
    background: color-mix(in srgb, var(--theme-accent) 95%, #0b1020 5%);
    color: #0b1020;
    cursor: pointer;
    font-weight: 600;
    font-size: 13px;
    transition: transform 0.2s ease, box-shadow 0.2s ease, opacity 0.2s ease;
  }

  .refresh-btn:hover:not(:disabled) {
    transform: translateY(-1px);
    box-shadow: 0 8px 20px rgba(5, 7, 14, 0.3);
  }

  .refresh-btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .error-message {
    padding: 12px 14px;
    background: rgba(239, 68, 68, 0.12);
    border: 1px solid rgba(239, 68, 68, 0.24);
    color: rgb(248, 180, 180);
    border-radius: 10px;
    font-size: 0.94rem;
  }

  .loading-panel,
  .empty-panel {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 12px;
    padding: 48px 24px;
    text-align: center;
    color: var(--theme-text-soft);
  }

  .loading-spinner {
    width: 32px;
    height: 32px;
    border: 3px solid color-mix(in srgb, var(--theme-accent) 30%, transparent);
    border-top-color: var(--theme-accent);
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
  }

  .table-container {
    overflow-x: auto;
    padding: 0;
  }

  .flip-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 14px;
  }

  .flip-table th,
  .flip-table td {
    padding: 12px 14px;
    text-align: left;
    border-bottom: 1px solid color-mix(in srgb, var(--theme-surface-border) 50%, transparent);
  }

  .flip-table th {
    font-size: 12px;
    font-weight: 600;
    color: var(--theme-text-soft);
    text-transform: uppercase;
    letter-spacing: 0.04em;
    background: color-mix(in srgb, var(--theme-surface) 80%, transparent);
    position: sticky;
    top: 0;
  }

  .flip-table tbody tr {
    transition: background 0.15s ease;
  }

  .flip-table tbody tr:hover {
    background: color-mix(in srgb, var(--theme-accent-alpha-22) 30%, transparent);
  }

  .flip-table tbody tr:last-child td {
    border-bottom: none;
  }

  .col-item {
    min-width: 180px;
  }

  .item-name {
    font-weight: 500;
    color: var(--theme-text-primary);
  }

  .col-price,
  .col-margin,
  .col-percent,
  .col-volume {
    text-align: right;
    font-variant-numeric: tabular-nums;
  }

  .buy-price {
    color: #f87171;
  }

  .sell-price {
    color: #4ade80;
  }

  .positive {
    color: #4ade80;
  }

  .negative {
    color: #f87171;
  }

  @media (max-width: 768px) {
    .wrap {
      margin-top: 24px;
    }

    .control-row {
      flex-direction: column;
      align-items: stretch;
    }

    .control-group {
      flex-direction: column;
      align-items: flex-start;
    }

    .refresh-btn {
      width: 100%;
    }

    .flip-table {
      font-size: 12px;
    }

    .flip-table th,
    .flip-table td {
      padding: 10px 8px;
    }

    .col-item {
      min-width: 120px;
    }
  }
</style>
