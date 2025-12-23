<script lang="ts">
  import { onMount } from 'svelte';
  import type { MuseumData, MuseumItem, MuseumMissingItem } from './profileTypes';
  import { texturePackStore } from '$lib/stores/texturePack';
  import { 
    loadHypixelItems, 
    getItemTextureUrl, 
    itemsLoaded, 
    loadFurfskytextures, 
    furfskyCacheLoaded 
  } from '$lib/stores/hypixelItems';

  export let museum: MuseumData | null = null;

  // Load Hypixel items on mount
  onMount(() => {
    loadHypixelItems();
  });

  // Reactive: force re-render when items are loaded
  $: itemsReady = $itemsLoaded;
  
  // Load furfsky textures when pack is furfsky and we have missing items
  $: if ($texturePackStore === 'furfsky' && missingData?.all_missing?.length) {
    const itemIds = missingData.all_missing.map(item => item.id);
    loadFurfskytextures(itemIds);
  }
  
  // Track if furfsky textures are ready
  $: furfskReady = $furfskyCacheLoaded;

  // View mode: 'donated' or 'missing'
  type ViewMode = 'donated' | 'missing';
  let viewMode: ViewMode = 'missing';

  // Category filter for missing items
  type CategoryFilter = 'all' | 'weapons' | 'armor' | 'rarities';
  let categoryFilter: CategoryFilter = 'all';

  // Show all missing items or just top 20
  let showAllMissing = false;

  // Format coin values
  function formatCoins(amount: number): string {
    if (amount >= 1_000_000_000) {
      return `${(amount / 1_000_000_000).toFixed(1)}B`;
    }
    if (amount >= 1_000_000) {
      return `${(amount / 1_000_000).toFixed(1)}M`;
    }
    if (amount >= 1_000) {
      return `${(amount / 1_000).toFixed(1)}K`;
    }
    return amount.toLocaleString();
  }

  // Format timestamp to readable date
  function formatDate(timestamp: number | null | undefined): string {
    if (!timestamp) return 'Unknown';
    const date = new Date(timestamp);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  }

  // Get rarity color
  function getRarityColor(rarity: string | null | undefined): string {
    const colors: Record<string, string> = {
      COMMON: '#ffffff',
      UNCOMMON: '#55ff55',
      RARE: '#5555ff',
      EPIC: '#aa00aa',
      LEGENDARY: '#ffaa00',
      MYTHIC: '#ff55ff',
      DIVINE: '#55ffff',
      SPECIAL: '#ff5555',
      VERY_SPECIAL: '#ff5555'
    };
    return colors[rarity?.toUpperCase() ?? ''] ?? '#aaaaaa';
  }

  // Get rarity background
  function getRarityBg(rarity: string | null | undefined): string {
    const color = getRarityColor(rarity);
    return `${color}15`;
  }

  // Get category color
  function getCategoryColor(category: string): string {
    const colors: Record<string, string> = {
      weapons: '#ff6b6b',
      armor: '#4ecdc4',
      rarities: '#ffd93d'
    };
    return colors[category] ?? '#aaaaaa';
  }

  // Get category icon
  function getCategoryIcon(category: string): string {
    const icons: Record<string, string> = {
      weapons: '⚔️',
      armor: '🛡️',
      rarities: '💎'
    };
    return icons[category] ?? '📦';
  }

  // Progress percentage
  function progressPercent(current: number, total: number): number {
    return total > 0 ? Math.round((current / total) * 100) : 0;
  }

  // Sort items by rarity then name
  function sortItems(items: MuseumItem[]): MuseumItem[] {
    const rarityOrder = [
      'VERY_SPECIAL', 'SPECIAL', 'DIVINE', 'MYTHIC', 
      'LEGENDARY', 'EPIC', 'RARE', 'UNCOMMON', 'COMMON'
    ];
    
    return [...items].sort((a, b) => {
      const aIndex = rarityOrder.indexOf(a.rarity?.toUpperCase() ?? '');
      const bIndex = rarityOrder.indexOf(b.rarity?.toUpperCase() ?? '');
      
      if (aIndex !== bIndex) {
        return aIndex - bIndex;
      }
      return a.name.localeCompare(b.name);
    });
  }

  // Filter missing items by category
  function filterMissingItems(items: MuseumMissingItem[], filter: CategoryFilter): MuseumMissingItem[] {
    if (filter === 'all') return items;
    return items.filter(item => item.category === filter);
  }

  $: sortedItems = museum?.items ? sortItems(museum.items) : [];
  $: sortedSpecial = museum?.special ? sortItems(museum.special) : [];
  $: missingData = museum?.missing;
  $: filteredMissing = missingData?.all_missing 
    ? filterMissingItems(missingData.all_missing, categoryFilter) 
    : [];
  $: displayedMissing = showAllMissing ? filteredMissing : filteredMissing.slice(0, 20);
  $: cheapestItems = missingData?.cheapest ?? [];
  
  // Debug: Log cheapest items to console
  $: if (cheapestItems.length > 0 && itemsReady) {
    console.log('=== Museum Cheapest Items Debug ===');
    console.log('First item:', cheapestItems[0]);
    console.log('Icon URL:', getItemTextureUrl(cheapestItems[0]?.id, $texturePackStore));
  }

  // Get icon URL for missing item - use Hypixel items API with texture pack support
  function getMissingItemIcon(itemId: string): string | null {
    if (!itemsReady) return null;
    return getItemTextureUrl(itemId, $texturePackStore);
  }
</script>

<div class="museum-container">
  {#if !museum || !museum.available}
    <!-- Museum Not Available State -->
    <div class="museum-unavailable">
      <div class="unavailable-icon">🏛️</div>
      <h2>Museum Not Available</h2>
      <p>This player's museum data is not available. The museum may not be unlocked or the data hasn't been loaded yet.</p>
      <div class="unavailable-hint">
        <span class="hint-icon">💡</span>
        <span>Museum data requires a separate API call. Try refreshing the profile to load it.</span>
      </div>
    </div>
  {:else}
    <!-- View Toggle -->
    <div class="view-toggle">
      <button 
        type="button"
        class:active={viewMode === 'missing'}
        on:click={() => viewMode = 'missing'}
      >
        🎯 Missing Items
      </button>
      <button 
        type="button"
        class:active={viewMode === 'donated'}
        on:click={() => viewMode = 'donated'}
      >
        ✅ Donated Items
      </button>
    </div>

    <!-- Museum Overview Stats -->
    <div class="overview-section">
      <h2>🏛️ Museum Overview</h2>
      
      <div class="stats-row">
        <div class="stat-card value">
          <div class="stat-icon">💰</div>
          <div class="stat-content">
            <div class="stat-value">{formatCoins(museum.value)}</div>
            <div class="stat-label">Museum Value</div>
            <div class="stat-sub">Total coin value of donated items</div>
          </div>
        </div>

        <div class="stat-card progress-card">
          <div class="stat-icon">📊</div>
          <div class="stat-content">
            <div class="stat-value">
              {missingData?.progress_percent ?? 0}%
            </div>
            <div class="stat-label">Progress</div>
            <div class="stat-sub">
              {missingData?.total_donated ?? museum.total_donated} / {missingData?.total_museum_items ?? '?'} items
            </div>
            {#if missingData}
              <div class="progress-bar-mini">
                <div class="progress-fill" style="width: {missingData.progress_percent}%"></div>
              </div>
            {/if}
          </div>
        </div>

        <div class="stat-card missing-card">
          <div class="stat-icon">🎯</div>
          <div class="stat-content">
            <div class="stat-value">{missingData?.total_missing ?? '?'}</div>
            <div class="stat-label">Missing Items</div>
            <div class="stat-sub">Items left to donate</div>
          </div>
        </div>

        <div class="stat-card appraisal" class:active={museum.appraisal}>
          <div class="stat-icon">{museum.appraisal ? '✅' : '❌'}</div>
          <div class="stat-content">
            <div class="stat-value">{museum.appraisal ? 'Unlocked' : 'Locked'}</div>
            <div class="stat-label">Appraisal</div>
            <div class="stat-sub">{museum.appraisal ? 'Full value visible' : 'Donate more to unlock'}</div>
          </div>
        </div>
      </div>

      <!-- Category Progress -->
      {#if missingData}
        <div class="category-progress">
          <div class="category-bar">
            <div class="category-info">
              <span class="category-icon">⚔️</span>
              <span class="category-name">Weapons</span>
              <span class="category-count">{missingData.weapons.donated}/{missingData.weapons.total}</span>
            </div>
            <div class="category-progress-bar">
              <div class="category-fill weapons" style="width: {progressPercent(missingData.weapons.donated, missingData.weapons.total)}%"></div>
            </div>
          </div>
          <div class="category-bar">
            <div class="category-info">
              <span class="category-icon">🛡️</span>
              <span class="category-name">Armor</span>
              <span class="category-count">{missingData.armor.donated}/{missingData.armor.total}</span>
            </div>
            <div class="category-progress-bar">
              <div class="category-fill armor" style="width: {progressPercent(missingData.armor.donated, missingData.armor.total)}%"></div>
            </div>
          </div>
          <div class="category-bar">
            <div class="category-info">
              <span class="category-icon">💎</span>
              <span class="category-name">Rarities</span>
              <span class="category-count">{missingData.rarities.donated}/{missingData.rarities.total}</span>
            </div>
            <div class="category-progress-bar">
              <div class="category-fill rarities" style="width: {progressPercent(missingData.rarities.donated, missingData.rarities.total)}%"></div>
            </div>
          </div>
        </div>
      {/if}
    </div>

    {#if viewMode === 'missing'}
      <!-- Missing Items Section -->
      {#if missingData && missingData.all_missing.length > 0}
        <!-- Cheapest Quick View -->
        <div class="cheapest-section">
          <div class="section-header">
            <span class="section-icon">💎</span>
            <h3>Cheapest Missing Items</h3>
            <span class="item-count">Best value for museum progress</span>
          </div>

          {#key `${itemsReady}-${furfskReady}-${$texturePackStore}`}
          <div class="cheapest-grid">
            {#each cheapestItems.slice(0, 10) as item, index}
              {@const iconSrc = getMissingItemIcon(item.id)}
              <div class="cheapest-card" style="--category-color: {getCategoryColor(item.category)}">
                <div class="cheapest-rank">#{index + 1}</div>
                <div class="item-icon-small">
                  {#if iconSrc}
                    <img
                      src={iconSrc}
                      alt=""
                      loading="lazy"
                      width="24"
                      height="24"
                      on:error={(e) => {
                        e.currentTarget.style.display = 'none';
                      }}
                    />
                  {:else}
                    <span class="icon-placeholder">{getCategoryIcon(item.category)}</span>
                  {/if}
                </div>
                <div class="cheapest-info">
                  <div class="cheapest-name">{item.name}</div>
                  <div class="cheapest-meta">
                    <span class="cheapest-category" style="color: {getCategoryColor(item.category)}">
                      {getCategoryIcon(item.category)} {item.category}
                    </span>
                  </div>
                </div>
                <div class="cheapest-price">
                  {#if item.price_formatted}
                    <span class="price-value">💰 {item.price_formatted}</span>
                  {:else}
                    <span class="price-unknown">Price N/A</span>
                  {/if}
                </div>
              </div>
            {/each}
          </div>
          {/key}
        </div>

        <!-- All Missing Items -->
        <div class="missing-section">
          <div class="section-header">
            <span class="section-icon">📋</span>
            <h3>All Missing Items</h3>
            <span class="item-count">{missingData.total_missing} items</span>
          </div>

          <!-- Category Filter -->
          <div class="filter-row">
            <button 
              type="button"
              class="filter-btn" 
              class:active={categoryFilter === 'all'}
              on:click={() => categoryFilter = 'all'}
            >
              All ({missingData.total_missing})
            </button>
            <button 
              type="button"
              class="filter-btn weapons" 
              class:active={categoryFilter === 'weapons'}
              on:click={() => categoryFilter = 'weapons'}
            >
              ⚔️ Weapons ({missingData.weapons.missing.length})
            </button>
            <button 
              type="button"
              class="filter-btn armor" 
              class:active={categoryFilter === 'armor'}
              on:click={() => categoryFilter = 'armor'}
            >
              🛡️ Armor ({missingData.armor.missing.length})
            </button>
            <button 
              type="button"
              class="filter-btn rarities" 
              class:active={categoryFilter === 'rarities'}
              on:click={() => categoryFilter = 'rarities'}
            >
              💎 Rarities ({missingData.rarities.missing.length})
            </button>
          </div>

          {#key `${itemsReady}-${furfskReady}-${$texturePackStore}`}
          <div class="missing-grid">
            {#each displayedMissing as item}
              {@const iconSrc = getMissingItemIcon(item.id)}
              <div class="missing-card" style="--category-color: {getCategoryColor(item.category)}">
                <div class="missing-header">
                  <div class="item-icon-small">
                    {#if iconSrc}
                      <img
                        src={iconSrc}
                        alt=""
                        loading="lazy"
                        width="24"
                        height="24"
                        on:error={(e) => {
                          e.currentTarget.style.display = 'none';
                        }}
                      />
                    {:else}
                      <span class="icon-placeholder">{getCategoryIcon(item.category)}</span>
                    {/if}
                  </div>
                  <div class="missing-name">{item.name}</div>
                </div>
                <div class="missing-footer">
                  <span class="missing-category" style="color: {getCategoryColor(item.category)}">
                    {item.category}
                  </span>
                  {#if item.price_formatted}
                    <span class="missing-price">💰 {item.price_formatted}</span>
                  {:else}
                    <span class="missing-price unknown">Price N/A</span>
                  {/if}
                </div>
              </div>
            {/each}
          </div>
          {/key}

          {#if filteredMissing.length > 20 && !showAllMissing}
            <button type="button" class="show-more-btn" on:click={() => showAllMissing = true}>
              Show All {filteredMissing.length} Items
            </button>
          {:else if showAllMissing && filteredMissing.length > 20}
            <button type="button" class="show-more-btn" on:click={() => showAllMissing = false}>
              Show Less
            </button>
          {/if}
        </div>
      {:else}
        <div class="empty-state">
          <div class="empty-icon">🎉</div>
          <h3>Museum Complete!</h3>
          <p>Congratulations! All museum items have been donated.</p>
        </div>
      {/if}
    {:else}
      <!-- Donated Items View -->
      <!-- Regular Items Section -->
      {#if sortedItems.length > 0}
        <div class="items-section">
          <div class="section-header">
            <span class="section-icon">⚔️</span>
            <h3>Donated Items</h3>
            <span class="item-count">{sortedItems.length} items</span>
          </div>

          <div class="items-grid">
            {#each sortedItems as item}
              {@const iconSrc = item.icon_variants?.[$texturePackStore] ?? item.icon_variants?.furfsky ?? item.icon_variants?.vanilla ?? item.icon_url ?? null}
              {@const fallbackIcon = iconSrc === item.icon_variants?.furfsky ? item.icon_variants?.vanilla ?? item.icon_url : item.icon_variants?.furfsky ?? item.icon_url}
              <div 
                class="item-card" 
                class:borrowing={item.borrowing}
                style="--rarity-color: {getRarityColor(item.rarity)}; --rarity-bg: {getRarityBg(item.rarity)}"
              >
                <div class="item-header">
                  {#if iconSrc}
                    <div class="item-icon" class:furfsky={$texturePackStore === 'furfsky'}>
                      <img
                        src={iconSrc}
                        alt=""
                        loading="lazy"
                        width="32"
                        height="32"
                        on:error={(e) => {
                          if (fallbackIcon && e.currentTarget.src !== fallbackIcon) {
                            e.currentTarget.src = fallbackIcon;
                          }
                        }}
                      />
                    </div>
                  {/if}
                  <div class="item-info">
                    <div class="item-name" style="color: {getRarityColor(item.rarity)}">
                      {item.name}
                    </div>
                    {#if item.borrowing}
                      <span class="borrowing-badge" title="Currently borrowing this item">📖</span>
                    {/if}
                  </div>
                </div>
                
                <div class="item-details">
                  {#if item.rarity}
                    <span class="item-rarity" style="color: {getRarityColor(item.rarity)}">
                      {item.rarity}
                    </span>
                  {/if}
                  {#if item.donated_time}
                    <span class="item-date">
                      Donated: {formatDate(item.donated_time)}
                    </span>
                  {/if}
                </div>
              </div>
            {/each}
          </div>
        </div>
      {/if}

      <!-- Special Items Section -->
      {#if sortedSpecial.length > 0}
        <div class="items-section special">
          <div class="section-header">
            <span class="section-icon">⭐</span>
            <h3>Special Items</h3>
            <span class="item-count">{sortedSpecial.length} items</span>
          </div>

          <div class="items-grid">
            {#each sortedSpecial as item}
              {@const iconSrc = item.icon_variants?.[$texturePackStore] ?? item.icon_variants?.furfsky ?? item.icon_variants?.vanilla ?? item.icon_url ?? null}
              {@const fallbackIcon = iconSrc === item.icon_variants?.furfsky ? item.icon_variants?.vanilla ?? item.icon_url : item.icon_variants?.furfsky ?? item.icon_url}
              <div 
                class="item-card special" 
                class:borrowing={item.borrowing}
                style="--rarity-color: {getRarityColor(item.rarity)}; --rarity-bg: {getRarityBg(item.rarity)}"
              >
                <div class="item-header">
                  {#if iconSrc}
                    <div class="item-icon" class:furfsky={$texturePackStore === 'furfsky'}>
                      <img
                        src={iconSrc}
                        alt=""
                        loading="lazy"
                        width="32"
                        height="32"
                        on:error={(e) => {
                          if (fallbackIcon && e.currentTarget.src !== fallbackIcon) {
                            e.currentTarget.src = fallbackIcon;
                          }
                        }}
                      />
                    </div>
                  {/if}
                  <div class="item-info">
                    <div class="item-name" style="color: {getRarityColor(item.rarity)}">
                      {item.name}
                    </div>
                    {#if item.borrowing}
                      <span class="borrowing-badge" title="Currently borrowing this item">📖</span>
                    {/if}
                  </div>
                </div>
                
                <div class="item-details">
                  {#if item.rarity}
                    <span class="item-rarity" style="color: {getRarityColor(item.rarity)}">
                      {item.rarity}
                    </span>
                  {/if}
                  {#if item.donated_time}
                    <span class="item-date">
                      Donated: {formatDate(item.donated_time)}
                    </span>
                  {/if}
                </div>
              </div>
            {/each}
          </div>
        </div>
      {/if}

      <!-- Empty State for Donated -->
      {#if sortedItems.length === 0 && sortedSpecial.length === 0}
        <div class="empty-state">
          <div class="empty-icon">📭</div>
          <h3>No Items Donated</h3>
          <p>This player hasn't donated any items to their museum yet.</p>
        </div>
      {/if}
    {/if}
  {/if}
</div>

<style>
  .museum-container {
    display: flex;
    flex-direction: column;
    gap: 24px;
    padding: 16px 0;
  }

  /* View Toggle */
  .view-toggle {
    display: flex;
    gap: 8px;
    background: var(--theme-card-bg);
    padding: 8px;
    border-radius: 12px;
    width: fit-content;
  }

  .view-toggle button {
    padding: 10px 20px;
    border: none;
    border-radius: 8px;
    background: transparent;
    color: var(--theme-text-soft);
    font-weight: 600;
    font-size: 0.95rem;
    cursor: pointer;
    transition: all 0.2s;
  }

  .view-toggle button:hover {
    background: rgba(148, 163, 184, 0.1);
  }

  .view-toggle button.active {
    background: linear-gradient(135deg, var(--theme-accent), var(--theme-accent-secondary));
    color: white;
  }

  /* Unavailable State */
  .museum-unavailable {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 48px 24px;
    background: var(--theme-card-bg);
    border-radius: 16px;
    text-align: center;
  }

  .unavailable-icon {
    font-size: 4rem;
    margin-bottom: 16px;
    opacity: 0.6;
  }

  .museum-unavailable h2 {
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--theme-text-primary);
    margin-bottom: 8px;
  }

  .museum-unavailable p {
    color: var(--theme-text-soft);
    max-width: 400px;
    margin-bottom: 24px;
  }

  .unavailable-hint {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 12px 20px;
    background: rgba(var(--theme-accent-rgb), 0.1);
    border-radius: 8px;
    color: var(--theme-text-soft);
    font-size: 0.9rem;
  }

  .hint-icon {
    font-size: 1.2rem;
  }

  /* Overview Section */
  .overview-section {
    background: var(--theme-card-bg);
    border-radius: 16px;
    padding: 24px;
  }

  .overview-section h2 {
    font-size: 1.3rem;
    font-weight: 700;
    color: var(--theme-text-primary);
    margin-bottom: 20px;
  }

  .stats-row {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 16px;
  }

  .stat-card {
    display: flex;
    gap: 14px;
    padding: 16px;
    background: rgba(148, 163, 184, 0.08);
    border-radius: 12px;
    border: 1px solid rgba(148, 163, 184, 0.12);
    transition: transform 0.2s, box-shadow 0.2s;
  }

  .stat-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  }

  .stat-card.value {
    border-color: rgba(255, 170, 0, 0.3);
    background: rgba(255, 170, 0, 0.08);
  }

  .stat-card.progress-card {
    border-color: rgba(85, 85, 255, 0.3);
    background: rgba(85, 85, 255, 0.08);
  }

  .stat-card.missing-card {
    border-color: rgba(255, 107, 107, 0.3);
    background: rgba(255, 107, 107, 0.08);
  }

  .stat-card.appraisal.active {
    border-color: rgba(85, 255, 85, 0.3);
    background: rgba(85, 255, 85, 0.08);
  }

  .stat-card.items {
    border-color: rgba(85, 85, 255, 0.3);
    background: rgba(85, 85, 255, 0.08);
  }

  .stat-icon {
    font-size: 2rem;
    display: flex;
    align-items: center;
    justify-content: center;
    width: 48px;
    height: 48px;
    background: rgba(148, 163, 184, 0.1);
    border-radius: 10px;
  }

  .stat-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .stat-value {
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--theme-text-primary);
  }

  .stat-label {
    font-size: 0.85rem;
    font-weight: 600;
    color: var(--theme-text-soft);
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .stat-sub {
    font-size: 0.8rem;
    color: var(--theme-text-soft);
    opacity: 0.8;
  }

  /* Progress Bar Mini */
  .progress-bar-mini {
    height: 6px;
    background: rgba(148, 163, 184, 0.2);
    border-radius: 3px;
    margin-top: 6px;
    overflow: hidden;
  }

  .progress-bar-mini .progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #5555ff, #55ffff);
    border-radius: 3px;
    transition: width 0.4s ease;
  }

  /* Category Progress */
  .category-progress {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 16px;
    margin-top: 24px;
    padding-top: 20px;
    border-top: 1px solid rgba(148, 163, 184, 0.12);
  }

  .category-bar {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .category-info {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .category-icon {
    font-size: 1.2rem;
  }

  .category-name {
    font-weight: 600;
    color: var(--theme-text-primary);
  }

  .category-count {
    margin-left: auto;
    font-size: 0.85rem;
    color: var(--theme-text-soft);
  }

  .category-progress-bar {
    height: 8px;
    background: rgba(148, 163, 184, 0.15);
    border-radius: 4px;
    overflow: hidden;
  }

  .category-fill {
    height: 100%;
    border-radius: 4px;
    transition: width 0.4s ease;
  }

  .category-fill.weapons {
    background: linear-gradient(90deg, #ff6b6b, #ff8e8e);
  }

  .category-fill.armor {
    background: linear-gradient(90deg, #4ecdc4, #7eddd6);
  }

  .category-fill.rarities {
    background: linear-gradient(90deg, #ffd93d, #ffe066);
  }

  /* Cheapest Section */
  .cheapest-section {
    background: var(--theme-card-bg);
    border-radius: 16px;
    padding: 24px;
    border: 1px solid rgba(255, 215, 0, 0.2);
  }

  .cheapest-grid {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .cheapest-card {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 16px;
    background: rgba(148, 163, 184, 0.06);
    border-radius: 10px;
    border-left: 3px solid var(--category-color, #aaa);
    transition: transform 0.15s, background 0.15s;
  }

  .cheapest-card:hover {
    background: rgba(148, 163, 184, 0.1);
    transform: translateX(4px);
  }

  .cheapest-rank {
    font-size: 0.9rem;
    font-weight: 700;
    color: var(--theme-text-soft);
    min-width: 28px;
  }

  .cheapest-info {
    flex: 1;
    min-width: 0;
  }

  .cheapest-name {
    font-weight: 600;
    color: var(--theme-text-primary);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .cheapest-meta {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-top: 2px;
  }

  .cheapest-category {
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
  }

  .cheapest-price {
    text-align: right;
  }

  .cheapest-price .price-value {
    font-weight: 700;
    color: #ffaa00;
  }

  .cheapest-price .price-unknown {
    font-size: 0.85rem;
    color: var(--theme-text-soft);
    opacity: 0.6;
  }

  /* Missing Section */
  .missing-section {
    background: var(--theme-card-bg);
    border-radius: 16px;
    padding: 24px;
  }

  .filter-row {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 20px;
  }

  .filter-btn {
    padding: 8px 16px;
    border: 1px solid rgba(148, 163, 184, 0.2);
    border-radius: 20px;
    background: transparent;
    color: var(--theme-text-soft);
    font-size: 0.85rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
  }

  .filter-btn:hover {
    background: rgba(148, 163, 184, 0.1);
  }

  .filter-btn.active {
    background: rgba(148, 163, 184, 0.15);
    border-color: var(--theme-accent);
    color: var(--theme-text-primary);
  }

  .filter-btn.weapons.active {
    background: rgba(255, 107, 107, 0.15);
    border-color: #ff6b6b;
  }

  .filter-btn.armor.active {
    background: rgba(78, 205, 196, 0.15);
    border-color: #4ecdc4;
  }

  .filter-btn.rarities.active {
    background: rgba(255, 217, 61, 0.15);
    border-color: #ffd93d;
  }

  .missing-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 10px;
  }

  .missing-card {
    padding: 12px;
    background: rgba(148, 163, 184, 0.06);
    border-radius: 8px;
    border-left: 3px solid var(--category-color, #aaa);
    transition: transform 0.15s, box-shadow 0.15s;
  }

  .missing-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  }

  .missing-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 8px;
  }

  .missing-category-icon {
    font-size: 1rem;
    flex-shrink: 0;
  }

  .missing-name {
    font-size: 0.9rem;
    font-weight: 600;
    color: var(--theme-text-primary);
    line-height: 1.3;
    flex: 1;
    min-width: 0;
  }

  .missing-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .missing-category {
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.03em;
  }

  .missing-price {
    font-size: 0.8rem;
    font-weight: 600;
    color: #ffaa00;
  }

  .missing-price.unknown {
    color: var(--theme-text-soft);
    opacity: 0.6;
  }

  .show-more-btn {
    display: block;
    width: 100%;
    margin-top: 16px;
    padding: 12px;
    border: 1px dashed rgba(148, 163, 184, 0.3);
    border-radius: 10px;
    background: transparent;
    color: var(--theme-text-soft);
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
  }

  .show-more-btn:hover {
    background: rgba(148, 163, 184, 0.1);
    border-color: rgba(148, 163, 184, 0.5);
  }

  /* Items Section */
  .items-section {
    background: var(--theme-card-bg);
    border-radius: 16px;
    padding: 24px;
  }

  .items-section.special {
    border: 1px solid rgba(255, 170, 0, 0.3);
  }

  .section-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 20px;
  }

  .section-icon {
    font-size: 1.5rem;
  }

  .section-header h3 {
    font-size: 1.2rem;
    font-weight: 700;
    color: var(--theme-text-primary);
    margin: 0;
  }

  .item-count {
    margin-left: auto;
    padding: 4px 12px;
    background: rgba(148, 163, 184, 0.15);
    border-radius: 20px;
    font-size: 0.85rem;
    color: var(--theme-text-soft);
  }

  .items-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
    gap: 12px;
  }

  .item-card {
    padding: 14px;
    background: var(--rarity-bg, rgba(148, 163, 184, 0.08));
    border-radius: 10px;
    border: 1px solid rgba(var(--rarity-color, #aaaaaa), 0.2);
    border-left: 3px solid var(--rarity-color, #aaaaaa);
    transition: transform 0.15s, box-shadow 0.15s;
  }

  .item-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
  }

  .item-card.special {
    background: linear-gradient(135deg, rgba(255, 170, 0, 0.08), rgba(255, 85, 255, 0.08));
  }

  .item-card.borrowing {
    opacity: 0.7;
    border-style: dashed;
  }

  .item-header {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    margin-bottom: 8px;
  }

  .item-icon {
    width: 32px;
    height: 32px;
    flex-shrink: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 4px;
    background: rgba(148, 163, 184, 0.1);
  }

  .item-icon img {
    width: 100%;
    height: 100%;
    object-fit: contain;
    image-rendering: pixelated;
  }

  .item-icon.furfsky img {
    image-rendering: auto;
  }

  .item-icon-small {
    width: 24px;
    height: 24px;
    flex-shrink: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 3px;
    background: rgba(148, 163, 184, 0.1);
  }

  .item-icon-small img {
    width: 100%;
    height: 100%;
    object-fit: contain;
    image-rendering: pixelated;
  }

  .item-icon-small.furfsky img {
    image-rendering: auto;
  }

  .icon-placeholder {
    font-size: 14px;
    opacity: 0.7;
  }

  .item-info {
    flex: 1;
    min-width: 0;
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 8px;
  }

  .item-name {
    font-size: 0.95rem;
    font-weight: 600;
    line-height: 1.3;
    word-break: break-word;
  }

  .borrowing-badge {
    font-size: 1rem;
    flex-shrink: 0;
  }

  .item-details {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .item-rarity {
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .item-date {
    font-size: 0.75rem;
    color: var(--theme-text-soft);
    opacity: 0.8;
  }

  /* Empty State */
  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 48px 24px;
    background: var(--theme-card-bg);
    border-radius: 16px;
    text-align: center;
  }

  .empty-icon {
    font-size: 3rem;
    margin-bottom: 12px;
    opacity: 0.6;
  }

  .empty-state h3 {
    font-size: 1.2rem;
    font-weight: 700;
    color: var(--theme-text-primary);
    margin-bottom: 8px;
  }

  .empty-state p {
    color: var(--theme-text-soft);
  }

  /* Responsive */
  @media (max-width: 640px) {
    .stats-row {
      grid-template-columns: 1fr;
    }

    .items-grid,
    .missing-grid {
      grid-template-columns: 1fr;
    }

    .stat-card {
      flex-direction: column;
      text-align: center;
    }

    .stat-icon {
      align-self: center;
    }

    .filter-row {
      justify-content: center;
    }

    .view-toggle {
      width: 100%;
      justify-content: center;
    }

    .cheapest-card {
      flex-wrap: wrap;
    }

    .cheapest-price {
      width: 100%;
      text-align: left;
      margin-top: 4px;
    }
  }
</style>
