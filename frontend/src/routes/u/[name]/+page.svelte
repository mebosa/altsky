<script lang="ts">
  import { onMount } from 'svelte';
  import { get } from '$lib/api';
  import { timeAgo, saveRecent } from '$lib/utils';
  import Tabs from '$lib/ui/Tabs.svelte';

  export let params: { name: string };
  export let data: {
    player: Player | null;
    fetchError?: string;
  };

  type Player = {
    name: string;
    uuid: string;
    profiles?: any[];
    last_updated?: string;
    error?: string;
    error_detail?: any;
    message?: string;
  };

  let loading = false;
  let errorMsg = '';
  let player: Player | null = null;
  let profiles: any[] = [];
  let lastUpdated = '';
  const REQUEST_TIMEOUT_MS = 15000;
  let activeController: AbortController | null = null;
  let hydrated = false;
  let lastParamsName = params.name;
  let activeTab = 'overview';
  let selectedProfileId: string | null = null;
  
  const tabs = [
    { id: 'overview', label: 'Overview' },
    { id: 'skills', label: 'Skills' },
    { id: 'stats', label: 'Stats' },
    { id: 'slayer', label: 'Slayer' },
    { id: 'dungeons', label: 'Dungeons' },
    { id: 'wardrobe', label: 'Wardrobe' }
  ];

  function formatErrorFromPayload(payload: Player | null) {
    if (!payload) return '';

    if (payload.error) {
      let message: string;
      if (payload.error === 'no_profiles') {
        message = 'SkyBlock profiles were not found.';
      } else if (payload.error === 'rate_limited') {
        message = 'Hypixel API rate limit hit. Please try again in a moment.';
      } else if (payload.error === 'hypixel_api_key_missing') {
        message = 'Hypixel API key is missing on the server.';
      } else {
        message = payload.error;
      }

      const detailSource = payload.error_detail ?? payload.message;
      if (detailSource) {
        const detail =
          typeof detailSource === 'string' ? detailSource : JSON.stringify(detailSource);
        message += ` (${detail})`;
      }
      return message;
    }

    if (!(payload.profiles ?? []).length) {
      return 'No profiles available.';
    }

    return '';
  }

  function applyPlayerPayload(payload: Player | null, fallbackError?: string) {
    player = payload;
    profiles = payload?.profiles ?? [];
    lastUpdated = payload?.last_updated || '';
    errorMsg = fallbackError ?? '';
    if (!fallbackError) {
      errorMsg = formatErrorFromPayload(payload);
    }
  }

  applyPlayerPayload(data?.player ?? null, data?.fetchError);

  onMount(() => {
    hydrated = true;
    lastParamsName = params.name;
    if (player?.name) {
      saveRecent(player.name);
    }
  });

  $: if (hydrated && params.name !== lastParamsName) {
    applyPlayerPayload(data?.player ?? null, data?.fetchError);
    lastParamsName = params.name;
    if (player?.name) {
      saveRecent(player.name);
    }
  }

  async function refreshPlayer(force = false) {
    if (activeController) {
      activeController.abort();
      activeController = null;
    }

    const controller = typeof AbortController !== 'undefined' ? new AbortController() : null;
    const signal = controller?.signal;
    let timeoutHandle: ReturnType<typeof setTimeout> | null = null;

    loading = true;
    errorMsg = '';
    if (controller) {
      activeController = controller;
    }

    if (typeof window !== 'undefined' && controller) {
      timeoutHandle = window.setTimeout(() => {
        if (!controller.signal.aborted) {
          console.warn(`Player request exceeded ${REQUEST_TIMEOUT_MS}ms, aborting`);
          controller.abort();
        }
      }, REQUEST_TIMEOUT_MS);
    }

    try {
      const encodedName = encodeURIComponent(params.name).replace(/%20/g, '+');
      const fetchedPlayer = await get<Player>(`/api/player/${encodedName}`, {
        signal,
        query: force ? { force: '1' } : undefined
      });

      applyPlayerPayload(fetchedPlayer);
      if (hydrated && fetchedPlayer?.name) {
        saveRecent(fetchedPlayer.name);
      }
    } catch (err) {
      const error = err as Error & { name?: string };
      const isAbortError = error?.name === 'AbortError';
      errorMsg = isAbortError
        ? 'Request timed out. Please try again.'
        : `Failed to load: ${error.message}`;
    } finally {
      loading = false;
      if (timeoutHandle) {
        clearTimeout(timeoutHandle);
      }
      if (activeController === controller) {
        activeController = null;
      }
    }
  }

  function shortUUID(value?: string) {
    if (!value) return '';
    return `${value.slice(0, 8)}...`;
  }

  import { goto } from '$app/navigation';

  function toDetail(profileId: string) {
    goto(`/u/${encodeURIComponent(params.name)}/p/${encodeURIComponent(profileId)}`);
  }
</script>

<style>
  .wrap {
    max-width: 960px;
    margin: 48px auto;
    padding: 0 16px 48px;
    color: var(--theme-text-primary);
    display: flex;
    flex-direction: column;
    gap: 24px;
  }

  .header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 20px;
    flex-wrap: wrap;
  }

  .title-section {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  h1 {
    font-size: 24px;
    margin: 0;
    letter-spacing: -0.02em;
    color: var(--theme-text-primary);
  }

  h1 strong {
    display: block;
    font-size: 32px;
    margin-top: 4px;
  }

  .uuid {
    font-size: 14px;
    color: var(--theme-text-soft);
  }

  .actions {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .muted {
    color: var(--theme-text-soft);
  }

  .back-button {
    width: auto;
    padding: 8px 16px;
  }

  button {
    padding: 10px 16px;
    border-radius: 12px;
    border: none;
    background: linear-gradient(135deg, var(--theme-accent), var(--theme-accent-secondary));
    color: #ffffff;
    cursor: pointer;
    font-weight: 600;
    transition: transform 0.25s ease, box-shadow 0.25s ease, filter 0.25s ease, opacity 0.25s ease;
    box-shadow: 0 16px 28px rgba(15, 23, 42, 0.32);
  }

  button:hover {
    transform: translateY(-2px);
    box-shadow: 0 20px 34px rgba(15, 23, 42, 0.4);
  }

  button:disabled {
    opacity: 0.65;
    cursor: wait;
  }

  .ghost {
    background: var(--theme-control-bg);
    color: var(--theme-text-secondary);
    border: 1px solid var(--theme-control-border);
    box-shadow: 0 12px 24px rgba(15, 23, 42, 0.18);
  }

  .ghost:hover {
    background: var(--theme-control-hover);
    transform: translateY(-2px);
  }

  .card {
    border: 1px solid var(--theme-surface-border);
    border-radius: 18px;
    padding: 20px 22px;
    background: var(--theme-surface);
    box-shadow: var(--theme-card-shadow);
    backdrop-filter: blur(12px);
    display: flex;
    flex-direction: column;
    gap: 6px;
    transition: background 0.4s ease, border-color 0.4s ease, box-shadow 0.4s ease, transform 0.3s ease;
  }

  .card:hover {
    transform: translateY(-3px);
  }

  .card strong {
    color: var(--theme-text-primary);
  }

  .grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
    gap: 16px;
    margin-top: 12px;
  }

  .spinner {
    width: 20px;
    height: 20px;
    border: 3px solid rgba(148, 163, 184, 0.28);
    border-top-color: var(--theme-accent);
    border-radius: 50%;
    animation: sp 1s linear infinite;
  }

  @keyframes sp {
    to {
      transform: rotate(360deg);
    }
  }

  .err {
    padding: 14px 16px;
    border-radius: 14px;
    background: rgba(239, 68, 68, 0.12);
    border: 1px solid rgba(248, 113, 113, 0.32);
    color: #fecaca;
    box-shadow: 0 16px 28px rgba(15, 23, 42, 0.24);
  }

  .row-end {
    display: flex;
    gap: 8px;
    margin-top: 10px;
  }

  .card .muted {
    color: var(--theme-text-soft);
  }

  .section {
    background: var(--theme-surface);
    border: 1px solid var(--theme-surface-border);
    border-radius: 18px;
    padding: 24px;
    box-shadow: var(--theme-card-shadow);
  }

  @media (max-width: 640px) {
    button,
    button.ghost {
      width: 100%;
      text-align: center;
    }
  }
</style>

<div class="wrap">
  <div class="header">
    <div class="title-section">
      <button 
        class="ghost back-button" 
        on:click={async () => {
          try {
            await goto('/', { replaceState: true });
          } catch (error) {
            console.error('Navigation error:', error);
            // Fallback to simple location change if SvelteKit navigation fails
            window.location.href = '/';
          }
        }}
      >
        ← Back
      </button>
      <h1>Player: <strong>{params.name}</strong></h1>
      {#if player}<span class="uuid">UUID: {shortUUID(player.uuid)}</span>{/if}
    </div>
    <div class="actions">
      <button on:click={() => refreshPlayer(true)} disabled={loading}>
        {#if loading}<span class="spinner" style="vertical-align:-3px;margin-right:6px;"></span>{/if}
        Refresh
      </button>
      {#if lastUpdated}
        <span class="muted">Cached: {timeAgo(lastUpdated)}</span>
      {/if}
    </div>
  </div>

  <Tabs {tabs} bind:value={activeTab} />

  {#if errorMsg}
    <div class="err">{errorMsg}</div>
  {/if}

  {#if loading && !errorMsg}
    <div class="card" style="display:flex;gap:10px;align-items:center">
      <span class="spinner"></span>
      <span>Loading...</span>
    </div>
  {/if}

  {#if !loading && !errorMsg}
    {#if !selectedProfileId}
      {#if profiles.length}
        <div class="grid">
          {#each profiles as prf}
            <div class="card">
              <div><strong>{prf.cute_name ?? prf.name ?? 'Profile'}</strong></div>
              {#if prf.member_count !== undefined}
                <div class="muted" style="margin-top:6px">Members: {prf.member_count}</div>
              {:else if prf.members}
                <div class="muted" style="margin-top:6px">Members: {Object.keys(prf.members).length}</div>
              {/if}
              {#if prf.game_mode}<div class="muted">Mode: {prf.game_mode}</div>{/if}
              {#if prf.last_save}
                <div class="muted">Last Saved: {timeAgo(prf.last_save)}</div>
              {/if}
              {#if prf.profile_id}
                <div class="row-end">
                  <button class="ghost" on:click={() => {
                    selectedProfileId = prf.profile_id;
                    if (activeTab !== 'overview') {
                      toDetail(prf.profile_id);
                    }
                  }}>
                    {activeTab === 'overview' ? 'Select' : 'View Details'}
                  </button>
                </div>
              {/if}
            </div>
          {/each}
        </div>
      {/if}
    {:else if activeTab !== 'overview'}
      <button 
        class="ghost back-button" 
        style="margin-bottom: 1rem"
        on:click={() => selectedProfileId = null}
      >
        ← Back to Profile Selection
      </button>
      {#if activeTab !== 'overview'}
        <div class="section">
          Loading {activeTab} content... 
          <button class="primary" style="margin-left: 1rem" on:click={() => toDetail(selectedProfileId)}>
            Go to Detail Page
          </button>
        </div>
      {/if}
    {/if}
  {/if}
</div>
