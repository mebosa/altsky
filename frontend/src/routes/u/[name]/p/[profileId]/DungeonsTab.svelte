<script lang="ts">
  import { iconPack, iconPath } from '$lib/iconPack';
  import { formatNumber } from '$lib/utils';
  import type { ProfileSummaryResponse } from './profileTypes';

  export let summary: ProfileSummaryResponse;
  export let dungeonClassLabels: Record<string, string>;
</script>

<section id="dungeons" class="grid dungeon-grid">
  <div class="card dungeon-card featured">
    <div class="skill-header">
      <span class="skill-icon" aria-hidden="true">
        <img
          src={iconPath($iconPack, 'catacombs', 'dungeons')}
          alt=""
          loading="lazy"
          width="28"
          height="28"
        />
      </span>
      <h3>Catacombs</h3>
    </div>
    <div class="catacombs-level">Lv. {summary.dungeons.catacombs.level}</div>
    <div class="sub">Total XP {formatNumber(summary.dungeons.catacombs.xp)}</div>
  </div>

  {#each Object.entries(summary.dungeons.classes) as [key, info]}
    <div class="card dungeon-card">
      <div class="skill-header">
        <span class="skill-icon" aria-hidden="true">
          <img
            src={iconPath($iconPack, key, 'dungeons')}
            alt=""
            loading="lazy"
            width="28"
            height="28"
          />
        </span>
        <span class="dungeon-name">{dungeonClassLabels[key] ?? key}</span>
      </div>
      <span class="dungeon-level">Lv. {info.level}</span>
      <span class="sub">{formatNumber(info.xp)} XP</span>
    </div>
  {/each}
</section>

<style>
  .dungeon-grid {
    grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  }

  .dungeon-card {
    display: flex;
    flex-direction: column;
    gap: 10px;
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

  .catacombs-level {
    font-size: 2rem;
    font-weight: 700;
    color: var(--theme-text-primary);
  }

  .dungeon-name {
    font-weight: 600;
    color: var(--theme-text-primary);
  }

  .dungeon-level {
    font-size: 1.1rem;
    font-weight: 600;
    color: var(--theme-text-primary);
  }

  .sub {
    font-size: 0.95rem;
    color: var(--theme-text-soft);
  }
</style>
