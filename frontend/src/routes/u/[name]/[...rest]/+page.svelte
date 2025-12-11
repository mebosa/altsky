<script lang="ts">
  import PlayerPage from '../+page.svelte';
  import type { PageData } from '../$types';
  export let data: PageData;
</script>

<PlayerPage {data} />
