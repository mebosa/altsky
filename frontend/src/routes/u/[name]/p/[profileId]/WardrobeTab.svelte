<script lang="ts">
  import { formatNumber } from '$lib/utils';
  import type {
    AggregatedStat,
    ProfileSummaryResponse,
    WardrobeItem
  } from './profileTypes';

  export let summary: ProfileSummaryResponse;

  const WARDROBE_NUM_COLUMNS = 9;

  function buildWardrobeColumns(items: (WardrobeItem | null)[]) {
    const columns: (WardrobeItem | null)[][] = Array.from(
      { length: WARDROBE_NUM_COLUMNS },
      () => []
    );
    for (let i = 0; i < items.length; i++) {
      const item = items[i];
      if (item) {
        const columnIndex = item.slot % WARDROBE_NUM_COLUMNS;
        columns[columnIndex].push(item);
      }
    }
    return columns.filter((col) => col.length > 0);
  }

  const TRACKED_STATS = new Set([
    'Health',
    'Defense',
    'Strength',
    'Crit Chance',
    'Crit Damage',
    'Attack Speed',
    'Intelligence',
    'Speed',
    'Ferocity',
    'Magic Find',
    'True Defense',
    'Ability Damage',
    'Sea Creature Chance',
    'Farming Fortune',
    'Pet Luck'
  ]);

  function toTitleCase(value: string) {
    return value
      .toLowerCase()
      .split(' ')
      .map((segment) => (segment ? segment[0].toUpperCase() + segment.slice(1) : segment))
      .join(' ');
  }

  function baseSetNameFromId(id: string) {
    const parts = id.split('_');
    if (parts.length <= 1) return toTitleCase(id);
    const piece = parts.pop();
    if (!piece) return toTitleCase(parts.join(' '));
    return toTitleCase(parts.join(' '));
  }

  type ParsedStatLine = {
    label: string;
    value: number;
    suffix: '' | '%';
  };

  function parseStatLine(line: string): ParsedStatLine | null {
    const colonIndex = line.indexOf(':');
    if (colonIndex === -1) return null;
    const label = line.slice(0, colonIndex).trim();
    if (!TRACKED_STATS.has(label)) return null;

    const rawValue = line.slice(colonIndex + 1).split('(')[0].trim();
    const hasPercent = rawValue.includes('%');
    const numeric = parseFloat(rawValue.replace(/[^0-9.\-]/g, ''));
    if (Number.isNaN(numeric)) return null;

    return {
      label,
      value: numeric,
      suffix: hasPercent ? '%' : ''
    };
  }

  function formatStatValue(value: number, suffix: '' | '%') {
    const fractionDigits = Math.abs(value) % 1 ? 1 : 0;
    const formatted = formatNumber(value, fractionDigits);
    return suffix === '%' ? `${formatted}${suffix}` : formatted;
  }

  function aggregateSetStats(items: WardrobeItem[]): AggregatedStat[] {
    const totals = new Map<string, { value: number; suffix: '' | '%' }>();
    for (const item of items) {
      for (const line of item.lore) {
        const parsed = parseStatLine(line);
        if (!parsed) continue;
        const existing = totals.get(parsed.label);
        if (existing) {
          existing.value += parsed.value;
        } else {
          totals.set(parsed.label, { value: parsed.value, suffix: parsed.suffix });
        }
      }
    }

    return Array.from(totals.entries())
      .map(([label, info]) => ({
        label,
        value: info.value,
        suffix: info.suffix,
        display: formatStatValue(info.value, info.suffix)
      }))
      .sort((a, b) => a.label.localeCompare(b.label));
  }

  function deriveSetLabel(items: WardrobeItem[]) {
    if (!items.length) return '';
    const baseNames = Array.from(new Set(items.map((item) => baseSetNameFromId(item.id))));
    if (baseNames.length === 1) {
      return `${baseNames[0]} Set`;
    }
    if (baseNames.length === 2) {
      return `${baseNames[0]} with ${baseNames[1]}`;
    }
    return `${baseNames[0]} with ${baseNames.slice(1).join(', ')}`;
  }

  function gatherSetBonusLines(items: WardrobeItem[]): string[] {
    const bonuses = new Set<string>();
    for (const item of items) {
      let capturing = false;
      const buffer: string[] = [];
      for (const line of item.lore) {
        if (line.startsWith('Full Set Bonus')) {
          capturing = true;
        }
        if (capturing) {
          if (!bonuses.has(line)) buffer.push(line);
          if (!line.trim()) {
            capturing = false;
            break;
          }
        }
      }
      for (const line of buffer) {
        bonuses.add(line);
      }
    }
    return Array.from(bonuses).filter((line) => line.trim().length);
  }

  function toEquippedItems(columnIndex: number | null, items: (WardrobeItem | null)[]): WardrobeItem[] {
    if (columnIndex === null || columnIndex < 0) return [];
    return items.filter(
      (item): item is WardrobeItem => !!item && item.slot % WARDROBE_NUM_COLUMNS === columnIndex
    );
  }

  function pieceLabel(item: WardrobeItem) {
    const parts = item.id.split('_');
    if (!parts.length) return item.name;
    const slotName = parts[parts.length - 1].toLowerCase();
    return toTitleCase(slotName);
  }

  function rarityClass(rarity?: string | null) {
    if (!rarity) return 'rarity-basic';
    return `rarity-${rarity.toLowerCase().replace(/\s+/g, '-')}`;
  }

  let wardrobeItems: (WardrobeItem | null)[] = [];
  let wardrobeHasItems = false;
  let firstBankColumns: (WardrobeItem | null)[][] = [];
  let secondBankColumns: (WardrobeItem | null)[][] = [];
  let equippedItems: WardrobeItem[] = [];
  let equippedSetLabel = '';
  let equippedStats: AggregatedStat[] = [];
  let equippedBonuses: string[] = [];
  let equippedColumnIndex: number | null = null;

  $: wardrobeItems = summary?.wardrobe?.items ?? [];
  $: wardrobeHasItems = wardrobeItems.some((item) => !!item);
  $: if (wardrobeItems.length) {
    const firstBankRaw = wardrobeItems.filter((item) => item && item.slot < 36);
    const secondBankRaw = wardrobeItems.filter((item) => item && item.slot >= 36);
    firstBankColumns = buildWardrobeColumns(firstBankRaw);
    secondBankColumns = buildWardrobeColumns(secondBankRaw);
  } else {
    firstBankColumns = [];
    secondBankColumns = [];
  }
  $: equippedColumnIndex = summary?.wardrobe?.equipped_slot ?? null;
  $: equippedItems = toEquippedItems(equippedColumnIndex, wardrobeItems);
  $: equippedSetLabel = deriveSetLabel(equippedItems);
  $: equippedStats = aggregateSetStats(equippedItems);
  $: equippedBonuses = gatherSetBonusLines(equippedItems);
</script>

<section id="wardrobe" class="wardrobe-section">
  {#if !summary?.wardrobe}
    <div class="card loading-card">
      <p>Loading wardrobe data...</p>
    </div>
  {:else if !wardrobeHasItems}
    <div class="card empty-card">
      <p>No items found in wardrobe.</p>
    </div>
  {:else}
    {#if equippedItems.length}
      <div class="equipped-summary">
        <div class="equipped-heading">
          <h3>Currently Equipped</h3>
          {#if equippedColumnIndex !== null}
            <span class="equipped-slot-pill">Wardrobe Slot {equippedColumnIndex + 1}</span>
          {/if}
        </div>
        <div class="equipped-body">
          <div class="equipped-icons">
            {#each equippedItems as item (item.slot)}
              <div
                class={`equipped-icon ${item.icon_url ? '' : 'placeholder'} ${item.leather_color ? 'leather' : ''}`}
                style={item.leather_color ? `--leather-color:${item.leather_color}` : undefined}
              >
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

    <div class="wardrobe-grid">
      {#each firstBankColumns as column}
        <div class="wardrobe-column">
          {#each column as item}
            {#if item}
              <div
                class={`card wardrobe-card ${rarityClass(item.rarity)} ${
                  summary.wardrobe.equipped_slot === item.slot ? 'equipped' : ''
                }`}
              >
                <div class="wardrobe-head">
                  <div
                    class={`wardrobe-icon ${item.icon_url ? '' : 'placeholder'} ${
                      item.leather_color ? 'leather' : ''
                    }`}
                    style={item.leather_color ? `--leather-color:${item.leather_color}` : undefined}
                  >
                    {#if item.icon_url}
                      <img
                        src={item.icon_url}
                        alt={`${item.name} icon`}
                        loading="lazy"
                        width="64"
                        height="64"
                        on:error={(event) => {
                          const target = event.currentTarget as HTMLImageElement;
                          target.dataset.failed = '1';
                          target.parentElement?.classList.add('placeholder');
                        }}
                      />
                    {/if}
                    <span class="placeholder-letter">{item.name.slice(0, 1).toUpperCase()}</span>
                  </div>
                  <div class="wardrobe-info">
                    <div class="wardrobe-top">
                      <span class="slot">Slot {item.slot + 1}</span>
                      <span class="rarity">{item.rarity ?? 'Unknown'}</span>
                    </div>
                    <div class="item-name">{item.name}</div>
                    <div class="item-meta">Item ID: {item.id}</div>
                    {#if item.count > 1}
                      <div class="item-meta">Count: {item.count}</div>
                    {/if}
                  </div>
                </div>
                {#if item.lore.length}
                  <div class="lore">
                    {#each item.lore.slice(0, 8) as line}
                      <p>{line}</p>
                    {/each}
                  </div>
                {/if}
              </div>
            {/if}
          {/each}
        </div>
      {/each}
    </div>

    {#if secondBankColumns.length > 0}
      <h3 class="wardrobe-bank-title">Additional Wardrobe Slots</h3>
      <div class="wardrobe-grid">
        {#each secondBankColumns as column}
          <div class="wardrobe-column">
            {#each column as item}
              {#if item}
                <div
                  class={`card wardrobe-card ${rarityClass(item.rarity)} ${
                    summary.wardrobe.equipped_slot === item.slot ? 'equipped' : ''
                  }`}
                >
                  <div class="wardrobe-head">
                    <div
                      class={`wardrobe-icon ${item.icon_url ? '' : 'placeholder'} ${
                        item.leather_color ? 'leather' : ''
                      }`}
                      style={item.leather_color ? `--leather-color:${item.leather_color}` : undefined}
                    >
                      {#if item.icon_url}
                        <img
                          src={item.icon_url}
                          alt={`${item.name} icon`}
                          loading="lazy"
                          width="64"
                          height="64"
                          on:error={(event) => {
                            const target = event.currentTarget as HTMLImageElement;
                            target.dataset.failed = '1';
                            target.parentElement?.classList.add('placeholder');
                          }}
                        />
                      {/if}
                      <span class="placeholder-letter">{item.name.slice(0, 1).toUpperCase()}</span>
                    </div>
                    <div class="wardrobe-info">
                      <div class="wardrobe-top">
                        <span class="slot">Slot {item.slot + 1}</span>
                        <span class="rarity">{item.rarity ?? 'Unknown'}</span>
                      </div>
                      <div class="item-name">{item.name}</div>
                      <div class="item-meta">Item ID: {item.id}</div>
                      {#if item.count > 1}
                        <div class="item-meta">Count: {item.count}</div>
                      {/if}
                    </div>
                  </div>
                  {#if item.lore.length}
                    <div class="lore">
                      {#each item.lore.slice(0, 8) as line}
                        <p>{line}</p>
                      {/each}
                    </div>
                  {/if}
                </div>
              {/if}
            {/each}
          </div>
        {/each}
      </div>
    {/if}
  {/if}
</section>

<style>
  .wardrobe-section {
    display: flex;
    flex-direction: column;
    gap: 32px;
  }

  .loading-card,
  .empty-card {
    padding: 32px;
    text-align: center;
    color: var(--theme-text-soft);
  }

  .loading-card p,
  .empty-card p {
    margin: 0;
    font-size: 1.1rem;
  }

  .equipped-summary {
    display: flex;
    flex-direction: column;
    gap: 18px;
  }

  .equipped-heading {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .equipped-slot-pill {
    background: rgba(99, 102, 241, 0.12);
    color: var(--theme-accent);
    padding: 6px 12px;
    border-radius: 999px;
    font-weight: 600;
    font-size: 0.85rem;
  }

  .equipped-body {
    display: flex;
    flex-wrap: wrap;
    gap: 18px;
  }

  .equipped-icons {
    display: flex;
    gap: 12px;
  }

  .equipped-icon {
    width: 72px;
    height: 88px;
    border-radius: 16px;
    background: rgba(15, 23, 42, 0.25);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 6px;
    border: 1px solid rgba(148, 163, 184, 0.18);
    position: relative;
    overflow: hidden;
  }

  .equipped-icon.placeholder {
    background: linear-gradient(135deg, rgba(148, 163, 184, 0.18), rgba(226, 232, 240, 0.12));
  }

  .equipped-icon.leather {
    background: var(--leather-color, rgba(15, 23, 42, 0.25));
  }

  .equipped-icon img {
    width: 60px;
    height: 60px;
    object-fit: contain;
  }

  .equipped-piece {
    font-size: 0.8rem;
    font-weight: 600;
  }

  .equipped-details {
    display: flex;
    flex-direction: column;
    gap: 12px;
    min-width: 220px;
  }

  .equipped-set-name {
    font-size: 1.2rem;
    font-weight: 600;
    color: var(--theme-text-primary);
  }

  .equipped-stats {
    list-style: none;
    margin: 0;
    padding: 0;
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .equipped-stats li {
    display: flex;
    justify-content: space-between;
    color: var(--theme-text-primary);
  }

  .equipped-bonuses {
    border-top: 1px solid var(--theme-border);
    padding-top: 16px;
    color: var(--theme-text-soft);
  }

  .equipped-bonuses p {
    margin: 0 0 8px;
  }

  .equipped-bonuses p:last-child {
    margin-bottom: 0;
  }

  .wardrobe-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 18px;
  }

  .wardrobe-column {
    display: flex;
    flex-direction: column;
    gap: 18px;
  }

  .wardrobe-card {
    gap: 16px;
    border-width: 2px;
    border-style: solid;
  }

  .wardrobe-card.equipped {
    box-shadow: 0 0 0 2px var(--theme-accent);
  }

  .wardrobe-head {
    display: flex;
    gap: 14px;
  }

  .wardrobe-icon {
    width: 80px;
    height: 80px;
    border-radius: 16px;
    background: rgba(15, 23, 42, 0.22);
    position: relative;
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
  }

  .wardrobe-icon.placeholder {
    background: linear-gradient(135deg, rgba(148, 163, 184, 0.18), rgba(226, 232, 240, 0.12));
  }

  .wardrobe-icon.leather {
    background: var(--leather-color, rgba(15, 23, 42, 0.22));
  }

  .wardrobe-icon img {
    width: 64px;
    height: 64px;
    object-fit: contain;
  }

  .placeholder-letter {
    position: absolute;
    inset: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 2rem;
    font-weight: 700;
    opacity: 0.5;
    color: var(--theme-text-primary);
  }

  .wardrobe-info {
    display: flex;
    flex-direction: column;
    gap: 6px;
    flex: 1;
  }

  .wardrobe-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 8px;
  }

  .slot {
    font-weight: 600;
    color: var(--theme-text-primary);
  }

  .rarity {
    font-size: 0.85rem;
    color: var(--theme-text-soft);
  }

  .item-name {
    font-weight: 600;
    color: var(--theme-text-primary);
  }

  .item-meta {
    font-size: 0.85rem;
    color: var(--theme-text-soft);
  }

  .lore {
    background: rgba(15, 23, 42, 0.16);
    border-radius: 12px;
    padding: 12px 14px;
    font-size: 0.85rem;
    color: var(--theme-text-soft);
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .lore p {
    margin: 0;
  }

  .wardrobe-bank-title {
    margin: 0;
    font-size: 1.4rem;
    font-weight: 600;
    color: var(--theme-text-primary);
  }

  .wardrobe-empty {
    text-align: center;
    color: var(--theme-text-soft);
  }

  .rarity-basic {
    border-color: rgba(148, 163, 184, 0.4);
  }

  .rarity-common {
    border-color: rgba(113, 113, 122, 0.6);
  }

  .rarity-uncommon {
    border-color: rgba(34, 197, 94, 0.6);
  }

  .rarity-rare {
    border-color: rgba(59, 130, 246, 0.6);
  }

  .rarity-epic {
    border-color: rgba(168, 85, 247, 0.6);
  }

  .rarity-legendary {
    border-color: rgba(250, 204, 21, 0.7);
  }

  .rarity-mythic {
    border-color: rgba(236, 72, 153, 0.7);
  }

  .rarity-divine {
    border-color: rgba(129, 140, 248, 0.75);
  }

  .rarity-special,
  .rarity-very-special {
    border-color: rgba(239, 68, 68, 0.75);
  }

  :global(body[data-icon-pack='flufsky']) .wardrobe-icon img {
    filter: saturate(1.12) contrast(1.05) brightness(1.08);
  }

  :global(body[data-icon-pack='flufsky']) .wardrobe-icon.placeholder {
    background: linear-gradient(
      135deg,
      rgba(236, 72, 153, 0.32),
      rgba(56, 189, 248, 0.28)
    );
  }

  @media (max-width: 768px) {
    .equipped-body {
      flex-direction: column;
    }

    .equipped-icons {
      flex-wrap: wrap;
    }
  }
</style>
