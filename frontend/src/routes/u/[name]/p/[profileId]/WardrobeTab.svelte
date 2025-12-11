<script lang="ts">
  import { formatNumber } from '$lib/utils';
  import {
    ensureTintedIcon,
    peekTintedIcon,
    rarityToBackground,
    isFallbackIcon,
    parseLegacyText,
    type LegacySegment
  } from '$lib/utils/wardrobe';
  import { texturePackStore } from '$lib/stores/texturePack';
  import type { TexturePack } from '$lib/stores/texturePack';
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
  const RARITY_ORDER = [
    'basic',
    'common',
    'uncommon',
    'rare',
    'epic',
    'legendary',
    'mythic',
    'divine',
    'supreme',
    'special',
    'very_special',
    'ultimate',
    'admin'
  ] as const;
  const RARITY_RANK = RARITY_ORDER.reduce<Record<string, number>>((acc, rarity, index) => {
    acc[rarity] = index;
    return acc;
  }, {});
  const DEFAULT_ACCENT = 'rgba(120, 137, 255, 0.28)';
  const ICON_RETRY_LIMIT = 3;
  const ICON_RETRY_BASE_DELAY = 400;
  const ICON_RETRY_BACKOFF = 1.5;
  const TEXTURE_PACK_ORDER: TexturePack[] = ['furfsky', 'vanilla'];
  const pendingTintKeys = new Set<string>();
  let tintedIconVersion = 0;

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

  function groupingFromSlot(slot: number, offset: number): WardrobeGrouping {
    const normalized = Math.max(0, slot - offset);
    const columnIndex =
      ((normalized % WARDROBE_SETS_PER_BANK) + WARDROBE_SETS_PER_BANK) % WARDROBE_SETS_PER_BANK;
    const pieceIndex = Math.floor(normalized / WARDROBE_SETS_PER_BANK) % WARDROBE_SET_SIZE;
    const bankIndex = Math.floor(normalized / WARDROBE_BANK_SLOT_COUNT);
    const setIndex = bankIndex * WARDROBE_SETS_PER_BANK + columnIndex;
    return { setIndex, bankIndex, columnIndex, pieceIndex };
  }

  function buildWardrobeSets(items: (WardrobeItem | null)[], offset: number): WardrobeSetGroup[] {
    const grouped = new Map<string, WardrobeSetGroup>();

    for (const item of items) {
      if (!item) continue;
      const grouping = groupingFromSlot(item.slot ?? 0, offset);
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
      const clampedIndex = Math.min(WARDROBE_SET_SIZE - 1, Math.max(0, grouping.pieceIndex));
      group.items[clampedIndex] = item;
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

  function normalizeRarity(value?: string | null) {
    if (!value) return null;
    return value.trim().toLowerCase().replace(/\s+/g, '_');
  }

  function rarityRank(value?: string | null) {
    if (!value) return -1;
    return RARITY_RANK[value] ?? -1;
  }

  function selectPrimaryRarity(items: (WardrobeItem | null)[]) {
    let best: { raw: string; normalized: string } | null = null;
    for (const item of items) {
      const raw = item?.rarity;
      if (!raw) continue;
      const normalized = normalizeRarity(raw);
      if (!normalized) continue;
      if (!best || rarityRank(normalized) > rarityRank(best.normalized)) {
        best = { raw, normalized };
      }
    }
    return best;
  }

  function formatRarityLabel(value?: string | null) {
    const normalized = normalizeRarity(value);
    if (!normalized) return '';
    return normalized
      .split('_')
      .map((segment) => (segment ? segment[0].toUpperCase() + segment.slice(1) : segment))
      .join(' ');
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
    if (!rarity) return '';
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

  function buildCacheBustedUrl(url: string, attempt: number) {
    const separator = url.includes('?') ? '&' : '?';
    return `${url}${separator}retry=${attempt}-${Date.now()}`;
  }

  function markPlaceholder(target: HTMLImageElement, shouldShow: boolean) {
    target.parentElement?.classList.toggle('placeholder', shouldShow);
  }

  function handleIconLoad(event: Event) {
    const target = event.currentTarget as HTMLImageElement | null;
    if (!target) return;
    delete target.dataset.retryCount;
    delete target.dataset.failed;
    markPlaceholder(target, false);
  }

  function handleIconError(event: Event, iconUrl?: string | null) {
    const target = event.currentTarget as HTMLImageElement | null;
    if (!target) return;
    if (!iconUrl) {
      target.dataset.failed = '1';
      markPlaceholder(target, true);
      return;
    }
    const attempt = Number(target.dataset.retryCount ?? '0');
    if (attempt >= ICON_RETRY_LIMIT) {
      target.dataset.failed = '1';
      markPlaceholder(target, true);
      return;
    }
    const nextAttempt = attempt + 1;
    target.dataset.retryCount = String(nextAttempt);
    target.dataset.failed = '';
    markPlaceholder(target, false);
    const delay = Math.round(ICON_RETRY_BASE_DELAY * Math.pow(ICON_RETRY_BACKOFF, attempt));
    setTimeout(() => {
      if (!target.isConnected) return;
      target.src = buildCacheBustedUrl(iconUrl, nextAttempt);
    }, delay);
  }

  type IconSource = TexturePack | 'legacy';

  function pickIconVariant(
    item: WardrobeItem | null,
    pack?: TexturePack
  ): { url: string; source: IconSource } | null {
    if (!item) return null;
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

  function resolveDisplayIcon(
    item: WardrobeItem | null,
    _version: number,
    pack?: TexturePack
  ): string | null {
    if (!item) return null;
    const picked = pickIconVariant(item, pack);
    if (!picked) {
      return null;
    }

    const { url: baseIcon, source } = picked;
    if (source !== 'vanilla') {
      return baseIcon;
    }

    const leatherColor = formatLeatherColor(item.leather_color);
    if (!leatherColor || isFallbackIcon(baseIcon)) {
      return baseIcon;
    }

    const key = `${baseIcon}|${leatherColor}`;
    const cached = peekTintedIcon(baseIcon, leatherColor);
    if (cached) {
      return cached;
    }

    if (!pendingTintKeys.has(key)) {
      pendingTintKeys.add(key);
      ensureTintedIcon(baseIcon, leatherColor)
        .catch(() => baseIcon)
        .then(() => {
          pendingTintKeys.delete(key);
          tintedIconVersion += 1;
        });
    }

    return baseIcon;
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
  let slotOffset = 0;

  function formatWardrobeSlot(setIndex: number | null) {
    if (setIndex === null) return '';
    const bankIndex = Math.floor(setIndex / WARDROBE_SETS_PER_BANK);
    const columnIndex = setIndex % WARDROBE_SETS_PER_BANK;
    return bankIndex * WARDROBE_SETS_PER_BANK + columnIndex + 1;
  }

  $: wardrobeItems = summary?.wardrobe?.items ?? [];
  $: wardrobeHasItems = wardrobeItems.some((item) => !!item);
  $: slotOffset = (() => {
    const slots = wardrobeItems
      .map((item) => (item ? item.slot : null))
      .filter((slot): slot is number => typeof slot === 'number' && Number.isFinite(slot));
    if (!slots.length) return 0;
    const minSlot = Math.min(...slots);
    return minSlot >= 1 ? 1 : 0;
  })();
  $: if (wardrobeItems.length) {
    setGroups = buildWardrobeSets(wardrobeItems, slotOffset);
    setGroupMap = new Map(setGroups.map((group) => [group.setIndex, group]));
  } else {
    setGroups = [];
    setGroupMap = new Map();
  }

  function resolveEquippedSetIndex(raw: number | null): number | null {
    if (raw === null) return null;
    // Try direct match (API may already provide set index)
    if (setGroupMap.has(raw)) return raw;

    // Convert raw wardrobe slot (absolute slot) into set index (column within bank)
    const grouping = groupingFromSlot(raw, slotOffset);
    if (setGroupMap.has(grouping.setIndex)) return grouping.setIndex;

    // Fallback: try normalized by slotOffset
    const candidate = raw - slotOffset;
    if (setGroupMap.has(candidate)) return candidate;

    // If no match, it likely means the equipped armor isn't in the wardrobe.
    return null;
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
  $: equippedRarityInfo = selectPrimaryRarity(equippedGroupItems);
  $: equippedAccent = equippedRarityInfo
    ? rarityToBackground(equippedRarityInfo.raw) ?? null
    : null;
  $: equippedRarityLabel = formatRarityLabel(equippedRarityInfo?.raw);
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
    {#if equippedSetIndex !== null && equippedItems.length}
      <div
        class="equipped-summary"
        style={`--rarity-accent:${equippedAccent ?? DEFAULT_ACCENT}`}
      >
        <div class="equipped-heading">
          <div class="heading-copy">
            <span class="equipped-label">Currently Equipped</span>
            <h3>{equippedSetLabel || 'Custom Mix'}</h3>
          </div>
          <div class="equipped-meta">
            {#if equippedRarityLabel}
              <span class="rarity-chip">{equippedRarityLabel} Set</span>
            {/if}
            {#if equippedSetIndex !== null}
              <span class="equipped-slot-pill">Wardrobe Slot {formatWardrobeSlot(equippedSetIndex)}</span>
            {/if}
          </div>
        </div>
        <div class="equipped-body">
          <div class="equipped-icons">
            {#each equippedGroupItems as item, index (index)}
              {@const leatherColor = item ? formatLeatherColor(item.leather_color) : null}
              {@const iconSrc = resolveDisplayIcon(item ?? null, tintedIconVersion, $texturePackStore)}
              <div
                class={`equipped-icon ${iconSrc ? '' : 'placeholder'} ${item?.leather_color ? 'leather' : ''}`}
                style={leatherColor ? `--leather-color:${leatherColor}` : undefined}
              >
                {#if iconSrc}
                  <img
                    src={iconSrc}
                    alt={`${item.name} icon`}
                    loading="lazy"
                    width="60"
                    height="60"
                    on:load={handleIconLoad}
                    on:error={(event) => handleIconError(event, iconSrc)}
                  />
                {/if}
                <span class="equipped-piece">{pieceLabelFromIndex(index)}</span>
              </div>
            {/each}
          </div>
          <div class="equipped-details">
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
                <p class="section-label">Full Set Bonus</p>
                {#each equippedBonuses as line}
                  <p>{line}</p>
                {/each}
              </div>
            {/if}
          </div>
        </div>
      </div>
    {:else}
      <div class="card empty-card">
        <p>Equipped armor is not present in the wardrobe slots.</p>
      </div>
    {/if}

    <div class="wardrobe-grid">
      {#each setGroups as column (column.setIndex)}
        {@const groupRarityInfo = selectPrimaryRarity(column.items)}
        {@const groupAccent = groupRarityInfo ? rarityToBackground(groupRarityInfo.raw) : null}
        {@const groupRarityLabel = formatRarityLabel(groupRarityInfo?.raw)}
        <div
          class={`wardrobe-set ${equippedSetIndex === column.setIndex ? 'equipped' : ''} bank-${column.bankIndex}`}
          data-bank={column.bankIndex}
          style={`--rarity-accent:${groupAccent ?? 'rgba(148, 163, 184, 0.18)'}`}
        >
          <div class="set-header">
            <span class="set-label">Set {formatWardrobeSlot(column.setIndex)}</span>
            {#if groupRarityLabel}
              <span class="rarity-chip subtle">{groupRarityLabel}</span>
            {/if}
          </div>
          <div class="set-slots">
            {#each column.items as item, index (index)}
              {@const leatherColor = item ? formatLeatherColor(item.leather_color) : null}
              {@const slotIcon = resolveDisplayIcon(item ?? null, tintedIconVersion, $texturePackStore)}
              <button class="slot-shell" data-piece={pieceLabelFromIndex(index)} type="button">
                <div
                  class={`slot-icon ${slotIcon ? '' : 'placeholder'} ${item?.leather_color ? 'leather' : ''} ${item?.rarity ? rarityClass(item.rarity) : ''}`}
                  style={leatherColor ? `--leather-color:${leatherColor}` : undefined}
                >
                  {#if slotIcon}
                    <img
                      src={slotIcon}
                      alt={`${item.name} icon`}
                      loading="lazy"
                      width="42"
                      height="42"
                      on:load={handleIconLoad}
                      on:error={(event) => handleIconError(event, slotIcon)}
                    />
                  {:else if item}
                    <span class="slot-initial">{item.name.slice(0, 1).toUpperCase()}</span>
                  {:else}
                    <span class="slot-initial empty">?</span>
                  {/if}
                </div>
                <div class="slot-details">
                  <div class="slot-meta">
                    <span class="slot-piece-label">{pieceLabelFromIndex(index)}</span>
                    {#if item?.rarity}
                      <span class="slot-rarity-pill">{formatRarityLabel(item.rarity)}</span>
                    {:else}
                      <span class="slot-rarity-pill muted">Unassigned</span>
                    {/if}
                  </div>
                  <p class={`slot-name ${item ? '' : 'slot-placeholder'}`}>
                    {item?.name ?? 'No armor selected'}
                  </p>
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
                        {#each item.lore as line}
                          <p>{line}</p>
                        {/each}
                      </div>
                    {/if}
                  {:else}
                    <div class="tooltip-empty">Empty slot</div>
                  {/if}
                </div>
              </button>
            {/each}
          </div>
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

  .equipped-summary {
    position: relative;
    display: flex;
    flex-direction: column;
    gap: 20px;
    padding: 26px 28px;
    border-radius: 24px;
    border: 1px solid var(--rarity-accent, rgba(99, 102, 241, 0.4));
    background: rgba(6, 11, 30, 0.92);
    box-shadow: 0 18px 34px rgba(2, 6, 23, 0.55);
    overflow: hidden;
  }

  .equipped-summary::before {
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(
        135deg,
        rgba(255, 255, 255, 0.06),
        transparent 45%
      ),
      radial-gradient(
        circle at 0% 0%,
        var(--rarity-accent, rgba(99, 102, 241, 0.3)),
        transparent 65%
      );
    opacity: 0.9;
    pointer-events: none;
  }

  .equipped-heading {
    display: flex;
    justify-content: space-between;
    gap: 24px;
    align-items: flex-start;
    position: relative;
    z-index: 1;
  }

  .heading-copy {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .equipped-label {
    text-transform: uppercase;
    letter-spacing: 0.2em;
    font-size: 0.75rem;
    color: rgba(248, 250, 252, 0.7);
  }

  .heading-copy h3 {
    margin: 0;
    font-size: 1.6rem;
    color: #fff;
  }

  .equipped-meta {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    justify-content: flex-end;
  }

  .rarity-chip {
    background: rgba(255, 255, 255, 0.14);
    color: #fff;
    border-radius: 999px;
    padding: 6px 14px;
    border: 1px solid rgba(255, 255, 255, 0.25);
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 0.05em;
  }

  .rarity-chip.subtle {
    color: var(--theme-text);
    border-color: rgba(255, 255, 255, 0.2);
    background: rgba(255, 255, 255, 0.08);
  }

  .equipped-slot-pill {
    background: rgba(15, 23, 42, 0.4);
    color: #e0e7ff;
    padding: 6px 14px;
    border-radius: 999px;
    font-weight: 600;
    font-size: 0.85rem;
    border: 1px solid rgba(255, 255, 255, 0.2);
  }

  .equipped-body {
    position: relative;
    z-index: 1;
    display: grid;
    grid-template-columns: minmax(240px, 0.9fr) minmax(240px, 1fr);
    gap: 20px;
    align-items: stretch;
  }

  .equipped-icons {
    display: flex;
    gap: 14px;
    flex-wrap: wrap;
    padding: 16px;
    border-radius: 18px;
    background: rgba(2, 6, 23, 0.45);
    border: 1px solid rgba(148, 163, 184, 0.16);
    box-shadow: inset 0 0 24px rgba(15, 23, 42, 0.35);
    justify-content: flex-start;
  }

  .equipped-icon {
    width: 72px;
    height: 92px;
    border-radius: 16px;
    background: rgba(15, 23, 42, 0.7);
    border: 1px solid rgba(148, 163, 184, 0.2);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 8px;
  }

  .equipped-icon.placeholder {
    background: rgba(15, 23, 42, 0.35);
    border-style: dashed;
  }

  .equipped-icon img {
    width: 64px;
    height: 64px;
    image-rendering: pixelated;
  }

  .equipped-piece {
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: rgba(248, 250, 252, 0.88);
  }

  .equipped-details {
    background: rgba(2, 6, 23, 0.45);
    border-radius: 18px;
    border: 1px solid rgba(148, 163, 184, 0.16);
    padding: 18px 22px;
    display: flex;
    flex-direction: column;
    gap: 18px;
  }

  .equipped-stats {
    list-style: none;
    margin: 0;
    padding: 0;
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 12px 20px;
  }

  .equipped-stats li {
    display: flex;
    justify-content: space-between;
    gap: 16px;
    font-weight: 600;
    color: #f8fafc;
  }

  .equipped-stats li span:first-child {
    color: rgba(226, 232, 240, 0.7);
    font-weight: 500;
  }

  .section-label {
    margin: 0 0 6px;
    text-transform: uppercase;
    font-size: 0.74rem;
    letter-spacing: 0.18em;
    color: rgba(226, 232, 240, 0.65);
  }

  .equipped-bonuses {
    border-top: 1px solid rgba(148, 163, 184, 0.18);
    padding-top: 12px;
    color: rgba(248, 250, 252, 0.9);
  }

  .equipped-bonuses p {
    margin: 0 0 6px;
    line-height: 1.45;
  }

  .wardrobe-grid {
    display: grid;
    gap: 20px;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  }

  .wardrobe-set {
    position: relative;
    padding: 18px;
    border-radius: 22px;
    border: 1px solid rgba(148, 163, 184, 0.16);
    background: radial-gradient(
        circle at 0% 0%,
        var(--rarity-accent, rgba(99, 102, 241, 0.08)),
        transparent 65%
      ),
      rgba(8, 12, 26, 0.88);
    box-shadow: 0 18px 36px rgba(2, 6, 23, 0.45);
    overflow: visible;
    transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
    display: flex;
    flex-direction: column;
    min-height: 240px;
    backdrop-filter: blur(6px);
  }

  .wardrobe-set::after {
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(120deg, rgba(255, 255, 255, 0.08), transparent 35%);
    opacity: 0.4;
    pointer-events: none;
    border-radius: inherit;
  }

  .wardrobe-set > * {
    position: relative;
    z-index: 1;
  }

  .wardrobe-set.equipped {
    border-color: var(--rarity-accent, rgba(99, 102, 241, 0.5));
    box-shadow: 0 28px 50px rgba(2, 6, 23, 0.65);
    transform: translateY(-4px);
  }

  .set-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
    gap: 12px;
  }

  .set-label {
    font-weight: 600;
    color: rgba(248, 250, 252, 0.92);
    letter-spacing: 0.05em;
    font-size: 0.9rem;
  }

  .set-slots {
    display: flex;
    flex-direction: column;
    gap: 12px;
    flex: 1;
    min-height: 0;
    margin-top: 4px;
  }

  .slot-shell {
    background: none;
    border: none;
    padding: 10px 12px;
    width: 100%;
    text-align: left;
    position: relative;
    cursor: default;
    display: flex;
    align-items: center;
    gap: 12px;
    min-height: 0;
    border-radius: 18px;
    background: rgba(15, 23, 42, 0.45);
    border: 1px solid rgba(148, 163, 184, 0.14);
    transition: border-color 0.2s ease, transform 0.2s ease, background 0.2s ease;
    box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.02);
  }

  .slot-shell:hover,
  .slot-shell:focus-visible {
    border-color: rgba(226, 232, 240, 0.35);
    background: rgba(15, 23, 42, 0.6);
    transform: translateY(-1px);
  }

  .slot-icon {
    border-radius: 16px;
    border: 1px solid rgba(148, 163, 184, 0.28);
    background: rgba(15, 23, 42, 0.5);
    width: 58px;
    height: 58px;
    padding: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: border-color 0.2s ease, transform 0.2s ease, box-shadow 0.2s ease;
    flex-shrink: 0;
  }

  .slot-icon.placeholder {
    border-style: dashed;
    color: rgba(226, 232, 240, 0.45);
  }

  .slot-icon img {
    width: 100%;
    height: 100%;
    object-fit: contain;
    image-rendering: pixelated;
  }

  .slot-icon.leather {
    background: rgba(15, 23, 42, 0.45);
    box-shadow: inset 0 0 0 1px var(--leather-color, rgba(255, 255, 255, 0.08));
  }

  .wardrobe-set.equipped .slot-icon {
    border-color: var(--rarity-accent, rgba(99, 102, 241, 0.45));
  }

  .slot-shell:hover .slot-icon {
    border-color: rgba(255, 255, 255, 0.35);
    transform: translateY(-1px) scale(1.02);
    box-shadow: 0 10px 18px rgba(0, 0, 0, 0.35);
  }

  .slot-initial {
    font-size: 1.1rem;
    font-weight: 700;
    color: var(--theme-text);
  }

  .slot-initial.empty {
    opacity: 0.18;
  }

  .slot-details {
    display: flex;
    flex-direction: column;
    gap: 4px;
    flex: 1;
    min-width: 0;
  }

  .slot-meta {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 10px;
  }

  .slot-piece-label {
    font-size: 0.78rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: rgba(226, 232, 240, 0.7);
  }

  .slot-rarity-pill {
    border-radius: 999px;
    padding: 2px 10px;
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    border: 1px solid rgba(255, 255, 255, 0.2);
    color: rgba(248, 250, 252, 0.85);
    background: rgba(255, 255, 255, 0.08);
    white-space: nowrap;
  }

  .slot-rarity-pill.muted {
    color: rgba(226, 232, 240, 0.6);
    border-color: rgba(226, 232, 240, 0.18);
    background: rgba(15, 23, 42, 0.35);
  }

  .slot-name {
    margin: 0;
    font-weight: 600;
    color: rgba(248, 250, 252, 0.95);
    font-size: 0.92rem;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .slot-placeholder {
    color: rgba(226, 232, 240, 0.55);
    font-weight: 500;
  }

  .slot-tooltip {
    position: absolute;
    inset: auto auto calc(100% + 12px) 50%;
    transform: translateX(-50%) translateY(4px);
    background: rgba(15, 23, 42, 0.96);
    border: 1px solid rgba(148, 163, 184, 0.35);
    border-radius: 10px;
    padding: 10px 12px;
    min-width: 180px;
    max-width: 240px;
    box-shadow: 0 16px 32px rgba(15, 23, 42, 0.42);
    opacity: 0;
    pointer-events: none;
    transition: opacity 0.18s ease, transform 0.18s ease;
    color: #e2e8f0;
    z-index: 20;
  }

  .slot-shell:hover .slot-tooltip,
  .slot-shell:focus-within .slot-tooltip {
    opacity: 1;
    transform: translateX(-50%) translateY(0);
    pointer-events: auto;
  }

  .tooltip-header {
    display: flex;
    justify-content: space-between;
    gap: 8px;
    font-size: 0.68rem;
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
    max-height: min(280px, 50vh);
    overflow-y: auto;
    padding-right: 4px;
  }

  .tooltip-lore p {
    margin: 0;
    line-height: 1.35;
  }

  .tooltip-empty {
    font-size: 0.8rem;
    opacity: 0.75;
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

  @media (max-width: 900px) {
    .equipped-body {
      grid-template-columns: 1fr;
    }

    .equipped-icons {
      justify-content: flex-start;
    }
  }

  @media (max-width: 640px) {
    .set-slots {
      grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    }
  }
</style>
