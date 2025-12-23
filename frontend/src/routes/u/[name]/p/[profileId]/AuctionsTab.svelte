<script lang="ts">
  import { onMount } from 'svelte';
  import { get } from '$lib/api';
  import { formatNumber, formatLargeNumber } from '$lib/utils';
  import { rarityToBackground, parseLegacyText, type LegacySegment } from '$lib/utils/wardrobe';
  import { texturePackStore } from '$lib/stores/texturePack';
  import type { TexturePack } from '$lib/stores/texturePack';
  import type { Player } from './profileTypes';

  export let player: Player;

  type AuctionItem = {
    uuid: string;
    auctioneer: string;
    profile_id: string;
    coop: string[];
    start: number;
    end: number;
    item_name: string;
    item_lore: string;
    extra: string;
    category: string;
    tier: string;
    starting_bid: number;
    item_bytes: string;
    claimed: boolean;
    claimed_bidders: string[];
    highest_bid_amount: number;
    last_updated: number;
    bin: boolean;
    bids: {
      auction_id: string;
      bidder: string;
      profile_id: string;
      amount: number;
      timestamp: number;
    }[];
    item_uuid?: string;
    // Enriched fields from backend
    skyblock_id?: string;
    mc_id?: string;
    icon_url?: string | null;
    icon_variants?: Partial<Record<TexturePack, string>>;
    leather_color?: string | null;
    lore?: string[];
    lore_colored?: string[];
  };

  type AuctionsResponse = {
    auctions: AuctionItem[];
    error?: string;
    detail?: string;
  };

  let auctions: AuctionItem[] = [];
  let loading = true;
  let error = '';
  let now = Date.now();
  
  // Players to hide auctions for (privacy/testing)
  const HIDDEN_AUCTION_PLAYERS = ['mebosa'];
  $: isHiddenPlayer = HIDDEN_AUCTION_PLAYERS.some(
    (name) => player.name?.toLowerCase() === name.toLowerCase()
  );

  const TEXTURE_PACK_ORDER: TexturePack[] = ['furfsky', 'vanilla'];

  const RARITY_ORDER = [
    'DIVINE',
    'SUPREME',
    'MYTHIC',
    'LEGENDARY',
    'EPIC',
    'RARE',
    'UNCOMMON',
    'COMMON',
    'SPECIAL',
    'VERY_SPECIAL'
  ] as const;

  const rarityPriority = new Map<string, number>(
    RARITY_ORDER.map((value, index) => [value, index])
  );

  function normalizeRarity(value?: string | null) {
    if (!value) return '';
    return value.replace(/[_-]+/g, ' ').replace(/\s+/g, ' ').trim().toUpperCase();
  }

  function getRarityBackground(rarity?: string | null) {
    const normalized = normalizeRarity(rarity);
    return rarityToBackground(normalized) || 'rgba(120, 137, 255, 0.18)';
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

  function getIconUrl(auction: AuctionItem, pack: TexturePack): string | null {
    if (!auction.icon_variants) {
      return auction.icon_url || null;
    }
    // Try the selected pack first, then fallback through the order
    if (auction.icon_variants[pack]) {
      return auction.icon_variants[pack] || null;
    }
    for (const fallbackPack of TEXTURE_PACK_ORDER) {
      if (auction.icon_variants[fallbackPack]) {
        return auction.icon_variants[fallbackPack] || null;
      }
    }
    return auction.icon_url || null;
  }

  function handleIconError(event: Event, auction: AuctionItem, currentPack: TexturePack) {
    const target = event.currentTarget as HTMLImageElement | null;
    if (!target) return;
    
    // Try fallback to other texture packs
    const fallbackOrder = TEXTURE_PACK_ORDER.filter((p) => p !== currentPack);
    for (const pack of fallbackOrder) {
      const fallbackUrl = auction.icon_variants?.[pack];
      if (fallbackUrl && target.src !== fallbackUrl) {
        target.src = fallbackUrl;
        return;
      }
    }
    
    // Hide the image if all fallbacks fail
    target.style.display = 'none';
  }

  function formatTimeRemaining(endTime: number): string {
    const remaining = endTime - now;
    if (remaining <= 0) return 'Ended';
    
    const seconds = Math.floor(remaining / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (days > 0) return `${days}d ${hours % 24}h`;
    if (hours > 0) return `${hours}h ${minutes % 60}m`;
    if (minutes > 0) return `${minutes}m ${seconds % 60}s`;
    return `${seconds}s`;
  }

  function getTimeRemainingClass(endTime: number): string {
    const remaining = endTime - now;
    if (remaining <= 0) return 'ended';
    if (remaining < 60 * 60 * 1000) return 'urgent'; // < 1 hour
    if (remaining < 24 * 60 * 60 * 1000) return 'soon'; // < 1 day
    return '';
  }

  function formatPrice(amount: number): string {
    return formatLargeNumber(amount);
  }

  function getCurrentPrice(auction: AuctionItem): number {
    if (auction.bin) {
      return auction.starting_bid;
    }
    return auction.highest_bid_amount || auction.starting_bid;
  }

  function getBidCount(auction: AuctionItem): number {
    return auction.bids?.length ?? 0;
  }

  function sortAuctions(items: AuctionItem[]): AuctionItem[] {
    return [...items].sort((a, b) => {
      // Active auctions first
      const aEnded = a.end < now;
      const bEnded = b.end < now;
      if (aEnded !== bEnded) return aEnded ? 1 : -1;

      // Then by end time (soonest first for active)
      if (!aEnded && !bEnded) {
        return a.end - b.end;
      }

      // For ended, most recent first
      return b.end - a.end;
    });
  }

  async function fetchAuctions(forceRefresh = false) {
    loading = true;
    error = '';
    try {
      const url = forceRefresh 
        ? `/api/hypixel/auctions/${encodeURIComponent(player.uuid)}?refresh=1`
        : `/api/hypixel/auctions/${encodeURIComponent(player.uuid)}`;
      const response = await get<AuctionsResponse>(url);
      if (response.error) {
        error = response.detail || response.error;
      } else {
        auctions = sortAuctions(response.auctions || []);
      }
    } catch (err) {
      error = `Failed to load auctions: ${(err as Error).message}`;
    } finally {
      loading = false;
    }
  }

  onMount(() => {
    // Skip fetching for hidden players
    if (isHiddenPlayer) {
      loading = false;
      return;
    }
    fetchAuctions();
    // Update time remaining every second
    const interval = setInterval(() => {
      now = Date.now();
    }, 1000);
    return () => clearInterval(interval);
  });

  $: currentPack = $texturePackStore;
  $: activeAuctions = auctions.filter((a) => a.end > now && !a.claimed);
  $: endedAuctions = auctions.filter((a) => a.end <= now || a.claimed);
</script>

<style>
  .auctions-tab {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }

  .section-title {
    font-size: 1.125rem;
    font-weight: 600;
    color: #fff;
    margin-bottom: 0.75rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .section-title .count {
    font-size: 0.875rem;
    color: #888;
    font-weight: 400;
  }

  .loading, .error, .empty {
    padding: 2rem;
    text-align: center;
    color: #888;
  }

  .error {
    color: #ff6b6b;
  }

  .auctions-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
    gap: 1rem;
  }

  .auction-card {
    background: rgba(30, 30, 40, 0.6);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 8px;
    padding: 1rem;
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    transition: border-color 0.2s;
  }

  .auction-card:hover {
    border-color: rgba(255, 255, 255, 0.15);
  }

  .auction-card.ended {
    opacity: 0.6;
  }

  .auction-header {
    display: flex;
    align-items: flex-start;
    gap: 0.75rem;
  }

  .item-icon {
    width: 48px;
    height: 48px;
    border-radius: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    overflow: hidden;
    position: relative;
  }

  .item-icon img {
    width: 100%;
    height: 100%;
    object-fit: contain;
    image-rendering: pixelated;
  }

  .item-icon .fallback-emoji {
    font-size: 1.5rem;
  }

  .skyblock-id {
    font-size: 0.7rem;
    color: #666;
    font-family: monospace;
    margin-top: 2px;
  }

  .item-info {
    flex: 1;
    min-width: 0;
  }

  .item-name {
    font-weight: 600;
    font-size: 0.95rem;
    color: #fff;
    word-break: break-word;
  }

  .item-tier {
    font-size: 0.75rem;
    color: #888;
    text-transform: capitalize;
  }

  .auction-type {
    display: inline-block;
    padding: 0.125rem 0.5rem;
    border-radius: 4px;
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
  }

  .auction-type.bin {
    background: rgba(255, 170, 0, 0.2);
    color: #ffaa00;
  }

  .auction-type.auction {
    background: rgba(100, 180, 255, 0.2);
    color: #64b4ff;
  }

  .auction-details {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .detail-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.875rem;
  }

  .detail-label {
    color: #888;
  }

  .detail-value {
    color: #fff;
    font-weight: 500;
  }

  .price {
    color: #ffd700;
    font-weight: 600;
  }

  .time-remaining {
    font-weight: 500;
  }

  .time-remaining.urgent {
    color: #ff6b6b;
  }

  .time-remaining.soon {
    color: #ffaa00;
  }

  .time-remaining.ended {
    color: #888;
  }

  .bids-count {
    color: #888;
    font-size: 0.8rem;
  }

  .lore-preview {
    font-size: 0.75rem;
    color: #aaa;
    max-height: 3.6em;
    overflow: hidden;
    line-height: 1.2;
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
  }

  .no-auctions {
    text-align: center;
    padding: 3rem 1rem;
    color: #666;
  }

  .no-auctions-icon {
    font-size: 3rem;
    margin-bottom: 1rem;
    opacity: 0.5;
  }

  .mc-span { display: inline; }
  .mc-bold { font-weight: bold; }
  .mc-italic { font-style: italic; }
  .mc-obfuscated { 
    animation: obfuscate 0.1s infinite;
    display: inline-block;
  }

  @keyframes obfuscate {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
  }

  .refresh-btn {
    background: rgba(120, 137, 255, 0.2);
    border: 1px solid rgba(120, 137, 255, 0.3);
    color: #fff;
    padding: 0.5rem 1rem;
    border-radius: 6px;
    cursor: pointer;
    font-size: 0.875rem;
    transition: all 0.2s;
    align-self: flex-start;
  }

  .refresh-btn:hover:not(:disabled) {
    background: rgba(120, 137, 255, 0.3);
  }

  .refresh-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .header-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 1rem;
  }
</style>

<section id="auctions" class="auctions-tab">
  {#if isHiddenPlayer}
    <!-- Hidden player: show empty state -->
    <div class="header-row">
      <h2 class="section-title">Auctions</h2>
    </div>
    <div class="no-auctions">
      <div class="no-auctions-icon">🔒</div>
      <p>Auction data not available</p>
    </div>
  {:else}
    <div class="header-row">
      <h2 class="section-title">
        Auctions
        {#if !loading}
          <span class="count">({auctions.length} total)</span>
        {/if}
      </h2>
      <button 
        class="refresh-btn" 
        on:click={() => fetchAuctions(true)} 
        disabled={loading}
      >
        {loading ? 'Loading...' : 'Refresh'}
      </button>
    </div>

    {#if loading}
      <div class="loading">Loading auctions...</div>
    {:else if error}
      <div class="error">{error}</div>
    {:else if auctions.length === 0}
      <div class="no-auctions">
        <div class="no-auctions-icon">🏷️</div>
        <p>No active auctions</p>
        <p style="font-size: 0.875rem; margin-top: 0.5rem;">
          This player doesn't have any items listed on the auction house.
        </p>
      </div>
  {:else}
    {#if activeAuctions.length > 0}
      <div>
        <h3 class="section-title">
          Active
          <span class="count">({activeAuctions.length})</span>
        </h3>
        <div class="auctions-grid">
          {#each activeAuctions as auction (auction.uuid)}
            {@const iconUrl = getIconUrl(auction, currentPack)}
            <div class="auction-card">
              <div class="auction-header">
                <div 
                  class="item-icon" 
                  style="background: {getRarityBackground(auction.tier)}"
                >
                  {#if iconUrl}
                    <img 
                      src={iconUrl} 
                      alt={auction.item_name}
                      on:error={(e) => handleIconError(e, auction, currentPack)}
                    />
                  {:else}
                    <span class="fallback-emoji">🏷️</span>
                  {/if}
                </div>
                <div class="item-info">
                  <div class="item-name">{auction.item_name}</div>
                  <div class="item-tier">
                    {auction.tier?.toLowerCase() ?? 'Unknown'}
                    {#if auction.category}
                      • {auction.category}
                    {/if}
                  </div>
                  {#if auction.skyblock_id}
                    <div class="skyblock-id">{auction.skyblock_id}</div>
                  {/if}
                </div>
                <span class="auction-type {auction.bin ? 'bin' : 'auction'}">
                  {auction.bin ? 'BIN' : 'Auction'}
                </span>
              </div>

              <div class="auction-details">
                <div class="detail-row">
                  <span class="detail-label">
                    {auction.bin ? 'Price' : 'Current Bid'}
                  </span>
                  <span class="detail-value price">
                    {formatPrice(getCurrentPrice(auction))} coins
                  </span>
                </div>

                {#if !auction.bin}
                  <div class="detail-row">
                    <span class="detail-label">Bids</span>
                    <span class="detail-value bids-count">
                      {getBidCount(auction)}
                    </span>
                  </div>
                {/if}

                <div class="detail-row">
                  <span class="detail-label">Time Left</span>
                  <span 
                    class="detail-value time-remaining {getTimeRemainingClass(auction.end)}"
                  >
                    {formatTimeRemaining(auction.end)}
                  </span>
                </div>
              </div>

              {#if auction.lore && auction.lore.length > 0}
                <div class="lore-preview">
                  {auction.lore.slice(0, 3).join(' ')}
                </div>
              {:else if auction.extra}
                <div class="lore-preview">{auction.extra}</div>
              {/if}
            </div>
          {/each}
        </div>
      </div>
    {/if}
  {/if}
  {/if}
</section>
