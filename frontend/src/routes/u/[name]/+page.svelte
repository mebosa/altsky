<script lang='ts'>
  import ProfileHeader from '/components/ProfileHeader.svelte';
  import Card from '/components/Card.svelte';
  import StatCard from '/components/StatCard.svelte';
  import { get } from '/api';

  export let params: { name: string };

  let loading = true;
  let errorMsg = '';
  let uuid = '';
  let prof: any = null;

  async function loadAll() {
    loading = true; errorMsg = ''; prof = null;
    try {
      // 1) 이름 -> UUID
      const p = await get<{name:string, uuid:string}>(/api/player/);
      uuid = p.uuid;

      // 2) 프로필 (임시 raw API 사용)
      //   백엔드에서 /api/profile/<uuid>?raw=1 만들어 둔 상태 가정
      prof = await get<any>(/api/profile/?raw=1);
    } catch (e) {
      console.error(e);
      errorMsg = (e as Error).message ?? 'error';
    } finally {
      loading = false;
    }
  }

  loadAll();
</script>

<ProfileHeader name={params.name} {uuid} />

{#if loading}
  <p>불러오는 중…</p>
{:else if errorMsg}
  <p style='color:#ef4444'>에러: {errorMsg}</p>
{:else if prof}
  <div class='grid'>
    <StatCard label='Combat Lv.' value={prof?.skills?.combat ?? null} />
    <StatCard label='Foraging Lv.' value={prof?.skills?.foraging ?? null} />
    <StatCard label='Mining Lv.' value={prof?.skills?.mining ?? null} />
    <StatCard label='Enchanting Lv.' value={prof?.skills?.enchanting ?? null} />
  </div>

  <div class='twogrid'>
    <Card title='Purse'>
      <div class='mono'>{prof?.purse ?? '-'}</div>
    </Card>
    <Card title='Fairy Souls'>
      <div class='mono'>{prof?.fairy_souls?.found ?? 0} / {prof?.fairy_souls?.total ?? '-'}</div>
    </Card>
  </div>

  <Card title='Raw (임시)'>
    <pre>{JSON.stringify(prof, null, 2)}</pre>
  </Card>
{/if}

<style>
  :global(body){background:#f6f7fb}
  .grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin:16px 0}
  .twogrid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;margin:12px 0 16px}
  pre{max-height:420px;overflow:auto;margin:0}
  .mono{font-family:ui-monospace, SFMono-Regular, Menlo, monospace}
</style>