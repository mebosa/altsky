<script lang="ts">
  import { iconPack, iconPath } from '$lib/iconPack';
  import { formatNumber } from '$lib/utils';
  import type { ProfileSummaryResponse, SlayerBoss } from './profileTypes';

  export let summary: ProfileSummaryResponse;
  export let slayerLabels: Record<string, string>;

  const formatDropLabel = (value: string) =>
    value.replace(/^drops?_/, '').replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase());

  const sortTierEntries = (tiers: Record<string, number>) =>
    Object.entries(tiers).sort((a, b) => Number(a[0]) - Number(b[0]));
</script>

<section id="slayer" class="grid slayer-grid">
  {#each Object.entries(summary.slayer) as [key, info]}
    {#if key !== 'total_xp' && typeof info !== 'number'}
      {@const slayerInfo = info as SlayerBoss}
      {@const killsTotal = slayerInfo.kills?.total ?? 0}
      {@const killEntries = slayerInfo.kills ? sortTierEntries(slayerInfo.kills.tiers ?? {}) : []}
      {@const dropEntries = slayerInfo.drops ? Object.entries(slayerInfo.drops).sort((a, b) => Number(b[1]) - Number(a[1]) || a[0].localeCompare(b[0])) : []}
      <div class="card slayer-card">
        <div class="skill-header">
          <span class="skill-icon" aria-hidden="true">
            <img
              src={iconPath($iconPack, key, 'slayer')}
              alt=""
              loading="lazy"
              width="28"
              height="28"
            />
          </span>
          <div class="skill-info">
            <span class="slayer-name">{slayerLabels[key] ?? key}</span>
            <div class="slayer-level">Lv. {slayerInfo.level}</div>
            <div class="slayer-xp">{formatNumber(slayerInfo.xp)} XP</div>
          </div>
        </div>
        <div class="slayer-metric">
          <span class="metric-label">Boss kills</span>
          <span class="metric-value">{formatNumber(killsTotal)}</span>
        </div>
        {#if killEntries.length}
          <div class="slayer-kill-tiers">
            {#each killEntries as [tier, count]}
              <span class="tier-chip">T{tier} {formatNumber(count)}</span>
            {/each}
          </div>
        {/if}
        <div class="slayer-drops">
          <span class="metric-label">Drops</span>
          {#if dropEntries.length}
            <div class="slayer-drop-list">
              {#each dropEntries as [drop, count]}
                <span class="drop-chip">
                  {formatDropLabel(drop)}
                  <span class="drop-count">{formatNumber(count)}</span>
                </span>
              {/each}
            </div>
          {:else}
            <span class="slayer-drop-empty">No drop data available</span>
          {/if}
        </div>
      </div>
    {/if}
  {/each}
</section>

<style>
  .slayer-grid {
    grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  }

  .slayer-card {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .skill-header {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .skill-icon {
    display: inline-flex;
    width: 44px;
    height: 44px;
    border-radius: 14px;
    align-items: center;
    justify-content: center;
    background: rgba(148, 163, 184, 0.12);
  }

  .skill-icon img {
    width: 28px;
    height: 28px;
    object-fit: contain;
  }

  .skill-info {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .slayer-name {
    font-weight: 600;
    color: var(--theme-text-primary);
  }

  .slayer-level,
  .slayer-xp {
    font-size: 0.9rem;
    color: var(--theme-text-soft);
  }

  .slayer-metric {
    display: flex;
    align-items: baseline;
    gap: 8px;
    font-size: 0.9rem;
    color: var(--theme-text-soft);
  }

  .metric-label {
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-size: 0.7rem;
  }

  .metric-value {
    font-weight: 600;
    color: var(--theme-text-primary);
    letter-spacing: 0.02em;
  }

  .slayer-kill-tiers,
  .slayer-drop-list {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
  }

  .tier-chip,
  .drop-chip {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 3px 10px;
    border-radius: 999px;
    border: 1px solid rgba(148, 163, 184, 0.2);
    background: rgba(148, 163, 184, 0.08);
    font-size: 0.75rem;
    color: var(--theme-text-secondary);
  }

  .drop-count {
    font-weight: 600;
    color: var(--theme-text-primary);
  }

  .slayer-drops {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .slayer-drop-empty {
    font-size: 0.85rem;
    color: var(--theme-text-soft);
    opacity: 0.75;
  }
</style>
