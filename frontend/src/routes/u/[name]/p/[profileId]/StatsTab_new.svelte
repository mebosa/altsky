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
    'health',
    'defense',
    'strength',
    'speed',
    'crit_chance',
    'crit_damage',
    'intelligence',
    'bonus_attack_speed',
    'sea_creature_chance',
    'magic_find',
    'pet_luck',
    'ferocity'
  ] as const;

  const additionalStatOrder = [
    'true_defense',
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
  
  const statIcons: Partial<Record<KnownStatKey, string>> = {
    health: '❤',
    defense: '❈',
    strength: '❁',
    speed: '✦',
    crit_chance: '☣',
    crit_damage: '☠',
    intelligence: '✎',
    bonus_attack_speed: '⚔',
    sea_creature_chance: 'α',
    magic_find: '✯',
    pet_luck: '♣',
    ferocity: '⫽',
    true_defense: '❂',
    ability_damage: '๑',
    mining_speed: '⸕',
    mining_fortune: '☘',
    farming_fortune: '☘',
    foraging_fortune: '☘',
    pristine: '✧'
  };

  const statColors: Partial<Record<KnownStatKey, string>> = {
    health: '#ff5555',
    defense: '#55ff55',
    strength: '#ff5555',
    speed: '#ffffff',
    crit_chance: '#5555ff',
    crit_damage: '#5555ff',
    intelligence: '#55ffff',
    bonus_attack_speed: '#ffff55',
    sea_creature_chance: '#00aaaa',
    magic_find: '#55ffff',
    pet_luck: '#ff55ff',
    ferocity: '#ff5555',
    true_defense: '#ffffff',
    ability_damage: '#ff5555',
    mining_speed: '#ffaa00',
    mining_fortune: '#ffaa00',
    farming_fortune: '#ffaa00',
    foraging_fortune: '#ffaa00',
    pristine: '#aa00aa'
  };

  const precisionMap: Partial<Record<KnownStatKey, number>> = {
    speed: 0,
    strength: 0,
    defense: 0,
    crit_damage: 0,
    crit_chance: 0,
    health: 0,
    intelligence: 0,
    bonus_attack_speed: 0,
    ferocity: 0,
    magic_find: 0,
    pet_luck: 0,
    true_defense: 0,
    sea_creature_chance: 0,
    ability_damage: 0,
    mining_speed: 0,
    mining_fortune: 0,
    farming_fortune: 0,
    foraging_fortune: 0,
    pristine: 1,
    fishing_speed: 0,
    health_regen: 1,
    vitality: 0,
    mending: 0,
    mana_regen: 1
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

</script>

<div class="stats-container">
  <div class="main-stats">
    {#each primaryStatOrder as key}
      {@const diff = getDifference(key)}
      {@const hasBreakdown = !!breakdown[key]}
      {@const color = statColors[key] || '#ffffff'}
      
      <!-- svelte-ignore a11y-click-events-have-key-events -->
      <!-- svelte-ignore a11y-no-static-element-interactions -->
      <div 
        class="stat-card" 
        class:clickable={hasBreakdown}
        class:expanded={expandedStat === key}
        on:click={() => toggleBreakdown(key)}
        style="--stat-color: {color}"
      >
        <div class="stat-header">
          <span class="stat-icon">{statIcons[key] || ''}</span>
          <span class="stat-name">{getStatLabel(key)}</span>
          <span class="stat-value">{formatStatValue(key, getStatValue(key))}</span>
        </div>
        
        {#if computed?.[key] !== undefined}
          <div class="stat-computed">
            <span class="computed-label">Calc:</span>
            <span class="computed-val">{formatStatValue(key, computed?.[key])}</span>
            {#if diff !== null}
              <span class="diff {diff > 0 ? 'positive' : 'negative'}">
                {diff > 0 ? '+' : ''}{formatStatValue(key, diff)}
              </span>
            {/if}
          </div>
        {/if}

        {#if expandedStat === key && hasBreakdown}
          <div class="breakdown">
            <div class="breakdown-row base">
              <span>Base</span>
              <span>{formatStatValue(key, breakdown[key].base)}</span>
            </div>
            {#each breakdown[key].bonuses as bonus}
              <div class="breakdown-row">
                <span class="source">{bonus.source}</span>
                <span class="val">+{formatStatValue(key, bonus.value)}</span>
              </div>
            {/each}
          </div>
        {/if}
      </div>
    {/each}
  </div>

  <div class="misc-stats">
    <h3>Misc Stats</h3>
    <div class="misc-grid">
      {#each additionalStatOrder as key}
        <div class="misc-item">
          <span class="misc-label">{getStatLabel(key)}</span>
          <span class="misc-value">{formatStatValue(key, computed?.[key] ?? getStatValue(key))}</span>
        </div>
      {/each}
    </div>
  </div>
</div>

<style>
  .stats-container {
    display: flex;
    flex-direction: column;
    gap: 24px;
  }

  .main-stats {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 12px;
  }

  .stat-card {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    padding: 12px;
    transition: background 0.2s;
  }

  .stat-card.clickable:hover {
    background: rgba(255, 255, 255, 0.1);
    cursor: pointer;
  }

  .stat-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 4px;
  }

  .stat-icon {
    color: var(--stat-color);
    font-size: 1.2rem;
    width: 20px;
    text-align: center;
  }

  .stat-name {
    color: #aaa;
    font-size: 0.9rem;
    flex: 1;
  }

  .stat-value {
    color: var(--stat-color);
    font-weight: bold;
    font-size: 1.1rem;
  }

  .stat-computed {
    font-size: 0.8rem;
    color: #666;
    display: flex;
    justify-content: flex-end;
    gap: 4px;
  }

  .diff.positive { color: #55ff55; }
  .diff.negative { color: #ff5555; }

  .breakdown {
    margin-top: 12px;
    padding-top: 8px;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
    font-size: 0.85rem;
  }

  .breakdown-row {
    display: flex;
    justify-content: space-between;
    padding: 2px 0;
    color: #ccc;
  }

  .breakdown-row.base {
    color: #fff;
    font-weight: bold;
    margin-bottom: 4px;
  }

  .misc-stats {
    background: rgba(0, 0, 0, 0.2);
    border-radius: 8px;
    padding: 16px;
  }

  .misc-stats h3 {
    margin: 0 0 16px;
    font-size: 1.1rem;
    color: #fff;
  }

  .misc-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
    gap: 12px;
  }

  .misc-item {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .misc-label {
    font-size: 0.8rem;
    color: #888;
  }

  .misc-value {
    font-size: 1rem;
    color: #ddd;
  }
</style>