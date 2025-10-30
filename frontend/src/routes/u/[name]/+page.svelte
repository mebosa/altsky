<script lang="ts">
  import { onMount } from 'svelte';
  import { get } from '$lib/api';
  import { timeAgo, saveRecent } from '$lib/utils';

  export let params: { name: string };

  type Player = { name: string; uuid: string };
  type ProfilesResponse = {
    ok?: boolean;
    last_updated?: string;     // 백엔드가 주면 표시, 없으면 숨김
    profiles?: any[];
    error?: string;
    reason?: string;           // rate_limited 등
  };

  let loading = false;
  let errorMsg = '';
  let player: Player | null = null;
  let profiles: any[] = [];
  let lastUpdated = ''; // ISO string

  async function load(force = false) {
    loading = true;
    errorMsg = '';
    profiles = [];
    lastUpdated = '';

    try {
      // 1) name -> uuid
      const p = await get<Player>(`/api/player/${encodeURIComponent(params.name)}`);
      player = p;
      saveRecent(p.name);

      // 2) uuid -> profiles
      const res = await get<ProfilesResponse>(`/api/hypixel/profile/${encodeURIComponent(p.uuid)}`, {
        query: force ? { refresh: 1 } : undefined
      });

      if (res.error) {
        // 백엔드 에러 코드에 따라 메시지 분기
        if (res.reason === 'player_not_found') errorMsg = '플레이어를 찾을 수 없습니다.';
        else if (res.reason === 'no_profiles') errorMsg = 'SkyBlock 프로필이 없습니다.';
        else if (res.reason === 'rate_limited') errorMsg = 'Hypixel API 제한에 걸렸습니다. 잠시 후 다시 시도하세요.';
        else errorMsg = res.error;
        return;
      }

      profiles = res.profiles ?? [];
      lastUpdated = res.last_updated || '';
      if (!profiles.length) errorMsg = '프로필이 없습니다.';
    } catch (e) {
      errorMsg = '불러오기에 실패했습니다: ' + (e as Error).message;
    } finally {
      loading = false;
    }
  }

  onMount(() => load(false));

  function shortUUID(u?: string) {
    if (!u) return '';
    return `${u.slice(0,8)}…`;
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
</style>

<div class="wrap">
  <h1>AltSky</h1>

  <p class="muted">
    플레이어: <strong>{params.name}</strong>
    {#if player}&nbsp;(<span class="muted">{shortUUID(player.uuid)}</span>){/if}
  </p>

  <div class="row" style="margin:8px 0 20px">
    <button class="ghost" on:click={() => history.back()}>← 뒤로</button>
    <button on:click={() => load(true)} disabled={loading}>
      {#if loading}<span class="spinner" style="vertical-align:-3px;margin-right:6px;"></span>{/if}
      새로고침
    </button>
    {#if lastUpdated}
      <span class="muted">· 캐시: {timeAgo(lastUpdated)}</span>
    {/if}
  </div>

  {#if errorMsg}
    <div class="err">{errorMsg}</div>
  {/if}

  {#if loading && !errorMsg}
    <div class="card" style="display:flex;gap:10px;align-items:center">
      <span class="spinner"></span>
      <span>불러오는 중…</span>
    </div>
  {/if}

  {#if !loading && !errorMsg && profiles.length}
    <div class="grid">
      {#each profiles as prf}
        <div class="card">
          <div><strong>{prf.cute_name ?? prf.name ?? 'Profile'}</strong></div>
          {#if prf.members}
            <div class="muted" style="margin-top:6px">멤버 수: {Object.keys(prf.members).length}</div>
          {/if}
          {#if prf.game_mode}<div class="muted">모드: {prf.game_mode}</div>{/if}
          {#if prf.last_save}
            <div class="muted">최근 저장: {timeAgo(prf.last_save)}</div>
          {/if}
        </div>
      {/each}
    </div>
  {/if}
</div>
