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
  import MinecraftSlot from '$lib/components/MinecraftSlot.svelte';
  import MinecraftTooltip from '$lib/components/MinecraftTooltip.svelte';

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

  let activeTab: 'search' | 'details' = 'search';
  let isLoading = true;
  let error = '';
  let lastUpdated = '';

  // Search tab state
  let searchQuery = '';
  let searchResults: SearchItem[] = [];
  let isSearching = false;

  // Details tab state
  let selectedItem: ItemDetails | null = null;
  let isLoadingDetails = false;

  let hoveredItem: any = null;
  let mouseX = 0;
  let mouseY = 0;

  function handleMouseMove(e: MouseEvent) {
    mouseX = e.clientX;
    mouseY = e.clientY;
  }

  $: displayItems = searchResults.map(item => ({
    ...item,
    tierColor: getTierColor(item.tier),
    lore: `§7Price: §6${item.price?.median ? formatCoins(item.price.median) : 'N/A'}\n§7Volume: §e${item.price?.volume || 0}`
  }));

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
    error = '';
    
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 15000); // 15s timeout

    try {
      console.log('Loading details for:', itemTag);
      const data = await get<ItemDetails & { success: boolean }>(
        `/api/auction/item/${encodeURIComponent(itemTag)}`,
        { signal: controller.signal }
      );
      
      if (data.success) {
        selectedItem = data;
      } else {
        error = 'Failed to load item data';
      }
    } catch (err) {
      console.error('Load details error:', err);
      if (err instanceof Error && err.name === 'AbortError') {
        error = 'Request timed out. The server took too long to respond.';
      } else {
        error = err instanceof Error ? err.message : 'Failed to load item details';
      }
    } finally {
      clearTimeout(timeoutId);
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

  function getTierColor(tier: string): string {
    return tierColors[tier] || tierColors.COMMON;
  }

  function onSearchKey(event: KeyboardEvent) {
    if (event.key === 'Enter') {
      handleSearch();
    }
  }

  onMount(() => {
    loadHypixelItems();
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
  <title>Hypixel SkyBlock Auction Prices & Lowballing Helper | AltSky</title>
  <meta name="description" content="Check Hypixel SkyBlock Auction prices, history, and lowballing margins. The best tool for auction flipping and price checking. 하이픽셀 스카이블럭 경매장 시세 및 로우볼 계산기." />
  <meta name="keywords" content="Hypixel SkyBlock Auction, Auction Prices, Price Checker, Lowballing Helper, Auction Flipping, SkyBlock Economy, AltSky, 하이픽셀 스카이블럭 경매장, 시세 확인, 로우볼, Hypixel空岛, 拍卖助手, 价格查询" />
</svelte:head>

<svelte:window on:mousemove={handleMouseMove} />

<div class="wrap">
  <div class="header">
    <div class="header-main">
      <a href="/" class="back-link">← Back</a>
      <div class="title-section">
        <h1>Auction Helper</h1>
        <p class="muted">Search for items and calculate lowballing prices.</p>
      </div>
    </div>
    {#if lastUpdated}
      <span class="badge">Updated: {lastUpdated}</span>
    {/if}
  </div>

  <div class="tabs">
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
        <div class="chest-gui">
          <div class="chest-grid">
            {#each displayItems as item}
              <MinecraftSlot 
                item={item} 
                on:click={() => loadItemDetails(item.tag)}
                on:mouseenter={() => hoveredItem = item}
                on:mouseleave={() => hoveredItem = null}
              />
            {/each}
          </div>
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
  {#if hoveredItem}
    <MinecraftTooltip item={hoveredItem} x={mouseX} y={mouseY} />
  {/if}
</div>

<style>
  .chest-gui {
    background-color: #c6c6c6;
    padding: 18px;
    border: 2px solid;
    border-color: #fff #555 #555 #fff;
    border-radius: 2px;
    box-shadow: 0 0 10px rgba(0,0,0,0.5);
    margin-top: 20px;
  }

  .chest-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, 48px);
    gap: 4px;
    justify-content: center;
  }

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
