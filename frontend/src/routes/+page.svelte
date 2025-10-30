<script lang='ts'>
  import { get } from '/api';
  let name = '';
  let data: any = null;
  let errorMsg = '';

  async function lookup() {
    errorMsg = '';
    data = null;
    const q = name.trim();
    if (!q) return;
    try {
      data = await get(/api/player/);
    } catch (e) {
      errorMsg = '검색 실패: ' + (e as Error).message;
    }
  }
</script>

<h1>AltSky</h1>
<input placeholder='Player name' bind:value={name} />
<button on:click={lookup}>Search</button>

{#if errorMsg}<p>{errorMsg}</p>{/if}
{#if data}<pre>{JSON.stringify(data, null, 2)}</pre>{/if}
