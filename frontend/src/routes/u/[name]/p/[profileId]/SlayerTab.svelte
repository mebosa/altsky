<script lang="ts">
  import { iconPack, iconPath } from '$lib/iconPack';
  import { formatNumber } from '$lib/utils';
  import type { ProfileSummaryResponse } from './profileTypes';

  export let summary: ProfileSummaryResponse;
  export let slayerLabels: Record<string, string>;
</script>

<section id="slayer" class="grid slayer-grid">
  {#each Object.entries(summary.slayer) as [key, info]}
    {#if key !== 'total_xp' && typeof info !== 'number'}
      {@const slayerInfo = info as { level: number; xp: number }}
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
</style>
