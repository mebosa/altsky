<script lang="ts">
  import { formatNumber } from '$lib/utils';
  import type { ProfileSummaryResponse } from './profileTypes';

  export let summary: ProfileSummaryResponse;
  export let statLabels: Record<string, string>;

  const primaryStatOrder = [
    'speed',
    'strength',
    'defense',
    'crit_damage',
    'crit_chance',
    'health',
    'intelligence'
  ] as const;

  const secondaryStatOrder = [
    'attack_speed',
    'ferocity',
    'magic_find',
    'pet_luck',
    'true_defense'
  ] as const;

  const orderedStatKeys = [...primaryStatOrder, ...secondaryStatOrder] as const;
  type KnownStatKey = (typeof orderedStatKeys)[number];

  const percentStats = new Set<KnownStatKey>(['crit_damage', 'crit_chance', 'attack_speed']);
  const precisionMap: Partial<Record<KnownStatKey, number>> = {
    speed: 2,
    strength: 2,
    defense: 2,
    crit_damage: 2,
    crit_chance: 2,
    health: 2,
    intelligence: 2,
    attack_speed: 2,
    ferocity: 2,
    magic_find: 2,
    pet_luck: 2,
    true_defense: 2
  };

  const formatStatValue = (key: KnownStatKey, rawValue?: number) => {
    if (typeof rawValue !== 'number' || !Number.isFinite(rawValue)) {
      return '-';
    }

    const fraction = precisionMap[key] ?? (Number.isInteger(rawValue) ? 0 : 2);
    const formatted = formatNumber(rawValue, fraction);
    return percentStats.has(key) ? `${formatted}%` : formatted;
  };
</script>

<section id="stats" class="grid stats-grid">
  <div class="card stat-panel">
    <div class="stat-panel-head">
      <p class="stat-panel-title">Your SkyBlock Profile</p>
      <p class="stat-panel-sub">View your equipment, stats, and more!</p>
    </div>
    <div class="stat-panel-body">
      {#each primaryStatOrder as key}
        <div class="stat-row" data-stat={key}>
          <span class="stat-row-label">{statLabels[key] ?? key}</span>
          <span class="stat-row-value">{formatStatValue(key, summary.stats?.[key])}</span>
        </div>
      {/each}
      <p class="stat-panel-foot">Also accessible via /stats</p>
    </div>
  </div>

  <div class="card extra-stats">
    <h3>Additional Stats</h3>
    <div class="stat-list">
      {#each secondaryStatOrder as key}
        <div class="stat-chip" data-stat={key}>
          <span class="label">{statLabels[key] ?? key}</span>
          <span class="value">{formatStatValue(key, summary.stats?.[key])}</span>
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
    padding: 20px 24px 8px;
  }

  .stat-panel-title {
    margin: 0;
    font-size: 1.2rem;
    font-weight: 700;
    color: #a6ff77;
    text-shadow: 0 2px 12px rgba(0, 0, 0, 0.45);
  }

  .stat-panel-sub {
    margin: 6px 0 0;
    color: rgba(255, 255, 255, 0.9);
  }

  .stat-panel-body {
    padding: 4px 24px 18px;
  }

  .stat-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 20px;
    padding: 10px 0;
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
    margin: 12px 0 0;
    font-size: 0.85rem;
    color: rgba(255, 255, 255, 0.7);
  }

  .extra-stats h3 {
    margin-top: 0;
    font-size: 1rem;
    color: var(--theme-text-primary);
  }

  .extra-stats .stat-list {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 12px;
  }

  .stat-chip {
    border: 1px solid var(--theme-surface-border);
    border-radius: 12px;
    padding: 12px 14px;
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

  .stat-chip[data-stat='attack_speed'] .value {
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
</style>
