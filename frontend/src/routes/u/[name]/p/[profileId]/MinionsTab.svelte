<script lang="ts">
  import type { ProfileSummaryResponse } from './profileTypes';

  export let summary: ProfileSummaryResponse;

  $: minionsData = summary.minions;
  $: categories = minionsData?.categories || {};
  $: totalMinions = minionsData?.totalMinions || 0;
  $: maxedMinions = minionsData?.maxedMinions || 0;
  $: unlockedTiers = minionsData?.unlockedTiers || 0;
  $: unlockableTiers = minionsData?.unlockableTiers || 0;
  $: slots = minionsData?.slots || { current: 5, next_threshold: 5, tiers_until_next: 5 };

  // Category display names and icons
  const categoryMeta: Record<string, { name: string; icon: string; color: string }> = {
    farming: { name: 'Farming', icon: '🌾', color: '#7cd95a' },
    mining: { name: 'Mining', icon: '⛏️', color: '#5ac8d9' },
    combat: { name: 'Combat', icon: '⚔️', color: '#d95a5a' },
    foraging: { name: 'Foraging', icon: '🌲', color: '#8b5a2b' },
    fishing: { name: 'Fishing', icon: '🎣', color: '#5a9cd9' }
  };

  const categoryOrder = ['farming', 'mining', 'combat', 'foraging', 'fishing'];

  // Convert roman numeral
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
</script>

<div class="minions-container">
  <!-- Overview Stats -->
  <div class="overview-section">
    <h2>Minions Overview</h2>
    <div class="stats-row">
      <div class="stat-card slots">
        <div class="stat-icon">🏠</div>
        <div class="stat-content">
          <div class="stat-value">{slots.current}</div>
          <div class="stat-label">Minion Slots</div>
          {#if slots.tiers_until_next}
            <div class="stat-sub">{slots.tiers_until_next} tiers until next slot</div>
          {:else}
            <div class="stat-sub maxed">Max slots unlocked!</div>
          {/if}
        </div>
      </div>

      <div class="stat-card tiers">
        <div class="stat-icon">📊</div>
        <div class="stat-content">
          <div class="stat-value">{unlockedTiers}<span class="stat-max">/{unlockableTiers}</span></div>
          <div class="stat-label">Unique Tiers Crafted</div>
          <div class="progress-bar">
            <div class="progress-fill" style="width: {progressPercent(unlockedTiers, unlockableTiers)}%"></div>
          </div>
        </div>
      </div>

      <div class="stat-card maxed">
        <div class="stat-icon">⭐</div>
        <div class="stat-content">
          <div class="stat-value">{maxedMinions}<span class="stat-max">/{totalMinions}</span></div>
          <div class="stat-label">Maxed Minions</div>
          <div class="progress-bar gold">
            <div class="progress-fill" style="width: {progressPercent(maxedMinions, totalMinions)}%"></div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Category Sections -->
  {#each categoryOrder as catKey}
    {@const cat = categories[catKey]}
    {@const meta = categoryMeta[catKey]}
    {#if cat}
      <div class="category-section">
        <div class="category-header" style="--cat-color: {meta.color}">
          <span class="category-icon">{meta.icon}</span>
          <h3>{meta.name}</h3>
          <div class="category-stats">
            <span class="tier-count">{cat.unlockedTiers}/{cat.unlockableTiers} tiers</span>
            <span class="maxed-count">{cat.maxedMinions}/{cat.totalMinions} maxed</span>
          </div>
        </div>
        
        <div class="minions-grid">
          {#each cat.minions as minion}
            <div class="minion-card" class:unlocked={minion.tier > 0} class:maxed={minion.isMaxed}>
              <div class="minion-name">{minion.name}</div>
              <div class="minion-tier" style="color: {getTierColor(minion.tier, minion.maxTier)}">
                {#if minion.tier > 0}
                  {toRoman(minion.tier)}
                  {#if minion.isMaxed}
                    <span class="maxed-star">★</span>
                  {/if}
                {:else}
                  —
                {/if}
              </div>
              <div class="tier-dots">
                {#each Array(minion.maxTier) as _, i}
                  <span 
                    class="tier-dot" 
                    class:filled={minion.tiers.includes(i + 1)}
                    class:current={i + 1 === minion.tier}
                  ></span>
                {/each}
              </div>
              <div class="tier-progress">{minion.unlockedTiers}/{minion.maxTier}</div>
            </div>
          {/each}
        </div>
      </div>
    {/if}
  {/each}
</div>

<style>
  .minions-container {
    display: flex;
    flex-direction: column;
    gap: 24px;
  }

  h2 {
    margin: 0 0 16px;
    font-size: 1.25rem;
    color: var(--theme-text-primary);
  }

  h3 {
    margin: 0;
    font-size: 1.1rem;
    font-weight: 600;
  }

  /* Overview Section */
  .overview-section {
    background: var(--theme-surface-bg);
    border: 1px solid var(--theme-surface-border);
    border-radius: 16px;
    padding: 20px;
  }

  .stats-row {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
    gap: 16px;
  }

  .stat-card {
    display: flex;
    align-items: flex-start;
    gap: 16px;
    background: rgba(148, 163, 184, 0.06);
    border: 1px solid var(--theme-surface-border);
    border-radius: 12px;
    padding: 16px;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
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
    min-width: 0;
  }

  .stat-value {
    font-size: 1.75rem;
    font-weight: 700;
    color: var(--theme-text-primary);
    line-height: 1.2;
  }

  .stat-max {
    font-size: 1rem;
    color: var(--theme-text-soft);
    font-weight: 500;
  }

  .stat-label {
    color: var(--theme-text-soft);
    font-size: 0.9rem;
    margin-top: 2px;
  }

  .stat-sub {
    font-size: 0.8rem;
    color: var(--theme-text-soft);
    margin-top: 4px;
  }

  .stat-sub.maxed {
    color: #ffd700;
  }

  .progress-bar {
    height: 6px;
    background: rgba(148, 163, 184, 0.15);
    border-radius: 3px;
    margin-top: 8px;
    overflow: hidden;
  }

  .progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #5ac8d9, #7cd95a);
    border-radius: 3px;
    transition: width 0.4s ease;
  }

  .progress-bar.gold .progress-fill {
    background: linear-gradient(90deg, #ffd700, #ffed4a);
  }

  /* Category Section */
  .category-section {
    background: var(--theme-surface-bg);
    border: 1px solid var(--theme-surface-border);
    border-radius: 16px;
    padding: 20px;
  }

  .category-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 16px;
    padding-bottom: 12px;
    border-bottom: 2px solid var(--cat-color, var(--theme-surface-border));
  }

  .category-icon {
    font-size: 1.4rem;
  }

  .category-stats {
    margin-left: auto;
    display: flex;
    gap: 16px;
    font-size: 0.85rem;
    color: var(--theme-text-soft);
  }

  .tier-count {
    color: var(--cat-color);
    font-weight: 600;
  }

  .maxed-count {
    color: #ffd700;
    font-weight: 600;
  }

  /* Minions Grid */
  .minions-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
    gap: 12px;
  }

  .minion-card {
    background: rgba(148, 163, 184, 0.06);
    border: 1px solid var(--theme-surface-border);
    border-radius: 12px;
    padding: 14px 12px;
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    transition: all 0.2s ease;
    opacity: 0.5;
  }

  .minion-card.unlocked {
    opacity: 1;
  }

  .minion-card.maxed {
    border-color: rgba(255, 215, 0, 0.4);
    background: rgba(255, 215, 0, 0.05);
  }

  .minion-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
  }

  .minion-name {
    font-weight: 600;
    font-size: 0.85rem;
    margin-bottom: 6px;
    color: var(--theme-text-primary);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    width: 100%;
  }

  .minion-tier {
    font-size: 1.3rem;
    font-weight: 700;
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    gap: 4px;
  }

  .maxed-star {
    color: #ffd700;
    font-size: 0.9rem;
  }

  .tier-dots {
    display: flex;
    flex-wrap: wrap;
    gap: 3px;
    justify-content: center;
    margin-bottom: 6px;
    max-width: 100%;
  }

  .tier-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: rgba(148, 163, 184, 0.2);
    transition: all 0.2s ease;
  }

  .tier-dot.filled {
    background: #7cd95a;
  }

  .tier-dot.current {
    background: #5ac8d9;
    box-shadow: 0 0 4px #5ac8d9;
  }

  .tier-progress {
    font-size: 0.75rem;
    color: var(--theme-text-soft);
  }

  /* Responsive adjustments */
  @media (max-width: 600px) {
    .stats-row {
      grid-template-columns: 1fr;
    }

    .category-stats {
      flex-direction: column;
      gap: 4px;
      text-align: right;
    }

    .minions-grid {
      grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
      gap: 8px;
    }

    .minion-card {
      padding: 10px 8px;
    }

    .minion-name {
      font-size: 0.75rem;
    }

    .minion-tier {
      font-size: 1.1rem;
    }

    .tier-dot {
      width: 5px;
      height: 5px;
    }
  }
</style>
