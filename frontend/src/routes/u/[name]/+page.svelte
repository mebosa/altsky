<script lang="ts">
  import { onMount, afterNavigate } from 'svelte';
  import { goto } from '$app/navigation';
  import { get } from '$lib/api';
  import { timeAgo, saveRecent } from '$lib/utils';

  export let params: { name: string };

  type Player = {
    name: string;
    uuid: string;
    profiles?: any[];
    last_updated?: string;
    error?: string;
    error_detail?: any;
  };

  let loading = false;
  let errorMsg = '';
  let player: Player | null = null;
  let profiles: any[] = [];
  let lastUpdated = '';

  async function load(force = false) {
    loading = true;
    errorMsg = '';
    profiles = [];
    lastUpdated = '';

    try {
      // Safely encode the player name and make the API call
      const encodedName = encodeURIComponent(params.name).replace(/%20/g, '+');
      const fetchedPlayer = await get<Player>(`/api/player/${encodedName}`);
      
      if (!fetchedPlayer || !fetchedPlayer.uuid) {
        throw new Error('Invalid player data received');
      }

      player = fetchedPlayer;
      await saveRecent(fetchedPlayer.name);

      profiles = fetchedPlayer.profiles ?? [];
      lastUpdated = fetchedPlayer.last_updated || '';

      // Surface known backend errors with user-friendly messages
      if (fetchedPlayer.error) {
        if (fetchedPlayer.error === 'no_profiles') {
          errorMsg = 'SkyBlock profiles were not found.';
        } else if (fetchedPlayer.error === 'rate_limited') {
          errorMsg = 'Hypixel API rate limit hit. Please try again in a moment.';
        } else {
          errorMsg = fetchedPlayer.error;
        }
      } else if (!profiles.length) {
        errorMsg = 'No profiles available.';
      }
    } catch (err) {
      errorMsg = `Failed to load: ${(err as Error).message}`;
    } finally {
      loading = false;
    }
  }

  onMount(() => load(false));

  function shortUUID(value?: string) {
    if (!value) return '';
    return `${value.slice(0, 8)}...`;
  }

  function toDetail(profileId: string) {
    location.href = `/u/${encodeURIComponent(params.name)}/p/${encodeURIComponent(profileId)}`;
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

  .row {
    display: flex;
    gap: 10px;
    align-items: center;
    flex-wrap: wrap;
    margin: 8px 0 20px;
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

  @media (max-width: 640px) {
    .row {
      flex-direction: column;
      align-items: stretch;
    }

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
      <button on:click={() => load(true)} disabled={loading}>
        {#if loading}<span class="spinner" style="vertical-align:-3px;margin-right:6px;"></span>{/if}
        Refresh
      </button>
      {#if lastUpdated}
        <span class="muted">Cached: {timeAgo(lastUpdated)}</span>
      {/if}
    </div>
  </div>

  {#if errorMsg}
    <div class="err">{errorMsg}</div>
  {/if}

  {#if loading && !errorMsg}
    <div class="card" style="display:flex;gap:10px;align-items:center">
      <span class="spinner"></span>
      <span>Loading...</span>
    </div>
  {/if}

  {#if !loading && !errorMsg && profiles.length}
    <div class="grid">
      {#each profiles as prf}
        <div class="card">
          <div><strong>{prf.cute_name ?? prf.name ?? 'Profile'}</strong></div>
          {#if prf.members}
            <div class="muted" style="margin-top:6px">Members: {Object.keys(prf.members).length}</div>
          {/if}
          {#if prf.game_mode}<div class="muted">Mode: {prf.game_mode}</div>{/if}
          {#if prf.last_save}
            <div class="muted">Last Saved: {timeAgo(prf.last_save)}</div>
          {/if}
          {#if prf.profile_id}
            <div class="row-end">
              <button class="ghost" on:click={() => toDetail(prf.profile_id)}>
                Open → /u/{params.name}/p/{prf.profile_id}
              </button>
            </div>
          {/if}
        </div>
      {/each}
    </div>
  {/if}
</div>
