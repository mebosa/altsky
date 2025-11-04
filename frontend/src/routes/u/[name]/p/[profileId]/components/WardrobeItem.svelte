<script lang="ts">
  import { getArmorTexturePath } from '$lib/utils/armor';
  import { texturePackStore } from '$lib/stores/texturePack';
  import type { WardrobeItem } from '../profileTypes';
  import type { ArmorPiece } from '$lib/types/armor';

  export let item: WardrobeItem | null;

  $: armorType = item?.id?.toLowerCase()?.split('_')[0] || '';
  $: armorPiece = (item?.id?.toLowerCase()?.split('_')[1] || '') as ArmorPiece;
  $: imageSrc = item ? getArmorTexturePath(armorType, armorPiece, $texturePackStore) : '';

  function handleError(event: Event) {
    const img = event.target as HTMLImageElement;
    img.onerror = null;
    img.src = `/static/icons/armor/vanilla/${armorType}_${armorPiece}.png`;
  }
</script>

{#if item}
  <div class="relative w-12 h-12 bg-base-300 rounded">
    {#if imageSrc}
      <img
        src={imageSrc}
        alt={item.id}
        class="w-full h-full object-contain"
        on:error={handleError}
      />
    {/if}
  </div>
{:else}
  <div class="w-12 h-12 bg-base-300 rounded opacity-50" />
{/if}

<style>
  img {
    image-rendering: pixelated;
  }
</style>