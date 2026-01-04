<script lang="ts">
  import PlayerPage from '../+page.svelte';
  import type { PageData } from '../$types';
  import { page } from '$app/stores';
  export let data: PageData;
</script>

<PlayerPage {data} params={{ name: $page.params.name ?? '' }} />
