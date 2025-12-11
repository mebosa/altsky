<script lang="ts">
  import { formatNumber } from '$lib/utils';
  import { rarityToBackground, parseLegacyText, type LegacySegment } from '$lib/utils/wardrobe';
  import { texturePackStore } from '$lib/stores/texturePack';
  import type { ProfileSummaryResponse } from './profileTypes';

  export let summary: ProfileSummaryResponse;

  const RARITY_ORDER = [
    'DIVINE',
    'SUPREME',
    'MYTHIC',
    'LEGENDARY',
    'EPIC',
    'RARE',
    'VERY SPECIAL',
    'UNCOMMON',
    'SPECIAL',
    'COMMON',
    'BASIC',
    'ULTIMATE',
    'ADMIN'
  ] as const;

  const rarityPriority = new Map<string, number>(RARITY_ORDER.map((value, index) => [value, index]));

  function normalizeIdentifier(value?: string | null) {
    if (!value) return '';
    return value.replace(/[_-]+/g, ' ').replace(/\s+/g, ' ').trim();
  }

  function titleize(value: string) {
    return value
      .toLowerCase()
      .split(' ')
      .map((segment) => (segment ? segment[0].toUpperCase() + segment.slice(1) : segment))
      .join(' ');
  }

  function formatIdentifier(value?: string | null) {
    const normalized = normalizeIdentifier(value);
    return normalized ? titleize(normalized) : null;
  }

  function legacySegmentStyle(segment: LegacySegment) {
    const styles: string[] = [];
    if (segment.color) {
      styles.push(`color:${segment.color}`);
    }
    const decorations: string[] = [];
    if (segment.underline) decorations.push('underline');
    if (segment.strikethrough) decorations.push('line-through');
    if (decorations.length) {
      styles.push(`text-decoration:${decorations.join(' ')}`);
    }
    return styles.length ? styles.join(';') : undefined;
  }

  function legacySegmentClasses(segment: LegacySegment) {
    return [
      'mc-span',
      segment.bold ? 'mc-bold' : '',
      segment.italic ? 'mc-italic' : '',
      segment.obfuscated ? 'mc-obfuscated' : ''
    ]
      .filter(Boolean)
      .join(' ');
  }

  function normalizeRarity(value?: string | null) {
    const normalized = normalizeIdentifier(value);
    return normalized ? normalized.toUpperCase() : '';
  }

  function raritySortKey(value?: string | null) {
    const key = normalizeRarity(value);
    return rarityPriority.get(key) ?? rarityPriority.size + 1;
  }

  function rarityLabel(value?: string | null) {
    const normalized = normalizeIdentifier(value);
    return normalized ? titleize(normalized) : null;
  }

  function formatSlot(slot: number) {
    return slot + 1;
  }

  function formatTuningLabel(key: string) {
    return formatIdentifier(key) ?? key;
  }

  $: accessories = summary?.accessories;
  $: items = accessories?.items ?? [];
  $: sortedItems = items
    .slice()
    .sort((a, b) => {
      const rarityDiff = raritySortKey(a.rarity) - raritySortKey(b.rarity);
      if (rarityDiff !== 0) return rarityDiff;
      const nameA = a.name?.toLowerCase() ?? '';
      const nameB = b.name?.toLowerCase() ?? '';
      if (nameA !== nameB) return nameA.localeCompare(nameB);
      return a.slot - b.slot;
    });
  $: rarityEntries = accessories
    ? Object.entries(accessories.rarity_counts ?? {})
        .map(([rarity, count]) => [normalizeRarity(rarity) || rarity, count] as const)
        .filter(([, count]) => (count ?? 0) > 0)
        .sort((a, b) => raritySortKey(a[0]) - raritySortKey(b[0]))
    : [];
  $: tuningEntries = accessories
    ? Object.entries(accessories.tuning ?? {}).sort(([, a], [, b]) => Number(b) - Number(a))
    : [];
  $: powerStoneEntries = accessories
    ? Object.entries(accessories.power_stones ?? {})
        .filter(([, count]) => (count ?? 0) > 0)
        .sort(([, a], [, b]) => Number(b) - Number(a))
    : [];
  $: formattedUnlockedPowers = accessories
    ? accessories.unlocked_powers
        .map((power) => formatIdentifier(power))
        .filter((value): value is string => !!value)
    : [];
  $: bagCapacity = accessories?.slots ?? sortedItems.length;
  $: uniqueCount = accessories?.unique_count ?? sortedItems.length;
</script>

<section id="accessories" class="accessories-section">
  {#if !accessories || !sortedItems.length}
    <div class="card empty-card">
      <p>No accessories found.</p>
    </div>
  {:else}
    <div class="summary-grid">
      <div class="card metric-card">
        <span class="metric-label">Magical Power</span>
        <span class="metric-value">{formatNumber(accessories.magical_power ?? 0, 0)}</span>
        {#if accessories.highest_magical_power > (accessories.magical_power ?? 0)}
          <span class="metric-note">
            Highest {formatNumber(accessories.highest_magical_power, 0)}
          </span>
        {/if}
      </div>
      <div class="card metric-card">
        <span class="metric-label">Selected Power</span>
        <span class="metric-value">
          {formatIdentifier(accessories.selected_power_label ?? accessories.selected_power) ?? 'None'}
        </span>
        {#if formattedUnlockedPowers.length}
          <span class="metric-note">{formattedUnlockedPowers.length} unlocked</span>
        {/if}
      </div>
      <div class="card metric-card">
        <span class="metric-label">Unique Accessories</span>
        <span class="metric-value">{formatNumber(uniqueCount ?? 0, 0)}</span>
        <span class="metric-note">of {formatNumber(sortedItems.length, 0)} total</span>
      </div>
      <div class="card metric-card">
        <span class="metric-label">Bag Capacity</span>
        <span class="metric-value">{formatNumber(bagCapacity, 0)}</span>
        <span class="metric-note">{formatNumber(sortedItems.length, 0)} used</span>
      </div>
    </div>

    <div class="info-grid">
      {#if rarityEntries.length}
        <div class="card info-card">
          <h3>By Rarity</h3>
          <ul class="rarity-list">
            {#each rarityEntries as [rarity, count]}
              {@const label = rarityLabel(rarity)}
              {@const color = rarityToBackground(rarity)}
              <li>
                <span class="rarity-pill" style={color ? `background:${color}` : undefined}>
                  {label ?? rarity}
                </span>
                <span class="rarity-count">{formatNumber(count, 0)}</span>
              </li>
            {/each}
          </ul>
        </div>
      {/if}

      {#if tuningEntries.length}
        <div class="card info-card">
          <h3>Accessory Tuning</h3>
          <ul class="stat-list">
            {#each tuningEntries as [stat, value]}
              <li>
                <span>{formatTuningLabel(stat)}</span>
                <span>{formatNumber(value, 0)}</span>
              </li>
            {/each}
          </ul>
        </div>
      {/if}

      {#if formattedUnlockedPowers.length}
        <div class="card info-card">
          <h3>Unlocked Powers</h3>
          <div class="tag-row">
            {#each formattedUnlockedPowers as power}
              <span class="tag">{power}</span>
            {/each}
          </div>
        </div>
      {/if}

      {#if powerStoneEntries.length}
        <div class="card info-card">
          <h3>Power Stones</h3>
          <ul class="stat-list">
            {#each powerStoneEntries as [stone, count]}
              <li>
                <span>{formatIdentifier(stone) ?? stone}</span>
                <span>{formatNumber(count, 0)}</span>
              </li>
            {/each}
          </ul>
        </div>
      {/if}
    </div>

    <div class="accessory-grid">
      {#each sortedItems as item (item.slot)}
        {@const rarityColor = rarityToBackground(item.rarity)}
        {@const iconSrc =
            item.icon_variants?.[$texturePackStore] ??
            item.icon_variants?.furfsky ??
            item.icon_variants?.vanilla ??
            item.icon_url ??
            null}
        <div class="accessory-slot">
          <button
            type="button"
            class={`accessory-icon ${iconSrc ? '' : 'placeholder'}`}
            style={rarityColor ? `--rarity-color:${rarityColor}` : undefined}
            aria-label={item.name}
          >
            {#if iconSrc}
              <img
                src={iconSrc}
                alt=""
                loading="lazy"
                width="56"
                height="56"
              />
            {:else}
              <span class="initial">{item.name.slice(0, 1).toUpperCase()}</span>
            {/if}
          </button>
          <div class="accessory-tooltip">
            <div class="tooltip-header">
              <span class="tooltip-name">{item.name}</span>
              <span class="tooltip-rarity">{rarityLabel(item.rarity) ?? 'Unknown'}</span>
            </div>
            <div class="tooltip-meta">
              <span>Slot {formatSlot(item.slot)}</span>
              {#if item.modifier}
                <span>Reforge: {formatIdentifier(item.modifier)}</span>
              {/if}
              {#if item.enrichment}
                <span>Enrichment: {formatIdentifier(item.enrichment)}</span>
              {/if}
              {#if item.recombobulated}
                <span class="highlight">Recombobulated</span>
              {/if}
            </div>
            {#if item.lore_colored?.length}
              <div class="tooltip-lore">
                {#each item.lore_colored as line, lineIndex (lineIndex)}
                  {@const segments = parseLegacyText(line)}
                  <p>
                    {#if segments.length}
                      {#each segments as segment, segIndex (segIndex)}
                        <span
                          class={legacySegmentClasses(segment)}
                          style={legacySegmentStyle(segment)}
                        >
                          {segment.text}
                        </span>
                      {/each}
                    {:else}
                      <span class="mc-span">&nbsp;</span>
                    {/if}
                  </p>
                {/each}
              </div>
            {:else if item.lore.length}
              <div class="tooltip-lore">
                {#each item.lore as line, index (index)}
                  <p>{line}</p>
                {/each}
              </div>
            {/if}
          </div>
        </div>
      {/each}
    </div>
  {/if}
</section>

<style>
  .accessories-section {
    display: flex;
    flex-direction: column;
    gap: 24px;
  }

  .empty-card {
    text-align: center;
    color: var(--theme-text-soft);
    padding: 32px;
  }

  .summary-grid {
    display: grid;
    gap: 18px;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  }

  .metric-card {
    gap: 8px;
  }

  .metric-label {
    font-size: 0.85rem;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    color: var(--theme-text-soft);
  }

  .metric-value {
    font-size: 1.8rem;
    font-weight: 600;
    color: var(--theme-text-primary);
  }

  .metric-note {
    font-size: 0.85rem;
    color: var(--theme-text-soft);
  }

  .info-grid {
    display: grid;
    gap: 18px;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  }

  .info-card h3 {
    margin: 0;
    font-size: 1rem;
    color: var(--theme-text-primary);
  }

  .rarity-list,
  .stat-list {
    list-style: none;
    margin: 8px 0 0;
    padding: 0;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .rarity-list li,
  .stat-list li {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    font-size: 0.9rem;
  }

  .rarity-pill {
    display: inline-flex;
    align-items: center;
    padding: 4px 10px;
    border-radius: 999px;
    background: rgba(148, 163, 184, 0.18);
    color: var(--theme-text-primary);
    font-weight: 600;
    font-size: 0.85rem;
  }

  .rarity-count {
    font-variant-numeric: tabular-nums;
    color: var(--theme-text-soft);
  }

  .tag-row {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 10px;
  }

  .tag {
    padding: 6px 12px;
    border-radius: 999px;
    background: rgba(148, 163, 184, 0.16);
    font-size: 0.85rem;
    font-weight: 600;
    color: var(--theme-text-primary);
  }

  .accessory-grid {
    display: grid;
    gap: 16px;
    grid-template-columns: repeat(auto-fit, minmax(64px, 1fr));
    justify-items: center;
  }

  .accessory-slot {
    position: relative;
    display: flex;
    justify-content: center;
  }

  .accessory-icon {
    width: 64px;
    height: 64px;
    border-radius: 18px;
    border: 1px solid rgba(148, 163, 184, 0.45);
    background: var(--rarity-color, rgba(148, 163, 184, 0.12));
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
    padding: 0;
  }

  .accessory-icon.placeholder {
    background: rgba(148, 163, 184, 0.12);
  }

  .accessory-icon:hover,
  .accessory-slot:focus-within .accessory-icon {
    transform: translateY(-4px) scale(1.05);
    box-shadow: 0 16px 32px rgba(15, 23, 42, 0.35);
    border-color: rgba(148, 163, 184, 0.6);
  }

  .accessory-icon img {
    width: 48px;
    height: 48px;
    object-fit: contain;
  }

  .initial {
    font-size: 1.2rem;
    font-weight: 600;
    color: var(--theme-text-primary);
  }

  .accessory-tooltip {
    position: absolute;
    bottom: calc(100% + 12px);
    left: 50%;
    transform: translate(-50%, 6px);
    min-width: 220px;
    max-width: 260px;
    padding: 14px 16px;
    border-radius: 12px;
    background: rgba(15, 23, 42, 0.92);
    border: 1px solid rgba(148, 163, 184, 0.35);
    color: #e2e8f0;
    box-shadow: 0 16px 32px rgba(15, 23, 42, 0.4);
    opacity: 0;
    pointer-events: none;
    transition: opacity 0.18s ease, transform 0.18s ease;
    z-index: 10;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .accessory-slot:hover .accessory-tooltip,
  .accessory-slot:focus-within .accessory-tooltip {
    opacity: 1;
    transform: translate(-50%, 0);
    pointer-events: auto;
  }

  .tooltip-header {
    display: flex;
    justify-content: space-between;
    gap: 12px;
    align-items: baseline;
  }

  .tooltip-name {
    font-weight: 600;
    color: #f8fafc;
  }

  .tooltip-rarity {
    font-size: 0.85rem;
    color: var(--theme-accent);
  }

  .tooltip-meta {
    display: flex;
    flex-wrap: wrap;
    gap: 6px 12px;
    font-size: 0.85rem;
    color: rgba(226, 232, 240, 0.85);
  }

  .tooltip-meta .highlight {
    color: #facc15;
    font-weight: 600;
  }

  .tooltip-lore {
    display: flex;
    flex-direction: column;
    gap: 4px;
    max-height: min(280px, 50vh);
    overflow-y: auto;
    padding-right: 4px;
  }

  .tooltip-lore p {
    margin: 0;
    font-size: 0.8rem;
    color: rgba(226, 232, 240, 0.88);
    line-height: 1.35;
  }

  .mc-span {
    display: inline;
  }

  .mc-bold {
    font-weight: 700;
  }

  .mc-italic {
    font-style: italic;
  }

  .mc-obfuscated {
    animation: obfuscate 1s steps(10) infinite;
  }

  @keyframes obfuscate {
    0% {
      filter: blur(0.6px);
    }
    50% {
      filter: blur(0);
    }
    100% {
      filter: blur(0.6px);
    }
  }

  @media (max-width: 768px) {
    .accessories-section {
      gap: 20px;
    }

    .accessory-grid {
      grid-template-columns: repeat(auto-fit, minmax(54px, 1fr));
      gap: 12px;
    }

    .accessory-icon {
      width: 56px;
      height: 56px;
      border-radius: 16px;
    }

    .accessory-icon img {
      width: 44px;
      height: 44px;
    }

    .accessory-tooltip {
      min-width: 200px;
      max-width: 240px;
    }
  }
</style>
