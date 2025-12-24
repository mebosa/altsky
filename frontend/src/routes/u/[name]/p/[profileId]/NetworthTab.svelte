<script lang="ts">
  import { formatLargeNumber, formatNumber } from '$lib/utils';
  import type { ProfileSummaryResponse, NetworthData, NetworthCategory } from './profileTypes';

  export let summary: ProfileSummaryResponse;

  $: networth = summary.networth;

  // Category display config
  const categoryConfig: Record<string, { label: string; icon: string; color: string }> = {
    purse: { label: 'Purse', icon: '💰', color: '#ffd700' },
    bank: { label: 'Bank', icon: '🏦', color: '#4ade80' },
    inventory: { label: 'Inventory', icon: '🎒', color: '#60a5fa' },
    armor: { label: 'Armor', icon: '🛡️', color: '#a78bfa' },
    equipment: { label: 'Equipment', icon: '⚔️', color: '#f472b6' },
    wardrobe: { label: 'Wardrobe', icon: '👕', color: '#fb923c' },
    enderchest: { label: 'Ender Chest', icon: '📦', color: '#c084fc' },
    storage: { label: 'Storage', icon: '🗃️', color: '#22d3ee' },
    accessories: { label: 'Accessories', icon: '💍', color: '#f43f5e' },
    pets: { label: 'Pets', icon: '🐾', color: '#84cc16' },
    sacks: { label: 'Sacks', icon: '🛍️', color: '#eab308' },
    essence: { label: 'Essence', icon: '✨', color: '#06b6d4' },
  };

  $: sortedCategories = networth
    ? Object.entries(networth.categories)
        .map(([id, cat]) => ({
          id,
          ...cat,
          config: categoryConfig[id] || { label: cat.name, icon: '📊', color: '#94a3b8' },
        }))
        .filter((c) => c.total > 0)
        .sort((a, b) => b.total - a.total)
    : [];

  $: totalNetworth = networth?.total || 0;
</script>

<section id="networth" class="networth-section">
  {#if networth}
    <div class="networth-header">
      <div class="total-card">
        <div class="total-label">Total Networth</div>
        <div class="total-value">{formatLargeNumber(totalNetworth)}</div>
        <div class="total-exact">{Math.floor(totalNetworth).toLocaleString()} coins</div>
      </div>
      <div class="unsoulbound-card">
        <div class="unsb-label">Unsoulbound (Tradeable)</div>
        <div class="unsb-value">{formatLargeNumber(networth.unsoulbound)}</div>
      </div>
    </div>

    <div class="breakdown-title">
      <h3>Breakdown by Category</h3>
    </div>

    <div class="categories-grid">
      {#each sortedCategories as category}
        {@const percentage = totalNetworth > 0 ? (category.total / totalNetworth) * 100 : 0}
        <div class="category-card">
          <div class="category-header">
            <span class="category-icon">{category.config.icon}</span>
            <span class="category-name">{category.config.label}</span>
          </div>
          <div class="category-value" style="color: {category.config.color}">
            {formatLargeNumber(category.total)}
          </div>
          <div class="category-bar">
            <div
              class="category-bar-fill"
              style="width: {Math.min(100, percentage)}%; background: {category.config.color}"
            ></div>
          </div>
          <div class="category-percentage">{percentage.toFixed(1)}%</div>
        </div>
      {/each}
    </div>

    {#if sortedCategories.length === 0}
      <div class="card empty-state">
        <p>No valuable items found in this profile.</p>
        <p class="hint">This could mean the inventory API is disabled or the profile is new.</p>
      </div>
    {/if}
  {:else}
    <div class="card empty-state">
      <p>Networth data is not available.</p>
      <p class="hint">Try refreshing the profile to calculate networth.</p>
    </div>
  {/if}
</section>

<style>
  .networth-section {
    display: flex;
    flex-direction: column;
    gap: 24px;
  }

  .networth-header {
    display: grid;
    grid-template-columns: 2fr 1fr;
    gap: 20px;
  }

  @media (max-width: 640px) {
    .networth-header {
      grid-template-columns: 1fr;
    }
  }

  .total-card {
    background: linear-gradient(135deg, rgba(255, 215, 0, 0.15), rgba(255, 215, 0, 0.05));
    border: 1px solid rgba(255, 215, 0, 0.3);
    border-radius: 16px;
    padding: 28px 32px;
    text-align: center;
  }

  .total-label {
    font-size: 0.9rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: var(--theme-text-soft);
    margin-bottom: 8px;
  }

  .total-value {
    font-size: 3rem;
    font-weight: 800;
    color: #ffd700;
    line-height: 1.1;
    text-shadow: 0 0 20px rgba(255, 215, 0, 0.3);
  }

  .total-exact {
    font-size: 0.85rem;
    color: var(--theme-text-soft);
    margin-top: 8px;
  }

  .unsoulbound-card {
    background: var(--theme-card-bg);
    border: 1px solid var(--theme-secondary-alpha-32);
    border-radius: 16px;
    padding: 28px 24px;
    text-align: center;
    display: flex;
    flex-direction: column;
    justify-content: center;
  }

  .unsb-label {
    font-size: 0.85rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--theme-text-soft);
    margin-bottom: 8px;
  }

  .unsb-value {
    font-size: 1.8rem;
    font-weight: 700;
    color: #4ade80;
  }

  .breakdown-title {
    margin-top: 8px;
  }

  .breakdown-title h3 {
    font-size: 1.1rem;
    font-weight: 600;
    color: var(--theme-text-primary);
    margin: 0;
  }

  .categories-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
    gap: 16px;
  }

  .category-card {
    background: var(--theme-card-bg);
    border: 1px solid var(--theme-secondary-alpha-32);
    border-radius: 12px;
    padding: 18px 20px;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
  }

  .category-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
  }

  .category-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 12px;
  }

  .category-icon {
    font-size: 1.4rem;
  }

  .category-name {
    font-size: 0.95rem;
    font-weight: 600;
    color: var(--theme-text-primary);
  }

  .category-value {
    font-size: 1.5rem;
    font-weight: 700;
    margin-bottom: 10px;
  }

  .category-bar {
    height: 6px;
    background: rgba(148, 163, 184, 0.2);
    border-radius: 999px;
    overflow: hidden;
    margin-bottom: 8px;
  }

  .category-bar-fill {
    height: 100%;
    border-radius: 999px;
    transition: width 0.4s ease;
  }

  .category-percentage {
    font-size: 0.8rem;
    color: var(--theme-text-soft);
    text-align: right;
  }

  .empty-state {
    text-align: center;
    padding: 48px 24px;
    color: var(--theme-text-soft);
  }

  .empty-state p {
    margin: 0 0 8px;
  }

  .empty-state .hint {
    font-size: 0.9rem;
    opacity: 0.7;
  }

  .card {
    background: var(--theme-card-bg);
    border: 1px solid var(--theme-secondary-alpha-32);
    border-radius: 16px;
    padding: 24px;
  }
</style>
