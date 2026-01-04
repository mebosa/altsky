<script lang="ts">
  import { onMount } from 'svelte';
  import { get } from '$lib/api';
  import { texturePackStore } from '$lib/stores/texturePack';
  import {
    loadHypixelItems,
    getItemTextureUrl,
    itemsLoaded,
    loadItemTextures,
    furfskyCacheLoaded,
    vanillaCacheLoaded
  } from '$lib/stores/hypixelItems';

  interface FlipScore {
    score: number;
    label: string;
    profit_potential: number;
    profit_percent: number;
    volume_factor: number;
    stability_factor: number;
  }

  interface AuctionFlip {
    item_name: string;
    tier: string;
    category: string;
    lowest_price: number;
    avg_price: number;
    median_price: number;
    profit: number;
    profit_percent: number;
    volume: number;
    flip_score: FlipScore;
    auction_uuid: string;
    seller: string;
    end_time: number;
    lore: string;
  }

  interface SearchItem {
    tag: string;
    name: string;
    tier: string;
    category: string;
    icon: string | null;
    price: {
      buy?: number;
      sell?: number;
      median?: number;
      mean?: number;
      volume?: number;
    } | null;
  }

  interface ItemDetails {
    item_id: string;
    name: string;
    statistics: {
      avg_price: number;
      median_price: number;
      min_price: number;
      max_price: number;
      sample_size: number;
    };
    current_lowest_bin: number | null;
    recent_sales: Array<{
      price: number;
      timestamp: number;
      buyer?: string;
    }>;
    lowball_target: number | null;
    flip_target: number | null;
  }

  let activeTab: 'flips' | 'search' | 'details' = 'flips';
  let isLoading = true;
  let error = '';
  let lastUpdated = '';

  // Flips tab state
  let flips: AuctionFlip[] = [];
  let minProfit = 100000;
  let minProfitPercent = 10;
  let sortBy = 'profit';

  // Search tab state
  let searchQuery = '';
  let searchResults: SearchItem[] = [];
  let isSearching = false;

  // Details tab state
  let selectedItem: ItemDetails | null = null;
  let isLoadingDetails = false;

  $: itemsReady = $itemsLoaded;
  $: texturesCacheReady = $texturePackStore === 'furfsky' ? $furfskyCacheLoaded : $vanillaCacheLoaded;

  const tierColors: Record<string, string> = {
    COMMON: '#AAAAAA',
    UNCOMMON: '#55FF55',
    RARE: '#5555FF',
    EPIC: '#AA00AA',
    LEGENDARY: '#FFAA00',
    MYTHIC: '#FF55FF',
    DIVINE: '#55FFFF',
    SPECIAL: '#FF5555',
    VERY_SPECIAL: '#FF5555',
    SUPREME: '#55FFFF',
  };

  const sortOptions = [
    { value: 'profit', label: 'Profit' },
    { value: 'profit_percent', label: 'Profit %' },
    { value: 'score', label: 'Score' },
    { value: 'volume', label: 'Volume' },
  ];

  async function fetchFlips(refresh = false) {
    isLoading = true;
    error = '';
    
    try {
      const params: Record<string, string> = {
        limit: '100',
        min_profit: String(minProfit),
        min_profit_percent: String(minProfitPercent),
      };
      if (refresh) params.refresh = '1';
      
      const data = await get<{
        success: boolean;
        flips: AuctionFlip[];
        last_updated: string;
      }>('/api/auction/flips', { query: params });
      
      if (data.success) {
        flips = data.flips;
        lastUpdated = new Date(data.last_updated).toLocaleString('en-US', {
          year: 'numeric',
          month: 'short',
          day: '2-digit',
          hour: '2-digit',
          minute: '2-digit',
        });
        sortFlips();
      } else {
        error = 'Failed to fetch auction data';
      }
    } catch (err) {
      error = err instanceof Error ? err.message : 'Failed to fetch auction data';
    } finally {
      isLoading = false;
    }
  }

  function sortFlips() {
    const sortKeys: Record<string, (x: AuctionFlip) => number> = {
      profit: (x) => x.profit,
      profit_percent: (x) => x.profit_percent,
      score: (x) => x.flip_score?.score || 0,
      volume: (x) => x.volume,
    };
    const keyFn = sortKeys[sortBy] || sortKeys.profit;
    flips = [...flips].sort((a, b) => keyFn(b) - keyFn(a));
  }

  async function handleSearch() {
    if (!searchQuery.trim() || searchQuery.length < 2) return;
    
    isSearching = true;
    error = '';
    
    try {
      const data = await get<{
        success: boolean;
        items: SearchItem[];
      }>('/api/auction/search', { query: { query: searchQuery, limit: '30' } });
      
      if (data.success) {
        searchResults = data.items;
      }
    } catch (err) {
      error = err instanceof Error ? err.message : 'Search failed';
    } finally {
      isSearching = false;
    }
  }

  async function loadItemDetails(itemTag: string) {
    isLoadingDetails = true;
    activeTab = 'details';
    
    try {
      const data = await get<ItemDetails & { success: boolean }>(`/api/auction/item/${encodeURIComponent(itemTag)}`);
      
      if (data.success) {
        selectedItem = data;
      }
    } catch (err) {
      error = err instanceof Error ? err.message : 'Failed to load item details';
    } finally {
      isLoadingDetails = false;
    }
  }

  function formatNumber(num: number): string {
    if (num >= 1_000_000_000) return (num / 1_000_000_000).toFixed(2) + 'B';
    if (num >= 1_000_000) return (num / 1_000_000).toFixed(2) + 'M';
    if (num >= 1_000) return (num / 1_000).toFixed(2) + 'K';
    return num.toLocaleString();
  }

  function formatCoins(num: number): string {
    return num.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 });
  }

  function getScoreColor(label: string): string {
    switch (label) {
      case 'Excellent': return '#4ade80';
      case 'Good': return '#a3e635';
      case 'Fair': return '#fbbf24';
      case 'Low': return '#fb923c';
      default: return '#f87171';
    }
  }

  function getTierColor(tier: string): string {
    return tierColors[tier] || tierColors.COMMON;
  }

  function handleSort(newSort: string) {
    sortBy = newSort;
    sortFlips();
  }

  function onSearchKey(event: KeyboardEvent) {
    if (event.key === 'Enter') {
      handleSearch();
    }
  }

  onMount(() => {
    loadHypixelItems();
    fetchFlips();
  });

  function getItemIcon(itemName: string): string | null {
    void texturesCacheReady;
    const itemId = itemName.toUpperCase().replace(/\s+/g, '_');
    return getItemTextureUrl(itemId, $texturePackStore);
  }

  let failedImages = new Set<string>();

  function handleImageError(event: Event, itemId: string) {
    failedImages.add(itemId);
    failedImages = failedImages;
  }

  function getFallbackEmoji(tier: string): string {
    switch (tier) {
      case 'MYTHIC': return '💎';
      case 'LEGENDARY': return '⭐';
      case 'EPIC': return '💜';
      case 'RARE': return '💙';
      case 'UNCOMMON': return '💚';
      default: return '📦';
    }
  }
</script>

<svelte:head>
  <title>Auction Helper · AltSky (경매 시세 / 拍卖助手)</title>
  <meta name="description" content="Hypixel SkyBlock Auction price tracker and lowballing helper. Find underpriced items and flip for profit. 하이픽셀 스카이블럭 경매 시세, lowballing 도우미." />
</svelte:head>

<div class="wrap">
  <div class="header">
    <div class="header-main">
      <a href="/" class="back-link">← Back</a>
      <div class="title-section">
        <h1>Auction Helper</h1>
        <p class="muted">Find underpriced auctions and flip for profit (Coflnet-style)</p>
      </div>
    </div>
    {#if lastUpdated}
      <span class="badge">Updated: {lastUpdated}</span>
    {/if}
  </div>

  <div class="tabs">
    <button
      class="tab"
      class:active={activeTab === 'flips'}
      on:click={() => { activeTab = 'flips'; if (flips.length === 0) fetchFlips(); }}
    >
      🔥 Flip Finder
    </button>
    <button
      class="tab"
      class:active={activeTab === 'search'}
      on:click={() => { activeTab = 'search'; }}
    >
      🔍 Item Search
    </button>
    {#if selectedItem}
      <button
        class="tab"
        class:active={activeTab === 'details'}
        on:click={() => { activeTab = 'details'; }}
      >
        📊 {selectedItem.name}
      </button>
    {/if}
  </div>

  {#if error}
    <div class="error-message">{error}</div>
  {/if}

  {#if activeTab === 'flips'}
    <div class="controls panel">
      <div class="control-row">
        <div class="control-group">
          <span class="control-label">Min Profit</span>
          <input
            type="number"
            class="control-input"
            bind:value={minProfit}
            min="0"
            step="10000"
          />
        </div>
        <div class="control-group">
          <span class="control-label">Min %</span>
          <input
            type="number"
            class="control-input small"
            bind:value={minProfitPercent}
            min="0"
            max="100"
          />
        </div>
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
        <button type="button" class="refresh-btn" on:click={() => fetchFlips(true)} disabled={isLoading}>
          {isLoading ? 'Loading...' : 'Refresh'}
        </button>
      </div>
    </div>

    {#if isLoading && flips.length === 0}
      <div class="panel loading-panel">
        <div class="loading-spinner"></div>
        <p>Loading auction data...</p>
      </div>
    {:else if flips.length === 0}
      <div class="panel empty-panel">
        <p>No flip opportunities found. Try lowering the minimum profit threshold.</p>
      </div>
    {:else}
      <div class="table-container panel">
        <table class="flip-table">
          <thead>
            <tr>
              <th class="col-item">Item</th>
              <th class="col-price">Lowest BIN</th>
              <th class="col-price">Avg Price</th>
              <th class="col-margin">Profit</th>
              <th class="col-percent">Profit %</th>
              <th class="col-score">Score</th>
              <th class="col-volume">Volume</th>
            </tr>
          </thead>
          <tbody>
            {#each flips as flip}
              {@const iconSrc = getItemIcon(flip.item_name)}
              <tr on:click={() => loadItemDetails(flip.item_name.toUpperCase().replace(/\s+/g, '_'))}>
                <td class="col-item">
                  <span class="item-cell">
                    {#if iconSrc && !failedImages.has(flip.item_name)}
                      <img
                        class="item-icon"
                        src={iconSrc}
                        alt=""
                        loading="lazy"
                        on:error={(e) => handleImageError(e, flip.item_name)}
                      />
                    {:else}
                      <span class="item-icon placeholder">{getFallbackEmoji(flip.tier)}</span>
                    {/if}
                    <span class="item-info">
                      <span class="item-name" style="color: {getTierColor(flip.tier)}">{flip.item_name}</span>
                      <span class="item-tier">{flip.tier}</span>
                    </span>
                  </span>
                </td>
                <td class="col-price sell-price">{formatCoins(flip.lowest_price)}</td>
                <td class="col-price">{formatCoins(flip.avg_price)}</td>
                <td class="col-margin positive">+{formatCoins(flip.profit)}</td>
                <td class="col-percent positive">+{flip.profit_percent.toFixed(1)}%</td>
                <td class="col-score">
                  <span class="score-badge" style="background: {getScoreColor(flip.flip_score.label)}20; color: {getScoreColor(flip.flip_score.label)}">
                    {flip.flip_score.label}
                  </span>
                </td>
                <td class="col-volume">{flip.volume}</td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    {/if}
  {/if}

  {#if activeTab === 'search'}
    <div class="search-panel panel">
      <div class="search-row">
        <input
          type="text"
          class="search-input"
          placeholder="Search for an item (e.g. Hyperion, Shadow Fury...)"
          bind:value={searchQuery}
          on:keydown={onSearchKey}
        />
        <button
          type="button"
          class="refresh-btn"
          on:click={handleSearch}
          disabled={isSearching || searchQuery.length < 2}
        >
          {isSearching ? 'Searching...' : 'Search'}
        </button>
      </div>

      {#if searchResults.length > 0}
        <div class="search-results">
          {#each searchResults as item}
            <button
              class="search-result-card"
              on:click={() => loadItemDetails(item.tag)}
            >
              <div class="result-header">
                <span class="result-name" style="color: {getTierColor(item.tier)}">{item.name}</span>
                <span class="result-tier">{item.tier}</span>
              </div>
              {#if item.price}
                <div class="result-prices">
                  {#if item.price.median}
                    <span class="result-price">Median: {formatCoins(item.price.median)}</span>
                  {/if}
                  {#if item.price.volume}
                    <span class="result-volume">Vol: {formatNumber(item.price.volume)}</span>
                  {/if}
                </div>
              {:else}
                <span class="result-no-data">No price data</span>
              {/if}
            </button>
          {/each}
        </div>
      {:else if searchQuery && !isSearching}
        <div class="empty-panel">
          <p>No items found. Try a different search term.</p>
        </div>
      {/if}
    </div>
  {/if}

  {#if activeTab === 'details'}
    {#if isLoadingDetails}
      <div class="panel loading-panel">
        <div class="loading-spinner"></div>
        <p>Loading item details...</p>
      </div>
    {:else if selectedItem}
      <div class="details-panel panel">
        <div class="details-header">
          <h2>{selectedItem.name}</h2>
          <button class="close-btn" on:click={() => { selectedItem = null; activeTab = 'search'; }}>×</button>
        </div>

        <div class="details-grid">
          <div class="stat-card">
            <span class="stat-label">Current Lowest BIN</span>
            <span class="stat-value highlight">
              {selectedItem.current_lowest_bin ? formatCoins(selectedItem.current_lowest_bin) : 'N/A'}
            </span>
          </div>
          <div class="stat-card">
            <span class="stat-label">Average Price</span>
            <span class="stat-value">{formatCoins(selectedItem.statistics.avg_price)}</span>
          </div>
          <div class="stat-card">
            <span class="stat-label">Median Price</span>
            <span class="stat-value">{formatCoins(selectedItem.statistics.median_price)}</span>
          </div>
          <div class="stat-card">
            <span class="stat-label">Sample Size</span>
            <span class="stat-value">{selectedItem.statistics.sample_size} sales</span>
          </div>
        </div>

        <div class="lowball-section">
          <h3>💰 Lowballing Targets</h3>
          <div class="target-grid">
            <div class="target-card good">
              <span class="target-label">Flip Target (15% margin)</span>
              <span class="target-value">
                {selectedItem.flip_target ? formatCoins(selectedItem.flip_target) : 'N/A'}
              </span>
              <span class="target-hint">Buy below this for quick profit</span>
            </div>
            <div class="target-card excellent">
              <span class="target-label">Lowball Target (30% margin)</span>
              <span class="target-value">
                {selectedItem.lowball_target ? formatCoins(selectedItem.lowball_target) : 'N/A'}
              </span>
              <span class="target-hint">Maximum lowball offer</span>
            </div>
          </div>
        </div>

        <div class="price-range">
          <h3>📊 Price Range (Recent Sales)</h3>
          <div class="range-bar">
            <span class="range-min">Min: {formatCoins(selectedItem.statistics.min_price)}</span>
            <div class="range-visual">
              <div class="range-fill"></div>
            </div>
            <span class="range-max">Max: {formatCoins(selectedItem.statistics.max_price)}</span>
          </div>
        </div>

        {#if selectedItem.recent_sales.length > 0}
          <div class="recent-sales">
            <h3>🕐 Recent Sales</h3>
            <div class="sales-list">
              {#each selectedItem.recent_sales.slice(0, 10) as sale}
                <div class="sale-item">
                  <span class="sale-price">{formatCoins(sale.price)}</span>
                  <span class="sale-time">
                    {sale.timestamp ? new Date(sale.timestamp).toLocaleString() : 'Unknown'}
                  </span>
                </div>
              {/each}
            </div>
          </div>
        {/if}
      </div>
    {/if}
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
  }

  .muted {
    color: var(--theme-text-soft);
    margin: 0;
    font-size: 14px;
  }

  .badge {
    display: inline-flex;
    align-items: center;
    padding: 8px 12px;
    border-radius: 10px;
    border: 1px solid color-mix(in srgb, var(--theme-accent) 40%, #ffffff 10%);
    color: var(--theme-text-primary);
    background: color-mix(in srgb, var(--theme-accent-alpha-22) 60%, transparent);
    font-size: 12px;
    font-weight: 500;
  }

  .tabs {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
  }

  .tab {
    padding: 10px 18px;
    border-radius: 10px;
    border: 1px solid color-mix(in srgb, var(--theme-surface-border) 80%, transparent);
    background: color-mix(in srgb, var(--theme-surface) 96%, transparent);
    color: var(--theme-text-primary);
    font-weight: 600;
    font-size: 14px;
    cursor: pointer;
    transition: all 0.2s;
  }

  .tab:hover {
    background: color-mix(in srgb, var(--theme-accent-alpha-22) 60%, transparent);
  }

  .tab.active {
    background: var(--theme-accent);
    color: #0b1020;
    border-color: var(--theme-accent);
  }

  .panel {
    border: 1px solid color-mix(in srgb, var(--theme-surface-border) 80%, transparent);
    border-radius: 16px;
    background: color-mix(in srgb, var(--theme-surface) 96%, transparent);
    padding: 18px;
    box-shadow: var(--neu-elevated);
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
    justify-content: flex-start;
    gap: 20px;
    flex-wrap: wrap;
  }

  .control-group {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .control-label {
    font-size: 13px;
    font-weight: 600;
    color: var(--theme-text-soft);
  }

  .control-input {
    padding: 8px 12px;
    border-radius: 8px;
    border: 1px solid var(--theme-surface-border);
    background: var(--theme-form-bg);
    color: var(--theme-text-primary);
    font-size: 14px;
    width: 120px;
  }

  .control-input.small {
    width: 70px;
  }

  .chips {
    display: flex;
    gap: 6px;
  }

  .chip {
    padding: 6px 12px;
    border-radius: 8px;
    background: color-mix(in srgb, var(--theme-chip-bg) 95%, transparent);
    border: 1px solid var(--theme-chip-border);
    color: var(--theme-chip-text);
    font-size: 12px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
  }

  .chip:hover {
    background: color-mix(in srgb, var(--theme-accent-alpha-25) 70%, transparent);
  }

  .chip.active {
    background: var(--theme-accent);
    color: #0b1020;
  }

  .refresh-btn {
    padding: 10px 18px;
    border-radius: 10px;
    border: 1px solid var(--theme-accent);
    background: var(--theme-accent);
    color: #0b1020;
    font-weight: 600;
    font-size: 13px;
    cursor: pointer;
    transition: all 0.2s;
    margin-left: auto;
  }

  .refresh-btn:hover:not(:disabled) {
    transform: translateY(-1px);
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
    background: color-mix(in srgb, var(--theme-surface) 80%, transparent);
    position: sticky;
    top: 0;
  }

  .flip-table tbody tr {
    transition: background 0.15s ease;
    cursor: pointer;
  }

  .flip-table tbody tr:hover {
    background: color-mix(in srgb, var(--theme-accent-alpha-22) 30%, transparent);
  }

  .col-item {
    min-width: 200px;
  }

  .item-cell {
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .item-icon {
    width: 28px;
    height: 28px;
    border-radius: 6px;
    image-rendering: pixelated;
    border: 1px solid var(--theme-surface-border);
    background: var(--theme-surface);
  }

  .item-icon.placeholder {
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 16px;
  }

  .item-info {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .item-name {
    font-weight: 600;
  }

  .item-tier {
    font-size: 11px;
    color: var(--theme-text-soft);
    text-transform: uppercase;
  }

  .col-price,
  .col-margin,
  .col-percent,
  .col-volume,
  .col-score {
    text-align: right;
    font-variant-numeric: tabular-nums;
  }

  .positive { color: #4ade80; }
  .sell-price { color: #fbbf24; }

  .score-badge {
    padding: 4px 8px;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 600;
  }

  /* Search styles */
  .search-panel {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .search-row {
    display: flex;
    gap: 12px;
  }

  .search-input {
    flex: 1;
    padding: 12px 16px;
    border-radius: 10px;
    border: 1px solid var(--theme-form-border);
    background: var(--theme-form-bg);
    color: var(--theme-text-primary);
    font-size: 15px;
  }

  .search-input:focus {
    outline: none;
    border-color: var(--theme-accent);
  }

  .search-results {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 12px;
  }

  .search-result-card {
    padding: 14px;
    border-radius: 12px;
    border: 1px solid var(--theme-surface-border);
    background: var(--theme-surface);
    cursor: pointer;
    transition: all 0.2s;
    text-align: left;
  }

  .search-result-card:hover {
    border-color: var(--theme-accent);
    transform: translateY(-2px);
  }

  .result-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
  }

  .result-name {
    font-weight: 600;
    font-size: 14px;
  }

  .result-tier {
    font-size: 11px;
    color: var(--theme-text-soft);
    text-transform: uppercase;
  }

  .result-prices {
    display: flex;
    gap: 12px;
    font-size: 13px;
    color: var(--theme-text-soft);
  }

  .result-no-data {
    font-size: 12px;
    color: var(--theme-text-soft);
  }

  /* Details styles */
  .details-panel {
    display: flex;
    flex-direction: column;
    gap: 24px;
  }

  .details-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .details-header h2 {
    margin: 0;
    font-size: 24px;
  }

  .close-btn {
    width: 32px;
    height: 32px;
    border-radius: 8px;
    border: 1px solid var(--theme-surface-border);
    background: transparent;
    color: var(--theme-text-soft);
    font-size: 20px;
    cursor: pointer;
    transition: all 0.2s;
  }

  .close-btn:hover {
    background: rgba(239, 68, 68, 0.2);
    color: #f87171;
  }

  .details-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 12px;
  }

  .stat-card {
    padding: 16px;
    border-radius: 12px;
    background: color-mix(in srgb, var(--theme-surface) 80%, transparent);
    border: 1px solid var(--theme-surface-border);
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .stat-label {
    font-size: 12px;
    color: var(--theme-text-soft);
    text-transform: uppercase;
  }

  .stat-value {
    font-size: 20px;
    font-weight: 700;
    font-variant-numeric: tabular-nums;
  }

  .stat-value.highlight {
    color: #4ade80;
  }

  .lowball-section h3,
  .price-range h3,
  .recent-sales h3 {
    margin: 0 0 12px;
    font-size: 16px;
  }

  .target-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 12px;
  }

  .target-card {
    padding: 16px;
    border-radius: 12px;
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .target-card.good {
    background: rgba(74, 222, 128, 0.1);
    border: 1px solid rgba(74, 222, 128, 0.3);
  }

  .target-card.excellent {
    background: rgba(251, 191, 36, 0.1);
    border: 1px solid rgba(251, 191, 36, 0.3);
  }

  .target-label {
    font-size: 12px;
    color: var(--theme-text-soft);
  }

  .target-value {
    font-size: 24px;
    font-weight: 700;
    color: #4ade80;
  }

  .target-card.excellent .target-value {
    color: #fbbf24;
  }

  .target-hint {
    font-size: 11px;
    color: var(--theme-text-soft);
  }

  .price-range {
    padding: 16px;
    background: color-mix(in srgb, var(--theme-surface) 80%, transparent);
    border-radius: 12px;
  }

  .range-bar {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .range-min,
  .range-max {
    font-size: 13px;
    color: var(--theme-text-soft);
    white-space: nowrap;
  }

  .range-visual {
    flex: 1;
    height: 8px;
    background: var(--theme-surface-border);
    border-radius: 4px;
    overflow: hidden;
  }

  .range-fill {
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, #4ade80, #fbbf24, #f87171);
    border-radius: 4px;
  }

  .sales-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
    max-height: 300px;
    overflow-y: auto;
  }

  .sale-item {
    display: flex;
    justify-content: space-between;
    padding: 10px 12px;
    background: color-mix(in srgb, var(--theme-surface) 80%, transparent);
    border-radius: 8px;
  }

  .sale-price {
    font-weight: 600;
    color: #4ade80;
  }

  .sale-time {
    font-size: 12px;
    color: var(--theme-text-soft);
  }

  @media (max-width: 768px) {
    .control-row {
      flex-direction: column;
      align-items: stretch;
    }

    .control-group {
      flex-wrap: wrap;
    }

    .refresh-btn {
      margin-left: 0;
      width: 100%;
    }

    .search-row {
      flex-direction: column;
    }
  }
</style>
