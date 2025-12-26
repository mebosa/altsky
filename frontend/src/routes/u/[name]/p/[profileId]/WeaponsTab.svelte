<script lang="ts">
  import { createEventDispatcher } from 'svelte';
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
  import type { ProfileSummaryResponse, InventoryItem } from './profileTypes';
  import { slide, fade } from 'svelte/transition';

  export let summary: ProfileSummaryResponse;

  const dispatch = createEventDispatcher<{
    weaponchange: { slot: number | null; id: string | null };
  }>();

  // Constants
  const TEXTURE_PACK_ORDER: TexturePack[] = ['furfsky', 'vanilla'];
  const ICON_RETRY_BASE_DELAY = 400;
  const ICON_RETRY_BACKOFF = 1.5;
  const ICON_RETRY_MAX_DELAY = 8000;
  const RARITY_ORDER = [
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

  // State
  let selectedWeaponSlot: number | null = null;
  let selectedWeaponId: string | null = null;
  let hoveredWeapon: WeaponCandidate | null = null;
  let sortBy: 'slot' | 'name' | 'rarity' = 'slot';
  let filterRarity: string = 'all';
  let searchQuery: string = '';
  let showCatalog = false;
  let catalogSearch = '';
  let tintedIconVersion = 0;
  const pendingTintKeys = new Set<string>();
  const pendingRetryTimers = new WeakMap<HTMLImageElement, ReturnType<typeof setTimeout>>();

  // Types
  type WeaponCandidate = {
    slot: number;
    id: string;
    name?: string | null;
    rarity?: string | null;
    icon_url?: string | null;
    icon_variants?: Partial<Record<TexturePack, string>>;
    lore?: string[];
    lore_colored?: string[];
  };

  type CatalogWeapon = {
    id: string;
    name?: string | null;
  };

  // Reactive data
  $: weaponCandidates = (summary?.weapon_candidates ?? []) as WeaponCandidate[];
  $: weaponCatalog = (summary?.weapon_catalog ?? []) as CatalogWeapon[];
  $: inventory = summary?.inventory;
  $: playerInventory = inventory?.player_inventory ?? [];
  
  // Get detailed weapon info from inventory
  $: weaponsWithDetails = weaponCandidates.map((candidate) => {
    const inventoryItem = playerInventory.find(
      (item) => item && item.slot === candidate.slot
    );
    return {
      ...candidate,
      icon_url: inventoryItem?.icon_url ?? null,
      icon_variants: inventoryItem?.icon_variants ?? {},
      lore: inventoryItem?.lore ?? [],
      lore_colored: inventoryItem?.lore_colored ?? [],
      leather_color: inventoryItem?.leather_color ?? null
    };
  });

  // Filter and sort
  $: filteredWeapons = weaponsWithDetails
    .filter((w) => {
      if (filterRarity !== 'all' && w.rarity?.toLowerCase() !== filterRarity) {
        return false;
      }
      if (searchQuery) {
        const query = searchQuery.toLowerCase();
        const matchName = w.name?.toLowerCase().includes(query);
        const matchId = w.id.toLowerCase().includes(query);
        return matchName || matchId;
      }
      return true;
    })
    .sort((a, b) => {
      if (sortBy === 'slot') {
        return a.slot - b.slot;
      }
      if (sortBy === 'name') {
        return (a.name ?? a.id).localeCompare(b.name ?? b.id);
      }
      if (sortBy === 'rarity') {
        const aRank = RARITY_ORDER.indexOf(a.rarity?.toLowerCase() as any) ?? -1;
        const bRank = RARITY_ORDER.indexOf(b.rarity?.toLowerCase() as any) ?? -1;
        return bRank - aRank;
      }
      return 0;
    });

  // Filtered catalog
  $: filteredCatalog = weaponCatalog.filter((w) => {
    if (!catalogSearch) return true;
    const query = catalogSearch.toLowerCase();
    return (
      w.id.toLowerCase().includes(query) ||
      w.name?.toLowerCase().includes(query)
    );
  });

  // Available rarities for filter
  $: availableRarities = [
    ...new Set(
      weaponCandidates
        .map((w) => w.rarity?.toLowerCase())
        .filter(Boolean)
    )
  ].sort((a, b) => {
    const aRank = RARITY_ORDER.indexOf(a as any) ?? -1;
    const bRank = RARITY_ORDER.indexOf(b as any) ?? -1;
    return aRank - bRank;
  });

  // Current selection sync
  $: if (summary) {
    if (summary.weapon_selected_slot !== undefined) {
      selectedWeaponSlot = summary.weapon_selected_slot;
    }
    if (summary.weapon_selected_id !== undefined) {
      selectedWeaponId = summary.weapon_selected_id ?? null;
    }
  }

  // Helpers
  function rarityClass(rarity?: string | null) {
    if (!rarity) return '';
    return `rarity-${rarity.toLowerCase().replace(/\s+/g, '-')}`;
  }

  function rarityLabel(rarity?: string | null) {
    if (!rarity) return 'Unknown';
    return rarity
      .split('_')
      .map((s) => s.charAt(0).toUpperCase() + s.slice(1).toLowerCase())
      .join(' ');
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
    weapon: WeaponCandidate,
    pack?: TexturePack
  ): { url: string; source: IconSource } | null {
    const variants = weapon.icon_variants ?? {};
    if (pack && variants[pack]) {
      return { url: variants[pack]!, source: pack };
    }
    for (const fallback of TEXTURE_PACK_ORDER) {
      const candidate = variants[fallback];
      if (candidate) {
        return { url: candidate, source: fallback };
      }
    }
    if (weapon.icon_url) {
      return { url: weapon.icon_url, source: 'legacy' };
    }
    return null;
  }

  function getIconUrl(weapon: WeaponCandidate): string | null {
    const picked = pickIconVariant(weapon, $texturePackStore);
    return picked?.url ?? null;
  }

  // Weapon selection
  function selectWeapon(weapon: WeaponCandidate) {
    selectedWeaponSlot = weapon.slot;
    selectedWeaponId = null;
    dispatch('weaponchange', { slot: weapon.slot, id: null });
  }

  function selectWeaponById(id: string) {
    selectedWeaponSlot = null;
    selectedWeaponId = id;
    dispatch('weaponchange', { slot: null, id });
  }

  function clearSelection() {
    selectedWeaponSlot = null;
    selectedWeaponId = null;
    dispatch('weaponchange', { slot: null, id: null });
  }

  function isSelected(weapon: WeaponCandidate): boolean {
    if (selectedWeaponId) {
      return weapon.id === selectedWeaponId;
    }
    if (selectedWeaponSlot !== null) {
      return weapon.slot === selectedWeaponSlot;
    }
    return false;
  }

  // Parse stat from lore
  function parseWeaponStats(lore: string[]): { label: string; value: string }[] {
    const stats: { label: string; value: string }[] = [];
    const statPattern = /^([A-Za-z\s]+):\s*\+?([\d,.]+%?)$/;
    
    for (const line of lore) {
      const cleanLine = line.replace(/§[0-9a-fklmnor]/gi, '');
      const match = cleanLine.match(statPattern);
      if (match) {
        stats.push({
          label: match[1].trim(),
          value: match[2]
        });
      }
    }
    return stats;
  }
</script>

<div class="weapons-container">
  <!-- Header -->
  <div class="section-header">
    <div class="title-group">
      <h2>Weapons</h2>
      <span class="count-badge">{weaponCandidates.length} in hotbar</span>
    </div>
    <p class="subtitle">
      View and select weapons from your hotbar. The selected weapon affects your stat calculations.
    </p>
  </div>

  <!-- Controls -->
  <div class="controls-bar">
    <div class="search-box">
      <svg class="search-icon" viewBox="0 0 20 20" fill="currentColor">
        <path
          fill-rule="evenodd"
          d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z"
          clip-rule="evenodd"
        />
      </svg>
      <input
        type="text"
        placeholder="Search weapons..."
        bind:value={searchQuery}
        class="search-input"
      />
    </div>

    <div class="filter-controls">
      <select bind:value={filterRarity} class="filter-select">
        <option value="all">All Rarities</option>
        {#each availableRarities as rarity}
          <option value={rarity}>{rarityLabel(rarity)}</option>
        {/each}
      </select>

      <select bind:value={sortBy} class="filter-select">
        <option value="slot">Sort by Slot</option>
        <option value="name">Sort by Name</option>
        <option value="rarity">Sort by Rarity</option>
      </select>
    </div>

    <button class="catalog-toggle" on:click={() => (showCatalog = !showCatalog)}>
      {showCatalog ? 'Hide Catalog' : 'Weapon Catalog'}
    </button>
  </div>

  <!-- Current Selection -->
  {#if selectedWeaponSlot !== null || selectedWeaponId}
    <div class="current-selection" transition:slide={{ duration: 200 }}>
      <div class="selection-info">
        <span class="selection-label">Selected Weapon:</span>
        {#if selectedWeaponId}
          <span class="selection-value">{selectedWeaponId}</span>
          <span class="selection-source">(from catalog)</span>
        {:else if selectedWeaponSlot !== null}
          {#each weaponsWithDetails.filter((w) => w.slot === selectedWeaponSlot) as weapon}
            <span class="selection-value {rarityClass(weapon.rarity)}">{weapon.name ?? weapon.id}</span>
            <span class="selection-source">(slot {weapon.slot})</span>
          {/each}
        {/if}
      </div>
      <button class="clear-btn" on:click={clearSelection}>Clear Selection</button>
    </div>
  {/if}

  <!-- Weapon Catalog (Expandable) -->
  {#if showCatalog}
    <div class="catalog-section" transition:slide={{ duration: 200 }}>
      <div class="catalog-header">
        <h3>Weapon Catalog</h3>
        <p class="catalog-subtitle">Search and select any weapon for stat calculation (even if not in inventory)</p>
        <input
          type="text"
          placeholder="Search catalog..."
          bind:value={catalogSearch}
          class="catalog-search"
        />
      </div>
      <div class="catalog-grid">
        {#each filteredCatalog.slice(0, 50) as catalogWeapon (catalogWeapon.id)}
          <button
            class="catalog-item"
            class:selected={selectedWeaponId === catalogWeapon.id}
            on:click={() => selectWeaponById(catalogWeapon.id)}
          >
            <span class="catalog-name">{catalogWeapon.name ?? catalogWeapon.id}</span>
            <span class="catalog-id">{catalogWeapon.id}</span>
          </button>
        {/each}
        {#if filteredCatalog.length > 50}
          <div class="catalog-more">
            +{filteredCatalog.length - 50} more weapons...
          </div>
        {/if}
      </div>
    </div>
  {/if}

  <!-- Weapons Grid -->
  {#if filteredWeapons.length > 0}
    <div class="weapons-grid">
      {#each filteredWeapons as weapon (weapon.slot)}
        <button
          class="weapon-card {rarityClass(weapon.rarity)}"
          class:selected={isSelected(weapon)}
          on:click={() => selectWeapon(weapon)}
          on:mouseenter={() => (hoveredWeapon = weapon)}
          on:mouseleave={() => (hoveredWeapon = null)}
        >
          <div class="weapon-icon-wrapper" style={rarityToBackground(weapon.rarity)}>
            {#if getIconUrl(weapon)}
              <img
                src={getIconUrl(weapon)}
                alt={weapon.name ?? weapon.id}
                class="weapon-icon"
                loading="lazy"
                on:load={handleIconLoad}
                on:error={(e) => handleIconError(e, getIconUrl(weapon))}
              />
            {:else}
              <div class="weapon-placeholder">
                <svg viewBox="0 0 24 24" fill="currentColor">
                  <path d="M14.12 4l1.83 1.83 1.41-1.41L19.78 6.83l-1.41 1.41L20 9.88 14.12 4z" />
                  <path d="M12.71 5.71L5 13.41V19h5.59l7.71-7.71-5.59-5.58zM9.17 17H7v-2.17l5.29-5.29 2.17 2.17L9.17 17z" />
                </svg>
              </div>
            {/if}
            <span class="slot-badge">Slot {weapon.slot + 1}</span>
          </div>
          
          <div class="weapon-info">
            <h4 class="weapon-name">{weapon.name ?? weapon.id}</h4>
            <span class="weapon-rarity">{rarityLabel(weapon.rarity)}</span>
            <span class="weapon-id">{weapon.id}</span>
          </div>

          {#if isSelected(weapon)}
            <div class="selected-indicator">
              <svg viewBox="0 0 20 20" fill="currentColor">
                <path
                  fill-rule="evenodd"
                  d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                  clip-rule="evenodd"
                />
              </svg>
            </div>
          {/if}
        </button>
      {/each}
    </div>
  {:else if weaponCandidates.length === 0}
    <div class="empty-state">
      <svg class="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.12 4l1.83 1.83 1.41-1.41L19.78 6.83l-1.41 1.41L20 9.88 14.12 4z" />
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12.71 5.71L5 13.41V19h5.59l7.71-7.71-5.59-5.58z" />
      </svg>
      <h3>No Weapons Found</h3>
      <p>No weapons detected in your hotbar. Make sure you have weapons in your inventory hotbar slots.</p>
      {#if weaponCatalog.length > 0}
        <button class="catalog-btn" on:click={() => (showCatalog = true)}>
          Browse Weapon Catalog
        </button>
      {/if}
    </div>
  {:else}
    <div class="empty-state">
      <h3>No Matches</h3>
      <p>No weapons match your current filters. Try adjusting your search or filters.</p>
    </div>
  {/if}

  <!-- Weapon Detail Tooltip -->
  {#if hoveredWeapon && hoveredWeapon.lore && hoveredWeapon.lore.length > 0}
    <div class="weapon-tooltip" transition:fade={{ duration: 100 }}>
      <div class="tooltip-header {rarityClass(hoveredWeapon.rarity)}">
        {hoveredWeapon.name ?? hoveredWeapon.id}
      </div>
      <div class="tooltip-lore">
        {#each hoveredWeapon.lore_colored ?? hoveredWeapon.lore as line}
          <div class="lore-line">
            {#each parseLegacyText(line) as segment}
              <span class={legacySegmentClasses(segment)} style={legacySegmentStyle(segment)}>
                {segment.text}
              </span>
            {/each}
          </div>
        {/each}
      </div>
    </div>
  {/if}
</div>

<style>
  .weapons-container {
    display: flex;
    flex-direction: column;
    gap: 20px;
  }

  .section-header {
    margin-bottom: 8px;
  }

  .title-group {
    display: flex;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
  }

  .section-header h2 {
    font-size: 1.5rem;
    margin: 0;
    color: var(--theme-text-primary);
  }

  .count-badge {
    background: var(--theme-secondary-alpha-16);
    color: var(--theme-text-soft);
    padding: 4px 12px;
    border-radius: 999px;
    font-size: 0.8rem;
    font-weight: 500;
  }

  .subtitle {
    color: var(--theme-text-soft);
    margin: 8px 0 0;
    font-size: 0.9rem;
  }

  /* Controls */
  .controls-bar {
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
    align-items: center;
  }

  .search-box {
    position: relative;
    flex: 1;
    min-width: 200px;
  }

  .search-icon {
    position: absolute;
    left: 12px;
    top: 50%;
    transform: translateY(-50%);
    width: 18px;
    height: 18px;
    color: var(--theme-text-soft);
    pointer-events: none;
  }

  .search-input {
    width: 100%;
    padding: 10px 12px 10px 40px;
    border: 1px solid var(--theme-surface-border);
    border-radius: 10px;
    background: var(--theme-control-bg);
    color: var(--theme-text-primary);
    font-size: 0.9rem;
    transition: border-color 0.2s, box-shadow 0.2s;
  }

  .search-input:focus {
    outline: none;
    border-color: var(--theme-accent);
    box-shadow: 0 0 0 3px var(--theme-accent-alpha-20);
  }

  .filter-controls {
    display: flex;
    gap: 8px;
  }

  .filter-select {
    padding: 10px 14px;
    border: 1px solid var(--theme-surface-border);
    border-radius: 10px;
    background: var(--theme-control-bg);
    color: var(--theme-text-primary);
    font-size: 0.85rem;
    cursor: pointer;
    transition: border-color 0.2s;
  }

  .filter-select:hover {
    border-color: var(--theme-accent);
  }

  .catalog-toggle {
    padding: 10px 18px;
    border: 1px solid var(--theme-accent);
    border-radius: 10px;
    background: transparent;
    color: var(--theme-accent);
    font-weight: 600;
    font-size: 0.85rem;
    cursor: pointer;
    transition: background 0.2s, color 0.2s;
  }

  .catalog-toggle:hover {
    background: var(--theme-accent);
    color: white;
  }

  /* Current Selection */
  .current-selection {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    padding: 12px 16px;
    background: var(--theme-accent-alpha-10);
    border: 1px solid var(--theme-accent-alpha-30);
    border-radius: 12px;
    flex-wrap: wrap;
  }

  .selection-info {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
  }

  .selection-label {
    color: var(--theme-text-soft);
    font-size: 0.9rem;
  }

  .selection-value {
    font-weight: 600;
    color: var(--theme-text-primary);
  }

  .selection-source {
    color: var(--theme-text-soft);
    font-size: 0.8rem;
  }

  .clear-btn {
    padding: 6px 14px;
    border: 1px solid var(--theme-surface-border);
    border-radius: 8px;
    background: var(--theme-control-bg);
    color: var(--theme-text-secondary);
    font-size: 0.8rem;
    cursor: pointer;
    transition: background 0.2s;
  }

  .clear-btn:hover {
    background: var(--theme-control-hover);
  }

  /* Catalog Section */
  .catalog-section {
    background: var(--theme-surface);
    border: 1px solid var(--theme-surface-border);
    border-radius: 16px;
    padding: 20px;
  }

  .catalog-header {
    margin-bottom: 16px;
  }

  .catalog-header h3 {
    margin: 0 0 4px;
    font-size: 1.1rem;
    color: var(--theme-text-primary);
  }

  .catalog-subtitle {
    margin: 0 0 12px;
    color: var(--theme-text-soft);
    font-size: 0.85rem;
  }

  .catalog-search {
    width: 100%;
    max-width: 400px;
    padding: 8px 14px;
    border: 1px solid var(--theme-surface-border);
    border-radius: 8px;
    background: var(--theme-control-bg);
    color: var(--theme-text-primary);
    font-size: 0.85rem;
  }

  .catalog-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 8px;
    max-height: 300px;
    overflow-y: auto;
    padding-right: 8px;
  }

  .catalog-item {
    display: flex;
    flex-direction: column;
    gap: 2px;
    padding: 10px 14px;
    border: 1px solid var(--theme-surface-border);
    border-radius: 8px;
    background: var(--theme-control-bg);
    cursor: pointer;
    text-align: left;
    transition: background 0.2s, border-color 0.2s, transform 0.15s;
  }

  .catalog-item:hover {
    background: var(--theme-control-hover);
    transform: translateY(-1px);
  }

  .catalog-item.selected {
    border-color: var(--theme-accent);
    background: var(--theme-accent-alpha-10);
  }

  .catalog-name {
    font-weight: 500;
    color: var(--theme-text-primary);
    font-size: 0.85rem;
  }

  .catalog-id {
    color: var(--theme-text-soft);
    font-size: 0.7rem;
    font-family: monospace;
  }

  .catalog-more {
    padding: 10px 14px;
    color: var(--theme-text-soft);
    font-size: 0.85rem;
    font-style: italic;
  }

  /* Weapons Grid */
  .weapons-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
    gap: 16px;
  }

  .weapon-card {
    position: relative;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 12px;
    padding: 16px;
    background: var(--theme-surface);
    border: 2px solid var(--theme-surface-border);
    border-radius: 16px;
    cursor: pointer;
    transition: transform 0.2s, border-color 0.2s, box-shadow 0.2s;
    text-align: center;
  }

  .weapon-card:hover {
    transform: translateY(-4px);
    box-shadow: var(--neu-elevated);
  }

  .weapon-card.selected {
    border-color: var(--theme-accent);
    box-shadow: 0 0 0 3px var(--theme-accent-alpha-30);
  }

  /* Rarity colors */
  .weapon-card.rarity-common { border-color: #9ca3af; }
  .weapon-card.rarity-uncommon { border-color: #22c55e; }
  .weapon-card.rarity-rare { border-color: #3b82f6; }
  .weapon-card.rarity-epic { border-color: #a855f7; }
  .weapon-card.rarity-legendary { border-color: #f97316; }
  .weapon-card.rarity-mythic { border-color: #ec4899; }
  .weapon-card.rarity-divine { border-color: #06b6d4; }
  .weapon-card.rarity-supreme { border-color: #14b8a6; }
  .weapon-card.rarity-special { border-color: #ef4444; }

  .weapon-icon-wrapper {
    position: relative;
    width: 64px;
    height: 64px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 12px;
    background: var(--theme-secondary-alpha-16);
    overflow: hidden;
  }

  .weapon-icon {
    width: 48px;
    height: 48px;
    object-fit: contain;
    image-rendering: pixelated;
  }

  .weapon-placeholder {
    width: 32px;
    height: 32px;
    color: var(--theme-text-soft);
    opacity: 0.5;
  }

  .slot-badge {
    position: absolute;
    bottom: -4px;
    right: -4px;
    background: var(--theme-surface);
    border: 1px solid var(--theme-surface-border);
    padding: 2px 6px;
    border-radius: 6px;
    font-size: 0.65rem;
    color: var(--theme-text-soft);
    font-weight: 500;
  }

  .weapon-info {
    display: flex;
    flex-direction: column;
    gap: 4px;
    width: 100%;
  }

  .weapon-name {
    margin: 0;
    font-size: 0.9rem;
    font-weight: 600;
    color: var(--theme-text-primary);
    line-height: 1.2;
    word-break: break-word;
  }

  .weapon-rarity {
    font-size: 0.75rem;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .rarity-common .weapon-rarity { color: #9ca3af; }
  .rarity-uncommon .weapon-rarity { color: #22c55e; }
  .rarity-rare .weapon-rarity { color: #3b82f6; }
  .rarity-epic .weapon-rarity { color: #a855f7; }
  .rarity-legendary .weapon-rarity { color: #f97316; }
  .rarity-mythic .weapon-rarity { color: #ec4899; }
  .rarity-divine .weapon-rarity { color: #06b6d4; }

  .weapon-id {
    font-size: 0.65rem;
    color: var(--theme-text-soft);
    font-family: monospace;
    opacity: 0.7;
  }

  .selected-indicator {
    position: absolute;
    top: 8px;
    right: 8px;
    width: 24px;
    height: 24px;
    background: var(--theme-accent);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
  }

  .selected-indicator svg {
    width: 14px;
    height: 14px;
  }

  /* Empty State */
  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 60px 20px;
    text-align: center;
    color: var(--theme-text-soft);
  }

  .empty-icon {
    width: 64px;
    height: 64px;
    margin-bottom: 16px;
    opacity: 0.4;
  }

  .empty-state h3 {
    margin: 0 0 8px;
    color: var(--theme-text-primary);
  }

  .empty-state p {
    margin: 0 0 20px;
    max-width: 400px;
  }

  .catalog-btn {
    padding: 10px 20px;
    background: var(--theme-accent);
    border: none;
    border-radius: 10px;
    color: white;
    font-weight: 600;
    cursor: pointer;
    transition: transform 0.2s, box-shadow 0.2s;
  }

  .catalog-btn:hover {
    transform: translateY(-2px);
    box-shadow: var(--neu-elevated);
  }

  /* Tooltip */
  .weapon-tooltip {
    position: fixed;
    bottom: 20px;
    right: 20px;
    max-width: 350px;
    background: rgba(15, 23, 42, 0.98);
    border: 1px solid var(--theme-surface-border);
    border-radius: 12px;
    box-shadow: var(--neu-elevated);
    z-index: 1000;
    overflow: hidden;
  }

  .tooltip-header {
    padding: 10px 14px;
    font-weight: 600;
    border-bottom: 1px solid var(--theme-surface-border);
  }

  .tooltip-header.rarity-common { color: #9ca3af; }
  .tooltip-header.rarity-uncommon { color: #22c55e; }
  .tooltip-header.rarity-rare { color: #3b82f6; }
  .tooltip-header.rarity-epic { color: #a855f7; }
  .tooltip-header.rarity-legendary { color: #f97316; }
  .tooltip-header.rarity-mythic { color: #ec4899; }

  .tooltip-lore {
    padding: 10px 14px;
    font-size: 0.8rem;
    max-height: 300px;
    overflow-y: auto;
  }

  .lore-line {
    line-height: 1.4;
    min-height: 1.1em;
  }

  .lore-line:empty::after {
    content: '\00a0';
  }

  /* Minecraft text styles */
  :global(.mc-span) {
    white-space: pre-wrap;
  }

  :global(.mc-bold) {
    font-weight: bold;
  }

  :global(.mc-italic) {
    font-style: italic;
  }

  :global(.mc-obfuscated) {
    animation: obfuscate 0.2s steps(3) infinite;
  }

  @keyframes obfuscate {
    0% { opacity: 0.9; }
    50% { opacity: 0.6; }
    100% { opacity: 0.9; }
  }

  /* Responsive */
  @media (max-width: 768px) {
    .controls-bar {
      flex-direction: column;
      align-items: stretch;
    }

    .search-box {
      min-width: 100%;
    }

    .filter-controls {
      flex-wrap: wrap;
    }

    .weapons-grid {
      grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
      gap: 12px;
    }

    .weapon-card {
      padding: 12px;
    }

    .weapon-icon-wrapper {
      width: 48px;
      height: 48px;
    }

    .weapon-icon {
      width: 36px;
      height: 36px;
    }

    .weapon-tooltip {
      left: 10px;
      right: 10px;
      bottom: 10px;
      max-width: none;
    }
  }
</style>
