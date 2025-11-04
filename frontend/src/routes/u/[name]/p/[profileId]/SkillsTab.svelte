<script lang="ts">
  import { iconPack, iconPath } from '$lib/iconPack';
  import { formatNumber, formatPercent } from '$lib/utils';
  import type { ProfileSummaryResponse, SkillStat } from './profileTypes';

  export let summary: ProfileSummaryResponse;
  export let skillOrder: ReadonlyArray<{ key: string; label: string }>;
</script>

<section id="skills" class="grid">
  {#each skillOrder as skill}
    {@const data = summary.skills[skill.key] as SkillStat | undefined}
    {#if data}
      <div class="card skill-card">
        <div class="skill-header">
          <span class="skill-icon" aria-hidden="true">
            <img src={iconPath($iconPack, skill.key)} alt="" loading="lazy" width="28" height="28" />
          </span>
          <div class="skill-info">
            <span class="skill-name">{skill.label}</span>
            <span class="skill-level">Lv. {data.level}</span>
          </div>
        </div>
        <div class="progress">
          <div
            class="progress-bar"
            style={`width:${Math.min(100, data.progress * 100).toFixed(1)}%`}
          ></div>
        </div>
        <div class="progress-label">
          {#if data.level >= 60}
            Total XP: {formatNumber(data.xp)}
          {:else}
            {formatPercent(data.progress * 100, 1)} | {formatNumber(data.current)} / {formatNumber(data.to_next)}
          {/if}
        </div>
      </div>
    {/if}
  {/each}
</section>

<style>
  .skill-card {
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
  }

  .skill-name {
    font-weight: 600;
    color: var(--theme-text-primary);
  }

  .skill-level {
    font-size: 0.9rem;
    color: var(--theme-text-soft);
  }

  .progress {
    height: 10px;
    background: rgba(148, 163, 184, 0.24);
    border-radius: 999px;
    overflow: hidden;
  }

  .progress-bar {
    height: 100%;
    background: linear-gradient(135deg, var(--theme-accent), var(--theme-accent-secondary));
    border-radius: 999px;
    transition: width 0.4s ease;
  }

  .progress-label {
    font-size: 0.9rem;
    color: var(--theme-text-soft);
  }
</style>
