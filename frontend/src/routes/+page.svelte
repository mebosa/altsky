<script lang="ts">
  import { get, API_BASE } from "$lib/api";
  let name = "";
  let data: any = null;
  let profile: any = null;
  let errorMsg = "";

  async function lookup() {
    errorMsg = "";
    profile = null;
    data = null;
    const q = name.trim();
    if (!q) return;
    try {
      data = await get(`/api/player/${encodeURIComponent(q)}`);
    } catch (e) {
      console.error(e);
      errorMsg = "검색 실패: " + (e as Error).message;
    }
  }

  async function loadProfile() {
    if (!data?.uuid) return;
    errorMsg = "";
    profile = null;
    try {
      profile = await get(`/api/profile/${data.uuid}`);
    } catch (e) {
      console.error(e);
      errorMsg = "프로필 로드 실패: " + (e as Error).message;
    }
  }
</script>

<h1>AltSky</h1>
<p style="font-size:12px;opacity:.7">API_BASE: {API_BASE}</p>

<input placeholder="Player name" bind:value={name} />
<button on:click={lookup}>Search</button>
<button on:click={loadProfile} disabled={!data}>Load profile</button>

{#if errorMsg}<p>{errorMsg}</p>{/if}

{#if data}
  <h3>Player</h3>
  <pre>{JSON.stringify(data, null, 2)}</pre>
{/if}

{#if profile}
  <h3>SkyBlock Profiles (summary)</h3>
  <pre>{JSON.stringify(profile, null, 2)}</pre>
{/if}
