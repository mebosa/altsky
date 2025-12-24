<script lang="ts">
  import { onMount } from 'svelte';
  import { get } from '$lib/api';
  import Tabs from '$lib/ui/Tabs.svelte';
  import { timeAgo, formatNumber, formatLargeNumber } from '$lib/utils';
  import SummaryTab from './SummaryTab.svelte';
  import { skillOrder, statLabels, slayerLabels, dungeonClassLabels } from './profileConstants';
  import type { Player, ProfileSummaryResponse } from './profileTypes';

  // Lazy load other tabs
  const lazyTabs = {
    skills: () => import('./SkillsTab.svelte'),
    stats: () => import('./StatsTab.svelte'),
    slayer: () => import('./SlayerTab.svelte'),
    dungeons: () => import('./DungeonsTab.svelte'),
    minions: () => import('./MinionsTab.svelte'),
    collections: () => import('./CollectionsTab.svelte'),
    pets: () => import('./PetsTab.svelte'),
    accessories: () => import('./AccessoriesTab.svelte'),
    wardrobe: () => import('./WardrobeTab.svelte'),
    museum: () => import('./MuseumTab.svelte'),
    auctions: () => import('./AuctionsTab.svelte'),
    dropcalc: () => import('./DropCalcTab.svelte')
  };

  // Cache loaded components
  let loadedTabs: Record<string, any> = {};
  let tabLoading = false;

  async function loadTab(tabId: string) {
    if (tabId === 'summary' || loadedTabs[tabId]) return;
    
    const loader = lazyTabs[tabId as keyof typeof lazyTabs];
    if (loader) {
      tabLoading = true;
      try {
        const module = await loader();
        loadedTabs[tabId] = module.default;
        loadedTabs = loadedTabs; // trigger reactivity
      } catch (e) {
        console.error(`Failed to load tab ${tabId}:`, e);
      }
      tabLoading = false;
    }
  }

  export let params: { name: string; profileId: string };
  export let data: {
    player: Player | null;
    summary: ProfileSummaryResponse | null;
    errorMsg?: string;
  };

  const SITE_BASE = import.meta.env.VITE_SITE_BASE ?? 'https://altsky.dev';

  const tabs = [
    { id: 'summary', label: 'Overview' },
    { id: 'skills', label: 'Skills' },
    { id: 'stats', label: 'Stats' },
    { id: 'slayer', label: 'Slayer' },
    { id: 'dungeons', label: 'Dungeons' },
    { id: 'minions', label: 'Minions' },
    { id: 'collections', label: 'Collections' },
    { id: 'pets', label: 'Pets' },
    { id: 'accessories', label: 'Accessories' },
    { id: 'wardrobe', label: 'Wardrobe' },
    { id: 'museum', label: 'Museum' },
    { id: 'auctions', label: 'Auctions' },
    { id: 'dropcalc', label: 'Drop Calc' }
  ] as const;

  const tabsList: { id: string; label: string }[] = tabs.map((tab) => ({ ...tab }));

  type TabId = (typeof tabs)[number]['id'];

  let player: Player | null = data.player;
  let summary: ProfileSummaryResponse | null = data.summary;
  let errorMsg = data.errorMsg ?? '';
  let loading = !summary && !errorMsg;
  let refreshing = false;
  let statsLoading = false; // stats 별도 로딩 상태
  let activeTab: TabId = 'summary';
  let selectedWeaponSlot: number | null = null;
  let selectedWeaponId: string | null = null;

  function scrollToTab(tab: TabId) {
    if (typeof window !== 'undefined') {
      setTimeout(() => {
        const section = document.getElementById(tab);
        if (section) {
          section.scrollIntoView({ behavior: 'smooth' });
        }
      }, 0);
    }
  }

  // Load tab when activeTab changes
  $: if (activeTab && !loading) {
    loadTab(activeTab);
    scrollToTab(activeTab);
  }

  async function fetchProfile(
    force = false,
    weaponSlot: number | null = selectedWeaponSlot,
    weaponId: string | null = selectedWeaponId
  ) {
    if (!player) {
      try {
        player = await get<Player>(`/api/player/${encodeURIComponent(params.name)}`);
      } catch (err) {
        errorMsg = `Failed to resolve player: ${(err as Error).message}`;
        return;
      }
    }

    const resolvedPlayer = player;
    if (!resolvedPlayer) {
      errorMsg = 'Failed to resolve player.';
      return;
    }

    loading = !summary && !force;
    refreshing = force;
    errorMsg = '';

    try {
      const query: Record<string, string | number> = {};
      if (force) {
        query.refresh = 1;
      }
      if (weaponId) {
        query.weapon_id = weaponId;
      } else if (weaponSlot !== null && weaponSlot !== undefined) {
        query.weapon_slot = weaponSlot;
      }
      summary = await get<ProfileSummaryResponse>(
        `/api/hypixel/profile/${encodeURIComponent(resolvedPlayer.uuid)}/${encodeURIComponent(params.profileId)}`,
        { query: Object.keys(query).length ? query : undefined }
      );
    } catch (err) {
      errorMsg = `Error while loading: ${(err as Error).message}`;
    } finally {
      loading = false;
      refreshing = false;
    }
  }

  function refresh() {
    if (!refreshing) fetchProfile(true, selectedWeaponSlot, selectedWeaponId);
  }

  // stats만 별도로 로드하는 함수 (SSR 후 클라이언트에서 호출)
  async function loadStats(
    weaponSlot: number | null = selectedWeaponSlot,
    weaponId: string | null = selectedWeaponId
  ) {
    if (!player || statsLoading) return;
    
    statsLoading = true;
    try {
      const query: Record<string, string | number> = {};
      if (weaponId) {
        query.weapon_id = weaponId;
      } else if (weaponSlot !== null && weaponSlot !== undefined) {
        query.weapon_slot = weaponSlot;
      }
      
      const fullSummary = await get<ProfileSummaryResponse>(
        `/api/hypixel/profile/${encodeURIComponent(player.uuid)}/${encodeURIComponent(params.profileId)}`,
        { query: Object.keys(query).length ? query : undefined }
      );
      
      // 기존 summary에 computed_stats와 museum만 업데이트
      if (fullSummary && summary) {
        summary = {
          ...summary,
          computed_stats: fullSummary.computed_stats,
          stat_breakdown: fullSummary.stat_breakdown,
          museum: fullSummary.museum,
          weapon_candidates: fullSummary.weapon_candidates,
          weapon_catalog: fullSummary.weapon_catalog,
          weapon_selected_slot: fullSummary.weapon_selected_slot,
          weapon_selected_id: fullSummary.weapon_selected_id,
        };
      }
    } catch (err) {
      console.error('Failed to load stats:', err);
    } finally {
      statsLoading = false;
    }
  }

  onMount(() => {
    if (!summary && !errorMsg) {
      fetchProfile();
    } else if (summary && !summary.computed_stats) {
      // SSR에서 skip_stats=1로 가져왔으므로 클라이언트에서 stats만 추가 로드
      loadStats(selectedWeaponSlot, selectedWeaponId);
    }
  });

  $: profileTitle =
    summary && player
      ? `AltSky - ${player.name} (${summary.profile.cute_name ?? 'SkyBlock'})`
      : 'AltSky Profile';

  $: profileDescription = summary
    ? `Level ${summary.skyblock_level.level} | Avg Skill ${summary.skills.average_level} | Slayer XP ${formatNumber(summary.slayer.total_xp)} | Coins ${formatLargeNumber(summary.currencies.total_coins)}`
    : 'Inspect Hypixel SkyBlock stats with AltSky.';

  $: shareImage = `${SITE_BASE}/api/og/player/${encodeURIComponent(params.name)}.png?v=${summary?.last_updated ?? Date.now()}`;
  $: if (summary) {
    if (summary.weapon_selected_id !== undefined) {
      selectedWeaponId = summary.weapon_selected_id ?? null;
      if (selectedWeaponId) {
        selectedWeaponSlot = null;
      }
    }
    if (summary.weapon_selected_slot !== undefined && !selectedWeaponId) {
      selectedWeaponSlot = summary.weapon_selected_slot ?? null;
    }
  }

  function handleWeaponChange(event: CustomEvent<{ slot: number | null; id: string | null }>) {
    selectedWeaponSlot = event.detail.slot;
    selectedWeaponId = event.detail.id;
    // weapon 변경 시 stats만 다시 로드 (전체 프로필 다시 안 가져옴)
    loadStats(selectedWeaponSlot, selectedWeaponId);
  }

  const canonicalUrl = `${SITE_BASE}/u/${encodeURIComponent(params.name)}/p/${encodeURIComponent(
    params.profileId
  )}`;
</script>

<svelte:head>
  <title>{profileTitle}</title>
  <link rel="canonical" href={canonicalUrl} />
  <meta property="og:type" content="article" />
  <meta property="og:title" content={profileTitle} />
  <meta property="og:description" content={profileDescription} />
  <meta property="og:url" content={canonicalUrl} />
  <meta property="og:image" content={shareImage} />
  <meta property="og:image:width" content="1200" />
  <meta property="og:image:height" content="630" />
  <meta property="og:site_name" content="AltSky" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content={profileTitle} />
  <meta name="twitter:description" content={profileDescription} />
  <meta name="twitter:image" content={shareImage} />
</svelte:head>

<div class="page">
  <header class="header-card">
    <div>
      <p class="breadcrumb"><a href="/">AltSky</a> / <a href={`/u/${params.name}`}>{params.name}</a></p>
      <h1>
        {player?.name ?? params.name}
        {#if summary?.profile.cute_name}
          <span class="profile-name">({summary.profile.cute_name})</span>
        {/if}
      </h1>
      <div class="meta">
        <span>Profile ID <code>{params.profileId}</code></span>
        {#if summary?.profile.game_mode}
          <span class="tag">{summary.profile.game_mode}</span>
        {/if}
        <span>Members {summary?.profile.member_count ?? '-'}</span>
      </div>
      {#if summary?.profile.last_save_iso}
        <div class="updated">Last save {timeAgo(summary.profile.last_save_iso)}</div>
      {/if}
      {#if summary?.last_updated}
        <div class="updated muted">Hypixel sync {timeAgo(summary.last_updated)}</div>
      {/if}
    </div>

    <div class="actions">
      <a class="ghost" href="/">Back to home</a>
      <button class:loading={refreshing} on:click={refresh} type="button">
        {refreshing ? 'Refreshing...' : 'Refresh'}
      </button>
    </div>
  </header>

  {#if errorMsg}
    <div class="alert error">{errorMsg}</div>
  {/if}

  {#if loading}
    <div class="card skeleton">
      <div class="bar wide"></div>
      <div class="bar"></div>
      <div class="bar"></div>
    </div>
  {:else if summary}
    <Tabs bind:value={activeTab} tabs={tabsList} />

    {#if activeTab === 'summary'}
      <SummaryTab {summary} {player} />
    {:else if tabLoading}
      <div class="card skeleton">
        <div class="bar wide"></div>
        <div class="bar"></div>
        <div class="bar"></div>
      </div>
    {:else if activeTab === 'skills' && loadedTabs.skills}
      <svelte:component this={loadedTabs.skills} {summary} {skillOrder} />
    {:else if activeTab === 'stats' && loadedTabs.stats}
      <svelte:component this={loadedTabs.stats} {summary} {statLabels} on:weaponchange={handleWeaponChange} />
    {:else if activeTab === 'slayer' && loadedTabs.slayer}
      <svelte:component this={loadedTabs.slayer} {summary} {slayerLabels} />
    {:else if activeTab === 'dungeons' && loadedTabs.dungeons}
      <svelte:component this={loadedTabs.dungeons} {summary} {dungeonClassLabels} />
    {:else if activeTab === 'minions' && loadedTabs.minions}
      <svelte:component this={loadedTabs.minions} {summary} />
    {:else if activeTab === 'collections' && loadedTabs.collections}
      <svelte:component this={loadedTabs.collections} {summary} />
    {:else if activeTab === 'pets' && loadedTabs.pets}
      <svelte:component this={loadedTabs.pets} {summary} />
    {:else if activeTab === 'accessories' && loadedTabs.accessories}
      <svelte:component this={loadedTabs.accessories} {summary} />
    {:else if activeTab === 'wardrobe' && loadedTabs.wardrobe}
      <svelte:component this={loadedTabs.wardrobe} {summary} />
    {:else if activeTab === 'museum' && loadedTabs.museum}
      <svelte:component this={loadedTabs.museum} museum={summary.museum} />
    {:else if activeTab === 'auctions' && loadedTabs.auctions}
      <svelte:component this={loadedTabs.auctions} {summary} {player} />
    {:else if activeTab === 'dropcalc' && loadedTabs.dropcalc}
      <svelte:component this={loadedTabs.dropcalc} {summary} />
    {/if}
  {/if}
</div>

<style>
  a {
    color: inherit;
    text-decoration: none;
  }

  .page {
    max-width: 1200px;
    margin: 48px auto;
    padding: 0 20px 80px;
    display: flex;
    flex-direction: column;
    gap: 24px;
    color: var(--theme-text-primary);
  }

  .header-card {
    background: var(--theme-header-gradient);
    border: 1px solid var(--theme-secondary-alpha-32);
    border-radius: 24px;
    padding: 32px 36px;
    display: flex;
    justify-content: space-between;
    gap: 32px;
    transition: background 0.4s ease, border-color 0.4s ease, box-shadow 0.4s ease;
    box-shadow: var(--neu-elevated), inset 2px 2px 6px rgba(0, 0, 0, 0.18);
  }

  .breadcrumb {
    font-size: 0.85rem;
    color: var(--theme-text-soft);
    margin: 0 0 6px;
  }

  .breadcrumb a {
    color: var(--theme-text-soft);
  }

  .header-card h1 {
    font-size: 2.4rem;
    margin: 0;
    display: flex;
    align-items: baseline;
    gap: 12px;
  }

  .profile-name {
    font-size: 1.1rem;
    color: var(--theme-text-soft);
  }

  .meta {
    display: flex;
    gap: 12px;
    margin-top: 12px;
    flex-wrap: wrap;
    color: var(--theme-text-soft);
  }

  .meta .tag {
    background: var(--theme-tag-bg);
    border: 1px solid var(--theme-tag-border);
    padding: 2px 10px;
    border-radius: 999px;
    font-size: 0.8rem;
    letter-spacing: 0.05em;
  }

  .updated {
    margin-top: 10px;
    color: var(--theme-text-soft);
  }

  .updated.muted {
    opacity: 0.7;
  }

  .actions {
    display: flex;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
  }

  .actions a,
  .actions button {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 10px 18px;
    border-radius: 999px;
    font-weight: 600;
    cursor: pointer;
    text-decoration: none;
    transition: transform 0.25s ease, box-shadow 0.25s ease, background 0.25s ease, opacity 0.25s ease;
  }

  .actions a {
    background: var(--theme-control-bg);
    border: 1px solid var(--theme-control-border);
    color: var(--theme-text-secondary);
    box-shadow: var(--neu-soft);
  }

  .actions a:hover {
    background: var(--theme-control-hover);
    transform: translateY(-2px);
  }

  .actions button {
    border: none;
    background: linear-gradient(135deg, var(--theme-accent), var(--theme-accent-secondary));
    color: #ffffff;
    box-shadow: var(--neu-elevated);
  }

  .actions button:hover {
    transform: translateY(-2px);
  }

  .actions button.loading {
    opacity: 0.65;
    cursor: wait;
  }

  :global(.card) {
    background: var(--theme-surface);
    border: 1px solid var(--theme-surface-border);
    border-radius: 20px;
    padding: 22px 24px;
    display: flex;
    flex-direction: column;
    gap: 12px;
    transition: background 0.4s ease, border-color 0.4s ease, box-shadow 0.4s ease, transform 0.3s ease;
  }

  :global(.card:hover) {
    transform: translateY(-3px);
  }

  :global(.featured) {
    background: var(--theme-featured-gradient);
    border-color: var(--theme-secondary-alpha-32);
  }

  :global(.grid) {
    display: grid;
    gap: 20px;
  }

  .alert {
    margin-top: 16px;
    padding: 14px 18px;
    border-radius: 12px;
  }

  .alert.error {
    background: rgba(239, 68, 68, 0.15);
    border: 1px solid rgba(248, 113, 113, 0.45);
    color: #fecaca;
  }

  .skeleton {
    display: grid;
    gap: 12px;
  }

  .bar {
    height: 16px;
    background: rgba(148, 163, 184, 0.14);
    border-radius: 8px;
    animation: pulse 1.6s infinite;
  }

  .bar.wide {
    height: 32px;
  }

  @keyframes pulse {
    0% {
      opacity: 0.4;
    }
    50% {
      opacity: 1;
    }
    100% {
      opacity: 0.4;
    }
  }

  @media (max-width: 768px) {
    .header-card {
      flex-direction: column;
      align-items: stretch;
    }

    .actions {
      justify-content: flex-start;
    }
  }
</style>
