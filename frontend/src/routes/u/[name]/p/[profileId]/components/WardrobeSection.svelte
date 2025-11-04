<!-- WardrobeSection.svelte -->
<script lang="ts">
  import type { WardrobeItem } from '$lib/types/wardrobe';
  import type { ProfileSummaryResponse } from '$lib/types/profile';
  import { iconPath } from '$lib/iconPack';

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
              <div
                class={`equipped-icon ${item.icon_url ? '' : 'placeholder'} ${item.leather_color ? 'leather' : ''}`}
                style={item.leather_color ? `--leather-color:${item.leather_color}` : undefined}>
                {#if item.icon_url}
                  <img src={item.icon_url} alt={`${item.name} icon`} loading="lazy" width="60" height="60" />
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
    background: rgba(148, 163, 184, 0.1);
    overflow: hidden;
  }

  .equipped-icon.placeholder {
    background: rgba(148, 163, 184, 0.15);
  }

  .equipped-icon.leather {
    background: var(--leather-color);
  }

  .equipped-icon img {
    width: 100%;
    height: 100%;
    object-fit: contain;
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
</style>