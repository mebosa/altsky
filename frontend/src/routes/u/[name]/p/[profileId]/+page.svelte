<script lang="ts">
  import { onMount, tick } from 'svelte';
  import { get } from '$lib/api';
  import Tabs from '$lib/ui/Tabs.svelte';
  import { formatNumber, formatLargeNumber } from '$lib/utils/format';
  import { timeAgo } from '$lib/utils/time';
  import { TABS, type TabId } from '$lib/constants/tabs';
  import SummaryTab from './SummaryTab.svelte';
  import SkillsTab from './SkillsTab.svelte';
  import StatsTab from './StatsTab.svelte';
  import SlayerTab from './SlayerTab.svelte';
  import DungeonsTab from './DungeonsTab.svelte';
  import WardrobeTab from './WardrobeTab.svelte';
  import { skillOrder, statLabels, slayerLabels, dungeonClassLabels } from './profileConstants';
  import type { Player, ProfileSummaryResponse } from './profileTypes';

  export let params: { name: string; profileId: string };
  export let data: {
    player: Player | null;
    summary: ProfileSummaryResponse | null;
    errorMsg?: string;
  };

  const SITE_BASE = import.meta.env.VITE_SITE_BASE ?? 'https://altsky.dev';

  const tabs = TABS;

  let player: Player | null = data.player;
  let summary: ProfileSummaryResponse | null = data.summary;
  let errorMsg = data.errorMsg ?? '';
  let loading = !summary && !errorMsg;
  let refreshing = false;
  let activeTab: TabId = 'summary';

  async function scrollToSection(tab: TabId) {
    if (typeof window === 'undefined') return;
    await tick();
    const section = document.getElementById(tab);
    section?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  $: if (activeTab && !loading) {
    scrollToSection(activeTab);
  }

  async function fetchProfile(force = false) {
    if (!player) {
      try {
        player = await get<Player>(`/api/player/${encodeURIComponent(params.name)}`);
      } catch (err) {
        errorMsg = `Failed to resolve player: ${(err as Error).message}`;
        return;
      }
    }

    const resolved = player;
    if (!resolved) {
      errorMsg = 'Failed to resolve player.';
      return;
    }

    loading = !summary && !force;
    refreshing = force;
    errorMsg = '';

    try {
      summary = await get<ProfileSummaryResponse>(
        `/api/hypixel/profile/${encodeURIComponent(resolved.uuid)}/${encodeURIComponent(params.profileId)}`,
        { query: force ? { refresh: 1 } : undefined }
      );
    } catch (err) {
      errorMsg = `Error while loading: ${(err as Error).message}`;
    } finally {
      loading = false;
      refreshing = false;
    }
  }

  function refresh() {
    if (!refreshing) fetchProfile(true);
  }

  onMount(() => {
    if (!summary && !errorMsg) {
      fetchProfile();
    }
  });

  $: profileTitle =
    summary && player
      ? `AltSky - ${player.name} (${summary.profile.cute_name ?? 'SkyBlock'})`
      : 'AltSky Profile';

  $: profileDescription = summary
    ? `Level ${summary.skyblock_level.level} | Avg Skill ${summary.skills.average_level} | Slayer XP ${formatNumber(summary.slayer.total_xp)} | Coins ${formatLargeNumber(summary.currencies.total_coins)}`
    : 'Inspect Hypixel SkyBlock stats with AltSky.';

  $: shareImage = 'https://via.placeholder.com/1200x630.png?text=AltSky';

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
    <Tabs bind:value={activeTab} {tabs} />

    {#if activeTab === 'summary'}
      <SummaryTab {summary} {statLabels} />
    {:else if activeTab === 'skills'}
      <SkillsTab {summary} {skillOrder} />
    {:else if activeTab === 'stats'}
      <StatsTab {summary} {statLabels} />
    {:else if activeTab === 'slayer'}
      <SlayerTab {summary} {slayerLabels} />
    {:else if activeTab === 'dungeons'}
      <DungeonsTab {summary} {dungeonClassLabels} />
    {:else if activeTab === 'wardrobe'}
      <WardrobeTab {summary} />
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
    box-shadow: 0 12px 24px rgba(15, 23, 42, 0.18);
  }

  .actions a:hover {
    background: var(--theme-control-hover);
    transform: translateY(-2px);
  }

  .actions button {
    border: none;
    background: linear-gradient(135deg, var(--theme-accent), var(--theme-accent-secondary));
    color: #ffffff;
    box-shadow: 0 18px 36px rgba(15, 23, 42, 0.35);
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
