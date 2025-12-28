<script lang="ts">
  import type { ProfileSummaryResponse, ShardsData } from './profileTypes';
  import { onMount } from 'svelte';
  import { formatNumber } from '$lib/utils';
  import { get } from '$lib/api';

  export let summary: ProfileSummaryResponse;

  // Bazaar shard data
  interface BazaarShard {
    id: string;
    name: string;
    buyPrice: number | null;
    sellPrice: number | null;
  }

  let bazaarShards: BazaarShard[] = [];
  let bazaarLoading = true;
  let searchQuery = '';
  let sortBy: 'name' | 'buyPrice' | 'sellPrice' = 'name';
  let sortAsc = true;

  $: shardsData = summary.shards as ShardsData | null;
  $: stats = shardsData?.stats;

  // Filter and sort shards
  $: filteredShards = (() => {
    let shards = [...bazaarShards];

    // Search filter
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      shards = shards.filter(s => s.name.toLowerCase().includes(query));
    }

    // Sort
    shards.sort((a, b) => {
      let cmp = 0;
      if (sortBy === 'name') {
        cmp = a.name.localeCompare(b.name);
      } else if (sortBy === 'buyPrice') {
        const aPrice = a.buyPrice ?? Infinity;
        const bPrice = b.buyPrice ?? Infinity;
        cmp = aPrice - bPrice;
      } else if (sortBy === 'sellPrice') {
        const aPrice = a.sellPrice ?? -Infinity;
        const bPrice = b.sellPrice ?? -Infinity;
        cmp = bPrice - aPrice;
      }
      return sortAsc ? cmp : -cmp;
    });

    return shards;
  })();

  onMount(async () => {
    await loadBazaarShards();
  });

  async function loadBazaarShards() {
    bazaarLoading = true;
    try {
      const response = await get<{ products: Record<string, any> }>('/api/bazaar');
      if (response?.products) {
        const shards: BazaarShard[] = [];
        for (const [id, product] of Object.entries(response.products)) {
          // Filter only SHARD_ items (not PRISMARINE_SHARD, etc.)
          if (id.startsWith('SHARD_') || id === 'THUNDER_SHARDS') {
            const qs = product.quick_status || {};
            shards.push({
              id,
              name: formatShardName(id),
              buyPrice: qs.buyPrice ?? null,
              sellPrice: qs.sellPrice ?? null,
            });
          }
        }
        bazaarShards = shards;
      }
    } catch (e) {
      console.error('Failed to load bazaar shards:', e);
    } finally {
      bazaarLoading = false;
    }
  }

  function formatShardName(id: string): string {
    // SHARD_SALMON -> Salmon Shard
    // THUNDER_SHARDS -> Thunder Shards
    if (id === 'THUNDER_SHARDS') return 'Thunder Shards';
    return id
      .replace('SHARD_', '')
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
      .join(' ') + ' Shard';
  }

  function formatPrice(price: number | null | undefined): string {
    if (price == null) return 'N/A';
    if (price >= 1_000_000_000) {
      return `${(price / 1_000_000_000).toFixed(2)}B`;
    }
    if (price >= 1_000_000) {
      return `${(price / 1_000_000).toFixed(2)}M`;
    }
    if (price >= 1_000) {
      return `${(price / 1_000).toFixed(1)}K`;
    }
    return price.toFixed(0);
  }

  function toggleSort(field: 'name' | 'buyPrice' | 'sellPrice') {
    if (sortBy === field) {
      sortAsc = !sortAsc;
    } else {
      sortBy = field;
      sortAsc = field === 'name';
    }
  }

  function getItemUrl(id: string): string {
    return `https://sky.shiiyu.moe/item/${id}`;
  }
</script>

<section id="shards" class="shards-section">
  <h2>🔮 Shards</h2>
  
  <!-- Stats Overview -->
  {#if stats}
    <div class="stats-overview">
      <div class="stat-card">
        <div class="stat-value">{stats.unique_shards ?? stats.owned_count ?? 0}</div>
        <div class="stat-label">Unique Shards</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{bazaarShards.length || '...'}</div>
        <div class="stat-label">Total Available</div>
      </div>
      {#if stats.unique_shards > 0 && bazaarShards.length > 0}
        <div class="stat-card progress-card">
          <div class="stat-value">{Math.round((stats.unique_shards / bazaarShards.length) * 100)}%</div>
          <div class="stat-label">Progress</div>
          <div class="progress-bar">
            <div class="progress-fill" style="width: {(stats.unique_shards / bazaarShards.length) * 100}%"></div>
          </div>
        </div>
      {/if}
    </div>

    <!-- Hunt Stats -->
    {#if stats.hunts}
      <div class="hunt-stats">
        <h3>Hunt Statistics</h3>
        <div class="hunt-grid">
          <div class="hunt-item">
            <span class="hunt-icon">⚔️</span>
            <span class="hunt-value">{formatNumber(stats.hunts.combat)}</span>
            <span class="hunt-label">Combat</span>
          </div>
          <div class="hunt-item">
            <span class="hunt-icon">🎣</span>
            <span class="hunt-value">{formatNumber(stats.hunts.fishing)}</span>
            <span class="hunt-label">Fishing</span>
          </div>
          <div class="hunt-item">
            <span class="hunt-icon">🌲</span>
            <span class="hunt-value">{formatNumber(stats.hunts.forest)}</span>
            <span class="hunt-label">Forest</span>
          </div>
          <div class="hunt-item">
            <span class="hunt-icon">🪤</span>
            <span class="hunt-value">{formatNumber(stats.hunts.trap)}</span>
            <span class="hunt-label">Trap</span>
          </div>
          <div class="hunt-item">
            <span class="hunt-icon">🧂</span>
            <span class="hunt-value">{formatNumber(stats.hunts.salt)}</span>
            <span class="hunt-label">Salt</span>
          </div>
        </div>
      </div>
    {/if}
  {:else}
    <div class="no-data">
      <p>No shard hunting data available</p>
    </div>
  {/if}

  <!-- Bazaar Shards List -->
  <div class="bazaar-section">
    <h3>Bazaar Shard Prices</h3>
    <p class="section-desc">All tradeable shards from Galatea hunting. Click to view on SkyCrypt.</p>

    <div class="search-box">
      <input 
        type="text" 
        placeholder="Search shards..." 
        bind:value={searchQuery}
      />
    </div>

    {#if bazaarLoading}
      <div class="loading">Loading bazaar data...</div>
    {:else if filteredShards.length === 0}
      <div class="no-results">No shards found</div>
    {:else}
      <div class="shard-table-wrapper">
        <table class="shard-table">
          <thead>
            <tr>
              <th class="sortable" on:click={() => toggleSort('name')}>
                Shard {sortBy === 'name' ? (sortAsc ? '↑' : '↓') : ''}
              </th>
              <th class="sortable price-col" on:click={() => toggleSort('buyPrice')}>
                Buy {sortBy === 'buyPrice' ? (sortAsc ? '↑' : '↓') : ''}
              </th>
              <th class="sortable price-col" on:click={() => toggleSort('sellPrice')}>
                Sell {sortBy === 'sellPrice' ? (sortAsc ? '↑' : '↓') : ''}
              </th>
            </tr>
          </thead>
          <tbody>
            {#each filteredShards as shard}
              <tr>
                <td class="shard-name-cell">
                  <a href={getItemUrl(shard.id)} target="_blank" rel="noopener noreferrer">
                    <img 
                      src="https://sky.shiiyu.moe/item/{shard.id}"
                      alt=""
                      class="shard-icon"
                      loading="lazy"
                    />
                    <span>{shard.name}</span>
                  </a>
                </td>
                <td class="price-cell buy">
                  {formatPrice(shard.buyPrice)}
                </td>
                <td class="price-cell sell">
                  {formatPrice(shard.sellPrice)}
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
      <div class="shard-count">{filteredShards.length} shards</div>
    {/if}
  </div>
</section>

<style>
  .shards-section {
    padding: 20px 0;
  }

  h2 {
    font-size: 1.5rem;
    margin-bottom: 20px;
    color: var(--theme-text-primary);
  }

  h3 {
    font-size: 1.1rem;
    margin-bottom: 12px;
    color: var(--theme-text-primary);
  }

  .section-desc {
    font-size: 0.875rem;
    color: var(--theme-text-soft);
    margin-bottom: 16px;
  }

  .no-data, .no-results, .loading {
    text-align: center;
    padding: 40px;
    color: var(--theme-text-soft);
    background: var(--theme-surface);
    border-radius: 12px;
    border: 1px solid var(--theme-surface-border);
  }

  /* Stats Overview */
  .stats-overview {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 16px;
    margin-bottom: 24px;
  }

  .stat-card {
    background: var(--theme-surface);
    border: 1px solid var(--theme-surface-border);
    border-radius: 12px;
    padding: 16px;
    text-align: center;
  }

  .stat-value {
    font-size: 2rem;
    font-weight: 700;
    color: var(--theme-accent);
  }

  .stat-label {
    font-size: 0.875rem;
    color: var(--theme-text-soft);
    margin-top: 4px;
  }

  .progress-card .progress-bar {
    height: 6px;
    background: var(--theme-control-bg);
    border-radius: 3px;
    margin-top: 8px;
    overflow: hidden;
  }

  .progress-card .progress-fill {
    height: 100%;
    background: linear-gradient(90deg, var(--theme-accent), var(--theme-accent-secondary, var(--theme-accent)));
    border-radius: 3px;
    transition: width 0.3s ease;
  }

  /* Hunt Stats */
  .hunt-stats {
    background: var(--theme-surface);
    border: 1px solid var(--theme-surface-border);
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 24px;
  }

  .hunt-grid {
    display: flex;
    gap: 16px;
    flex-wrap: wrap;
  }

  .hunt-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 12px;
    background: var(--theme-control-bg);
    border-radius: 8px;
  }

  .hunt-icon {
    font-size: 1.25rem;
  }

  .hunt-value {
    font-weight: 600;
    color: var(--theme-text-primary);
  }

  .hunt-label {
    font-size: 0.875rem;
    color: var(--theme-text-soft);
  }

  /* Bazaar Section */
  .bazaar-section {
    background: var(--theme-surface);
    border: 1px solid var(--theme-surface-border);
    border-radius: 12px;
    padding: 20px;
  }

  .search-box input {
    width: 100%;
    max-width: 300px;
    padding: 8px 16px;
    border: 1px solid var(--theme-surface-border);
    background: var(--theme-control-bg);
    color: var(--theme-text-primary);
    border-radius: 8px;
    font-size: 0.875rem;
    margin-bottom: 16px;
  }

  .search-box input::placeholder {
    color: var(--theme-text-soft);
  }

  /* Table */
  .shard-table-wrapper {
    overflow-x: auto;
    max-height: 500px;
    overflow-y: auto;
  }

  .shard-table {
    width: 100%;
    border-collapse: collapse;
  }

  .shard-table thead {
    position: sticky;
    top: 0;
    background: var(--theme-surface);
    z-index: 1;
  }

  .shard-table th {
    text-align: left;
    padding: 12px 16px;
    border-bottom: 2px solid var(--theme-surface-border);
    font-size: 0.875rem;
    font-weight: 600;
    color: var(--theme-text-soft);
  }

  .shard-table th.sortable {
    cursor: pointer;
    user-select: none;
  }

  .shard-table th.sortable:hover {
    color: var(--theme-text-primary);
  }

  .shard-table th.price-col {
    text-align: right;
    width: 100px;
  }

  .shard-table td {
    padding: 10px 16px;
    border-bottom: 1px solid var(--theme-surface-border);
  }

  .shard-table tr:hover {
    background: var(--theme-control-bg);
  }

  .shard-name-cell a {
    display: flex;
    align-items: center;
    gap: 10px;
    color: var(--theme-text-primary);
    text-decoration: none;
  }

  .shard-name-cell a:hover {
    color: var(--theme-accent);
  }

  .shard-icon {
    width: 28px;
    height: 28px;
    image-rendering: pixelated;
    flex-shrink: 0;
  }

  .price-cell {
    text-align: right;
    font-family: monospace;
    font-size: 0.875rem;
  }

  .price-cell.buy {
    color: #ef4444;
  }

  .price-cell.sell {
    color: #22c55e;
  }

  .shard-count {
    margin-top: 12px;
    font-size: 0.875rem;
    color: var(--theme-text-soft);
    text-align: right;
  }

  @media (max-width: 768px) {
    .hunt-grid {
      flex-direction: column;
    }

    .stats-overview {
      grid-template-columns: repeat(2, 1fr);
    }

    .shard-table th.price-col,
    .shard-table td.price-cell {
      padding: 10px 8px;
    }
  }
</style>
