<script lang="ts">
  import { iconPack, iconPath } from '$lib/iconPack';
  import { formatNumber } from '$lib/utils';
  import type { ProfileSummaryResponse } from './profileTypes';

  export let summary: ProfileSummaryResponse;
  export let dungeonClassLabels: Record<string, string>;

  function formatTime(ms: number) {
    if (!ms) return '-';
    const seconds = Math.floor(ms / 1000);
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}:${s.toString().padStart(2, '0')}`;
  }

  function getScoreRank(score: number) {
    if (score >= 300) return 'S+';
    if (score >= 270) return 'S';
    if (score >= 230) return 'A';
    if (score >= 160) return 'B';
    if (score >= 100) return 'C';
    return 'D';
  }

  function getScoreColor(score: number) {
    if (score >= 300) return 'var(--theme-rank-s-plus)'; // Need to define or use existing
    if (score >= 270) return 'var(--theme-rank-s)';
    if (score >= 230) return 'var(--theme-rank-a)';
    return 'var(--theme-text-soft)';
  }

  const BOSS_HEADS: Record<string, string> = {
    'floor_0': '35c3024f4d9d12ddf5959b6aea3c810f5ee85176aab1b2e7f462aa1c194c342b', // Entrance (Watcher/Floor texture)
    'floor_1': '12716ecbf5b8da00b05f316ec6af61e8bd02805b21eb8e440151468dc656549c', // Bonzo
    'floor_2': '7de7bbbdf22bfe17980d4e20687e386f11d59ee1db6f8b4762391b79a5ac532d', // Scarf
    'floor_3': '9971cee8b833a62fc2a612f3503437fdf93cad692d216b8cf90bbb0538c47dd8', // Professor
    'floor_4': '8b6a72138d69fbbd2fea3fa251cabd87152e4f1c97e5f986bf685571db3cc0', // Thorn
    'floor_5': 'c1007c5b7114abec734206d4fc613da4f3a0e99f71ff949cedadc99079135a0b', // Livid
    'floor_6': 'fa06cb0c471c1c9bc169af270cd466ea701946776056e472ecdaeb49f0f4a4dc', // Sadan
    'floor_7': 'a435164c05cea299a3f016bbbed05706ebb720dac912ce4351c2296626aecd9a', // Necron
  };

  function getHeadUrl(textureId: string) {
    return `https://mc-heads.net/head/${textureId}/64`;
  }
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
    {#if summary.dungeons.catacombs.overflow > 0}
      <div class="sub accent">
        Overflow {formatNumber(summary.dungeons.catacombs.overflow)} XP
      </div>
    {/if}
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
      {#if info.overflow > 0}
        <span class="sub accent">Overflow {formatNumber(info.overflow)} XP</span>
      {/if}
    </div>
  {/each}
</section>

{#if summary.dungeons.catacombs.floors}
  <h3 class="section-title">Catacombs Floors</h3>
  <section class="grid dungeon-grid">
    {#each Object.entries(summary.dungeons.catacombs.floors) as [key, floor]}
      <div class="card dungeon-card">
        <div class="skill-header">
           {#if BOSS_HEADS[key]}
             <span class="skill-icon" aria-hidden="true">
               <img src={getHeadUrl(BOSS_HEADS[key])} alt={floor.name} loading="lazy" width="28" height="28" />
             </span>
           {/if}
           <span class="dungeon-name">{floor.name}</span>
        </div>
        <div class="sub">
          Completions: {formatNumber(floor.completions)}
          {#if floor.attempts > floor.completions}
            <span class="attempts">/ {formatNumber(floor.attempts)}</span>
          {/if}
        </div>
        <div class="sub">
          Best Score: {floor.best_score} 
          <span class="rank" style="color: {getScoreColor(floor.best_score)}">({getScoreRank(floor.best_score)})</span>
        </div>
        <div class="sub">Fastest: {formatTime(floor.fastest_time)}</div>
      </div>
    {/each}
  </section>
{/if}

{#if summary.dungeons.master_catacombs && summary.dungeons.master_catacombs.floors}
  <h3 class="section-title">Master Mode Floors</h3>
  <section class="grid dungeon-grid">
    {#each Object.entries(summary.dungeons.master_catacombs.floors) as [key, floor]}
      <div class="card dungeon-card">
        <div class="skill-header">
           {#if BOSS_HEADS[key]}
             <span class="skill-icon" aria-hidden="true">
               <img src={getHeadUrl(BOSS_HEADS[key])} alt={floor.name} loading="lazy" width="28" height="28" />
             </span>
           {/if}
           <span class="dungeon-name">{floor.name}</span>
        </div>
        <div class="sub">
          Completions: {formatNumber(floor.completions)}
          {#if floor.attempts > floor.completions}
            <span class="attempts">/ {formatNumber(floor.attempts)}</span>
          {/if}
        </div>
        <div class="sub">
          Best Score: {floor.best_score}
          <span class="rank" style="color: {getScoreColor(floor.best_score)}">({getScoreRank(floor.best_score)})</span>
        </div>
        <div class="sub">Fastest: {formatTime(floor.fastest_time)}</div>
      </div>
    {/each}
  </section>
{/if}

<style>
  .dungeon-grid {
    grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
    margin-bottom: 2rem;
  }

  .section-title {
    font-size: 1.5rem;
    font-weight: 700;
    margin: 2rem 0 1rem;
    color: var(--theme-text-primary);
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

  .sub.accent {
    color: var(--theme-accent);
    font-weight: 600;
  }

  .attempts {
    color: var(--theme-text-soft);
    font-size: 0.85em;
  }

  .rank {
    font-weight: 700;
    margin-left: 4px;
  }
</style>
