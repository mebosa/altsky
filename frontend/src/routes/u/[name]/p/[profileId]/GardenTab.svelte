<script lang="ts">
  import { formatNumber } from '$lib/utils';
  import type { GardenData } from './profileTypes';

  export let garden: GardenData;

  const CROP_ICONS: Record<string, string> = {
    'WHEAT': '/api/vanilla/item/wheat.png',
    'CARROT_ITEM': '/api/vanilla/item/carrot.png',
    'POTATO_ITEM': '/api/vanilla/item/potato.png',
    'PUMPKIN': '/api/vanilla/item/pumpkin.png',
    'MELON': '/api/vanilla/item/melon_slice.png',
    'MUSHROOM_COLLECTION': '/api/vanilla/item/red_mushroom.png',
    'CACTUS': '/api/vanilla/item/cactus.png',
    'SUGAR_CANE': '/api/vanilla/item/sugar_cane.png',
    'NETHER_STALK': '/api/vanilla/item/nether_wart.png',
    'INK_SACK:3': '/api/vanilla/item/cocoa_beans.png',
  };

  function getCropIcon(crop: string): string {
    return CROP_ICONS[crop] || '/api/vanilla/item/barrier.png';
  }

  function formatCropName(crop: string): string {
    return crop.replace(/_/g, ' ').replace('ITEM', '').replace('COLLECTION', '').replace('INK SACK:3', 'COCOA BEANS').trim();
  }

  // Calculate total medals
  $: totalMedals = garden.medals.gold + garden.medals.silver + garden.medals.bronze;
  $: totalUniqueGolds = garden.unique_golds.length;
</script>

<div class="garden-container">
  <!-- Overview Section -->
  <div class="overview-section">
    <h2>🌱 Garden Overview</h2>
    <div class="stats-row">
      <div class="stat-card featured">
        <div class="stat-icon">🌾</div>
        <div class="stat-content">
          <div class="stat-value">{garden.level}</div>
          <div class="stat-label">Garden Level</div>
          <div class="stat-sub">{formatNumber(garden.xp)} XP</div>
        </div>
      </div>

      <div class="stat-card copper">
        <div class="stat-icon">🪙</div>
        <div class="stat-content">
          <div class="stat-value">{formatNumber(garden.copper)}</div>
          <div class="stat-label">Copper</div>
          <div class="stat-sub">Garden currency</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon">👥</div>
        <div class="stat-content">
          <div class="stat-value">{formatNumber(garden.visitors_served)}</div>
          <div class="stat-label">Visitors Served</div>
          <div class="stat-sub">Lifetime visitors</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon">🏅</div>
        <div class="stat-content">
          <div class="stat-value">{formatNumber(totalMedals)}</div>
          <div class="stat-label">Total Medals</div>
          <div class="stat-sub">{totalUniqueGolds}/10 unique golds</div>
        </div>
      </div>
    </div>
  </div>

  <!-- Medals & Perks Row -->
  <div class="cards-row">
    <!-- Jacob's Medals Card -->
    <div class="card medals-card">
      <div class="card-header">
        <div class="card-icon medals">
          <img src="/api/vanilla/item/gold_ingot.png" alt="Medals" class="icon-img" />
        </div>
        <div class="card-title">
          <h3>Jacob's Medals</h3>
          <span class="card-subtitle">Contest rewards</span>
        </div>
      </div>
      <div class="medals-grid">
        <div class="medal-item gold">
          <div class="medal-icon">🥇</div>
          <div class="medal-info">
            <span class="medal-count">{garden.medals.gold}</span>
            <span class="medal-label">Gold</span>
          </div>
          <div class="medal-unique">{garden.unique_golds.length} unique</div>
        </div>
        <div class="medal-item silver">
          <div class="medal-icon">🥈</div>
          <div class="medal-info">
            <span class="medal-count">{garden.medals.silver}</span>
            <span class="medal-label">Silver</span>
          </div>
          <div class="medal-unique">{garden.unique_silvers.length} unique</div>
        </div>
        <div class="medal-item bronze">
          <div class="medal-icon">🥉</div>
          <div class="medal-info">
            <span class="medal-count">{garden.medals.bronze}</span>
            <span class="medal-label">Bronze</span>
          </div>
          <div class="medal-unique">{garden.unique_bronzes.length} unique</div>
        </div>
      </div>
    </div>

    <!-- Perks Card -->
    <div class="card perks-card">
      <div class="card-header">
        <div class="card-icon perks">
          <img src="/api/vanilla/item/emerald.png" alt="Perks" class="icon-img" />
        </div>
        <div class="card-title">
          <h3>Garden Perks</h3>
          <span class="card-subtitle">Unlocked bonuses</span>
        </div>
      </div>
      <div class="perks-list">
        <div class="perk-item">
          <div class="perk-header">
            <span class="perk-icon">🍀</span>
            <span class="perk-name">Double Drops</span>
          </div>
          <div class="perk-value-wrap">
            <span class="perk-value">{garden.perks.double_drops || 0}%</span>
          </div>
          <div class="perk-bar">
            <div class="perk-progress" style="width: {Math.min(100, garden.perks.double_drops || 0)}%"></div>
          </div>
        </div>
        <div class="perk-item">
          <div class="perk-header">
            <span class="perk-icon">⬆️</span>
            <span class="perk-name">Farming Level Cap</span>
          </div>
          <div class="perk-value-wrap">
            <span class="perk-value">+{garden.perks.farming_level_cap || 0}</span>
          </div>
          <div class="perk-bar">
            <div class="perk-progress" style="width: {((garden.perks.farming_level_cap || 0) / 10) * 100}%"></div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Contests Section -->
  <div class="contests-section">
    <div class="section-header">
      <div class="section-title">
        <span class="section-icon">📊</span>
        <h3>Recent Contests</h3>
      </div>
      <span class="contests-count">{garden.contests.length} total</span>
    </div>
    
    <div class="contests-table-wrap">
      <table class="contests-table">
        <thead>
          <tr>
            <th class="col-crop">Crop</th>
            <th class="col-collected">Collected</th>
            <th class="col-medal">Medal</th>
            <th class="col-position">Position</th>
            <th class="col-participants">Participants</th>
            <th class="col-top">Top %</th>
          </tr>
        </thead>
        <tbody>
          {#each garden.contests.slice(0, 20) as contest}
            <tr>
              <td class="col-crop">
                <div class="crop-cell">
                  <div class="crop-icon">
                    <img src={getCropIcon(contest.crop)} alt={contest.crop} class="crop-img" />
                  </div>
                  <span class="crop-name">{formatCropName(contest.crop)}</span>
                </div>
              </td>
              <td class="col-collected">
                <span class="value-num">{formatNumber(contest.collected)}</span>
              </td>
              <td class="col-medal">
                {#if contest.medal === 'gold'}
                  <span class="medal-badge gold">GOLD</span>
                {:else if contest.medal === 'silver'}
                  <span class="medal-badge silver">SILVER</span>
                {:else if contest.medal === 'bronze'}
                  <span class="medal-badge bronze">BRONZE</span>
                {:else}
                  <span class="medal-badge none">—</span>
                {/if}
              </td>
              <td class="col-position">
                {#if contest.position > 0}
                  <span class="value-num">#{formatNumber(contest.position)}</span>
                {:else}
                  <span class="value-dim">—</span>
                {/if}
              </td>
              <td class="col-participants">
                <span class="value-dim">{formatNumber(contest.participants)}</span>
              </td>
              <td class="col-top">
                {#if contest.participants > 0}
                  <span class="top-percent">{((contest.position / contest.participants) * 100).toFixed(1)}%</span>
                {:else}
                  <span class="value-dim">—</span>
                {/if}
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
    
    {#if garden.contests.length > 20}
      <div class="contests-footer">
        <span>Showing 20 of {garden.contests.length} contests</span>
      </div>
    {/if}
  </div>
</div>

<style>
  .garden-container {
    display: flex;
    flex-direction: column;
    gap: 24px;
  }

  /* Overview Section */
  .overview-section {
    display: flex;
    flex-direction: column;
    gap: 20px;
  }

  .overview-section h2 {
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--theme-text-primary);
    margin: 0;
  }

  .stats-row {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 16px;
  }

  .stat-card {
    display: flex;
    align-items: flex-start;
    gap: 16px;
    background: rgba(148, 163, 184, 0.06);
    border: 1px solid var(--theme-surface-border);
    border-radius: 16px;
    padding: 20px;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
  }

  .stat-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  }

  .stat-card.featured {
    background: linear-gradient(135deg, rgba(76, 175, 80, 0.12), rgba(76, 175, 80, 0.04));
    border-color: rgba(76, 175, 80, 0.3);
  }

  .stat-card.copper {
    background: linear-gradient(135deg, rgba(255, 193, 7, 0.12), rgba(255, 193, 7, 0.04));
    border-color: rgba(255, 193, 7, 0.3);
  }

  .stat-icon {
    font-size: 2rem;
    line-height: 1;
  }

  .stat-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .stat-value {
    font-size: 1.75rem;
    font-weight: 700;
    color: var(--theme-text-primary);
    line-height: 1;
  }

  .stat-label {
    font-size: 0.9rem;
    color: var(--theme-text-soft);
    font-weight: 500;
  }

  .stat-sub {
    font-size: 0.8rem;
    color: var(--theme-text-soft);
    opacity: 0.7;
  }

  /* Cards Row */
  .cards-row {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
    gap: 20px;
  }

  .card {
    background: var(--theme-surface);
    border: 1px solid var(--theme-surface-border);
    border-radius: 20px;
    padding: 24px;
    display: flex;
    flex-direction: column;
    gap: 20px;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
  }

  .card:hover {
    transform: translateY(-3px);
    box-shadow: 0 12px 32px rgba(0, 0, 0, 0.15);
  }

  .card-header {
    display: flex;
    align-items: center;
    gap: 14px;
  }

  .card-icon {
    width: 48px;
    height: 48px;
    border-radius: 14px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(148, 163, 184, 0.12);
  }

  .card-icon.medals {
    background: linear-gradient(135deg, rgba(255, 193, 7, 0.2), rgba(255, 152, 0, 0.1));
  }

  .card-icon.perks {
    background: linear-gradient(135deg, rgba(76, 175, 80, 0.2), rgba(56, 142, 60, 0.1));
  }

  .icon-img {
    width: 28px;
    height: 28px;
    image-rendering: pixelated;
  }

  .card-title h3 {
    font-size: 1.1rem;
    font-weight: 600;
    color: var(--theme-text-primary);
    margin: 0;
  }

  .card-subtitle {
    font-size: 0.8rem;
    color: var(--theme-text-soft);
  }

  /* Medals Grid */
  .medals-grid {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .medal-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 14px 16px;
    border-radius: 12px;
    background: rgba(148, 163, 184, 0.06);
    border-left: 4px solid transparent;
    transition: background 0.2s ease;
  }

  .medal-item:hover {
    background: rgba(148, 163, 184, 0.1);
  }

  .medal-item.gold {
    border-left-color: #ffd700;
    background: linear-gradient(90deg, rgba(255, 215, 0, 0.08), transparent);
  }

  .medal-item.silver {
    border-left-color: #c0c0c0;
    background: linear-gradient(90deg, rgba(192, 192, 192, 0.08), transparent);
  }

  .medal-item.bronze {
    border-left-color: #cd7f32;
    background: linear-gradient(90deg, rgba(205, 127, 50, 0.08), transparent);
  }

  .medal-icon {
    font-size: 1.5rem;
  }

  .medal-info {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .medal-count {
    font-size: 1.25rem;
    font-weight: 700;
    color: var(--theme-text-primary);
  }

  .medal-label {
    font-size: 0.8rem;
    color: var(--theme-text-soft);
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .medal-unique {
    font-size: 0.75rem;
    color: var(--theme-text-soft);
    padding: 4px 10px;
    background: rgba(148, 163, 184, 0.1);
    border-radius: 20px;
  }

  /* Perks List */
  .perks-list {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .perk-item {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .perk-header {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .perk-icon {
    font-size: 1rem;
  }

  .perk-name {
    font-size: 0.9rem;
    color: var(--theme-text-soft);
    font-weight: 500;
  }

  .perk-value-wrap {
    display: flex;
    justify-content: flex-end;
  }

  .perk-value {
    font-size: 1.25rem;
    font-weight: 700;
    color: #4caf50;
  }

  .perk-bar {
    height: 8px;
    background: rgba(148, 163, 184, 0.15);
    border-radius: 4px;
    overflow: hidden;
  }

  .perk-progress {
    height: 100%;
    background: linear-gradient(90deg, #4caf50, #81c784);
    border-radius: 4px;
    transition: width 0.4s ease;
  }

  /* Contests Section */
  .contests-section {
    background: var(--theme-surface);
    border: 1px solid var(--theme-surface-border);
    border-radius: 20px;
    overflow: hidden;
  }

  .section-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 20px 24px;
    border-bottom: 1px solid var(--theme-surface-border);
  }

  .section-title {
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .section-icon {
    font-size: 1.25rem;
  }

  .section-title h3 {
    font-size: 1.1rem;
    font-weight: 600;
    color: var(--theme-text-primary);
    margin: 0;
  }

  .contests-count {
    font-size: 0.85rem;
    color: var(--theme-text-soft);
    padding: 6px 12px;
    background: rgba(148, 163, 184, 0.1);
    border-radius: 20px;
  }

  .contests-table-wrap {
    overflow-x: auto;
  }

  .contests-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.9rem;
  }

  .contests-table thead {
    background: rgba(148, 163, 184, 0.06);
  }

  .contests-table th {
    padding: 14px 20px;
    text-align: left;
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--theme-text-soft);
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .contests-table th.col-collected,
  .contests-table th.col-position,
  .contests-table th.col-participants,
  .contests-table th.col-top {
    text-align: right;
  }

  .contests-table th.col-medal {
    text-align: center;
  }

  .contests-table tbody tr {
    border-bottom: 1px solid rgba(148, 163, 184, 0.08);
    transition: background 0.15s ease;
  }

  .contests-table tbody tr:hover {
    background: rgba(148, 163, 184, 0.06);
  }

  .contests-table td {
    padding: 14px 20px;
  }

  .contests-table td.col-collected,
  .contests-table td.col-position,
  .contests-table td.col-participants,
  .contests-table td.col-top {
    text-align: right;
  }

  .contests-table td.col-medal {
    text-align: center;
  }

  .crop-cell {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .crop-icon {
    width: 40px;
    height: 40px;
    border-radius: 10px;
    background: rgba(148, 163, 184, 0.1);
    display: flex;
    align-items: center;
    justify-content: center;
    border: 1px solid rgba(148, 163, 184, 0.15);
    transition: border-color 0.15s ease, background 0.15s ease;
  }

  tr:hover .crop-icon {
    border-color: rgba(148, 163, 184, 0.25);
    background: rgba(148, 163, 184, 0.15);
  }

  .crop-img {
    width: 24px;
    height: 24px;
    image-rendering: pixelated;
  }

  .crop-name {
    font-weight: 500;
    color: var(--theme-text-primary);
    text-transform: capitalize;
  }

  .value-num {
    font-family: var(--font-mono, monospace);
    color: var(--theme-text-primary);
    font-weight: 500;
  }

  .value-dim {
    color: var(--theme-text-soft);
    opacity: 0.6;
  }

  .top-percent {
    font-family: var(--font-mono, monospace);
    color: var(--theme-text-secondary);
    font-weight: 500;
  }

  .medal-badge {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 4px 10px;
    border-radius: 20px;
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.03em;
  }

  .medal-badge.gold {
    background: rgba(255, 215, 0, 0.15);
    color: #ffd700;
    border: 1px solid rgba(255, 215, 0, 0.25);
  }

  .medal-badge.silver {
    background: rgba(192, 192, 192, 0.15);
    color: #c0c0c0;
    border: 1px solid rgba(192, 192, 192, 0.25);
  }

  .medal-badge.bronze {
    background: rgba(205, 127, 50, 0.15);
    color: #cd7f32;
    border: 1px solid rgba(205, 127, 50, 0.25);
  }

  .medal-badge.none {
    background: transparent;
    color: var(--theme-text-soft);
    opacity: 0.4;
  }

  .contests-footer {
    padding: 16px 24px;
    text-align: center;
    border-top: 1px solid var(--theme-surface-border);
    background: rgba(148, 163, 184, 0.03);
  }

  .contests-footer span {
    font-size: 0.85rem;
    color: var(--theme-text-soft);
  }

  /* Responsive */
  @media (max-width: 768px) {
    .stats-row {
      grid-template-columns: repeat(2, 1fr);
    }

    .cards-row {
      grid-template-columns: 1fr;
    }

    .contests-table th,
    .contests-table td {
      padding: 12px 14px;
    }

    .stat-card {
      padding: 16px;
    }

    .stat-value {
      font-size: 1.5rem;
    }
  }

  @media (max-width: 480px) {
    .stats-row {
      grid-template-columns: 1fr;
    }

    .crop-name {
      max-width: 80px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
  }
</style>
