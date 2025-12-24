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
    ProfileSummaryResponse,
    InventoryItem,
    BackpackData
  } from './profileTypes';

  export let summary: ProfileSummaryResponse;

  // Constants
  const INVENTORY_COLS = 9;
  const INVENTORY_HOTBAR_SIZE = 9;
  const INVENTORY_MAIN_SIZE = 27;
  const ENDER_CHEST_PAGE_SIZE = 45; // 9x5 per page
  const TEXTURE_PACK_ORDER: TexturePack[] = ['furfsky', 'vanilla'];
  const ICON_RETRY_BASE_DELAY = 400;
  const ICON_RETRY_BACKOFF = 1.5;
  const ICON_RETRY_MAX_DELAY = 8000;

  // State
  let activeSection: 'inventory' | 'ender_chest' | 'backpacks' | 'bags' = 'inventory';
  let enderChestPage = 0;
  let expandedBackpacks = new Set<number>();
  let tintedIconVersion = 0;
  const pendingTintKeys = new Set<string>();
  const pendingRetryTimers = new WeakMap<HTMLImageElement, ReturnType<typeof setTimeout>>();

  // Reactive data
  $: inventory = summary?.inventory;
  $: playerInventory = inventory?.player_inventory ?? [];
  $: enderChest = inventory?.ender_chest ?? [];
  $: backpacks = inventory?.backpacks ?? [];
  $: equipment = inventory?.equipment ?? [];
  $: potionBag = inventory?.potion_bag ?? [];
  $: fishingBag = inventory?.fishing_bag ?? [];
  $: quiver = inventory?.quiver ?? [];
  $: personalVault = inventory?.personal_vault ?? [];

  // Split player inventory into hotbar and main
  $: hotbar = playerInventory.slice(0, INVENTORY_HOTBAR_SIZE);
  $: mainInventory = playerInventory.slice(INVENTORY_HOTBAR_SIZE, INVENTORY_HOTBAR_SIZE + INVENTORY_MAIN_SIZE);

  // Ender chest pages
  $: enderChestPageCount = Math.max(1, Math.ceil(enderChest.length / ENDER_CHEST_PAGE_SIZE));
  $: currentEnderChestItems = enderChest.slice(
    enderChestPage * ENDER_CHEST_PAGE_SIZE,
    (enderChestPage + 1) * ENDER_CHEST_PAGE_SIZE
  );

  // Counts for tabs
  $: inventoryItemCount = playerInventory.filter(Boolean).length;
  $: enderChestItemCount = enderChest.filter(Boolean).length;
  $: backpackItemCount = backpacks.reduce((sum, bp) => sum + bp.contents.filter(Boolean).length, 0);
  $: bagsItemCount = potionBag.filter(Boolean).length + fishingBag.filter(Boolean).length + quiver.filter(Boolean).length;

  // Helpers
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

  function rarityClass(rarity?: string | null) {
    if (!rarity) return '';
    return `rarity-${rarity.toLowerCase().replace(/\s+/g, '-')}`;
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
    ].filter(Boolean).join(' ');
  }

  function buildCacheBustedUrl(url: string, attempt: number) {
    const separator = url.includes('?') ? '&' : '?';
    return `${url}${separator}retry=${attempt}-${Date.now()}`;
  }

  function clearRetryTimer(target: HTMLImageElement) {
    const timerId = pendingRetryTimers.get(target);
    if (timerId !== undefined) {
      clearTimeout(timerId);
      pendingRetryTimers.delete(target);
    }
  }

  function computeRetryDelay(attempt: number) {
    const delay = ICON_RETRY_BASE_DELAY * Math.pow(ICON_RETRY_BACKOFF, attempt);
    return Math.min(ICON_RETRY_MAX_DELAY, Math.round(delay));
  }

  function markPlaceholder(target: HTMLImageElement, shouldShow: boolean) {
    target.parentElement?.classList.toggle('placeholder', shouldShow);
  }

  function handleIconLoad(event: Event) {
    const target = event.currentTarget as HTMLImageElement | null;
    if (!target) return;
    clearRetryTimer(target);
    delete target.dataset.retryCount;
    delete target.dataset.failed;
    markPlaceholder(target, false);
  }

  function handleIconError(event: Event, iconUrl?: string | null) {
    const target = event.currentTarget as HTMLImageElement | null;
    if (!target) return;
    const fallback = target.dataset.fallback;
    if (fallback && target.src !== fallback) {
      clearRetryTimer(target);
      target.dataset.fallback = '';
      target.src = fallback;
      return;
    }
    if (!iconUrl) {
      target.dataset.failed = '1';
      clearRetryTimer(target);
      markPlaceholder(target, true);
      return;
    }
    const attempt = Number(target.dataset.retryCount ?? '0');
    const nextAttempt = attempt + 1;
    target.dataset.retryCount = String(nextAttempt);
    target.dataset.failed = '';
    markPlaceholder(target, true);
    clearRetryTimer(target);
    const delay = computeRetryDelay(attempt);
    const timerId = setTimeout(() => {
      pendingRetryTimers.delete(target);
      if (!target.isConnected) return;
      const nextSrc = buildCacheBustedUrl(iconUrl, nextAttempt);
      if (target.src === nextSrc) {
        target.src = '';
        target.src = nextSrc;
      } else {
        target.src = nextSrc;
      }
    }, delay);
    pendingRetryTimers.set(target, timerId);
  }

  type IconSource = TexturePack | 'legacy';

  function pickIconVariant(
    item: InventoryItem | null,
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
    item: InventoryItem | null,
    _version: number,
    pack?: TexturePack
  ): string | null {
    if (!item) return null;
    const picked = pickIconVariant(item, pack);
    if (!picked) return null;

    const { url: baseIcon, source } = picked;
    if (source !== 'vanilla') return baseIcon;

    const leatherColor = formatLeatherColor(item.leather_color);
    if (!leatherColor || isFallbackIcon(baseIcon)) return baseIcon;

    const key = `${baseIcon}|${leatherColor}`;
    const cached = peekTintedIcon(baseIcon, leatherColor);
    if (cached) return cached;

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

  function resolveFallbackIcon(item: InventoryItem | null, primaryIcon: string | null): string | null {
    if (!item || !primaryIcon) return null;
    const variants = item.icon_variants ?? {};
    for (const pack of TEXTURE_PACK_ORDER) {
      const url = variants[pack];
      if (url && url !== primaryIcon) return url;
    }
    return item.icon_url && item.icon_url !== primaryIcon ? item.icon_url : null;
  }

  function toggleBackpack(slot: number) {
    if (expandedBackpacks.has(slot)) {
      expandedBackpacks.delete(slot);
    } else {
      expandedBackpacks.add(slot);
    }
    expandedBackpacks = expandedBackpacks;
  }

  // Backpack color mapping based on SkyBlock backpack types
  const BACKPACK_COLORS: Record<string, string> = {
    // By ID
    'SMALL_BACKPACK': '#8B4513',      // Brown
    'MEDIUM_BACKPACK': '#DAA520',     // Golden/Yellow
    'LARGE_BACKPACK': '#228B22',      // Green
    'GREATER_BACKPACK': '#4169E1',    // Blue
    'JUMBO_BACKPACK': '#DC143C',      // Red/Crimson
    // Variants
    'SMALL_ENDER_BACKPACK': '#8B4513',
    'MEDIUM_ENDER_BACKPACK': '#DAA520',
    'LARGE_ENDER_BACKPACK': '#228B22',
    'GREATER_ENDER_BACKPACK': '#4169E1',
    'JUMBO_ENDER_BACKPACK': '#DC143C',
  };

  function getBackpackColor(item: InventoryItem | null): string | null {
    if (!item) return null;
    
    // Check leather_color first (some custom backpacks might have it)
    const leatherColor = formatLeatherColor(item.leather_color);
    if (leatherColor) return leatherColor;
    
    // Check by item ID
    const itemId = item.id?.toUpperCase() ?? '';
    if (BACKPACK_COLORS[itemId]) {
      return BACKPACK_COLORS[itemId];
    }
    
    // Check by item name as fallback
    const name = item.name?.toLowerCase() ?? '';
    if (name.includes('small')) return '#8B4513';
    if (name.includes('medium')) return '#DAA520';
    if (name.includes('large') && !name.includes('greater')) return '#228B22';
    if (name.includes('greater')) return '#4169E1';
    if (name.includes('jumbo')) return '#DC143C';
    
    return null;
  }

  function getBackpackSlotCount(contents: (InventoryItem | null)[]): number {
    // Backpack sizes: Small=9, Medium=18, Large=27, Greater=36, Jumbo=45
    const len = contents.length;
    if (len <= 9) return 9;
    if (len <= 18) return 18;
    if (len <= 27) return 27;
    if (len <= 36) return 36;
    return 45;
  }
</script>

<section id="inventory" class="inventory-section">
  {#if !inventory}
    <div class="card loading-card">
      <p>Loading inventory data...</p>
    </div>
  {:else}
    <!-- Section Tabs -->
    <nav class="inventory-tabs">
      <button
        class="tab-btn"
        class:active={activeSection === 'inventory'}
        on:click={() => (activeSection = 'inventory')}
      >
        <span class="tab-icon">🎒</span>
        <span class="tab-label">Inventory</span>
        <span class="tab-count">{inventoryItemCount}</span>
      </button>
      <button
        class="tab-btn"
        class:active={activeSection === 'ender_chest'}
        on:click={() => (activeSection = 'ender_chest')}
      >
        <span class="tab-icon">📦</span>
        <span class="tab-label">Ender Chest</span>
        <span class="tab-count">{enderChestItemCount}</span>
      </button>
      <button
        class="tab-btn"
        class:active={activeSection === 'backpacks'}
        on:click={() => (activeSection = 'backpacks')}
      >
        <span class="tab-icon">🎒</span>
        <span class="tab-label">Backpacks</span>
        <span class="tab-count">{backpacks.length}</span>
      </button>
      <button
        class="tab-btn"
        class:active={activeSection === 'bags'}
        on:click={() => (activeSection = 'bags')}
      >
        <span class="tab-icon">👜</span>
        <span class="tab-label">Bags</span>
        <span class="tab-count">{bagsItemCount}</span>
      </button>
    </nav>

    <!-- Player Inventory Section -->
    {#if activeSection === 'inventory'}
      <div class="mc-container">
        <header class="container-header">
          <h3>Player Inventory</h3>
          <span class="item-count">{inventoryItemCount} items</span>
        </header>

        <!-- Main Inventory (3 rows x 9 cols) -->
        <div class="mc-grid mc-grid-9" data-label="Main Inventory">
          {#each mainInventory as item, index (index)}
            {@const leatherColor = item ? formatLeatherColor(item.leather_color) : null}
            {@const iconSrc = resolveDisplayIcon(item, tintedIconVersion, $texturePackStore)}
            {@const fallbackIcon = resolveFallbackIcon(item, iconSrc)}
            <button
              class="mc-slot"
              class:filled={!!item}
              class:leather={!!leatherColor}
              style={leatherColor ? `--leather-color:${leatherColor}` : undefined}
              type="button"
            >
              {#if iconSrc}
                <img
                  src={iconSrc}
                  alt={item?.name ?? 'Item'}
                  loading="lazy"
                  width="32"
                  height="32"
                  data-fallback={fallbackIcon ?? undefined}
                  on:load={handleIconLoad}
                  on:error={(e) => handleIconError(e, iconSrc)}
                />
              {/if}
              {#if item && item.count > 1}
                <span class="item-count-badge">{item.count}</span>
              {/if}
              <!-- Tooltip -->
              {#if item}
                <div class="mc-tooltip">
                  <div class="tooltip-name" class:rarity={item.rarity}>{item.name}</div>
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
                              >{segment.text}</span>
                            {/each}
                          {:else}
                            <span class="mc-span">&nbsp;</span>
                          {/if}
                        </p>
                      {/each}
                    </div>
                  {:else if item.lore?.length}
                    <div class="tooltip-lore">
                      {#each item.lore as line}
                        <p>{line}</p>
                      {/each}
                    </div>
                  {/if}
                </div>
              {/if}
            </button>
          {/each}
        </div>

        <!-- Hotbar (1 row x 9 cols, highlighted) -->
        <div class="mc-hotbar">
          <span class="hotbar-label">Hotbar</span>
          <div class="mc-grid mc-grid-9">
            {#each hotbar as item, index (index)}
              {@const leatherColor = item ? formatLeatherColor(item.leather_color) : null}
              {@const iconSrc = resolveDisplayIcon(item, tintedIconVersion, $texturePackStore)}
              {@const fallbackIcon = resolveFallbackIcon(item, iconSrc)}
              <button
                class="mc-slot hotbar-slot"
                class:filled={!!item}
                class:leather={!!leatherColor}
                style={leatherColor ? `--leather-color:${leatherColor}` : undefined}
                type="button"
              >
                <span class="slot-number">{index + 1}</span>
                {#if iconSrc}
                  <img
                    src={iconSrc}
                    alt={item?.name ?? 'Item'}
                    loading="lazy"
                    width="32"
                    height="32"
                    data-fallback={fallbackIcon ?? undefined}
                    on:load={handleIconLoad}
                    on:error={(e) => handleIconError(e, iconSrc)}
                  />
                {/if}
                {#if item && item.count > 1}
                  <span class="item-count-badge">{item.count}</span>
                {/if}
                {#if item}
                  <div class="mc-tooltip">
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
                                >{segment.text}</span>
                              {/each}
                            {:else}
                              <span class="mc-span">&nbsp;</span>
                            {/if}
                          </p>
                        {/each}
                      </div>
                    {:else if item.lore?.length}
                      <div class="tooltip-lore">
                        {#each item.lore as line}
                          <p>{line}</p>
                        {/each}
                      </div>
                    {/if}
                  </div>
                {/if}
              </button>
            {/each}
          </div>
        </div>
      </div>
    {/if}

    <!-- Ender Chest Section -->
    {#if activeSection === 'ender_chest'}
      <div class="mc-container ender-chest">
        <header class="container-header">
          <h3>Ender Chest</h3>
          <div class="page-controls">
            <button
              class="page-btn"
              disabled={enderChestPage === 0}
              on:click={() => (enderChestPage = Math.max(0, enderChestPage - 1))}
            >
              ◀
            </button>
            <span class="page-indicator">Page {enderChestPage + 1} / {enderChestPageCount}</span>
            <button
              class="page-btn"
              disabled={enderChestPage >= enderChestPageCount - 1}
              on:click={() => (enderChestPage = Math.min(enderChestPageCount - 1, enderChestPage + 1))}
            >
              ▶
            </button>
          </div>
        </header>

        <div class="mc-grid mc-grid-9" data-label="Ender Chest">
          {#each currentEnderChestItems as item, index (index)}
            {@const leatherColor = item ? formatLeatherColor(item.leather_color) : null}
            {@const iconSrc = resolveDisplayIcon(item, tintedIconVersion, $texturePackStore)}
            {@const fallbackIcon = resolveFallbackIcon(item, iconSrc)}
            <button
              class="mc-slot"
              class:filled={!!item}
              class:leather={!!leatherColor}
              style={leatherColor ? `--leather-color:${leatherColor}` : undefined}
              type="button"
            >
              {#if iconSrc}
                <img
                  src={iconSrc}
                  alt={item?.name ?? 'Item'}
                  loading="lazy"
                  width="32"
                  height="32"
                  data-fallback={fallbackIcon ?? undefined}
                  on:load={handleIconLoad}
                  on:error={(e) => handleIconError(e, iconSrc)}
                />
              {/if}
              {#if item && item.count > 1}
                <span class="item-count-badge">{item.count}</span>
              {/if}
              {#if item}
                <div class="mc-tooltip">
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
                              >{segment.text}</span>
                            {/each}
                          {:else}
                            <span class="mc-span">&nbsp;</span>
                          {/if}
                        </p>
                      {/each}
                    </div>
                  {:else if item.lore?.length}
                    <div class="tooltip-lore">
                      {#each item.lore as line}
                        <p>{line}</p>
                      {/each}
                    </div>
                  {/if}
                </div>
              {/if}
            </button>
          {/each}
        </div>
      </div>
    {/if}

    <!-- Backpacks Section -->
    {#if activeSection === 'backpacks'}
      <div class="backpacks-list">
        {#if backpacks.length === 0}
          <div class="card empty-card">
            <p>No backpacks found.</p>
          </div>
        {:else}
          {#each backpacks as backpack (backpack.slot)}
            {@const isExpanded = expandedBackpacks.has(backpack.slot)}
            {@const backpackColor = getBackpackColor(backpack.icon)}
            {@const backpackIcon = resolveDisplayIcon(backpack.icon, tintedIconVersion, $texturePackStore)}
            {@const slotCount = getBackpackSlotCount(backpack.contents)}
            <div 
              class="backpack-card" 
              class:expanded={isExpanded}
              style={backpackColor ? `--backpack-color:${backpackColor}` : undefined}
            >
              <button class="backpack-header" on:click={() => toggleBackpack(backpack.slot)}>
                <div 
                  class="backpack-icon"
                  class:colored={!!backpackColor}
                >
                  {#if backpackIcon}
                    <img src={backpackIcon} alt={backpack.icon?.name ?? 'Backpack'} width="40" height="40" />
                  {:else}
                    <span class="backpack-placeholder">🎒</span>
                  {/if}
                </div>
                <div class="backpack-info">
                  <h4>{backpack.icon?.name ?? `Backpack ${backpack.slot + 1}`}</h4>
                  <span class="backpack-meta">
                    {backpack.contents.filter(Boolean).length} / {slotCount} slots used
                  </span>
                </div>
                <span class="expand-icon">{isExpanded ? '▲' : '▼'}</span>
              </button>

              {#if isExpanded}
                <div class="backpack-contents">
                  <div class="mc-grid mc-grid-9">
                    {#each backpack.contents as item, index (index)}
                      {@const leatherColor = item ? formatLeatherColor(item.leather_color) : null}
                      {@const iconSrc = resolveDisplayIcon(item, tintedIconVersion, $texturePackStore)}
                      {@const fallbackIcon = resolveFallbackIcon(item, iconSrc)}
                      <button
                        class="mc-slot"
                        class:filled={!!item}
                        class:leather={!!leatherColor}
                        style={leatherColor ? `--leather-color:${leatherColor}` : undefined}
                        type="button"
                      >
                        {#if iconSrc}
                          <img
                            src={iconSrc}
                            alt={item?.name ?? 'Item'}
                            loading="lazy"
                            width="32"
                            height="32"
                            data-fallback={fallbackIcon ?? undefined}
                            on:load={handleIconLoad}
                            on:error={(e) => handleIconError(e, iconSrc)}
                          />
                        {/if}
                        {#if item && item.count > 1}
                          <span class="item-count-badge">{item.count}</span>
                        {/if}
                        {#if item}
                          <div class="mc-tooltip">
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
                                        >{segment.text}</span>
                                      {/each}
                                    {:else}
                                      <span class="mc-span">&nbsp;</span>
                                    {/if}
                                  </p>
                                {/each}
                              </div>
                            {:else if item.lore?.length}
                              <div class="tooltip-lore">
                                {#each item.lore as line}
                                  <p>{line}</p>
                                {/each}
                              </div>
                            {/if}
                          </div>
                        {/if}
                      </button>
                    {/each}
                  </div>
                </div>
              {/if}
            </div>
          {/each}
        {/if}
      </div>
    {/if}

    <!-- Bags Section -->
    {#if activeSection === 'bags'}
      <div class="bags-container">
        {#if potionBag.length > 0}
          <div class="mc-container bag-section">
            <header class="container-header">
              <h3>🧪 Potion Bag</h3>
              <span class="item-count">{potionBag.filter(Boolean).length} items</span>
            </header>
            <div class="mc-grid mc-grid-9">
              {#each potionBag as item, index (index)}
                {@const leatherColor = item ? formatLeatherColor(item.leather_color) : null}
                {@const iconSrc = resolveDisplayIcon(item, tintedIconVersion, $texturePackStore)}
                {@const fallbackIcon = resolveFallbackIcon(item, iconSrc)}
                <button
                  class="mc-slot"
                  class:filled={!!item}
                  class:leather={!!leatherColor}
                  style={leatherColor ? `--leather-color:${leatherColor}` : undefined}
                  type="button"
                >
                  {#if iconSrc}
                    <img
                      src={iconSrc}
                      alt={item?.name ?? 'Item'}
                      loading="lazy"
                      width="32"
                      height="32"
                      data-fallback={fallbackIcon ?? undefined}
                      on:load={handleIconLoad}
                      on:error={(e) => handleIconError(e, iconSrc)}
                    />
                  {/if}
                  {#if item && item.count > 1}
                    <span class="item-count-badge">{item.count}</span>
                  {/if}
                  {#if item}
                    <div class="mc-tooltip">
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
                                  >{segment.text}</span>
                                {/each}
                              {:else}
                                <span class="mc-span">&nbsp;</span>
                              {/if}
                            </p>
                          {/each}
                        </div>
                      {/if}
                    </div>
                  {/if}
                </button>
              {/each}
            </div>
          </div>
        {/if}

        {#if fishingBag.length > 0}
          <div class="mc-container bag-section">
            <header class="container-header">
              <h3>🎣 Fishing Bag</h3>
              <span class="item-count">{fishingBag.filter(Boolean).length} items</span>
            </header>
            <div class="mc-grid mc-grid-9">
              {#each fishingBag as item, index (index)}
                {@const leatherColor = item ? formatLeatherColor(item.leather_color) : null}
                {@const iconSrc = resolveDisplayIcon(item, tintedIconVersion, $texturePackStore)}
                {@const fallbackIcon = resolveFallbackIcon(item, iconSrc)}
                <button
                  class="mc-slot"
                  class:filled={!!item}
                  class:leather={!!leatherColor}
                  style={leatherColor ? `--leather-color:${leatherColor}` : undefined}
                  type="button"
                >
                  {#if iconSrc}
                    <img
                      src={iconSrc}
                      alt={item?.name ?? 'Item'}
                      loading="lazy"
                      width="32"
                      height="32"
                      data-fallback={fallbackIcon ?? undefined}
                      on:load={handleIconLoad}
                      on:error={(e) => handleIconError(e, iconSrc)}
                    />
                  {/if}
                  {#if item && item.count > 1}
                    <span class="item-count-badge">{item.count}</span>
                  {/if}
                  {#if item}
                    <div class="mc-tooltip">
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
                                  >{segment.text}</span>
                                {/each}
                              {:else}
                                <span class="mc-span">&nbsp;</span>
                              {/if}
                            </p>
                          {/each}
                        </div>
                      {/if}
                    </div>
                  {/if}
                </button>
              {/each}
            </div>
          </div>
        {/if}

        {#if quiver.length > 0}
          <div class="mc-container bag-section">
            <header class="container-header">
              <h3>🏹 Quiver</h3>
              <span class="item-count">{quiver.filter(Boolean).length} items</span>
            </header>
            <div class="mc-grid mc-grid-9">
              {#each quiver as item, index (index)}
                {@const leatherColor = item ? formatLeatherColor(item.leather_color) : null}
                {@const iconSrc = resolveDisplayIcon(item, tintedIconVersion, $texturePackStore)}
                {@const fallbackIcon = resolveFallbackIcon(item, iconSrc)}
                <button
                  class="mc-slot"
                  class:filled={!!item}
                  class:leather={!!leatherColor}
                  style={leatherColor ? `--leather-color:${leatherColor}` : undefined}
                  type="button"
                >
                  {#if iconSrc}
                    <img
                      src={iconSrc}
                      alt={item?.name ?? 'Item'}
                      loading="lazy"
                      width="32"
                      height="32"
                      data-fallback={fallbackIcon ?? undefined}
                      on:load={handleIconLoad}
                      on:error={(e) => handleIconError(e, iconSrc)}
                    />
                  {/if}
                  {#if item && item.count > 1}
                    <span class="item-count-badge">{item.count}</span>
                  {/if}
                  {#if item}
                    <div class="mc-tooltip">
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
                                  >{segment.text}</span>
                                {/each}
                              {:else}
                                <span class="mc-span">&nbsp;</span>
                              {/if}
                            </p>
                          {/each}
                        </div>
                      {/if}
                    </div>
                  {/if}
                </button>
              {/each}
            </div>
          </div>
        {/if}

        {#if potionBag.length === 0 && fishingBag.length === 0 && quiver.length === 0}
          <div class="card empty-card">
            <p>No bags found.</p>
          </div>
        {/if}
      </div>
    {/if}
  {/if}
</section>

<style>
  .inventory-section {
    display: flex;
    flex-direction: column;
    gap: 20px;
  }

  .loading-card,
  .empty-card {
    padding: 32px;
    text-align: center;
    color: var(--theme-text-soft);
    background: rgba(10, 13, 22, 0.85);
    border-radius: 12px;
    border: 1px solid rgba(148, 163, 184, 0.12);
  }

  /* Tab Navigation */
  .inventory-tabs {
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
    background: rgba(8, 11, 20, 0.9);
    padding: 6px;
    border-radius: 12px;
    border: 1px solid rgba(148, 163, 184, 0.15);
  }

  .tab-btn {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 14px;
    border: 1px solid transparent;
    border-radius: 8px;
    background: transparent;
    color: rgba(226, 232, 240, 0.7);
    cursor: pointer;
    transition: all 0.2s ease;
    font-size: 0.85rem;
  }

  .tab-btn:hover {
    background: rgba(148, 163, 184, 0.1);
    color: rgba(248, 250, 252, 0.95);
  }

  .tab-btn.active {
    background: rgba(99, 102, 241, 0.2);
    border-color: rgba(99, 102, 241, 0.4);
    color: #fff;
  }

  .tab-icon {
    font-size: 1rem;
  }

  .tab-label {
    font-weight: 500;
  }

  .tab-count {
    background: rgba(255, 255, 255, 0.1);
    padding: 2px 7px;
    border-radius: 999px;
    font-size: 0.7rem;
    font-weight: 600;
  }

  .tab-btn.active .tab-count {
    background: rgba(99, 102, 241, 0.3);
  }

  /* Minecraft Container Styling */
  .mc-container {
    background: linear-gradient(180deg, rgba(22, 27, 45, 0.98) 0%, rgba(12, 16, 28, 0.99) 100%);
    border: 1px solid rgba(80, 90, 120, 0.4);
    border-radius: 8px;
    padding: 16px;
    box-shadow: 
      inset 0 1px 0 rgba(255, 255, 255, 0.04),
      0 4px 20px rgba(0, 0, 0, 0.3);
  }

  .mc-container.ender-chest {
    background: linear-gradient(180deg, rgba(35, 20, 55, 0.98) 0%, rgba(20, 12, 35, 0.99) 100%);
    border-color: rgba(138, 43, 226, 0.35);
  }

  .container-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
    padding-bottom: 10px;
    border-bottom: 1px solid rgba(148, 163, 184, 0.12);
  }

  .container-header h3 {
    margin: 0;
    font-size: 0.95rem;
    color: rgba(248, 250, 252, 0.9);
    font-weight: 600;
  }

  .item-count {
    font-size: 0.8rem;
    color: rgba(226, 232, 240, 0.5);
  }

  /* Minecraft Grid */
  .mc-grid {
    display: grid;
    gap: 2px;
    justify-content: center;
  }

  .mc-grid-9 {
    grid-template-columns: repeat(9, 52px);
  }

  /* Minecraft Slot */
  .mc-slot {
    position: relative;
    width: 52px;
    height: 52px;
    background: rgba(20, 24, 38, 0.95);
    border: 1px solid rgba(55, 60, 80, 0.7);
    border-radius: 3px;
    padding: 0;
    cursor: default;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 
      inset 1px 1px 0 rgba(0, 0, 0, 0.5),
      inset -1px -1px 0 rgba(255, 255, 255, 0.03);
    transition: all 0.12s ease;
  }

  .mc-slot:hover {
    border-color: rgba(130, 140, 180, 0.7);
    background: rgba(35, 40, 60, 0.95);
    z-index: 2;
  }

  .mc-slot.filled {
    border-color: rgba(70, 75, 95, 0.8);
  }

  .mc-slot.filled:hover {
    border-color: rgba(99, 102, 241, 0.6);
    box-shadow: 
      inset 1px 1px 0 rgba(0, 0, 0, 0.5),
      inset -1px -1px 0 rgba(255, 255, 255, 0.03),
      0 0 12px rgba(99, 102, 241, 0.2);
  }

  .mc-slot.leather {
    box-shadow: 
      inset 0 0 0 1px var(--leather-color, rgba(255, 255, 255, 0.08)),
      inset 1px 1px 0 rgba(0, 0, 0, 0.5),
      inset -1px -1px 0 rgba(255, 255, 255, 0.03);
  }

  .mc-slot img {
    width: 40px;
    height: 40px;
    object-fit: contain;
    image-rendering: pixelated;
    pointer-events: none;
  }

  .item-count-badge {
    position: absolute;
    bottom: 2px;
    right: 4px;
    font-size: 0.75rem;
    font-weight: 700;
    color: #fff;
    text-shadow: 
      1px 1px 0 #000,
      -1px 1px 0 #000,
      1px -1px 0 #000,
      -1px -1px 0 #000,
      0 0 4px rgba(0,0,0,0.8);
    pointer-events: none;
    line-height: 1;
  }

  /* Hotbar */
  .mc-hotbar {
    margin-top: 8px;
    padding-top: 12px;
    border-top: 1px solid rgba(100, 110, 130, 0.25);
  }

  .hotbar-label {
    display: block;
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: rgba(226, 232, 240, 0.4);
    margin-bottom: 8px;
    text-align: center;
  }

  .hotbar-slot {
    border-color: rgba(80, 85, 110, 0.8);
    background: rgba(25, 30, 48, 0.95);
  }

  .hotbar-slot.filled {
    border-color: rgba(99, 102, 241, 0.45);
  }

  .slot-number {
    position: absolute;
    top: 2px;
    left: 4px;
    font-size: 0.55rem;
    color: rgba(226, 232, 240, 0.3);
    pointer-events: none;
    font-weight: 600;
  }

  /* Tooltip */
  .mc-tooltip {
    position: absolute;
    inset: auto auto calc(100% + 8px) 50%;
    transform: translateX(-50%) translateY(4px);
    background: rgba(16, 0, 16, 0.96);
    border: 2px solid rgba(100, 40, 140, 0.9);
    border-radius: 0;
    padding: 8px 10px;
    min-width: 200px;
    max-width: 300px;
    max-height: min(350px, 70vh);
    box-shadow: 0 6px 32px rgba(0, 0, 0, 0.6);
    opacity: 0;
    pointer-events: none;
    transition: opacity 0.1s ease, transform 0.1s ease;
    color: #aaa;
    z-index: 100;
    overflow: auto;
    scrollbar-width: thin;
    font-family: 'Minecraft', monospace, sans-serif;
  }

  .mc-slot:hover .mc-tooltip,
  .mc-slot:focus-within .mc-tooltip {
    opacity: 1;
    transform: translateX(-50%) translateY(0);
    pointer-events: auto;
  }

  .tooltip-name {
    font-weight: 600;
    color: #fff;
    font-size: 0.9rem;
    margin-bottom: 2px;
  }

  .tooltip-rarity {
    font-size: 0.72rem;
    color: var(--theme-accent, #a78bfa);
    margin-bottom: 6px;
    text-transform: uppercase;
    letter-spacing: 0.03em;
  }

  .tooltip-lore {
    display: flex;
    flex-direction: column;
    gap: 1px;
    font-size: 0.72rem;
    line-height: 1.35;
  }

  .tooltip-lore p {
    margin: 0;
  }

  /* Page Controls */
  .page-controls {
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .page-btn {
    width: 26px;
    height: 26px;
    border: 1px solid rgba(148, 163, 184, 0.25);
    border-radius: 4px;
    background: rgba(30, 35, 50, 0.8);
    color: rgba(226, 232, 240, 0.8);
    cursor: pointer;
    transition: all 0.12s ease;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.75rem;
  }

  .page-btn:hover:not(:disabled) {
    background: rgba(99, 102, 241, 0.3);
    border-color: rgba(99, 102, 241, 0.5);
  }

  .page-btn:disabled {
    opacity: 0.3;
    cursor: not-allowed;
  }

  .page-indicator {
    font-size: 0.8rem;
    color: rgba(226, 232, 240, 0.6);
  }

  /* Backpacks */
  .backpacks-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .backpack-card {
    background: rgba(14, 18, 30, 0.95);
    border: 1px solid rgba(148, 163, 184, 0.12);
    border-radius: 10px;
    overflow: hidden;
    transition: all 0.2s ease;
    border-left: 3px solid var(--backpack-color, rgba(148, 163, 184, 0.12));
  }

  .backpack-card.expanded {
    border-color: rgba(99, 102, 241, 0.25);
    border-left-color: var(--backpack-color, rgba(99, 102, 241, 0.25));
  }

  .backpack-header {
    width: 100%;
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 12px 16px;
    background: none;
    border: none;
    cursor: pointer;
    color: inherit;
    text-align: left;
    transition: background 0.12s ease;
  }

  .backpack-header:hover {
    background: rgba(148, 163, 184, 0.06);
  }

  .backpack-icon {
    width: 44px;
    height: 44px;
    background: rgba(25, 30, 48, 0.9);
    border: 1px solid rgba(55, 60, 80, 0.7);
    border-radius: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    transition: border-color 0.15s ease, box-shadow 0.15s ease;
  }

  .backpack-icon.colored {
    border-color: var(--backpack-color, rgba(55, 60, 80, 0.7));
    box-shadow: 
      inset 0 0 12px var(--backpack-color),
      0 0 8px color-mix(in srgb, var(--backpack-color) 40%, transparent);
  }

  .backpack-icon img {
    width: 36px;
    height: 36px;
    object-fit: contain;
    image-rendering: pixelated;
  }

  .backpack-placeholder {
    font-size: 1.3rem;
  }

  .backpack-info {
    flex: 1;
    min-width: 0;
  }

  .backpack-info h4 {
    margin: 0;
    font-size: 0.95rem;
    color: rgba(248, 250, 252, 0.92);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .backpack-meta {
    font-size: 0.8rem;
    color: rgba(226, 232, 240, 0.5);
  }

  .expand-icon {
    font-size: 0.8rem;
    color: rgba(226, 232, 240, 0.4);
  }

  .backpack-contents {
    padding: 0 16px 16px;
  }

  /* Bags */
  .bags-container {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .bag-section {
    background: rgba(14, 18, 30, 0.95);
  }

  /* Minecraft Text Styles */
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
    0% { filter: blur(0.6px); }
    50% { filter: blur(0); }
    100% { filter: blur(0.6px); }
  }

  /* Responsive */
  @media (max-width: 540px) {
    .mc-grid-9 {
      grid-template-columns: repeat(9, 42px);
    }

    .mc-slot {
      width: 42px;
      height: 42px;
    }

    .mc-slot img {
      width: 32px;
      height: 32px;
    }

    .inventory-tabs {
      flex-direction: column;
    }

    .tab-btn {
      justify-content: center;
    }
  }

  @media (max-width: 420px) {
    .mc-grid-9 {
      grid-template-columns: repeat(9, 36px);
    }

    .mc-slot {
      width: 36px;
      height: 36px;
    }

    .mc-slot img {
      width: 28px;
      height: 28px;
    }
  }
</style>
