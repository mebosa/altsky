<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { formatNumber } from '$lib/utils';
  import type { ProfileSummaryResponse } from './profileTypes';
  import { slide } from 'svelte/transition';

  export let summary: ProfileSummaryResponse;
  $: computed = summary.computed_stats?.stats || null;
  $: breakdown = summary.computed_stats?.breakdown || {};
  export let statLabels: Record<string, string>;

  const dispatch = createEventDispatcher<{ weaponchange: { slot: number | null; id: string | null } }>();

  let weaponSlot = '';
  let weaponId = '';
  let weaponSlotDirty = false;
  let weaponIdDirty = false;
  $: if (summary) {
    if (!weaponSlotDirty && summary.weapon_selected_slot !== undefined) {
      weaponSlot =
        summary.weapon_selected_slot !== null ? String(summary.weapon_selected_slot) : '';
    }
    if (!weaponIdDirty && summary.weapon_selected_id !== undefined) {
      weaponId = summary.weapon_selected_id ?? '';
    }
    if (weaponSlotDirty && summary.weapon_selected_slot !== undefined) {
      const normalized = summary.weapon_selected_slot !== null ? String(summary.weapon_selected_slot) : '';
      if (normalized === weaponSlot) {
        weaponSlotDirty = false;
      }
    }
    if (weaponIdDirty && summary.weapon_selected_id !== undefined) {
      const normalizedId = summary.weapon_selected_id ?? '';
      if (normalizedId === weaponId) {
        weaponIdDirty = false;
      }
    }
  }

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
    'bonus_attack_speed'
  ] as const;

  const additionalStatOrder = [
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
    'rift_time',
    'damage',
    'swing_range',
    'sweep',
    'weapon_ability_damage',
    'treasure_chance',
    'trophy_fish_chance',
    'double_hook_chance',
    'rift_damage',
    'rift_health',
    'rift_intelligence',
    'rift_mana_regen',
    'rift_walk_speed',
    'cold_resistance',
    'heat_resistance',
    'pressure_resistance',
    'respiration'
  ] as const;

  type KnownStatKey = (typeof primaryStatOrder)[number] | (typeof additionalStatOrder)[number];

  const percentStats = new Set<KnownStatKey>([
    'crit_damage',
    'crit_chance',
    'bonus_attack_speed',
    'sea_creature_chance',
    'ability_damage',
    'treasure_chance',
    'trophy_fish_chance',
    'double_hook_chance'
  ]);

  const statColors: Partial<Record<KnownStatKey, string>> = {
    health: '#ef4444',      // Red
    defense: '#22c55e',     // Green
    strength: '#f97316',    // Orange
    speed: '#f0f9ff',       // White/Blueish
    crit_chance: '#3b82f6', // Blue
    crit_damage: '#6366f1', // Indigo
    intelligence: '#06b6d4',// Cyan
    bonus_attack_speed: '#eab308', // Yellow
    magic_find: '#fcd34d',
    pet_luck: '#d8b4fe',
    ferocity: '#f472b6',
    true_defense: '#cbd5e1'
  };

  const statIcons: Partial<Record<KnownStatKey, string>> = {
    health: '\u2764',
    defense: '\u2748',
    strength: '\u2741',
    speed: '\u2726',
    crit_chance: '\u2623',
    crit_damage: '\u2620',
    intelligence: '\u270E',
    bonus_attack_speed: '\u2694',
    ferocity: '\u2AFD',
    magic_find: '\u272F',
    pet_luck: '\u2663',
    true_defense: '\u2742',
    sea_creature_chance: '\u03B1',
    ability_damage: '\u0E51',
    mining_speed: '\u2E15',
    mining_fortune: '\u2618',
    farming_fortune: '\u2618',
    foraging_fortune: '\u2618',
    pristine: '\u2727',
    fishing_speed: '\u2602',
    health_regen: '\u2763',
    vitality: '\u2668',
    mending: '\u2604',
    mana_regen: '\u{1F5F2}',
    alchemy_wisdom: '\u262F',
    carpentry_wisdom: '\u262F',
    combat_wisdom: '\u262F',
    enchanting_wisdom: '\u262F',
    farming_wisdom: '\u262F',
    fishing_wisdom: '\u262F',
    foraging_wisdom: '\u262F',
    mining_wisdom: '\u262F',
    runecrafting_wisdom: '\u262F',
    social_wisdom: '\u262F',
    taming_wisdom: '\u262F',
    rift_time: '\u0444',
    damage: '\u2741',
    swing_range: '\u24C8',
    sweep: '\u24C8',
    weapon_ability_damage: '\u0E51',
    treasure_chance: '\u2618',
    trophy_fish_chance: '\u2602',
    double_hook_chance: '\u{1F3A3}',
    rift_damage: '\u2741',
    rift_health: '\u2764',
    rift_intelligence: '\u270E',
    rift_mana_regen: '\u{1F5F2}',
    rift_walk_speed: '\u2726',
    cold_resistance: '\u2744',
    heat_resistance: '\u2668',
    pressure_resistance: '\u24C5',
    respiration: '\u24C7'
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
    mana_regen: 1,
    rift_time: 0,
    swing_range: 1,
    sweep: 0,
    damage: 0,
    weapon_ability_damage: 0,
    treasure_chance: 1,
    trophy_fish_chance: 1,
    double_hook_chance: 1
  };

  const preferOriginalStats = new Set<KnownStatKey>([
    'rift_time',
    'rift_damage',
    'rift_health',
    'rift_intelligence',
    'rift_mana_regen',
    'rift_walk_speed',
    'double_hook_chance'
  ]);

  const prettifyKey = (value: string) =>
    value
      .split('_')
      .map((segment) => (segment ? segment[0].toUpperCase() + segment.slice(1) : segment))
      .join(' ')
      .trim();

  const getStatLabel = (key: KnownStatKey) => statLabels[key] ?? prettifyKey(key);

  const getOriginalStatValue = (key: KnownStatKey) => {
    if (key === 'bonus_attack_speed') {
      return summary.stats?.bonus_attack_speed ?? summary.stats?.attack_speed;
    }
    return summary.stats?.[key];
  };

  const getStatValue = (key: KnownStatKey) => {
    const original = getOriginalStatValue(key);
    if (preferOriginalStats.has(key) && original !== undefined) {
      return original;
    }
    const calculated = getComputedValue(key);
    if (calculated !== undefined) {
      return calculated;
    }
    return original;
  };

  const formatStatValue = (key: KnownStatKey, rawValue?: number | string | null) => {
    if (rawValue === null || rawValue === undefined) {
      return '-';
    }

    const numericValue = typeof rawValue === 'number' ? rawValue : Number(rawValue);
    if (!Number.isFinite(numericValue)) {
      return '-';
    }

    const fraction = precisionMap[key] ?? (Number.isInteger(numericValue) ? 0 : 1);
    const formatted = formatNumber(numericValue, fraction);
    return percentStats.has(key) ? `${formatted}%` : formatted;
  };

  const getComputedValue = (key: KnownStatKey) => {
    if (preferOriginalStats.has(key)) {
      const original = getOriginalStatValue(key);
      if (original !== undefined) {
        return undefined;
      }
    }
    if (key === 'bonus_attack_speed') {
      return computed?.bonus_attack_speed ?? computed?.attack_speed;
    }
    return computed?.[key];
  };

  const getDifference = (key: KnownStatKey) => {
    const original = getOriginalStatValue(key);
    const calculated = getComputedValue(key);
    
    if (original === undefined || calculated === undefined) {
      return null;
    }
    
    const diff = Number(calculated) - Number(original);
    return Math.abs(diff) > 0.1 ? diff : null;
  };

  const handleWeaponChange = (event: Event) => {
    const target = event.target as HTMLSelectElement;
    const value = target?.value ?? '';
    weaponSlot = value;
    weaponSlotDirty = true;
    weaponId = '';
    weaponIdDirty = true;
    if (!value) {
      dispatch('weaponchange', { slot: null, id: null });
      return;
    }
    const slot = Number(value);
    if (!Number.isFinite(slot)) {
      return;
    }
    dispatch('weaponchange', { slot, id: null });
  };

  const handleWeaponIdChange = (event: Event) => {
    const target = event.target as HTMLInputElement;
    const value = target?.value ?? '';
    const trimmed = value.trim();
    weaponId = value;
    weaponIdDirty = true;
    weaponSlot = '';
    weaponSlotDirty = true;
    if (!trimmed) {
      dispatch('weaponchange', { slot: null, id: null });
      return;
    }
    dispatch('weaponchange', { slot: null, id: trimmed });
  };

</script>

<div class="stats-container">
  <!-- Header -->
  <div class="section-header">
    <div class="title-group">
      <h2>Profile Stats</h2>
      {#if computed}
        <span class="badge-calculated">Server Calculated</span>
      {/if}
    </div>
    <p class="subtitle">Your equipment, skills, and accessory stats combined.</p>
    {#if summary?.weapon_candidates?.length}
      <div class="weapon-select">
        <label for="weapon-select">Weapon</label>
        <select id="weapon-select" bind:value={weaponSlot} on:change={handleWeaponChange}>
          <option value="">Auto</option>
          {#each summary.weapon_candidates as weapon}
            <option value={weapon.slot}>
              {weapon.name ?? weapon.id} (Slot {weapon.slot + 1})
            </option>
          {/each}
        </select>
      </div>
    {:else if summary?.weapon_catalog?.length}
      <div class="weapon-select">
        <label for="weapon-input">Weapon</label>
        <input
          id="weapon-input"
          list="weapon-catalog"
          placeholder="Type weapon ID or name"
          bind:value={weaponId}
          on:change={handleWeaponIdChange}
        />
        <datalist id="weapon-catalog">
          {#each summary.weapon_catalog as weapon}
            <option value={weapon.id}>{weapon.name ?? weapon.id}</option>
          {/each}
        </datalist>
      </div>
    {/if}
  </div>

  <!-- Primary Stats Grid -->
  <div class="primary-grid">
    {#each primaryStatOrder as key}
      {@const value = getStatValue(key)}
      {@const calcValue = getComputedValue(key)}
      {@const diff = getDifference(key)}
      {@const hasBreakdown = !!breakdown[key]}
      {@const color = statColors[key] || '#fff'}
      {@const icon = statIcons[key] || ''}
      
      <!-- svelte-ignore a11y-click-events-have-key-events -->
      <!-- svelte-ignore a11y-no-static-element-interactions -->
      <div 
        class="stat-card" 
        class:interactive={hasBreakdown}
        class:expanded={expandedStat === key}
        style="--stat-color: {color}"
        on:click={() => toggleBreakdown(key)}
      >
        <div class="stat-main">
          <div class="icon-box">
            <span class="stat-icon">{icon}</span>
          </div>
          <div class="info-box">
            <span class="stat-label">{getStatLabel(key)}</span>
            <div class="value-row">
              <span class="stat-value">
                {formatStatValue(key, calcValue ?? value)}
              </span>
              {#if diff !== null}
                <span class="diff-badge" class:positive={diff > 0} class:negative={diff < 0}>
                  {diff > 0 ? '+' : ''}{formatStatValue(key, diff)}
                </span>
              {/if}
            </div>
          </div>
          {#if hasBreakdown}
            <div class="chevron">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M6 9l6 6 6-6" />
              </svg>
            </div>
          {/if}
        </div>

        {#if expandedStat === key && hasBreakdown}
          <div class="breakdown" transition:slide={{ duration: 200 }}>
            <div class="breakdown-content">
              <div class="bd-row base">
                <span>Base</span>
                <span>{formatStatValue(key, breakdown[key].base)}</span>
              </div>
              {#each breakdown[key].bonuses as bonus}
                <div class="bd-row">
                  <span class="bd-source">{bonus.source}</span>
                  <span class="bd-val">+{formatStatValue(key, bonus.value)}</span>
                </div>
              {/each}
            </div>
          </div>
        {/if}
      </div>
    {/each}
  </div>

  <!-- Secondary Stats -->
  <div class="secondary-section">
    <h3>Misc Stats</h3>
    <div class="secondary-grid">
      {#each additionalStatOrder as key}
        {@const value = getStatValue(key)}
        {@const calcValue = getComputedValue(key)}
        {@const displayValue = calcValue ?? value}
        
        {#if displayValue && Number(displayValue) !== 0}
          <div class="mini-stat">
            <span class="mini-label">
              {#if statIcons[key]}
                <span class="mini-icon" style="color: {statColors[key] || 'var(--theme-text-soft)'}">
                  {statIcons[key]}
                </span>
              {/if}
              {getStatLabel(key)}
            </span>
            <span class="mini-value" style="color: {statColors[key] || 'var(--theme-text-primary)'}">
              {formatStatValue(key, displayValue)}
            </span>
          </div>
        {/if}
      {/each}
    </div>
  </div>

  <!-- Essence -->
  {#if summary.currencies.essence}
    <div class="essence-section">
      <h3>Essence</h3>
      <div class="essence-list">
        {#each Object.entries(summary.currencies.essence) as [key, value]}
          {#if Number(value) > 0}
            <div class="essence-item">
              <span class="ess-name">{key}</span>
              <span class="ess-val">{formatNumber(Number(value), 0)}</span>
            </div>
          {/if}
        {/each}
      </div>
    </div>
  {/if}
</div>

<style>
  .stats-container {
    display: flex;
    flex-direction: column;
    gap: 24px;
    padding: 8px 0;
  }

  .section-header {
    margin-bottom: 8px;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .title-group {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 6px;
  }

  h2 {
    font-size: 1.5rem;
    font-weight: 700;
    margin: 0;
    color: var(--theme-text-primary);
  }

  .subtitle {
    margin: 0;
    color: var(--theme-text-soft);
    font-size: 0.95rem;
  }

  .badge-calculated {
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    font-weight: 600;
    padding: 4px 10px;
    border-radius: 20px;
    background: rgba(99, 102, 241, 0.15);
    color: #818cf8;
    border: 1px solid rgba(99, 102, 241, 0.25);
  }

  .weapon-select {
    display: flex;
    flex-direction: column;
    gap: 6px;
    max-width: 280px;
  }

  .weapon-select label {
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--theme-text-soft);
    font-weight: 600;
  }

  .weapon-select select,
  .weapon-select input {
    background: var(--theme-surface);
    border: 1px solid var(--theme-surface-border);
    border-radius: 10px;
    padding: 8px 12px;
    color: var(--theme-text-primary);
  }

  /* Primary Grid */
  .primary-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
    gap: 16px;
  }

  .stat-card {
    background: var(--theme-surface);
    border: 1px solid var(--theme-surface-border);
    border-radius: 16px;
    overflow: hidden;
    transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
    position: relative;
  }

  .stat-card.interactive {
    cursor: pointer;
  }

  .stat-card.interactive:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 20px rgba(0, 0, 0, 0.2);
    border-color: rgba(255, 255, 255, 0.15);
  }

  .stat-card.expanded {
    border-color: var(--stat-color);
    background: linear-gradient(to bottom, var(--theme-surface), rgba(15, 23, 42, 0.95));
  }

  .stat-main {
    padding: 16px;
    display: flex;
    align-items: center;
    gap: 16px;
  }

  .icon-box {
    width: 42px;
    height: 42px;
    border-radius: 12px;
    background: color-mix(in srgb, var(--stat-color) 15%, transparent);
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }

  .stat-icon {
    font-size: 1.2rem;
    color: var(--stat-color);
  }

  .info-box {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .stat-label {
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--theme-text-soft);
    font-weight: 600;
  }

  .value-row {
    display: flex;
    align-items: baseline;
    gap: 8px;
  }

  .stat-value {
    font-size: 1.4rem;
    font-weight: 700;
    color: var(--theme-text-primary);
    line-height: 1;
  }

  .diff-badge {
    font-size: 0.75rem;
    font-weight: 600;
    padding: 2px 6px;
    border-radius: 4px;
  }

  .diff-badge.positive {
    color: #4ade80;
    background: rgba(74, 222, 128, 0.1);
  }

  .diff-badge.negative {
    color: #fb7185;
    background: rgba(251, 113, 133, 0.1);
  }

  .chevron {
    color: var(--theme-text-soft);
    opacity: 0.5;
    transition: transform 0.2s ease;
  }

  .stat-card.expanded .chevron {
    transform: rotate(180deg);
    opacity: 1;
  }

  /* Breakdown */
  .breakdown {
    border-top: 1px solid rgba(255, 255, 255, 0.06);
    background: rgba(0, 0, 0, 0.2);
  }

  .breakdown-content {
    padding: 12px 16px;
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .bd-row {
    display: flex;
    justify-content: space-between;
    font-size: 0.85rem;
    color: var(--theme-text-secondary);
  }

  .bd-row.base {
    padding-bottom: 6px;
    margin-bottom: 6px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
    font-weight: 500;
  }

  .bd-val {
    font-family: 'Space Grotesk', monospace;
    color: var(--theme-text-primary);
  }

  /* Secondary Stats */
  .secondary-section h3,
  .essence-section h3 {
    font-size: 1.1rem;
    color: var(--theme-text-primary);
    margin: 0 0 16px;
  }

  .secondary-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
    gap: 12px;
  }

  .mini-stat {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 10px;
    padding: 10px 14px;
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .mini-label {
    font-size: 0.75rem;
    color: var(--theme-text-soft);
    text-transform: uppercase;
    letter-spacing: 0.02em;
    display: inline-flex;
    align-items: center;
    gap: 6px;
  }

  .mini-icon {
    font-size: 0.85rem;
    line-height: 1;
  }

  .mini-value {
    font-size: 1rem;
    font-weight: 600;
  }

  /* Essence */
  .essence-list {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
  }

  .essence-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 6px 12px;
    background: rgba(0, 0, 0, 0.2);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 8px;
  }

  .ess-name {
    font-size: 0.85rem;
    color: var(--theme-text-secondary);
    text-transform: capitalize;
  }

  .ess-val {
    font-size: 0.9rem;
    font-weight: 600;
    color: #fbbf24; /* Amber */
  }

  @media (max-width: 640px) {
    .primary-grid {
      grid-template-columns: 1fr;
    }
  }
</style>
