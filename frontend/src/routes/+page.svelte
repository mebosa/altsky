<script lang="ts">
  import { onMount } from 'svelte';
  import { get, API_BASE } from '$lib/api';

  export let params: { name: string };

  let uuid = '';
  let profile: any = null;
  let loading = true;
  let errorMsg = '';

  onMount(async () => {
    loading = true;
    errorMsg = '';
    profile = null;

    try {
      // 1) 이름 -> UUID
      const p = await get<{ name: string; uuid: string }>(`/api/player/${encodeURIComponent(params.name)}`);
      uuid = p.uuid;

      // 2) Hypixel 프로필
      const h = await get<{ ok: boolean; data: any }>(`/api/hypixel/profile/${uuid}`);
      profile = h.data?.profiles ?? h.data ?? h;
    } catch (e) {
      errorMsg = (e as Error).message || '요청 실패';
      console.error('[AltSky] load error:', e);
    } finally {
      loading = false;
    }
  });
</script>

<svelte:head>
  <title>AltSky — {params.name}</title>
</svelte:head>

<section style="max-width:960px;margin:64px auto;padding:0 16px">
  <h1 style="font-size:56px;line-height:1.1;margin:0 0 16px">AltSky</h1>
  <p style="color:#6b7280">플레이어: <code>{uuid ? `${uuid.slice(0,8)}…` : '(불러오는 중)'}</code></p>

  {#if loading}
    <p>불러오는 중…</p>
  {:else if errorMsg}
    <p style="color:#ef4444">에러: {errorMsg}</p>
  {:else if profile}
    <div style="display:grid;gap:12px">
      <details open>
        <summary style="cursor:pointer">Raw profiles</summary>
        <pre style="background:#0b1020;color:#e5e7eb;padding:12px;overflow:auto;border-radius:8px">
{JSON.stringify(profile, null, 2)}
        </pre>
      </details>
    </div>
  {:else}
    <p>데이터가 없습니다.</p>
  {/if}

  <p style="margin-top:24px;font-size:12px;opacity:.6">API_BASE: {API_BASE}</p>
</section>
