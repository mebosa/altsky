<!-- WardrobeSection.svelte -->
<script lang="ts">
  import type { WardrobeItem } from '$lib/types/wardrobe';
  import type { ProfileSummaryResponse } from '$lib/types/profile';
  import { texturePackStore } from '$lib/stores/texturePack';
  import type { TexturePack } from '$lib/stores/texturePack';
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

  const pendingTintKeys = new Set<string>();
  const TEXTURE_PACK_ORDER: TexturePack[] = ['furfsky', 'vanilla'];

  type IconSource = TexturePack | 'legacy';

  function pickIconVariant(
    item: WardrobeItem | null,
    pack?: TexturePack
  ): { url: string; source: IconSource } | null {
    if (!item) return null;
    if (item.skin_url) {
      return { url: item.skin_url, source: 'legacy' };
    }
    const variants = item.icon_variants ?? {};
    if (pack && variants[pack]) {
      return { url: variants[pack]!, source: pack };
    }
    for (const fallback of TEXTURE_PACK_ORDER) {
      const candidate = variants[fallback];
      if (candidate) {
        return { url: candidate, source: fallback };
      }
    }
    if (item.icon_url) {
      return { url: item.icon_url, source: 'legacy' };
    }
    return null;
  }

  function resolveIconUrl(item: WardrobeItem | null, _version: number, pack?: TexturePack): string | null {
    if (!item) return null;
    const picked = pickIconVariant(item, pack);
    if (!picked) return null;
    const { url: iconUrl, source } = picked;
    if (source !== 'vanilla' || !iconUrl || isFallbackIcon(iconUrl)) {
      return iconUrl;
    }

    const leatherColor = formatLeatherColor(item.leather_color);
    if (!leatherColor) {
      return iconUrl;
    }

    const key = `${iconUrl}|${leatherColor}`;
    const cached = peekTintedIcon(iconUrl, leatherColor);
    if (cached) {
      return cached;
    }

    if (!pendingTintKeys.has(key)) {
      pendingTintKeys.add(key);
      ensureTintedIcon(iconUrl, leatherColor)
        .catch(() => iconUrl)
        .then(() => {
          pendingTintKeys.delete(key);
          iconVersion += 1;
        });
    }

    return iconUrl;
  }

  function itemInitial(item: WardrobeItem | null, fallback: string): string {
    if (!item) return '?';
    const first = item.name?.charAt(0)?.toUpperCase();
    if (first && /^[A-Z0-9]$/i.test(first)) {
      return first;
    }
    const alt = fallback?.charAt(0)?.toUpperCase();
    return alt || '?';
  }

  // Reactive declarations
  let iconVersion = 0;
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
              {@const rarityColor = item ? rarityToBackground(item.rarity) : null}
              {@const iconSrc = resolveIconUrl(item, iconVersion, $texturePackStore)}
              {@const hasIcon = !!iconSrc}
              {@const styleValue = buildStyleString([
                rarityColor ? `--rarity-color:${rarityColor}` : null
              ])}
              <div
                class={`equipped-icon ${hasIcon ? '' : 'placeholder'}`}
                style={styleValue}>
                {#if hasIcon}
                  <img
                    src={iconSrc}
                    alt={`${item?.name ?? 'Wardrobe item'} icon`}
                    loading="lazy"
                    width="60"
                    height="60"
                  />
                {:else if item}
                  <span class="equipped-initial">
                    {itemInitial(item, pieceLabel(item))}
                  </span>
                {:else}
                  <span class="equipped-initial">?</span>
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

</style>

