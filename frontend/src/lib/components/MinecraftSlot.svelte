<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { getItemTextureUrl } from '$lib/stores/hypixelItems';
  import { texturePackStore } from '$lib/stores/texturePack';

  export let item: any = null; // The item object
  export let isSelected = false;
  export let count = 1;

  const dispatch = createEventDispatcher();

  $: iconUrl = item ? getItemTextureUrl(item.tag || item.id, $texturePackStore) : null;

  function handleClick() {
    if (item) {
      dispatch('click', item);
    }
  }

  function handleMouseEnter() {
    if (item) {
      dispatch('mouseenter', item);
    }
  }

  function handleMouseLeave() {
    dispatch('mouseleave');
  }
</script>

<div 
  class="slot" 
  class:has-item={!!item} 
  class:selected={isSelected}
  on:click={handleClick}
  on:keydown={(e) => e.key === 'Enter' && handleClick()}
  on:mouseenter={handleMouseEnter}
  on:mouseleave={handleMouseLeave}
  role="button"
  tabindex="0"
>
  {#if item && iconUrl}
    <img src={iconUrl} alt={item.name} class="item-icon" />
    {#if count > 1}
      <span class="item-count">{count}</span>
    {/if}
  {/if}
  <div class="hover-overlay"></div>
</div>

<style>
  .slot {
    width: 48px; /* Slightly larger for web usability */
    height: 48px;
    background-color: #8b8b8b;
    border: 2px solid;
    border-color: #373737 #fff #fff #373737;
    position: relative;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    box-sizing: border-box;
    image-rendering: pixelated;
  }

  .slot:hover .hover-overlay {
    background-color: rgba(255, 255, 255, 0.2);
  }

  .hover-overlay {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    pointer-events: none;
  }

  .item-icon {
    width: 32px;
    height: 32px;
    object-fit: contain;
  }

  .item-count {
    position: absolute;
    bottom: 2px;
    right: 2px;
    font-family: monospace; 
    font-weight: bold;
    font-size: 14px;
    color: #fff;
    text-shadow: 1px 1px 0 #3f3f3f;
    pointer-events: none;
  }
  
  .selected {
    border: 2px solid yellow;
  }
</style>
