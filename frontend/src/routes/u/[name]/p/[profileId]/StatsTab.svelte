<script lang="ts">
  import { formatNumber } from '$lib/utils';
  import type { ProfileSummaryResponse } from './profileTypes';

  export let summary: ProfileSummaryResponse;
  $: computed = summary.computed_stats?.stats || null;
  $: breakdown = summary.computed_stats?.breakdown || {};
  export let statLabels: Record<string, string>;

  let expandedStat: string | null = null;

  function toggleBreakdown(key: string) {
    if (breakdown && breakdown[key]) {
      expandedStat = expandedStat === key ? null : key;
    }
  }

  const primaryStatOrder = [
    'speed',
    'strength',
    'defense',
    'crit_damage',
    'crit_chance',
    'health',
    'intelligence'
  ] as const;

  const additionalStatOrder = [
    'bonus_attack_speed',
    'ferocity',
    'magic_find',
    'pet_luck',
    'true_defense',
    'sea_creature_chance',
    'ability_damage',
    'mining_speed',
    'mining_fortune',
    'farming_fortune',
    'foraging_fortune',
    'pristine',
    'fishing_speed',
    'health_regen',
    'vitality',
    'mending',
    'mana_regen',
    'alchemy_wisdom',
    'carpentry_wisdom',
    'combat_wisdom',
    'enchanting_wisdom',
    'farming_wisdom',
    'fishing_wisdom',
    'foraging_wisdom',
    'mining_wisdom',
    'runecrafting_wisdom',
    'social_wisdom',
    'taming_wisdom',
    'rift_time'
  ] as const;

  type KnownStatKey = (typeof primaryStatOrder)[number] | (typeof additionalStatOrder)[number];

  const percentStats = new Set<KnownStatKey>([
    'crit_damage',
    'crit_chance',
    'bonus_attack_speed',
    'sea_creature_chance',
    'ability_damage'
  ]);
  const precisionMap: Partial<Record<KnownStatKey, number>> = {
    speed: 2,
    strength: 2,
    defense: 2,
    crit_damage: 2,
    crit_chance: 2,
    health: 2,
    intelligence: 2,
    bonus_attack_speed: 2,
    ferocity: 2,
    magic_find: 2,
    pet_luck: 2,
    true_defense: 2,
    sea_creature_chance: 2,
    ability_damage: 2,
    mining_speed: 2,
    mining_fortune: 2,
    farming_fortune: 2,
    foraging_fortune: 2,
    pristine: 2,
    fishing_speed: 2,
    health_regen: 2,
    vitality: 2,
    mending: 2,
    mana_regen: 2,
    alchemy_wisdom: 2,
    carpentry_wisdom: 2,
    combat_wisdom: 2,
    enchanting_wisdom: 2,
    farming_wisdom: 2,
    fishing_wisdom: 2,
    foraging_wisdom: 2,
    mining_wisdom: 2,
    runecrafting_wisdom: 2,
    social_wisdom: 2,
    taming_wisdom: 2,
    rift_time: 2
  };

  const prettifyKey = (value: string) =>
    value
      .split('_')
      .map((segment) => (segment ? segment[0].toUpperCase() + segment.slice(1) : segment))
      .join(' ')
      .trim();

  const getStatLabel = (key: KnownStatKey) => statLabels[key] ?? prettifyKey(key);

  const getStatValue = (key: KnownStatKey) => {
    if (key === 'bonus_attack_speed') {
      return summary.stats?.bonus_attack_speed ?? summary.stats?.attack_speed;
    }
    return summary.stats?.[key];
  };

  const formatStatValue = (key: KnownStatKey, rawValue?: number | string | null) => {
    if (rawValue === null || rawValue === undefined) {
      return '-';
    }

    const numericValue = typeof rawValue === 'number' ? rawValue : Number(rawValue);
    if (!Number.isFinite(numericValue)) {
      return '-';
    }

    const fraction = precisionMap[key] ?? (Number.isInteger(numericValue) ? 0 : 2);
    const formatted = formatNumber(numericValue, fraction);
    return percentStats.has(key) ? `${formatted}%` : formatted;
  };

  const getComputedValue = (key: string) => {
    return computed?.[key];
  };

  const getDifference = (key: KnownStatKey) => {
    const original = getStatValue(key);
    const calculated = getComputedValue(key);
    
    if (original === undefined || calculated === undefined) {
      return null;
    }
    
    const diff = Number(calculated) - Number(original);
    return Math.abs(diff) > 0.01 ? diff : null;
  };

  const getDiffClass = (diff: number | null) => {
    if (diff === null) return '';
    return diff > 0 ? 'positive' : 'negative';
  };

</script>

<section id="stats" class="grid stats-grid">
  <div class="card stat-panel">
    <div class="stat-panel-head">
      <p class="stat-panel-title">Your SkyBlock Profile</p>
      <p class="stat-panel-sub">
        View your equipment, stats, and more!
        {#if computed}
          <span class="pill">Server-calculated</span>
        {/if}
      </p>
    </div>
    <div class="stat-panel-body">
      {#each primaryStatOrder as key}
        {@const diff = getDifference(key)}
        {@const hasBreakdown = !!breakdown[key]}
        <!-- svelte-ignore a11y-click-events-have-key-events -->
        <!-- svelte-ignore a11y-no-static-element-interactions -->
        <div 
          class="stat-row" 
          data-stat={key} 
          class:clickable={hasBreakdown}
          class:expanded={expandedStat === key}
          on:click={() => toggleBreakdown(key)}
        >
          <span class="stat-row-label">{getStatLabel(key)}</span>
          <span class="stat-row-value">{formatStatValue(key, getStatValue(key))}</span>
          {#if computed?.[key] !== undefined}
            <span class="stat-row-computed">
              <span class="computed-label">Calculated:</span>
              <span class="computed-value">{formatStatValue(key, computed?.[key])}</span>
              {#if diff !== null}
                <span class="diff {getDiffClass(diff)}">
                  ({diff > 0 ? '+' : ''}{formatStatValue(key, diff)})
                </span>
              {/if}
            </span>
          {/if}
          {#if hasBreakdown}
            <span class="expand-icon">{expandedStat === key ? '▼' : '▶'}</span>
          {/if}
        </div>
        {#if expandedStat === key && hasBreakdown}
          <div class="breakdown-container">
            <div class="breakdown-row base">
              <span class="source">Base Stats</span>
              <span class="value">{formatStatValue(key, breakdown[key].base)}</span>
            </div>
            {#each breakdown[key].bonuses as bonus}
              <div class="breakdown-row">
                <span class="source">{bonus.source}</span>
                <span class="value">+{formatStatValue(key, bonus.value)}</span>
              </div>
            {/each}
            <div class="breakdown-row total">
              <span class="source">Total Calculated</span>
              <span class="value">{formatStatValue(key, breakdown[key].total)}</span>
            </div>
          </div>
        {/if}
      {/each}
      <p class="stat-panel-foot">Also accessible via /stats</p>
    </div>
  </div>

  <div class="card extra-stats">
    <h3>Additional Stats</h3>
    <p class="stat-note">Every SkyBlock stat beyond the highlights.</p>
    <div class="stat-list">
      {#each additionalStatOrder as key}
        {@const diff = getDifference(key)}
        <div class="stat-chip" data-stat={key}>
          <span class="label">{getStatLabel(key)}</span>
          <span class="value">{formatStatValue(key, getStatValue(key))}</span>
          {#if computed?.[key] !== undefined}
            <span class="computed">
              calc: {formatStatValue(key, computed?.[key])}
              {#if diff !== null}
                <span class="diff-small {getDiffClass(diff)}">
                  ({diff > 0 ? '+' : ''}{formatStatValue(key, diff)})
                </span>
              {/if}
            </span>
          {/if}
        </div>
      {/each}
    </div>
  </div>

  <div class="card essence-card">
    <h3>Essence</h3>
    <div class="essence-grid">
      {#each Object.entries(summary.currencies.essence) as [key, value]}
        <div>
          <span class="label">{key}</span>
          <span class="value">{formatNumber(value, 0)}</span>
        </div>
      {/each}
    </div>
  </div>
</section>

<style>
  .stats-grid {
    grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  }

  .stat-panel {
    grid-column: 1 / -1;
    padding: 0;
    background: radial-gradient(circle at top left, rgba(99, 102, 241, 0.4), rgba(2, 6, 23, 0.95));
    border: 1px solid rgba(99, 102, 241, 0.4);
    box-shadow: 0 18px 34px rgba(2, 6, 23, 0.65);
    color: #fff;
  }

  .stat-panel-head {
    padding: 16px 24px 4px;
  }

  .stat-panel-title {
    margin: 0;
    font-size: 1.2rem;
    font-weight: 700;
    color: #a6ff77;
    text-shadow: 0 2px 12px rgba(0, 0, 0, 0.45);
  }

  .stat-panel-sub {
    margin: 4px 0 0;
    color: rgba(255, 255, 255, 0.9);
  }

  .stat-panel-body {
    padding: 4px 24px 12px;
  }

  .stat-row {
    display: grid;
    grid-template-columns: 1fr auto auto;
    align-items: center;
    gap: 12px;
    padding: 6px 0;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  }

  .stat-row:last-of-type {
    border-bottom: none;
  }

  .stat-row::before {
    content: '';
    display: inline-block;
    flex: none;
    width: 8px;
    height: 8px;
    border-radius: 2px;
    margin-right: 12px;
    background: rgba(255, 255, 255, 0.7);
  }

  .stat-row-label {
    color: rgba(255, 255, 255, 0.75);
  }

  .stat-row-value {
    font-weight: 600;
    font-size: 1.15rem;
    color: #fff;
  }

  .stat-row-computed {
    font-size: 0.95rem;
    color: rgba(255, 255, 255, 0.8);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 10px;
    padding: 2px 8px;
    background: rgba(255, 255, 255, 0.04);
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .computed-label {
    font-size: 0.8rem;
    opacity: 0.7;
  }

  .computed-value {
    font-weight: 600;
  }

  .diff {
    font-size: 0.85rem;
    font-weight: 600;
    padding: 2px 6px;
    border-radius: 6px;
  }

  .diff.positive {
    color: #4ade80;
    background: rgba(74, 222, 128, 0.1);
  }

  .diff.negative {
    color: #fb7185;
    background: rgba(251, 113, 133, 0.1);
  }

  .stat-row[data-stat='speed']::before {
    background: #f8fafc;
  }

  .stat-row[data-stat='strength']::before {
    background: #fb7185;
  }

  .stat-row[data-stat='defense']::before {
    background: #4ade80;
  }

  .stat-row[data-stat='crit_damage']::before {
    background: #60a5fa;
  }

  .stat-row[data-stat='crit_chance']::before {
    background: #38bdf8;
  }

  .stat-row[data-stat='health']::before {
    background: #f472b6;
  }

  .stat-row[data-stat='intelligence']::before {
    background: #2dd4bf;
  }

  .stat-panel-foot {
    margin: 8px 0 0;
    font-size: 0.85rem;
    color: rgba(255, 255, 255, 0.7);
  }

  .extra-stats h3 {
    margin-top: 0;
    font-size: 1rem;
    color: var(--theme-text-primary);
  }

  .stat-note {
    margin: 0 0 8px;
    font-size: 0.85rem;
    color: var(--theme-text-soft);
  }

  .extra-stats .stat-list {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 10px;
  }

  .stat-chip {
    border: 1px solid var(--theme-surface-border);
    border-radius: 12px;
    padding: 8px 12px;
    display: flex;
    flex-direction: column;
    gap: 4px;
    background: var(--theme-surface);
  }

  .stat-chip .label {
    font-size: 0.85rem;
    color: var(--theme-text-soft);
    text-transform: uppercase;
    letter-spacing: 0.08em;
  }

  .stat-chip .value {
    font-size: 1.1rem;
    font-weight: 600;
    color: var(--theme-text-primary);
  }

  .stat-chip .computed {
    font-size: 0.85rem;
    color: var(--theme-text-soft);
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .diff-small {
    font-size: 0.75rem;
    font-weight: 600;
  }

  .diff-small.positive {
    color: #4ade80;
  }

  .diff-small.negative {
    color: #fb7185;
  }

  .stat-chip[data-stat='bonus_attack_speed'] .value {
    color: var(--theme-accent);
  }

  .stat-chip[data-stat='ferocity'] .value {
    color: #e879f9;
  }

  .stat-chip[data-stat='magic_find'] .value {
    color: #fcd34d;
  }

  .stat-chip[data-stat='pet_luck'] .value {
    color: #7dd3fc;
  }

  .stat-chip[data-stat='true_defense'] .value {
    color: #38bdf8;
  }

  .pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 2px 8px;
    margin-left: 8px;
    font-size: 0.8rem;
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.12);
    border: 1px solid rgba(255, 255, 255, 0.18);
    color: #fff;
  }

  .essence-card {
    grid-column: 1 / -1;
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .essence-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 14px;
  }

  .essence-grid .label {
    font-size: 0.85rem;
    color: var(--theme-text-soft);
    text-transform: uppercase;
    letter-spacing: 0.08em;
  }

  .essence-grid .value {
    font-weight: 600;
    color: var(--theme-text-primary);
  }

  .stat-row.clickable {
    cursor: pointer;
  }
  
  .stat-row.clickable:hover {
    background-color: rgba(255, 255, 255, 0.05);
  }

  .expand-icon {
    margin-left: auto;
    color: var(--theme-text-soft);
    font-size: 0.8rem;
  }

  .breakdown-container {
    background: rgba(0, 0, 0, 0.2);
    padding: 8px 16px;
    border-radius: 0 0 8px 8px;
    margin-top: -1px;
    margin-bottom: 8px;
    border: 1px solid var(--theme-surface-border);
    border-top: none;
  }

  .breakdown-row {
    display: flex;
    justify-content: space-between;
    padding: 4px 0;
    font-size: 0.9rem;
    color: var(--theme-text-secondary);
  }

  .breakdown-row.base {
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    margin-bottom: 4px;
    padding-bottom: 8px;
  }

  .breakdown-row.total {
    border-top: 1px solid rgba(255, 255, 255, 0.1);
    margin-top: 4px;
    padding-top: 8px;
    font-weight: bold;
    color: var(--theme-text-primary);
  }

  .breakdown-row .source {
    flex: 1;
  }

  .breakdown-row .value {
    font-family: monospace;
  }
</style>
