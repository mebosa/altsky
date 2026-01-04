<script lang="ts">
  import { onMount } from 'svelte';
  import { get } from '$lib/api';
  import { loadRecent, formatNumber, formatTime } from '$lib/utils';
  import { iconPack, iconPath } from '$lib/iconPack';
  import { dungeonClassLabels } from '../../u/[name]/p/[profileId]/profileConstants';

  let username = '';
  let loading = false;
  let error = '';
  let playerData: any = null;
  let selectedProfileId: string | null = null;

  // Reuse the logic from DungeonsTab
  function getScoreRank(score: number) {
    if (score >= 300) return 'S+';
    if (score >= 270) return 'S';
    if (score >= 230) return 'A';
    if (score >= 160) return 'B';
    if (score >= 100) return 'C';
    return 'D';
  }

  function getScoreColor(score: number) {
    if (score >= 300) return 'var(--theme-rank-s-plus)';
    if (score >= 270) return 'var(--theme-rank-s)';
    if (score >= 230) return 'var(--theme-rank-a)';
    return 'var(--theme-text-soft)';
  }

  const BOSS_HEADS: Record<string, string> = {
    'floor_0': '35c3024f4d9d12ddf5959b6aea3c810f5ee85176aab1b2e7f462aa1c194c342b',
    'floor_1': '12716ecbf5b8da00b05f316ec6af61e8bd02805b21eb8e440151468dc656549c',
    'floor_2': '7de7bbbdf22bfe17980d4e20687e386f11d59ee1db6f8b4762391b79a5ac532d',
    'floor_3': '9971cee8b833a62fc2a612f3503437fdf93cad692d216b8cf90bbb0538c47dd8',
    'floor_4': '8b6a72138d69fbbd2fea3fa251cabd87152e4f1c97e5f986bf685571db3cc0',
    'floor_5': 'c1007c5b7114abec734206d4fc613da4f3a0e99f71ff949cedadc99079135a0b',
    'floor_6': 'fa06cb0c471c1c9bc169af270cd466ea701946776056e472ecdaeb49f0f4a4dc',
    'floor_7': 'a435164c05cea299a3f016bbbed05706ebb720dac912ce4351c2296626aecd9a',
  };

  function getHeadUrl(textureId: string) {
    return `https://mc-heads.net/head/${textureId}/64`;
  }

  async function fetchPlayer(name: string) {
    if (!name) return;
    loading = true;
    error = '';
    playerData = null;
    try {
      const player = await get<any>(`/api/player/${name}`);
      if (player.error) {
        error = player.error;
      } else if (player.profiles && player.profiles.length > 0) {
        // Select the selected profile or the first one
        const profile = player.profiles.find((p: any) => p.selected) || player.profiles[0];
        selectedProfileId = profile.profile_id;
        
        // Fetch profile details including dungeons
        const summary = await get<any>(`/api/player/${name}/${selectedProfileId}`);
        playerData = summary;
      } else {
        error = 'No profiles found.';
      }
    } catch (e: any) {
      error = e.message || 'Failed to load player data.';
    } finally {
      loading = false;
    }
  }

  function handleSearch() {
    fetchPlayer(username);
  }

  onMount(() => {
    const recent = loadRecent();
    if (recent.length > 0) {
      username = recent[0];
      fetchPlayer(username);
    }
  });
</script>

<svelte:head>
  <title>Dungeon Dashboard | AltSky</title>
</svelte:head>

<div class="wrap">
  <div class="header">
    <a href="/dungeons" class="back-link">← Back to Dungeons</a>
    <h1>Dungeon Dashboard</h1>
  </div>

  <div class="search-bar">
    <input 
      type="text" 
      placeholder="Enter username" 
      bind:value={username} 
      on:keydown={(e) => e.key === 'Enter' && handleSearch()}
    />
    <button on:click={handleSearch} disabled={loading}>
      {loading ? 'Loading...' : 'Load Stats'}
    </button>
  </div>

  {#if error}
    <div class="error">{error}</div>
  {/if}

  {#if playerData && playerData.dungeons}
    <div class="dashboard-content">
      <section class="grid dungeon-grid">
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
          <div class="catacombs-level">Lv. {playerData.dungeons.catacombs.level}</div>
          <div class="sub">Total XP {formatNumber(playerData.dungeons.catacombs.xp)}</div>
          {#if playerData.dungeons.catacombs.overflow > 0}
            <div class="sub accent">
              Overflow {formatNumber(playerData.dungeons.catacombs.overflow)} XP
            </div>
          {/if}
        </div>

        {#each Object.entries(playerData.dungeons.classes) as [key, info]}
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
            <span class="dungeon-level">Lv. {(info as any).level}</span>
            <span class="sub">{formatNumber((info as any).xp)} XP</span>
            {#if (info as any).overflow > 0}
              <span class="sub accent">Overflow {formatNumber((info as any).overflow)} XP</span>
            {/if}
          </div>
        {/each}
      </section>

      {#if playerData.dungeons.catacombs.floors}
        <h3 class="section-title">Catacombs Floors</h3>
        <section class="grid dungeon-grid">
          {#each Object.entries(playerData.dungeons.catacombs.floors) as [key, floor]}
            <div class="card dungeon-card">
              <div class="skill-header">
                <span class="skill-icon" aria-hidden="true">
                  <img
                    src={getHeadUrl(BOSS_HEADS[key] || BOSS_HEADS['floor_0'])}
                    alt=""
                    loading="lazy"
                    width="28"
                    height="28"
                    class="head-icon"
                  />
                </span>
                <span class="dungeon-name">{(floor as any).name}</span>
              </div>
              <div class="floor-stats">
                <div class="stat-row">
                  <span class="label">Completions</span>
                  <span class="value">{formatNumber((floor as any).completions)}</span>
                </div>
                <div class="stat-row">
                  <span class="label">Best Score</span>
                  <span class="value" style="color: {getScoreColor((floor as any).best_score)}">
                    {(floor as any).best_score} ({getScoreRank((floor as any).best_score)})
                  </span>
                </div>
                <div class="stat-row">
                  <span class="label">Fastest Run</span>
                  <span class="value">{(floor as any).fastest_time ? formatTime((floor as any).fastest_time) : '-'}</span>
                </div>
              </div>
            </div>
          {/each}
        </section>
      {/if}
    </div>
  {/if}
</div>

<style>
  .wrap {
    max-width: 960px;
    margin: 40px auto;
    padding: 0 18px;
    color: var(--theme-text-primary);
  }

  .header {
    margin-bottom: 24px;
  }

  .back-link {
    display: inline-block;
    margin-bottom: 16px;
    color: var(--theme-text-soft);
    text-decoration: none;
    font-size: 14px;
    transition: color 0.2s;
  }

  .back-link:hover {
    color: var(--theme-accent);
  }

  h1 {
    font-size: 32px;
    margin: 0;
  }

  .search-bar {
    display: flex;
    gap: 10px;
    margin-bottom: 32px;
  }

  input {
    flex: 1;
    padding: 12px 16px;
    border-radius: 12px;
    border: 1px solid var(--theme-form-border);
    background: var(--theme-form-bg);
    color: var(--theme-text-primary);
    font-size: 16px;
  }

  button {
    padding: 12px 24px;
    border-radius: 12px;
    background: var(--theme-accent);
    color: white;
    border: none;
    font-weight: 600;
    cursor: pointer;
  }

  button:disabled {
    opacity: 0.7;
    cursor: not-allowed;
  }

  .error {
    padding: 16px;
    background: rgba(239, 68, 68, 0.1);
    border: 1px solid rgba(239, 68, 68, 0.2);
    color: #fca5a5;
    border-radius: 12px;
    margin-bottom: 24px;
  }

  /* Grid & Card Styles (Copied/Adapted from DungeonsTab) */
  .grid {
    display: grid;
    gap: 16px;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  }

  .dungeon-grid {
    margin-bottom: 32px;
  }

  .card {
    background: color-mix(in srgb, var(--theme-surface) 96%, transparent);
    border: 1px solid color-mix(in srgb, var(--theme-surface-border) 80%, transparent);
    border-radius: 16px;
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .featured {
    background: linear-gradient(135deg, rgba(95, 113, 245, 0.1), rgba(31, 182, 166, 0.1));
    border-color: var(--theme-accent-alpha-40);
  }

  .skill-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 8px;
  }

  .skill-icon {
    width: 28px;
    height: 28px;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .head-icon {
    border-radius: 4px;
  }

  h3 {
    margin: 0;
    font-size: 16px;
    font-weight: 700;
  }

  .dungeon-name {
    font-weight: 600;
    font-size: 15px;
  }

  .catacombs-level {
    font-size: 24px;
    font-weight: 700;
    color: var(--theme-accent);
  }

  .dungeon-level {
    font-size: 20px;
    font-weight: 700;
  }

  .sub {
    font-size: 13px;
    color: var(--theme-text-soft);
  }

  .accent {
    color: var(--theme-accent-secondary);
  }

  .section-title {
    font-size: 20px;
    margin: 0 0 16px;
    color: var(--theme-text-primary);
  }

  .floor-stats {
    display: flex;
    flex-direction: column;
    gap: 6px;
    margin-top: 8px;
  }

  .stat-row {
    display: flex;
    justify-content: space-between;
    font-size: 13px;
  }

  .label {
    color: var(--theme-text-soft);
  }

  .value {
    font-weight: 600;
  }
</style>
