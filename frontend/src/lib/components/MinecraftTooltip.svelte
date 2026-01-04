<script lang="ts">
  export let item: any;
  export let x: number;
  export let y: number;

  const COLOR_MAP: Record<string, string> = {
    '0': '#000000',
    '1': '#0000AA',
    '2': '#00AA00',
    '3': '#00AAAA',
    '4': '#AA0000',
    '5': '#AA00AA',
    '6': '#FFAA00',
    '7': '#AAAAAA',
    '8': '#555555',
    '9': '#5555FF',
    'a': '#55FF55',
    'b': '#55FFFF',
    'c': '#FF5555',
    'd': '#FF55FF',
    'e': '#FFFF55',
    'f': '#FFFFFF',
  };

  function parseLore(lore: string): string {
    if (!lore) return '';
    // Replace § with span
    let html = lore.replace(/§([0-9a-f])/g, (match, code) => {
      return `</span><span style="color: ${COLOR_MAP[code]}">`;
    });
    // Handle formatting codes (k, l, m, n, o, r) - simplified for now
    html = html.replace(/§([k-o])/g, ''); // Ignore formatting for now
    html = html.replace(/§r/g, '</span><span style="color: #AAAAAA">'); // Reset
    
    return '<span style="color: #AAAAAA">' + html + '</span>';
  }
  
  // Adjust position to keep on screen
  let innerWidth: number;
  let innerHeight: number;
  
  $: style = (() => {
    let top = y + 10;
    let left = x + 10;
    
    // Simple boundary check (approximate width/height)
    if (left + 250 > innerWidth) left = x - 260;
    if (top + 100 > innerHeight) top = y - 110; // Just a guess, better to measure
    
    return `top: ${top}px; left: ${left}px;`;
  })();
</script>

<svelte:window bind:innerWidth bind:innerHeight />

<div class="tooltip" style={style}>
  <div class="tooltip-name" style="color: {item.tierColor || '#fff'}">{item.name}</div>
  {#if item.lore}
    <div class="tooltip-lore">{@html parseLore(item.lore)}</div>
  {/if}
  <div class="tooltip-footer">
    <span class="rarity" style="color: {item.tierColor || '#fff'}">{item.tier} {item.category || 'ITEM'}</span>
  </div>
</div>

<style>
  .tooltip {
    position: fixed;
    z-index: 1000;
    background-color: rgba(16, 0, 16, 0.95);
    border: 2px solid #5000FF;
    border-radius: 4px;
    padding: 8px;
    pointer-events: none;
    min-width: 200px;
    max-width: 300px;
    font-family: monospace;
    box-shadow: 0 4px 8px rgba(0,0,0,0.5);
  }
  
  .tooltip-name {
    font-weight: bold;
    margin-bottom: 4px;
    text-shadow: 2px 2px 0 #000;
  }
  
  .tooltip-lore {
    white-space: pre-wrap;
    font-size: 14px;
    line-height: 1.4;
    text-shadow: 1px 1px 0 #000;
  }
  
  .tooltip-footer {
    margin-top: 8px;
    font-weight: bold;
    text-shadow: 2px 2px 0 #000;
  }
</style>
