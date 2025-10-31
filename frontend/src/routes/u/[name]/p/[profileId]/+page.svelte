<script lang="ts">
  import { onMount } from 'svelte';
  import { get } from '$lib/api';
  import Tabs from '$lib/ui/Tabs.svelte';
  import StatChip from '$lib/components/StatChip.svelte';
  import { StarIcon, DungeonIcon, SkullIcon } from '$lib/icons';
  import { timeAgo, formatNumber, formatPercent, formatLargeNumber } from '$lib/utils';

  export let params: { name: string; profileId: string };

  type Player = { name: string; uuid: string };

  type SkillStat = {
    level: number;
    progress: number;
    xp: number;
    current: number;
    to_next: number;
  };

  type WardrobeItem = {
    slot: number;
    id: string;
    mc_id: string;
    name: string;
    count: number;
    rarity?: string | null;
    lore: string[];
  };

  type ProfileSummaryResponse = {
    ok: boolean;
    last_updated?: string | number;
    profile: {
      profile_id: string;
      cute_name?: string | null;
      game_mode?: string | null;
      member_count: number;
      last_save?: number | null;
      last_save_iso?: string | null;
    };
    skyblock_level: {
      level: number;
      progress: number;
      experience: number;
    };
    skills: Record<string, SkillStat> & { average_level: number };
    slayer: Record<string, { level: number; xp: number }> & { total_xp: number };
    dungeons: {
      catacombs: { level: number; xp: number };
      classes: Record<string, { level: number; xp: number }>;
    };
    stats: Record<string, number>;
    currencies: {
      purse: number;
      bank: number;
      total_coins: number;
      motes: number;
      essence_total: number;
      essence: Record<string, number>;
    };
    wardrobe: {
      equipped_slot: number | null;
      items: (WardrobeItem | null)[];
    slots: number;
    };
  };

  const SITE_BASE = import.meta.env.VITE_SITE_BASE ?? 'https://altsky.dev';

  const tabs = [
    { id: 'summary', label: 'Overview' },
    { id: 'skills', label: 'Skills' },
    { id: 'stats', label: 'Stats' },
    { id: 'slayer', label: 'Slayer' },
    { id: 'dungeons', label: 'Dungeons' },
    { id: 'wardrobe', label: 'Wardrobe' }
  ];

  const skillOrder: { key: string; label: string }[] = [
    { key: 'farming', label: 'Farming' },
    { key: 'mining', label: 'Mining' },
    { key: 'combat', label: 'Combat' },
    { key: 'foraging', label: 'Foraging' },
    { key: 'fishing', label: 'Fishing' },
    { key: 'enchanting', label: 'Enchanting' },
    { key: 'alchemy', label: 'Alchemy' },
    { key: 'taming', label: 'Taming' },
    { key: 'carpentry', label: 'Carpentry' },
    { key: 'runecrafting', label: 'Runecrafting' },
    { key: 'social', label: 'Social' }
  ];

  const statLabels: Record<string, string> = {
    health: 'Health',
    defense: 'Defense',
    strength: 'Strength',
    intelligence: 'Intelligence',
    speed: 'Speed',
    crit_chance: 'Crit Chance',
    crit_damage: 'Crit Damage',
    attack_speed: 'Attack Speed',
    ferocity: 'Ferocity',
    magic_find: 'Magic Find',
    pet_luck: 'Pet Luck',
    true_defense: 'True Defense'
  };

  const slayerLabels: Record<string, string> = {
    zombie: 'Revenant Horror',
    spider: 'Tarantula Broodfather',
    wolf: 'Sven Packmaster',
    enderman: 'Voidgloom Seraph',
    blaze: 'Inferno Demonlord',
    vampire: 'Riftstalker Bloodfiend'
  };

  const dungeonClassLabels: Record<string, string> = {
    healer: 'Healer',
    mage: 'Mage',
    berserk: 'Berserk',
    archer: 'Archer',
    tank: 'Tank'
  };

  let player: Player | null = data.player;
  let summary: ProfileSummaryResponse | null = data.summary;
  let errorMsg = data.errorMsg ?? '';
  let loading = !summary && !errorMsg;
  let refreshing = false;
  let activeTab = 'summary';

  async function fetchProfile(force = false) {
    if (!player) {
      try {
        player = await get<Player>(`/api/player/${encodeURIComponent(params.name)}`);
      } catch (err) {
        errorMsg = `Failed to resolve player: ${(err as Error).message}`;
        return;
      }
    }

    loading = !summary && !force;
    refreshing = force;
    errorMsg = '';

    try {
      summary = await get<ProfileSummaryResponse>(
        `/api/hypixel/profile/${encodeURIComponent(player.uuid)}/${encodeURIComponent(params.profileId)}`,
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

  function rarityClass(rarity?: string | null) {
    if (!rarity) return 'rarity-basic';
    return `rarity-${rarity.toLowerCase().replace(/\s+/g, '-')}`;
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

  $: shareImage = player
    ? `https://dummyimage.com/1200x630/020617/E2E8F0.png&text=${encodeURIComponent(`${player.name}+SkyBlock`)}`
    : 'https://dummyimage.com/1200x630/020617/E2E8F0.png&text=AltSky';

  const canonicalUrl = `${SITE_BASE}/u/${encodeURIComponent(params.name)}/p/${encodeURIComponent(params.profileId)}`;
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
      <a class="ghost" href={`/u/${params.name}`}>Back to profiles</a>
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
      <section class="grid summary-grid">
        <div class="card featured">
          <h2>SkyBlock Level</h2>
          <div class="level-number">{summary.skyblock_level.level}</div>
          <div class="progress">
            <div class="progress-bar" style={`width:${Math.min(100, summary.skyblock_level.progress * 100).toFixed(1)}%`}></div>
          </div>
          <div class="progress-label">
            {formatPercent(summary.skyblock_level.progress * 100, 1)} | Total XP {formatNumber(summary.skyblock_level.experience)}
          </div>
          <div class="chips">
            <StatChip label="Avg Skill Level" value={summary.skills.average_level.toFixed(2)} icon={StarIcon} />
            <StatChip label="Catacombs" value={`Lv. ${summary.dungeons.catacombs.level}`} icon={DungeonIcon} />
            <StatChip label="Total Slayer XP" value={formatNumber(summary.slayer.total_xp)} icon={SkullIcon} />
          </div>
        </div>

        <div class="card">
          <h3>Coins & Networth</h3>
          <div class="stat-list">
            <div>
              <span class="label">Purse</span>
              <span class="value">{formatLargeNumber(summary.currencies.purse)}</span>
            </div>
            <div>
              <span class="label">Bank</span>
              <span class="value">{formatLargeNumber(summary.currencies.bank)}</span>
            </div>
            <div>
              <span class="label">Total Coins</span>
              <span class="value accent">{formatLargeNumber(summary.currencies.total_coins)}</span>
            </div>
            <div>
              <span class="label">Motes</span>
              <span class="value">{formatLargeNumber(summary.currencies.motes)}</span>
            </div>
            <div>
              <span class="label">Essence Total</span>
              <span class="value">{summary.currencies.essence_total.toLocaleString()}</span>
            </div>
          </div>
        </div>

        <div class="card">
          <h3>Core Stats</h3>
          <div class="chips">
            {#each Object.entries(summary.stats) as [key, value]}
              {#if key in statLabels}
                <StatChip label={statLabels[key]} value={formatNumber(value, 0)} />
              {/if}
            {/each}
          </div>
        </div>
      </section>
    {/if}

    {#if activeTab === 'skills'}
      <section class="grid">
        {#each skillOrder as skill}
          {@const data = summary.skills[skill.key] as SkillStat | undefined}
          {#if data}
            <div class="card skill-card">
              <div class="skill-header">
                <span class="skill-name">{skill.label}</span>
                <span class="skill-level">Lv. {data.level}</span>
              </div>
              <div class="progress">
                <div class="progress-bar" style={`width:${Math.min(100, data.progress * 100).toFixed(1)}%`}></div>
              </div>
              <div class="progress-label">
                {formatPercent(data.progress * 100, 1)} | {formatNumber(data.current)} / {formatNumber(data.to_next)}
              </div>
            </div>
          {/if}
        {/each}
      </section>
    {/if}

    {#if activeTab === 'stats'}
      <section class="grid stats-grid">
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
    {/if}

    {#if activeTab === 'slayer'}
      <section class="grid slayer-grid">
        {#each Object.entries(summary.slayer) as [key, info]}
          {#if key !== 'total_xp' && typeof info !== 'number'}
            {@const slayerInfo = info as { level: number; xp: number }}
            <div class="card slayer-card">
              <span class="slayer-name">{slayerLabels[key] ?? key}</span>
              <div class="slayer-level">Lv. {slayerInfo.level}</div>
              <div class="slayer-xp">{formatNumber(slayerInfo.xp)} XP</div>
            </div>
          {/if}
        {/each}
      </section>
    {/if}

    {#if activeTab === 'dungeons'}
      <section class="grid dungeon-grid">
        <div class="card dungeon-card featured">
          <h3>Catacombs</h3>
          <div class="catacombs-level">Lv. {summary.dungeons.catacombs.level}</div>
          <div class="sub">Total XP {formatNumber(summary.dungeons.catacombs.xp)}</div>
        </div>

        {#each Object.entries(summary.dungeons.classes) as [key, info]}
          <div class="card dungeon-card">
            <span class="dungeon-name">{dungeonClassLabels[key] ?? key}</span>
            <span class="dungeon-level">Lv. {info.level}</span>
            <span class="sub">{formatNumber(info.xp)} XP</span>
          </div>
        {/each}
      </section>
    {/if}

    {#if activeTab === 'wardrobe'}
      <section class="wardrobe-grid">
        {#each summary.wardrobe.items as item}
          {#if item}
            <div class={`card wardrobe-card ${rarityClass(item.rarity)} ${summary.wardrobe.equipped_slot === item.slot ? 'equipped' : ''}`}>
              <div class="wardrobe-top">
                <span class="slot">Slot {item.slot + 1}</span>
                <span class="rarity">{item.rarity ?? 'Unknown'}</span>
              </div>
              <div class="item-name">{item.name}</div>
              <div class="item-meta">Item ID: {item.id}</div>
              {#if item.count > 1}
                <div class="item-meta">Count: {item.count}</div>
              {/if}
              {#if item.lore.length}
                <div class="lore">
                  {#each item.lore.slice(0, 8) as line}
                    <p>{line}</p>
                  {/each}
                </div>
              {/if}
            </div>
          {/if}
        {/each}

        {#if !summary.wardrobe.items.filter(Boolean).length}
          <div class="card wardrobe-empty">
            <p>The wardrobe is empty.</p>
          </div>
        {/if}
      </section>
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
    backdrop-filter: blur(18px);
    box-shadow: var(--theme-card-shadow);
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

  .card {
    background: var(--theme-surface);
    border: 1px solid var(--theme-surface-border);
    border-radius: 20px;
    padding: 22px 24px;
    box-shadow: var(--theme-card-shadow);
    backdrop-filter: blur(12px);
    display: flex;
    flex-direction: column;
    gap: 12px;
    transition: background 0.4s ease, border-color 0.4s ease, box-shadow 0.4s ease, transform 0.3s ease;
  }

  .card:hover {
    transform: translateY(-3px);
  }

  .featured {
    background: var(--theme-featured-gradient);
    border-color: var(--theme-secondary-alpha-32);
  }

  .level-number {
    font-size: 3.2rem;
    font-weight: 800;
    margin: 6px 0 8px;
    letter-spacing: -0.04em;
    color: var(--theme-text-primary);
  }

  .card h2,
  .card h3 {
    margin: 0;
    color: var(--theme-text-primary);
  }

  .card strong {
    color: var(--theme-text-primary);
  }

  .grid {
    display: grid;
    gap: 20px;
  }

  .summary-grid {
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  }

  .chips {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin-top: 14px;
  }

  .skill-card,
  .stat-card,
  .slayer-card,
  .dungeon-card {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .skill-header {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
  }

  .skill-name {
    font-weight: 600;
    color: var(--theme-text-secondary);
  }

  .skill-level {
    font-size: 1.4rem;
    font-weight: 700;
    color: var(--theme-accent);
  }

  .progress {
    width: 100%;
    height: 8px;
    background: rgba(148, 163, 184, 0.28);
    border-radius: 999px;
    overflow: hidden;
  }

  .progress-bar {
    height: 100%;
    background: linear-gradient(135deg, var(--theme-progress-start), var(--theme-progress-end));
    border-radius: inherit;
  }

  .progress-label {
    color: var(--theme-text-soft);
    font-size: 0.85rem;
  }

  .stat-card {
    padding: 24px;
    align-items: flex-start;
  }

  .stat-name {
    font-size: 0.95rem;
    color: var(--theme-text-soft);
  }

  .stat-value {
    font-size: 1.6rem;
    font-weight: 700;
    margin-top: 6px;
  }

  .stats-grid {
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  }

  .stat-list {
    display: grid;
    gap: 10px;
  }

  .stat-list .label {
    color: var(--theme-text-soft);
  }

  .stat-list .value {
    font-weight: 600;
    color: var(--theme-text-primary);
  }

  .stat-list .value.accent {
    color: var(--theme-accent-secondary);
  }

  .essence-card .essence-grid {
    display: grid;
    gap: 8px;
    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  }

  .slayer-grid,
  .dungeon-grid {
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  }

  .slayer-name,
  .dungeon-name {
    font-weight: 600;
    color: var(--theme-text-secondary);
  }

  .slayer-level,
  .catacombs-level {
    font-size: 2rem;
    font-weight: 700;
    color: var(--theme-accent);
  }

  .slayer-xp {
    color: var(--theme-text-soft);
  }

  .dungeon-level {
    font-size: 2rem;
    font-weight: 700;
    color: var(--theme-accent-secondary);
  }

  .sub {
    color: var(--theme-text-soft);
  }

  .wardrobe-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
    gap: 18px;
  }

  .wardrobe-card {
    position: relative;
    display: flex;
    flex-direction: column;
    gap: 8px;
    border-width: 1px;
  }

  .wardrobe-card.equipped {
    border-width: 2px;
    box-shadow: 0 0 20px rgba(250, 204, 21, 0.35);
  }

  .wardrobe-top {
    display: flex;
    justify-content: space-between;
    color: var(--theme-text-soft);
  }

  .item-name {
    font-weight: 600;
    font-size: 1.05rem;
  }

  .item-meta {
    color: var(--theme-text-soft);
    font-size: 0.85rem;
  }

  .lore {
    margin-top: 6px;
    padding: 10px 12px;
    background: var(--theme-control-bg);
    border-radius: 12px;
    max-height: 160px;
    overflow: auto;
    font-size: 0.8rem;
    color: var(--theme-text-soft);
    border: 1px solid var(--theme-control-border);
  }

  .lore p {
    margin: 0;
    line-height: 1.35;
  }

  .wardrobe-empty {
    text-align: center;
    color: var(--theme-text-soft);
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

  .rarity-basic {
    border-color: rgba(148, 163, 184, 0.4);
  }

  .rarity-common {
    border-color: rgba(113, 113, 122, 0.6);
  }

  .rarity-uncommon {
    border-color: rgba(34, 197, 94, 0.6);
  }

  .rarity-rare {
    border-color: rgba(59, 130, 246, 0.6);
  }

  .rarity-epic {
    border-color: rgba(168, 85, 247, 0.6);
  }

  .rarity-legendary {
    border-color: rgba(250, 204, 21, 0.7);
  }

  .rarity-mythic {
    border-color: rgba(236, 72, 153, 0.7);
  }

  .rarity-divine {
    border-color: rgba(129, 140, 248, 0.75);
  }

  .rarity-special,
  .rarity-very-special {
    border-color: rgba(239, 68, 68, 0.75);
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
