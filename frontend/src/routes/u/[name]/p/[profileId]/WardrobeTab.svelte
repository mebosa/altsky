<script lang="ts">
  import { formatNumber } from '$lib/utils';
  import type {
    AggregatedStat,
    ProfileSummaryResponse,
    WardrobeItem
  } from './profileTypes';

  export let summary: ProfileSummaryResponse;

  const WARDROBE_SET_SIZE = 4;
  const WARDROBE_SETS_PER_BANK = 9;
  const WARDROBE_BANK_SLOT_COUNT = WARDROBE_SET_SIZE * WARDROBE_SETS_PER_BANK;
  const PIECE_LABELS = ['Helmet', 'Chestplate', 'Leggings', 'Boots'] as const;
  const WARDROBE_SET_STARTS_ONE_BASED = [
    1, 2, 3, 4, 5, 6, 7, 8, 9,
    37, 38, 39, 40, 41, 42, 43, 44, 45
  ];
  const WARDROBE_SET_STARTS_ZERO_BASED = WARDROBE_SET_STARTS_ONE_BASED.map((start) => start - 1);

  type WardrobeSetGroup = {
    setIndex: number;
    bankIndex: number;
    columnIndex: number;
    items: (WardrobeItem | null)[];
  };

  type WardrobeGrouping = {
    setIndex: number;
    bankIndex: number;
    columnIndex: number;
    pieceIndex: number;
  };

  function findGroupFromStarts(slot: number, starts: number[]): WardrobeGrouping | null {
    for (let i = starts.length - 1; i >= 0; i--) {
      const start = starts[i];
      if (slot < start) continue;
      const offset = slot - start;
      const pieceIndex = Math.floor(offset / WARDROBE_SETS_PER_BANK);
      if (pieceIndex >= 0 && pieceIndex < WARDROBE_SET_SIZE) {
        const setIndex = i;
        const bankIndex = Math.floor(setIndex / WARDROBE_SETS_PER_BANK);
        const columnIndex = setIndex % WARDROBE_SETS_PER_BANK;
        return { setIndex, bankIndex, columnIndex, pieceIndex };
      }
    }
    return null;
  }

  function fallbackGrouping(slot: number): WardrobeGrouping {
    const normalized = Math.max(0, slot);
    const bankIndex = Math.floor(normalized / WARDROBE_BANK_SLOT_COUNT);
    const withinBank = normalized % WARDROBE_BANK_SLOT_COUNT;
    const columnIndex = withinBank % WARDROBE_SETS_PER_BANK;
    const pieceIndex = Math.min(
      WARDROBE_SET_SIZE - 1,
      Math.max(0, Math.floor(withinBank / WARDROBE_SETS_PER_BANK))
    );
    const setIndex = bankIndex * WARDROBE_SETS_PER_BANK + columnIndex;
    return { setIndex, bankIndex, columnIndex, pieceIndex };
  }

  function deriveGrouping(slot: number): WardrobeGrouping {
    return (
      findGroupFromStarts(slot, WARDROBE_SET_STARTS_ONE_BASED) ??
      findGroupFromStarts(slot, WARDROBE_SET_STARTS_ZERO_BASED) ??
      fallbackGrouping(slot)
    );
  }

  function buildWardrobeSets(items: (WardrobeItem | null)[]): WardrobeSetGroup[] {
    const grouped = new Map<string, WardrobeSetGroup>();

    for (const item of items) {
      if (!item) continue;
      const grouping = deriveGrouping(item.slot);
      const key = `${grouping.bankIndex}-${grouping.columnIndex}`;
      if (!grouped.has(key)) {
        grouped.set(key, {
          setIndex: grouping.setIndex,
          bankIndex: grouping.bankIndex,
          columnIndex: grouping.columnIndex,
          items: Array.from({ length: WARDROBE_SET_SIZE }, () => null)
        });
      }
      const group = grouped.get(key)!;
      const pieceIndex = Math.min(
        WARDROBE_SET_SIZE - 1,
        Math.max(0, grouping.pieceIndex)
      );
      group.items[pieceIndex] = item;
    }

    return Array.from(grouped.values()).sort((a, b) => a.setIndex - b.setIndex);
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

  function pieceLabelFromIndex(index: number) {
    return PIECE_LABELS[index] ?? 'Slot';
  }

  function rarityClass(rarity?: string | null) {
    if (!rarity) return 'rarity-basic';
    return `rarity-${rarity.toLowerCase().replace(/\s+/g, '-')}`;
  }

  function formatLeatherColor(color?: string | null) {
    if (!color) return null;
    let value = color.trim();
    if (!value) return null;
    if (/^#?[0-9a-fA-F]{6}$/.test(value)) {
      return value.startsWith('#') ? value : `#${value}`;
    }
    const parts = value.split(/[:;,]/).map((part) => part.trim()).filter(Boolean);
    if (parts.length === 3 && parts.every((part) => !Number.isNaN(Number(part)))) {
      const normalized = parts.map((part) => {
        const num = Number(part);
        if (!Number.isFinite(num)) return 0;
        return Math.max(0, Math.min(255, Math.round(num)));
      });
      return `rgb(${normalized.join(',')})`;
    }
    return null;
  }

  let wardrobeItems: (WardrobeItem | null)[] = [];
  let wardrobeHasItems = false;
  let setGroups: WardrobeSetGroup[] = [];
  let setGroupMap = new Map<number, WardrobeSetGroup>();
  let equippedGroupItems: (WardrobeItem | null)[] = [];
  let equippedItems: WardrobeItem[] = [];
  let equippedSetLabel = '';
  let equippedStats: AggregatedStat[] = [];
  let equippedBonuses: string[] = [];
  let equippedSetIndexRaw: number | null = null;
  let equippedSetIndex: number | null = null;

  $: wardrobeItems = summary?.wardrobe?.items ?? [];
  $: wardrobeHasItems = wardrobeItems.some((item) => !!item);
  $: if (wardrobeItems.length) {
    setGroups = buildWardrobeSets(wardrobeItems);
    setGroupMap = new Map(setGroups.map((group) => [group.setIndex, group]));
  } else {
    setGroups = [];
    setGroupMap = new Map();
  }
  function resolveEquippedSetIndex(raw: number | null): number | null {
    if (raw === null) return null;
    if (setGroupMap.has(raw)) return raw;
    const derived =
      findGroupFromStarts(raw, WARDROBE_SET_STARTS_ONE_BASED) ??
      findGroupFromStarts(raw, WARDROBE_SET_STARTS_ZERO_BASED) ??
      fallbackGrouping(raw);
    return derived.setIndex;
  }

  $: equippedSetIndexRaw = summary?.wardrobe?.equipped_slot ?? null;
  $: equippedSetIndex = resolveEquippedSetIndex(equippedSetIndexRaw);
  $: {
    const group = equippedSetIndex !== null ? setGroupMap.get(equippedSetIndex) : undefined;
    equippedGroupItems = group ? group.items : Array.from({ length: WARDROBE_SET_SIZE }, () => null);
    equippedItems = equippedGroupItems.filter((item): item is WardrobeItem => !!item);
  }
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
          {#if equippedSetIndex !== null}
            <span class="equipped-slot-pill">Wardrobe Slot {equippedSetIndex + 1}</span>
          {/if}
        </div>
        <div class="equipped-body">
          <div class="equipped-icons">
            {#each equippedGroupItems as item, index (index)}
              {@const leatherColor = item ? formatLeatherColor(item.leather_color) : null}
              <div
                class={`equipped-icon ${item?.icon_url ? '' : 'placeholder'} ${item?.leather_color ? 'leather' : ''}`}
                style={leatherColor ? `--leather-color:${leatherColor}` : undefined}
              >
                {#if item?.icon_url}
                  <img src={item.icon_url} alt={`${item.name} icon`} loading="lazy" width="60" height="60" />
                {/if}
                <span class="equipped-piece">{pieceLabelFromIndex(index)}</span>
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
      {#each setGroups as column (column.setIndex)}
        <div
          class={`wardrobe-set ${equippedSetIndex === column.setIndex ? 'equipped' : ''} bank-${column.bankIndex}`}
          data-bank={column.bankIndex}
        >
          {#each column.items as item, index (index)}
            {@const leatherColor = item ? formatLeatherColor(item.leather_color) : null}
            <div class="slot-shell" data-piece={pieceLabelFromIndex(index)}>
              <div
                class={`slot-icon ${item?.icon_url ? '' : 'placeholder'} ${item?.leather_color ? 'leather' : ''}`}
                style={leatherColor ? `--leather-color:${leatherColor}` : undefined}
              >
                {#if item?.icon_url}
                  <img
                    src={item.icon_url}
                    alt={`${item.name} icon`}
                    loading="lazy"
                    width="42"
                    height="42"
                    on:error={(event) => {
                      const target = event.currentTarget as HTMLImageElement;
                      target.dataset.failed = '1';
                      target.parentElement?.classList.add('placeholder');
                    }}
                  />
                {:else if item}
                  <span class="slot-initial">{item.name.slice(0, 1).toUpperCase()}</span>
                {:else}
                  <span class="slot-initial empty">•</span>
                {/if}
              </div>
              <div class="slot-tooltip">
                <div class="tooltip-header">
                  <span class="tooltip-piece">{pieceLabelFromIndex(index)}</span>
                  <span class="tooltip-slot">Slot {column.setIndex + 1}</span>
                </div>
                {#if item}
                  <div class="tooltip-name">{item.name}</div>
                  {#if item.rarity}
                    <div class="tooltip-rarity">{item.rarity}</div>
                  {/if}
                  {#if item.lore.length}
                    <div class="tooltip-lore">
                      {#each item.lore as line}
                        <p>{line}</p>
                      {/each}
                    </div>
                  {/if}
                {:else}
                  <div class="tooltip-empty">Empty slot</div>
                {/if}
              </div>
            </div>
          {/each}
        </div>
      {/each}
    </div>
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
    --wardrobe-columns: 9;
    display: grid;
    grid-template-columns: repeat(var(--wardrobe-columns), minmax(44px, 1fr));
    gap: 8px;
    justify-content: center;
    padding: 0 4px;
  }

  @media (min-width: 1024px) {
    .wardrobe-grid {
      --wardrobe-columns: 18;
      gap: 10px;
    }
  }

  .wardrobe-set {
    display: grid;
    grid-template-rows: repeat(4, auto);
    gap: 6px;
    align-items: end;
    justify-items: center;
    position: relative;
  }

  @media (min-width: 1024px) {
    .wardrobe-set:nth-child(9) {
      margin-right: 18px;
    }
  }

  .wardrobe-set.equipped .slot-icon {
    box-shadow: 0 0 0 2px var(--theme-accent);
  }

  .slot-shell {
    position: relative;
    display: flex;
    justify-content: center;
  }

  .slot-icon {
    width: 48px;
    height: 48px;
    border-radius: 8px;
    background: rgba(15, 23, 42, 0.28);
    border: 1px solid rgba(148, 163, 184, 0.32);
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
    transition: transform 0.15s ease;
  }

  .slot-shell:hover .slot-icon {
    transform: translateY(-2px);
  }

  .slot-icon.placeholder {
    background: linear-gradient(135deg, rgba(148, 163, 184, 0.2), rgba(226, 232, 240, 0.12));
  }

  .slot-icon.leather {
    background: var(--leather-color, rgba(15, 23, 42, 0.28));
  }

  .slot-icon img {
    width: 40px;
    height: 40px;
    object-fit: contain;
  }

  .slot-initial {
    font-size: 1rem;
    font-weight: 600;
    color: var(--theme-text-primary);
    opacity: 0.85;
  }

  .slot-initial.empty {
    opacity: 0.2;
  }

  .slot-tooltip {
    position: absolute;
    bottom: calc(100% + 8px);
    left: 50%;
    transform: translate(-50%, 4px);
    background: rgba(15, 23, 42, 0.92);
    border: 1px solid rgba(148, 163, 184, 0.35);
    border-radius: 10px;
    padding: 10px 12px;
    min-width: 180px;
    max-width: 220px;
    box-shadow: 0 16px 32px rgba(15, 23, 42, 0.42);
    opacity: 0;
    pointer-events: none;
    transition: opacity 0.18s ease, transform 0.18s ease;
    color: #e2e8f0;
    z-index: 10;
  }

  .slot-shell:hover .slot-tooltip,
  .slot-shell:focus-within .slot-tooltip {
    opacity: 1;
    transform: translate(-50%, 0);
    pointer-events: auto;
  }

  .tooltip-header {
    display: flex;
    justify-content: space-between;
    gap: 8px;
    font-size: 0.7rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    opacity: 0.7;
  }

  .tooltip-name {
    font-weight: 600;
    margin: 6px 0 4px;
  }

  .tooltip-rarity {
    font-size: 0.8rem;
    color: var(--theme-accent);
    margin-bottom: 4px;
  }

  .tooltip-lore {
    display: flex;
    flex-direction: column;
    gap: 2px;
    font-size: 0.75rem;
    color: #cbd5f5;
    max-height: 160px;
    overflow-y: auto;
  }

  .tooltip-lore p {
    margin: 0;
  }

  .tooltip-empty {
    font-size: 0.8rem;
    opacity: 0.75;
  }

  .tooltip-slot {
    font-weight: 600;
  }

  .tooltip-piece {
    font-weight: 600;
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
