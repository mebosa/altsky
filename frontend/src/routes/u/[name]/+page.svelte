<script lang="ts">
  import { onMount } from 'svelte';
  import { get } from '$lib/api';
  import { timeAgo, saveRecent } from '$lib/utils';

  export let params: { name: string };

  type Player = { name: string; uuid: string };
  type ProfilesResponse = {
    ok?: boolean;
    last_updated?: string;
    profiles?: any[];
    error?: string;
    reason?: string;
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
      const fetchedPlayer = await get<Player>(`/api/player/${encodeURIComponent(params.name)}`);
      player = fetchedPlayer;
      saveRecent(fetchedPlayer.name);

      const res = await get<ProfilesResponse>(`/api/hypixel/profile/${encodeURIComponent(fetchedPlayer.uuid)}`, {
        query: force ? { refresh: 1 } : undefined
      });

      if (res.error) {
        if (res.reason === 'player_not_found') errorMsg = 'Player not found.';
        else if (res.reason === 'no_profiles') errorMsg = 'SkyBlock profiles were not found.';
        else if (res.reason === 'rate_limited') errorMsg = 'Hypixel API rate limit hit. Please try again in a moment.';
        else errorMsg = res.error;
        return;
      }

      profiles = res.profiles ?? [];
      lastUpdated = res.last_updated || '';
      if (!profiles.length) errorMsg = 'No profiles available.';
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
  .wrap{max-width:960px;margin:48px auto;padding:0 16px}
  h1{font-size:42px;margin:0 0 24px}
  .muted{color:#6b7280}
  .row{display:flex;gap:8px;align-items:center}
  button{padding:10px 14px;border-radius:10px;border:1px solid #111827;background:#111827;color:#fff;cursor:pointer}
  .ghost{background:white;color:#111827;border:1px solid #d1d5db}
  .card{border:1px solid #e5e7eb;border-radius:14px;padding:14px 16px}
  .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:12px;margin-top:12px}
  .spinner{width:20px;height:20px;border:3px solid #e5e7eb;border-top-color:#111827;border-radius:50%;animation:sp 1s linear infinite}
  @keyframes sp{to{transform:rotate(360deg)}}
  .err{padding:12px 14px;border-radius:12px;background:#fef2f2;border:1px solid #fecaca;color:#991b1b}
  .row-end{display:flex;gap:8px;margin-top:10px}
</style>

<div class="wrap">
  <h1>AltSky</h1>

  <p class="muted">
    Player: <strong>{params.name}</strong>
    {#if player}&nbsp;(<span class="muted">{shortUUID(player.uuid)}</span>){/if}
  </p>

  <div class="row" style="margin:8px 0 20px">
    <button class="ghost" on:click={() => history.back()}>← Back</button>
    <button on:click={() => load(true)} disabled={loading}>
      {#if loading}<span class="spinner" style="vertical-align:-3px;margin-right:6px;"></span>{/if}
      Refresh
    </button>
    {#if lastUpdated}
      <span class="muted">Cached: {timeAgo(lastUpdated)}</span>
    {/if}
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
