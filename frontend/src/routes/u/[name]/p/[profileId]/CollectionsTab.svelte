<script lang="ts">
  import type { ProfileSummaryResponse, CollectionItem, CollectionCategory } from './profileTypes';
  import { onMount } from 'svelte';
  import { texturePackStore } from '$lib/stores/texturePack';
  import { loadFurfskytextures, getFurfskyCachedTexture, furfskyCacheLoaded } from '$lib/stores/hypixelItems';

  export let summary: ProfileSummaryResponse;

  // Load furfsky textures when pack is furfsky
  $: if ($texturePackStore === 'furfsky' && collectionsData?.categories) {
    const allItemIds: string[] = [];
    for (const cat of Object.values(collectionsData.categories) as any[]) {
      for (const col of cat.collections || []) {
        allItemIds.push(col.texture || col.id);
      }
    }
    if (allItemIds.length > 0) {
      loadFurfskytextures(allItemIds);
    }
  }

  // Collection item ID to texture path mapping (vanilla)
  const COLLECTION_TEXTURES: Record<string, string> = {
    // Farming
    WHEAT: 'item/wheat',
    CARROT_ITEM: 'item/carrot',
    POTATO_ITEM: 'item/potato',
    PUMPKIN: 'block/pumpkin_side',
    MELON: 'item/melon_slice',
    SEEDS: 'item/wheat_seeds',
    RED_MUSHROOM: 'block/red_mushroom',
    BROWN_MUSHROOM: 'block/brown_mushroom',
    MUSHROOM_COLLECTION: 'block/red_mushroom',
    'INK_SACK:3': 'item/cocoa_beans',
    CACTUS: 'block/cactus_side',
    SUGAR_CANE: 'item/sugar_cane',
    FEATHER: 'item/feather',
    LEATHER: 'item/leather',
    PORK: 'item/porkchop',
    RAW_CHICKEN: 'item/chicken',
    MUTTON: 'item/mutton',
    RABBIT: 'item/rabbit',
    NETHER_STALK: 'item/nether_wart',
    EGG: 'item/egg',
    RAW_BEEF: 'item/beef',
    
    // Mining
    COBBLESTONE: 'block/cobblestone',
    COAL: 'item/coal',
    IRON_INGOT: 'item/iron_ingot',
    GOLD_INGOT: 'item/gold_ingot',
    DIAMOND: 'item/diamond',
    'INK_SACK:4': 'item/lapis_lazuli',
    EMERALD: 'item/emerald',
    REDSTONE: 'item/redstone',
    QUARTZ: 'item/quartz',
    OBSIDIAN: 'block/obsidian',
    GLOWSTONE_DUST: 'item/glowstone_dust',
    GRAVEL: 'block/gravel',
    ICE: 'block/ice',
    NETHERRACK: 'block/netherrack',
    SAND: 'block/sand',
    'SAND:1': 'block/red_sand',
    ENDER_STONE: 'block/end_stone',
    MITHRIL_ORE: 'item/prismarine_crystals',
    HARD_STONE: 'block/stone',
    GEMSTONE_COLLECTION: 'item/emerald',
    MYCEL: 'block/mycelium_side',
    RED_SAND: 'block/red_sand',
    SULPHUR_ORE: 'item/gunpowder',
    SNOW_BALL: 'item/snowball',
    TITANIUM_ORE: 'item/iron_ingot',
    STARFALL: 'item/nether_star',
    GLACITE: 'block/packed_ice',
    UMBER: 'item/cocoa_beans',
    TUNGSTEN: 'block/iron_block',
    
    // Combat
    ROTTEN_FLESH: 'item/rotten_flesh',
    BONE: 'item/bone',
    STRING: 'item/string',
    SPIDER_EYE: 'item/spider_eye',
    SULPHUR: 'item/gunpowder',
    GUNPOWDER: 'item/gunpowder',
    ENDER_PEARL: 'item/ender_pearl',
    GHAST_TEAR: 'item/ghast_tear',
    SLIME_BALL: 'item/slime_ball',
    BLAZE_ROD: 'item/blaze_rod',
    MAGMA_CREAM: 'item/magma_cream',
    CHILI_PEPPER: 'item/blaze_powder',
    
    // Foraging
    LOG: 'block/oak_log',
    'LOG:1': 'block/spruce_log',
    'LOG:2': 'block/birch_log',
    'LOG_2:1': 'block/dark_oak_log',
    LOG_2: 'block/acacia_log',
    'LOG:3': 'block/jungle_log',
    
    // Fishing
    RAW_FISH: 'item/cod',
    'RAW_FISH:1': 'item/salmon',
    'RAW_FISH:2': 'item/tropical_fish',
    'RAW_FISH:3': 'item/pufferfish',
    PRISMARINE_SHARD: 'item/prismarine_shard',
    PRISMARINE_CRYSTALS: 'item/prismarine_crystals',
    CLAY_BALL: 'item/clay_ball',
    WATER_LILY: 'block/lily_pad',
    INK_SACK: 'item/ink_sac',
    SPONGE: 'block/sponge',
    MAGMA_FISH: 'item/magma_cream',
    
    // Rift
    AGARICUS_CAP: 'block/red_mushroom',
    CADUCOUS_STEM: 'item/stick',
    WILTED_BERBERIS: 'block/dead_bush',
    HALF_EATEN_CARROT: 'item/carrot',
    HEMOVIBE: 'item/redstone',
    METAL_HEART: 'block/iron_block',
    TIMITE: 'item/clock',
  };

  const TEXTURE_BASE = 'https://assets.mcasset.cloud/1.20.4/assets/minecraft/textures';

  $: collectionsData = summary.collections;
  $: categories = collectionsData?.categories || {};
  $: totalCollections = collectionsData?.totalCollections || 0;
  $: maxedCollections = collectionsData?.maxedCollections || 0;
  $: totalTiers = collectionsData?.totalTiers || 0;
  $: unlockedTiers = collectionsData?.unlockedTiers || 0;

  // Category order for display
  const categoryOrder = ['farming', 'mining', 'combat', 'foraging', 'fishing', 'rift'];

  // Get texture URL for a collection item (supports furfsky)
  function getTextureUrl(itemId: string): string | null {
    // If furfsky pack is selected, check furfsky cache first
    if ($texturePackStore === 'furfsky') {
      const furfskUrl = getFurfskyCachedTexture(itemId);
      if (furfskUrl) {
        return furfskUrl;
      }
      // Fallback to vanilla if furfsky not available
    }
    
    // Vanilla texture
    const path = COLLECTION_TEXTURES[itemId];
    if (path) {
      return `${TEXTURE_BASE}/${path}.png`;
    }
    return null;
  }

  // Get tier color based on completion
  function getTierColor(tier: number, maxTier: number): string {
    if (tier === 0) return 'var(--theme-text-soft)';
    if (tier >= maxTier) return '#ffd700';
    const ratio = tier / maxTier;
    if (ratio >= 0.8) return '#7cd95a';
    if (ratio >= 0.5) return '#d9d95a';
    return '#d9985a';
  }

  // Progress percentage
  function progressPercent(current: number, total: number): number {
    return total > 0 ? Math.round((current / total) * 100) : 0;
  }

  // Convert tier number to Roman numeral
  function toRoman(num: number): string {
    const map: [number, string][] = [
      [12, 'XII'], [11, 'XI'], [10, 'X'], [9, 'IX'], [8, 'VIII'],
      [7, 'VII'], [6, 'VI'], [5, 'V'], [4, 'IV'], [3, 'III'], [2, 'II'], [1, 'I']
    ];
    for (const [val, roman] of map) {
      if (num >= val) return roman;
    }
    return '';
  }

  // Get ordered categories
  $: orderedCategories = categoryOrder
    .filter(key => categories[key])
    .map(key => ({ key, data: categories[key] }));
</script>

<div class="collections-container">
  <!-- Overview Stats -->
  <div class="overview-section">
    <h2>Collections Overview</h2>
    <div class="stats-row">
      <div class="stat-card tiers">
        <div class="stat-icon">📊</div>
        <div class="stat-content">
          <div class="stat-value">{unlockedTiers}<span class="stat-max">/{totalTiers}</span></div>
          <div class="stat-label">Unique Tiers Unlocked</div>
          <div class="progress-bar">
            <div class="progress-fill" style="width: {progressPercent(unlockedTiers, totalTiers)}%"></div>
          </div>
        </div>
      </div>

      <div class="stat-card maxed">
        <div class="stat-icon">⭐</div>
        <div class="stat-content">
          <div class="stat-value">{maxedCollections}<span class="stat-max">/{totalCollections}</span></div>
          <div class="stat-label">Maxed Collections</div>
          <div class="progress-bar gold">
            <div class="progress-fill" style="width: {progressPercent(maxedCollections, totalCollections)}%"></div>
          </div>
        </div>
      </div>

      <div class="stat-card total">
        <div class="stat-icon">📦</div>
        <div class="stat-content">
          <div class="stat-value">{totalCollections}</div>
          <div class="stat-label">Total Collections</div>
          <div class="stat-sub">{categoryOrder.filter(k => categories[k]).length} categories</div>
        </div>
      </div>
    </div>
  </div>

  <!-- Category Sections -->
  {#each orderedCategories as { key, data }}
    <div class="category-section">
      <div class="category-header">
        <div class="category-title">
          <span class="category-icon" style="color: {data.color}">{data.icon}</span>
          <h3>{data.name}</h3>
        </div>
        <div class="category-stats">
          <span class="stat-badge">{data.unlockedTiers}/{data.totalTiers} Tiers</span>
          <span class="stat-badge maxed-badge">{data.maxedCollections}/{data.totalCollections} Maxed</span>
        </div>
      </div>

      <div class="collections-grid">
        {#each data.collections as collection}
          {#key `${$texturePackStore}-${$furfskyCacheLoaded}`}
            {@const textureUrl = getTextureUrl(collection.texture)}
            <div class="collection-card" class:maxed={collection.isMaxed}>
              <div class="collection-header">
                <div class="collection-icon" class:furfsky={$texturePackStore === 'furfsky'}>
                  {#if textureUrl}
                    <img 
                      src={textureUrl} 
                      alt={collection.name}
                      onerror={(e) => { (e.currentTarget as HTMLImageElement).style.display = 'none'; }}
                    />
                  {:else}
                    <div class="fallback-icon">📦</div>
                  {/if}
                </div>
                <div class="collection-info">
                  <div class="collection-name">{collection.name}</div>
                  <div class="collection-amount">{collection.amountFormatted} collected</div>
                </div>
              </div>

              <div class="collection-tier">
              <div class="tier-display" style="color: {getTierColor(collection.tier, collection.maxTier)}">
                {#if collection.tier > 0}
                  {toRoman(collection.tier)}
                {:else}
                  Not Unlocked
                {/if}
              </div>
              <div class="tier-max">/ {toRoman(collection.maxTier)}</div>
            </div>

            {#if !collection.isMaxed}
              <div class="collection-progress">
                <div class="progress-info">
                  <span class="progress-label">Next Tier</span>
                  <span class="progress-value">{collection.nextTierReqFormatted || '?'}</span>
                </div>
                <div class="progress-bar small">
                  <div class="progress-fill" style="width: {collection.progress}%"></div>
                </div>
              </div>
            {:else}
              <div class="collection-maxed-badge">
                <span class="maxed-icon">✓</span>
                MAXED
              </div>
            {/if}
            </div>
          {/key}
        {/each}
      </div>
    </div>
  {/each}
</div>

<style>
  .collections-container {
    width: 100%;
    max-width: 1400px;
    margin: 0 auto;
    padding: 1rem;
  }

  /* Overview Section */
  .overview-section {
    margin-bottom: 2rem;
  }

  .overview-section h2 {
    margin: 0 0 1rem 0;
    font-size: 1.5rem;
    font-weight: 600;
    color: var(--theme-text);
  }

  .stats-row {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 1rem;
  }

  .stat-card {
    background: var(--theme-card-bg);
    border: 1px solid var(--theme-border);
    border-radius: 12px;
    padding: 1.25rem;
    display: flex;
    align-items: flex-start;
    gap: 1rem;
    transition: all 0.2s;
  }

  .stat-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  }

  .stat-icon {
    font-size: 2rem;
    line-height: 1;
  }

  .stat-content {
    flex: 1;
  }

  .stat-value {
    font-size: 1.75rem;
    font-weight: 700;
    color: var(--theme-text);
    line-height: 1;
    margin-bottom: 0.5rem;
  }

  .stat-max {
    font-size: 1.25rem;
    color: var(--theme-text-soft);
    font-weight: 500;
  }

  .stat-label {
    font-size: 0.875rem;
    color: var(--theme-text-soft);
    margin-bottom: 0.5rem;
  }

  .stat-sub {
    font-size: 0.75rem;
    color: var(--theme-text-muted);
  }

  .stat-sub.maxed {
    color: #ffd700;
    font-weight: 600;
  }

  /* Category Section */
  .category-section {
    margin-bottom: 2rem;
    background: var(--theme-card-bg);
    border: 1px solid var(--theme-border);
    border-radius: 12px;
    padding: 1.5rem;
  }

  .category-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1.5rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid var(--theme-border);
  }

  .category-title {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }

  .category-icon {
    font-size: 1.75rem;
  }

  .category-title h3 {
    margin: 0;
    font-size: 1.375rem;
    font-weight: 600;
    color: var(--theme-text);
  }

  .category-stats {
    display: flex;
    gap: 0.75rem;
  }

  .stat-badge {
    background: var(--theme-bg);
    padding: 0.375rem 0.75rem;
    border-radius: 6px;
    font-size: 0.875rem;
    font-weight: 500;
    color: var(--theme-text);
  }

  .maxed-badge {
    background: rgba(255, 215, 0, 0.1);
    color: #ffd700;
  }

  /* Collections Grid */
  .collections-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 1rem;
  }

  .collection-card {
    background: var(--theme-bg);
    border: 1px solid var(--theme-border);
    border-radius: 10px;
    padding: 1rem;
    transition: all 0.2s;
  }

  .collection-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
  }

  .collection-card.maxed {
    border-color: rgba(255, 215, 0, 0.3);
    background: linear-gradient(135deg, var(--theme-bg) 0%, rgba(255, 215, 0, 0.05) 100%);
  }

  .collection-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 0.75rem;
  }

  .collection-icon {
    width: 40px;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--theme-card-bg);
    border-radius: 8px;
    border: 1px solid var(--theme-border);
  }

  .collection-icon img {
    width: 32px;
    height: 32px;
    image-rendering: pixelated;
  }

  .collection-icon.furfsky img {
    width: 36px;
    height: 36px;
    image-rendering: auto;
  }

  .fallback-icon {
    font-size: 1.25rem;
    opacity: 0.6;
  }

  .collection-info {
    flex: 1;
    min-width: 0;
  }

  .collection-name {
    font-size: 0.9375rem;
    font-weight: 600;
    color: var(--theme-text);
    margin-bottom: 0.25rem;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .collection-amount {
    font-size: 0.8125rem;
    color: var(--theme-text-soft);
  }

  .collection-tier {
    display: flex;
    align-items: baseline;
    gap: 0.5rem;
    margin-bottom: 0.75rem;
    padding: 0.5rem;
    background: var(--theme-card-bg);
    border-radius: 6px;
    justify-content: center;
  }

  .tier-display {
    font-size: 1.5rem;
    font-weight: 700;
    line-height: 1;
  }

  .tier-max {
    font-size: 1rem;
    color: var(--theme-text-muted);
    font-weight: 500;
  }

  .collection-progress {
    margin-top: 0.75rem;
  }

  .progress-info {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.5rem;
    font-size: 0.8125rem;
  }

  .progress-label {
    color: var(--theme-text-soft);
  }

  .progress-value {
    color: var(--theme-text);
    font-weight: 600;
  }

  .progress-bar {
    height: 8px;
    background: var(--theme-bg);
    border-radius: 4px;
    overflow: hidden;
    position: relative;
  }

  .progress-bar.small {
    height: 6px;
  }

  .progress-bar.gold .progress-fill {
    background: linear-gradient(90deg, #ffb700, #ffd700);
  }

  .progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #5a9cd9, #7cd95a);
    border-radius: 4px;
    transition: width 0.3s ease;
    position: relative;
  }

  .progress-fill::after {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
    animation: shimmer 2s infinite;
  }

  @keyframes shimmer {
    0% {
      transform: translateX(-100%);
    }
    100% {
      transform: translateX(100%);
    }
  }

  .collection-maxed-badge {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    padding: 0.5rem;
    background: rgba(255, 215, 0, 0.15);
    border: 1px solid rgba(255, 215, 0, 0.3);
    border-radius: 6px;
    color: #ffd700;
    font-size: 0.875rem;
    font-weight: 700;
    margin-top: 0.75rem;
  }

  .maxed-icon {
    font-size: 1rem;
  }

  @media (max-width: 768px) {
    .collections-container {
      padding: 0.75rem;
    }

    .stats-row {
      grid-template-columns: 1fr;
    }

    .collections-grid {
      grid-template-columns: 1fr;
    }

    .category-header {
      flex-direction: column;
      align-items: flex-start;
      gap: 1rem;
    }

    .category-stats {
      width: 100%;
      justify-content: space-between;
    }
  }
</style>
