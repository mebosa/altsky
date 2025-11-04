<script lang="ts">
  import { formatNumber } from '$lib/utils';
  import type { ProfileSummaryResponse } from './profileTypes';

  export let summary: ProfileSummaryResponse;
  export let statLabels: Record<string, string>;
</script>

<section id="stats" class="grid stats-grid">
  {#each Object.entries(summary.stats) as [key, value]}
    {#if key in statLabels}
      <div class="card stat-card">
        <span class="stat-name">{statLabels[key]}</span>
        <span class="stat-value">{formatNumber(value, 0)}</span>
      </div>
    {/if}
  {/each}

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
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  }

  .stat-card {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .stat-name {
    font-size: 0.9rem;
    color: var(--theme-text-soft);
    text-transform: uppercase;
    letter-spacing: 0.08em;
  }

  .stat-value {
    font-size: 1.4rem;
    font-weight: 600;
    color: var(--theme-text-primary);
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
  }

  .essence-grid .value {
    font-weight: 600;
    color: var(--theme-text-primary);
  }
</style>
