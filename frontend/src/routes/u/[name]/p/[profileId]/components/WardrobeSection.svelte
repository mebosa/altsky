<!-- WardrobeSection.svelte -->
<script lang="ts">
  import type { WardrobeItem } from '$lib/types/wardrobe';
  import type { ProfileSummaryResponse } from '$lib/types/profile';
  import {
    buildStyleString,
    ensureTintedIcon,
    formatLeatherColor,
    isFallbackIcon,
    peekTintedIcon,
    rarityToBackground,
  } from '$lib/utils/wardrobe';

  export let summary: ProfileSummaryResponse;

  // Helper functions
  function buildWardrobeColumns(items: (WardrobeItem | null)[]) {
    const columns: (WardrobeItem | null)[][] = [];
    let currentColumn: (WardrobeItem | null)[] = [];

    for (const item of items) {
      currentColumn.push(item);
      if (currentColumn.length === 4) {
        columns.push(currentColumn);
        currentColumn = [];
      }
    }

    if (currentColumn.length > 0) {
      columns.push(currentColumn);
    }

    return columns;
  }

  function pieceLabel(item: WardrobeItem | null) {
    if (!item) return '';
    const match = item.id.match(/LEATHER_(\w+)$/);
    return match ? match[1].toLowerCase() : '';
  }

  // Reactive declarations
  $: wardrobeItems = summary?.wardrobe?.items ?? [];
  $: wardrobeHasItems = wardrobeItems.some((item) => !!item);
  $: {
    const firstBankRaw = wardrobeItems.filter(item => item && item.slot < 36);
    const secondBankRaw = wardrobeItems.filter(item => item && item.slot >= 36);
    firstBankColumns = buildWardrobeColumns(firstBankRaw);
    secondBankColumns = buildWardrobeColumns(secondBankRaw);
  }
  $: equippedColumnIndex = summary?.wardrobe?.equipped_slot ?? null;
  $: equippedItems = toEquippedItems(equippedColumnIndex, wardrobeItems);
  $: equippedSetLabel = deriveSetLabel(equippedItems);
  $: equippedStats = aggregateSetStats(equippedItems);
  $: equippedBonuses = gatherSetBonusLines(equippedItems);
</script>

<section class="wardrobe-section">
  <div class="wardrobe-grid">
    {#if data?.summary?.wardrobe}
      <div class="wardrobe-container">
        <div class="equipped-section">
          <div class="wardrobe-column">
            {#each column as item}
              {@const leatherColor = item ? formatLeatherColor(item.leather_color) : null}
              {@const rarityColor = item ? rarityToBackground(item.rarity) : null}
              {@const iconUrl = item?.icon_url ?? null}
              {@const hasIcon = iconUrl && !isFallbackIcon(iconUrl)}
              {@const iconStyle = buildStyleString([
                leatherColor ? `--leather-color:${leatherColor}` : null,
                leatherColor && hasIcon ? `--icon-url:url("${iconUrl}")` : null,
                rarityColor ? `--rarity-color:${rarityColor}` : null
              ])}
              <div
                class={`equipped-icon ${hasIcon ? '' : 'placeholder'} ${item?.leather_color ? 'leather' : ''}`}
                style={iconStyle}>
                {#if hasIcon}
                  <img
                    src={iconUrl}
                    alt={`${item.name} icon`}
                    loading="lazy"
                    width="60"
                    height="60"
                    class={item?.leather_color ? 'leather-base' : ''}
                  />
                  {#if leatherColor}
                    <span class="icon-tint" aria-hidden="true"></span>
                  {/if}
                {:else if item}
                  <span class="equipped-initial">
                    {item?.name?.charAt(0)?.toUpperCase() ?? pieceLabel(item)?.charAt(0) ?? '?'}
                  </span>
                {/if}
                <span class="equipped-piece">{pieceLabel(item)}</span>
              </div>
            {/each}
          </div>
          <div class="equipped-details">
            <div class="equipped-set-name">{equippedSetLabel || 'Custom Mix'}</div>
            {#if equippedStats.length}
              <ul class="equipped-stats">
                {#each equippedStats as stat}
                  <li>
                    <span>{stat.label}</span>
                    <span>{stat.display}</span>
                  </li>
                {/each}
              </ul>
            {/if}
            {#if equippedBonuses.length}
              <div class="equipped-bonuses">
                {#each equippedBonuses as line}
                  <p>{line}</p>
                {/each}
              </div>
            {/if}
          </div>
        </div>
      </div>
    {/if}
  </div>
</section>

<style>
  .wardrobe-section {
    display: flex;
    flex-direction: column;
    gap: 24px;
  }

  .wardrobe-grid {
    display: grid;
    gap: 24px;
  }

  .wardrobe-container {
    background: var(--theme-card-bg);
    border-radius: 16px;
    padding: 24px;
  }

  .equipped-section {
    display: flex;
    gap: 24px;
  }

  .wardrobe-column {
    display: grid;
    gap: 12px;
  }

  .equipped-icon {
    position: relative;
    width: 60px;
    height: 60px;
    border: 2px solid var(--theme-border);
    border-radius: 8px;
    background: var(--rarity-color, rgba(148, 163, 184, 0.1));
    overflow: hidden;
    isolation: isolate;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .equipped-icon.placeholder {
    background: rgba(148, 163, 184, 0.15);
  }

  .equipped-icon img {
    width: 100%;
    height: 100%;
    object-fit: contain;
    image-rendering: pixelated;
  }

  .equipped-icon .leather-base {
    filter: saturate(0);
  }

  .equipped-icon .icon-tint {
    position: absolute;
    inset: 0;
    background: var(--leather-color, transparent);
    mix-blend-mode: color;
    opacity: 0.82;
    pointer-events: none;
    -webkit-mask-image: var(--icon-url);
    -webkit-mask-repeat: no-repeat;
    -webkit-mask-position: center;
    -webkit-mask-size: contain;
    mask-image: var(--icon-url);
    mask-repeat: no-repeat;
    mask-position: center;
    mask-size: contain;
  }

  .equipped-piece {
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    padding: 2px 4px;
    background: rgba(0, 0, 0, 0.75);
    color: #fff;
    font-size: 0.75rem;
    text-align: center;
  }

  .equipped-initial {
    font-size: 1.2rem;
    font-weight: 700;
    color: var(--theme-text);
    position: relative;
    z-index: 1;
    text-shadow: 0 1px 2px rgba(15, 23, 42, 0.35);
  }

  .equipped-details {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .equipped-set-name {
    font-size: 1.25rem;
    font-weight: 600;
    color: var(--theme-text);
  }

  .equipped-stats {
    list-style: none;
    margin: 0;
    padding: 0;
    display: grid;
    gap: 8px;
  }

  .equipped-stats li {
    display: flex;
    justify-content: space-between;
    gap: 16px;
    color: var(--theme-text-soft);
  }

  .equipped-bonuses {
    border-top: 1px solid var(--theme-border);
    padding-top: 16px;
    color: var(--theme-text-soft);
  }

  .equipped-bonuses p {
    margin: 0;
    margin-bottom: 8px;
  }

  .equipped-bonuses p:last-child {
    margin-bottom: 0;
  }

  :global(body[data-icon-pack='flufsky']) .equipped-icon .leather-base {
    filter: none;
  }

  :global(body[data-icon-pack='flufsky']) .equipped-icon .icon-tint {
    display: none;
  }
</style>

