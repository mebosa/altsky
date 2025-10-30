<script lang="ts">
  import { goto } from '$app/navigation';
  import { debounce, loadRecent, saveRecent } from '$lib/utils';

  let name = '';
  let recent: string[] = [];

  function toUser(n: string) {
    const q = n.trim();
    if (!q) return;
    saveRecent(q);
    recent = loadRecent();
    goto(`/u/${encodeURIComponent(q)}`);
  }

  const debounced = debounce((v: string) => (name = v), 0); // svelte 바인딩 유지용

  function onKey(e: KeyboardEvent) {
    if (e.key === 'Enter') toUser(name);
  }

  $: recent = loadRecent();
</script>

<style>
  .wrap{max-width:720px;margin:48px auto;padding:0 16px}
  .row{display:flex;gap:8px}
  input{flex:1;padding:12px 14px;font-size:16px;border:1px solid #d1d5db;border-radius:10px}
  button{padding:12px 16px;border-radius:10px;border:1px solid #111827;background:#111827;color:white;cursor:pointer}
  .chips{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px}
  .chip{padding:6px 10px;border-radius:999px;background:#f3f4f6;cursor:pointer}
  h1{font-size:42px;margin:0 0 12px}
  p.muted{color:#6b7280;margin:0 0 24px}
</style>

<div class="wrap">
  <h1>AltSky</h1>
  <p class="muted">플레이어 이름을 입력하세요.</p>
  <div class="row">
    <input
      placeholder="예: mebosa"
      value={name}
      on:input={(e)=>debounced((e.target as HTMLInputElement).value)}
      on:keydown={onKey}
    />
    <button on:click={() => toUser(name)}>검색</button>
  </div>

  {#if recent.length}
    <div class="chips">
      {#each recent as r}
        <span class="chip" on:click={() => toUser(r)}>{r}</span>
      {/each}
    </div>
  {/if}
</div>
