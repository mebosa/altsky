<script lang="ts">
  import type { ProfileSummaryResponse, HOTMData } from './profileTypes';
  import {
    HOTM_PERKS,
    HOTM_TIERS,
    POWDER_COLORS,
    CRYSTALS,
    getTotalTokens,
    getHOTMProgress,
    getPerkStatus,
    formatPowder,
    type HOTMPerk
  } from './hotmConstants';
  import { formatNumber } from '$lib/utils';

  export let summary: ProfileSummaryResponse;

  $: hotm = summary.hotm as HOTMData | null;
  $: tier = hotm?.tier ?? 0;
  $: experience = hotm?.experience ?? 0;
  $: perks = hotm?.perks ?? {};
  $: powder = hotm?.powder ?? { mithril: 0, gemstone: 0, glacite: 0 };
  $: crystals = hotm?.crystals ?? {};
  $: selectedAbility = hotm?.selected_ability;

  // Calculate progress
  $: progress = getHOTMProgress(tier, experience);
  $: totalTokens = getTotalTokens(tier);
  $: tokensSpent = Object.entries(perks).reduce((sum, [id, level]) => {
    if (level > 0) return sum + 1;
    return sum;
  }, 0);

  // Build grid - 7 columns, 10 rows (tier 10 at top)
  const GRID_COLS = 7;
  const GRID_ROWS = 10;

  // Get all perks organized by position
  function getGridData(): (HOTMPerk & { level: number; status: string } | null)[][] {
    const grid: (HOTMPerk & { level: number; status: string } | null)[][] = [];
    
    for (let row = 0; row < GRID_ROWS; row++) {
      const rowData: (HOTMPerk & { level: number; status: string } | null)[] = [];
      for (let col = 0; col < GRID_COLS; col++) {
        rowData.push(null);
      }
      grid.push(rowData);
    }

    // Place perks in grid
    for (const perk of Object.values(HOTM_PERKS)) {
      const gridRow = Math.floor((perk.position - 1) / 7);
      const gridCol = (perk.position - 1) % 7;
      
      if (gridRow >= 0 && gridRow < GRID_ROWS && gridCol >= 0 && gridCol < GRID_COLS) {
        const level = perks[perk.id] ?? 0;
        const status = getPerkStatus(perk, level, tier);
        grid[gridRow][gridCol] = { ...perk, level, status };
      }
    }

    return grid;
  }

  $: gridData = getGridData();

  // Get tier for each row (row 0 = tier 10, row 9 = tier 1)
  function getTierForRow(row: number): number {
    return HOTM_TIERS - row;
  }

  // Check if row is unlocked
  function isRowUnlocked(row: number): boolean {
    return getTierForRow(row) <= tier;
  }

  // Selected perk for details panel
  let selectedPerk: (HOTMPerk & { level: number; status: string }) | null = null;

  function selectPerk(perk: HOTMPerk & { level: number; status: string } | null) {
    if (perk) {
      selectedPerk = perk;
    }
  }
</script>

{#if !hotm || tier === 0}
  <div class="card empty-card">
    <div class="empty-icon">⛏️</div>
    <h3>No HOTM Data</h3>
    <p>This player hasn't unlocked Heart of the Mountain yet, or the data is not available.</p>
  </div>
{:else}
  <section class="hotm-section">
    <!-- HOTM Header Stats -->
    <div class="stats-grid">
      <!-- Tier -->
      <div class="card stat-card">
        <div class="stat-label">HOTM Tier</div>
        <div class="stat-value tier-value">
          {tier}
          <span class="stat-value-max">/ {HOTM_TIERS}</span>
        </div>
        {#if tier < HOTM_TIERS}
          <div class="progress-container">
            <div class="progress-text">
              {formatNumber(progress.current)} / {formatNumber(progress.next)} XP
            </div>
            <div class="progress">
              <div
                class="progress-bar tier-progress"
                style="width: {progress.progress}%"
              ></div>
            </div>
          </div>
        {:else}
          <div class="max-label">✧ Maximum Tier ✧</div>
        {/if}
      </div>

      <!-- Tokens -->
      <div class="card stat-card">
        <div class="stat-label">Tokens of the Mountain</div>
        <div class="stat-value tokens-value">
          {tokensSpent}
          <span class="stat-value-max">/ {totalTokens}</span>
        </div>
        <div class="stat-sublabel">
          {totalTokens - tokensSpent} available
        </div>
      </div>

      <!-- Mithril Powder -->
      <div class="card stat-card">
        <div class="stat-label">
          <span class="powder-icon mithril">᠅</span> Mithril Powder
        </div>
        <div class="stat-value mithril-value">
          {formatPowder(powder.mithril)}
        </div>
        {#if powder.mithril_total}
          <div class="stat-sublabel">
            Total: {formatPowder(powder.mithril_total)}
          </div>
        {/if}
      </div>

      <!-- Gemstone Powder -->
      <div class="card stat-card">
        <div class="stat-label">
          <span class="powder-icon gemstone">᠅</span> Gemstone Powder
        </div>
        <div class="stat-value gemstone-value">
          {formatPowder(powder.gemstone)}
        </div>
        {#if powder.gemstone_total}
          <div class="stat-sublabel">
            Total: {formatPowder(powder.gemstone_total)}
          </div>
        {/if}
      </div>
    </div>

    <!-- Glacite Powder (if available) -->
    {#if powder.glacite > 0 || (powder.glacite_total && powder.glacite_total > 0)}
      <div class="card stat-card glacite-card">
        <div class="stat-label">
          <span class="powder-icon glacite">᠅</span> Glacite Powder
        </div>
        <div class="stat-value glacite-value">
          {formatPowder(powder.glacite)}
        </div>
        {#if powder.glacite_total}
          <div class="stat-sublabel">
            Total: {formatPowder(powder.glacite_total)}
          </div>
        {/if}
      </div>
    {/if}

    <!-- Main Content Container -->
    <div class="main-container">
      <!-- HOTM Tree Grid -->
      <div class="card tree-card">
        <h3 class="card-title">
          <span class="title-icon">⛏️</span>
          Heart of the Mountain
        </h3>

        <!-- Legend -->
        <div class="legend">
          <div class="legend-item">
            <div class="legend-box unlocked"></div>
            <span>Unlocked</span>
          </div>
          <div class="legend-item">
            <div class="legend-box maxed"></div>
            <span>Maxed</span>
          </div>
          <div class="legend-item">
            <div class="legend-box ability"></div>
            <span>Ability</span>
          </div>
          <div class="legend-item">
            <div class="legend-box special"></div>
            <span>Special</span>
          </div>
          <div class="legend-item">
            <div class="legend-box locked"></div>
            <span>Locked</span>
          </div>
        </div>

        <!-- Grid -->
        <div class="tree-scroll">
          <div class="tree-grid">
            {#each gridData as row, rowIndex}
              {@const rowTier = getTierForRow(rowIndex)}
              {@const rowUnlocked = isRowUnlocked(rowIndex)}
              <div class="tree-row">
                <!-- Tier indicator -->
                <div class="tier-indicator {rowUnlocked ? 'unlocked' : 'locked'}">
                  {rowTier}
                </div>

                <!-- Perk cells -->
                <div class="perk-cells">
                  {#each row as perk, colIndex}
                    {#if perk}
                      <button
                        class="perk-cell {perk.status}"
                        on:click={() => selectPerk(perk)}
                        title={perk.name}
                        type="button"
                      >
                        {#if perk.isAbility}
                          <div class="perk-icon">🔮</div>
                        {:else if perk.isSpecial}
                          <div class="perk-icon">⭐</div>
                        {:else if perk.status === 'maxed'}
                          <div class="perk-level maxed">MAX</div>
                        {:else if perk.level > 0}
                          <div class="perk-level active">
                            {perk.level}/{perk.maxLevel}
                          </div>
                        {:else}
                          <div class="perk-level inactive">0</div>
                        {/if}
                      </button>
                    {:else}
                      <!-- Empty cell -->
                      <div class="perk-cell empty"></div>
                    {/if}
                  {/each}
                </div>
              </div>
            {/each}
          </div>
        </div>
      </div>

      <!-- Perk Details Panel -->
      <div class="card details-card">
        {#if selectedPerk}
          <div class="perk-details">
            <!-- Perk Name -->
            <h4 class="perk-name {selectedPerk.status}">
              {selectedPerk.name}
            </h4>
            {#if selectedPerk.maxLevel > 1}
              <div class="perk-level-text">
                Level {selectedPerk.level}/{selectedPerk.maxLevel}
              </div>
            {/if}

            <!-- Level Progress Bar -->
            {#if selectedPerk.maxLevel > 1}
              <div class="progress">
                <div
                  class="progress-bar {selectedPerk.status === 'maxed' ? 'maxed' : 'active'}"
                  style="width: {(selectedPerk.level / selectedPerk.maxLevel) * 100}%"
                ></div>
              </div>
            {/if}

            <!-- Perk Info -->
            <div class="perk-info">
              <div class="info-row">
                <span class="info-label">Required Tier:</span>
                <span class="info-value">{selectedPerk.tier}</span>
              </div>
              {#if selectedPerk.powderType}
                <div class="info-row">
                  <span class="info-label">Powder Type:</span>
                  <span class="info-value powder-type {selectedPerk.powderType}">
                    {selectedPerk.powderType.charAt(0).toUpperCase() + selectedPerk.powderType.slice(1)}
                  </span>
                </div>
              {/if}
              {#if selectedPerk.isAbility}
                <div class="ability-badge">⚡ Pickaxe Ability</div>
              {/if}
            </div>

            <!-- Effect -->
            <div class="effect-box">
              <div class="effect-label">Current Effect:</div>
              <div class="effect-text">
                {#if selectedPerk.level > 0}
                  {selectedPerk.description(selectedPerk.level)}
                {:else}
                  {selectedPerk.description(1)}
                  <span class="effect-preview">(at level 1)</span>
                {/if}
              </div>
            </div>

            <!-- Next Level Preview -->
            {#if selectedPerk.level > 0 && selectedPerk.level < selectedPerk.maxLevel}
              <div class="preview-box next-level">
                <div class="preview-label">Next Level ({selectedPerk.level + 1}):</div>
                <div class="preview-text">
                  {selectedPerk.description(selectedPerk.level + 1)}
                </div>
              </div>
            {/if}

            <!-- Max Level Preview -->
            {#if selectedPerk.status !== 'maxed' && selectedPerk.maxLevel > 1}
              <div class="preview-box max-level">
                <div class="preview-label">At Max Level ({selectedPerk.maxLevel}):</div>
                <div class="preview-text">
                  {selectedPerk.description(selectedPerk.maxLevel)}
                </div>
              </div>
            {/if}
          </div>
        {:else}
          <div class="no-selection">
            <div class="no-selection-icon">👆</div>
            <p>Click a perk to see details</p>
          </div>
        {/if}
      </div>
    </div>

    <!-- Crystal Hollows Crystals -->
    {#if crystals && Object.keys(crystals).length > 0}
      <div class="card crystals-card">
        <h3 class="card-title">
          <span class="title-icon">💎</span>
          Crystal Hollows Crystals
        </h3>
        <div class="crystals-grid">
          {#each Object.entries(CRYSTALS) as [crystalId, crystalData]}
            {@const crystal = crystals[crystalId]}
            {@const isPlaced = crystal?.state === 'FOUND'}
            <div class="crystal-item {isPlaced ? 'placed' : 'not-placed'}">
              <div
                class="crystal-icon"
                style="text-shadow: 0 0 10px {crystalData.color}"
              >
                💎
              </div>
              <div class="crystal-name" style="color: {crystalData.color}">
                {crystalData.name}
              </div>
              <div class="crystal-status">
                {isPlaced ? '✓ Placed' : 'Not found'}
              </div>
              {#if crystal?.total_placed}
                <div class="crystal-count">
                  {crystal.total_placed}x placed
                </div>
              {/if}
            </div>
          {/each}
        </div>
      </div>
    {/if}

    <!-- Perk Summary Table -->
    <div class="card table-card">
      <h3 class="card-title">All Perks Summary</h3>
      <div class="table-scroll">
        <table class="perks-table">
          <thead>
            <tr>
              <th>Perk</th>
              <th>Tier</th>
              <th>Level</th>
              <th>Type</th>
              <th>Effect</th>
            </tr>
          </thead>
          <tbody>
            {#each Object.values(HOTM_PERKS).sort((a, b) => b.tier - a.tier || a.position - b.position) as perk}
              {@const level = perks[perk.id] ?? 0}
              {@const status = getPerkStatus(perk, level, tier)}
              <tr class="{status === 'locked' ? 'locked' : ''}">
                <td class="perk-name-col {status}">
                  {perk.name}
                </td>
                <td>{perk.tier}</td>
                <td>
                  {#if perk.maxLevel > 1}
                    <span class="{status === 'maxed' ? 'maxed-text' : ''}">
                      {level}/{perk.maxLevel}
                    </span>
                  {:else}
                    <span class="{level > 0 ? 'check' : 'cross'}">
                      {level > 0 ? '✓' : '✗'}
                    </span>
                  {/if}
                </td>
                <td class="type-col">
                  {#if perk.powderType}
                    <span class="powder-type {perk.powderType}">
                      {perk.powderType}
                    </span>
                  {:else if perk.isAbility}
                    <span class="ability-text">ability</span>
                  {:else}
                    <span class="special-text">special</span>
                  {/if}
                </td>
                <td class="effect-col">
                  {#if level > 0}
                    {perk.effect(level)}
                  {:else}
                    <span class="effect-preview">{perk.effect(1)}</span>
                  {/if}
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    </div>
  </section>
{/if}

<style>
  .hotm-section {
    display: flex;
    flex-direction: column;
    gap: 20px;
  }

  .empty-card {
    padding: 60px 20px;
    text-align: center;
  }

  .empty-icon {
    font-size: 4rem;
    margin-bottom: 16px;
    opacity: 0.4;
  }

  .empty-card h3 {
    margin: 0 0 8px;
    color: var(--theme-text-primary);
  }

  .empty-card p {
    margin: 0;
    color: var(--theme-text-soft);
  }

  /* Stats Grid */
  .stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 16px;
  }

  .stat-card {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .stat-label {
    font-size: 0.85rem;
    color: var(--theme-text-soft);
    display: flex;
    align-items: center;
    gap: 4px;
  }

  .powder-icon {
    font-size: 1rem;
  }

  .powder-icon.mithril {
    color: #2ecc71;
  }

  .powder-icon.gemstone {
    color: #d946ef;
  }

  .powder-icon.glacite {
    color: #67e8f9;
  }

  .stat-value {
    font-size: 1.75rem;
    font-weight: 700;
  }

  .stat-value-max {
    font-size: 1.1rem;
    color: var(--theme-text-soft);
    font-weight: 400;
  }

  .tier-value {
    color: #a78bfa;
  }

  .tokens-value {
    color: #fbbf24;
  }

  .mithril-value {
    color: #2ecc71;
  }

  .gemstone-value {
    color: #d946ef;
  }

  .glacite-value {
    color: #67e8f9;
  }

  .stat-sublabel {
    font-size: 0.8rem;
    color: var(--theme-text-soft);
  }

  .progress-container {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .progress-text {
    font-size: 0.75rem;
    color: var(--theme-text-soft);
  }

  .progress {
    height: 8px;
    background: rgba(148, 163, 184, 0.24);
    border-radius: 999px;
    overflow: hidden;
  }

  .progress-bar {
    height: 100%;
    border-radius: 999px;
    transition: width 0.3s ease;
  }

  .tier-progress {
    background: linear-gradient(90deg, #9333ea, #a855f7);
  }

  .progress-bar.active {
    background: linear-gradient(90deg, #22c55e, #4ade80);
  }

  .progress-bar.maxed {
    background: linear-gradient(90deg, #a855f7, #c084fc);
  }

  .max-label {
    font-size: 0.8rem;
    color: #a78bfa;
  }

  .glacite-card {
    max-width: 300px;
  }

  /* Main Container */
  .main-container {
    display: grid;
    grid-template-columns: 1fr;
    gap: 20px;
  }

  @media (min-width: 1024px) {
    .main-container {
      grid-template-columns: 1fr 320px;
    }
  }

  .card-title {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 1.1rem;
    font-weight: 600;
    color: var(--theme-text-primary);
    margin: 0 0 16px;
  }

  .title-icon {
    font-size: 1.5rem;
  }

  /* Tree Card */
  .tree-card {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .legend {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    font-size: 0.8rem;
  }

  .legend-item {
    display: flex;
    align-items: center;
    gap: 4px;
    color: var(--theme-text-soft);
  }

  .legend-box {
    width: 12px;
    height: 12px;
    border-radius: 3px;
    border: 2px solid;
  }

  .legend-box.unlocked {
    background: rgba(34, 197, 94, 0.3);
    border-color: #22c55e;
  }

  .legend-box.maxed {
    background: rgba(168, 85, 247, 0.3);
    border-color: #a855f7;
  }

  .legend-box.ability {
    background: rgba(59, 130, 246, 0.3);
    border-color: #3b82f6;
  }

  .legend-box.special {
    background: rgba(251, 191, 36, 0.3);
    border-color: #fbbf24;
  }

  .legend-box.locked {
    background: rgba(71, 85, 105, 0.3);
    border-color: #475569;
  }

  .tree-scroll {
    overflow-x: auto;
  }

  .tree-grid {
    min-width: 500px;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .tree-row {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .tier-indicator {
    width: 40px;
    height: 40px;
    flex-shrink: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 8px;
    font-size: 0.9rem;
    font-weight: 700;
  }

  .tier-indicator.unlocked {
    background: linear-gradient(135deg, #9333ea, #7c3aed);
    color: #fff;
    box-shadow: 0 4px 12px rgba(147, 51, 234, 0.3);
  }

  .tier-indicator.locked {
    background: rgba(71, 85, 105, 0.3);
    color: var(--theme-text-soft);
  }

  .perk-cells {
    display: flex;
    gap: 6px;
    flex: 1;
  }

  .perk-cell {
    width: 52px;
    height: 52px;
    border-radius: 8px;
    border: 2px solid;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s ease;
    cursor: pointer;
    background: rgba(30, 41, 59, 0.6);
  }

  .perk-cell:not(.empty):hover {
    transform: scale(1.05);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  }

  .perk-cell.empty {
    border: 1px solid rgba(71, 85, 105, 0.3);
    background: rgba(15, 23, 42, 0.3);
    cursor: default;
  }

  .perk-cell.unlocked {
    background: rgba(34, 197, 94, 0.2);
    border-color: #22c55e;
    box-shadow: 0 0 10px rgba(34, 197, 94, 0.2);
  }

  .perk-cell.maxed {
    background: rgba(168, 85, 247, 0.2);
    border-color: #a855f7;
    box-shadow: 0 0 10px rgba(168, 85, 247, 0.2);
  }

  .perk-cell.ability {
    background: rgba(59, 130, 246, 0.2);
    border-color: #3b82f6;
    box-shadow: 0 0 10px rgba(59, 130, 246, 0.2);
  }

  .perk-cell.special {
    background: rgba(251, 191, 36, 0.2);
    border-color: #fbbf24;
    box-shadow: 0 0 10px rgba(251, 191, 36, 0.2);
  }

  .perk-cell.locked {
    background: rgba(71, 85, 105, 0.2);
    border-color: #475569;
    opacity: 0.6;
  }

  .perk-icon {
    font-size: 1.2rem;
  }

  .perk-level {
    font-size: 0.7rem;
    font-weight: 700;
    text-align: center;
  }

  .perk-level.maxed {
    color: #c084fc;
  }

  .perk-level.active {
    color: #4ade80;
  }

  .perk-level.inactive {
    color: var(--theme-text-soft);
  }

  /* Details Card */
  .details-card {
    display: flex;
    flex-direction: column;
  }

  .perk-details {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .perk-name {
    font-size: 1.1rem;
    font-weight: 600;
    margin: 0;
  }

  .perk-name.maxed {
    color: #a855f7;
  }

  .perk-name.unlocked {
    color: #22c55e;
  }

  .perk-name.ability {
    color: #3b82f6;
  }

  .perk-name.special {
    color: #fbbf24;
  }

  .perk-name.locked {
    color: var(--theme-text-soft);
  }

  .perk-level-text {
    font-size: 0.85rem;
    color: var(--theme-text-soft);
  }

  .perk-info {
    display: flex;
    flex-direction: column;
    gap: 8px;
    font-size: 0.85rem;
  }

  .info-row {
    display: flex;
    justify-content: space-between;
  }

  .info-label {
    color: var(--theme-text-soft);
  }

  .info-value {
    color: var(--theme-text-primary);
  }

  .powder-type.mithril {
    color: #2ecc71;
  }

  .powder-type.gemstone {
    color: #d946ef;
  }

  .powder-type.glacite {
    color: #67e8f9;
  }

  .ability-badge {
    background: rgba(59, 130, 246, 0.2);
    border: 1px solid rgba(59, 130, 246, 0.4);
    color: #3b82f6;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 0.75rem;
    text-align: center;
  }

  .effect-box {
    background: rgba(15, 23, 42, 0.8);
    padding: 12px;
    border-radius: 8px;
  }

  .effect-label {
    font-size: 0.75rem;
    color: var(--theme-text-soft);
    margin-bottom: 4px;
  }

  .effect-text {
    font-size: 0.85rem;
    color: var(--theme-text-primary);
  }

  .effect-preview {
    font-size: 0.75rem;
    color: var(--theme-text-soft);
  }

  .preview-box {
    padding: 12px;
    border-radius: 8px;
    border: 1px solid;
  }

  .preview-box.next-level {
    background: rgba(34, 197, 94, 0.1);
    border-color: rgba(34, 197, 94, 0.3);
  }

  .preview-box.max-level {
    background: rgba(168, 85, 247, 0.1);
    border-color: rgba(168, 85, 247, 0.3);
  }

  .preview-label {
    font-size: 0.75rem;
    margin-bottom: 4px;
  }

  .preview-box.next-level .preview-label {
    color: #22c55e;
  }

  .preview-box.max-level .preview-label {
    color: #a855f7;
  }

  .preview-text {
    font-size: 0.85rem;
    color: var(--theme-text-primary);
  }

  .no-selection {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 60px 20px;
    text-align: center;
    color: var(--theme-text-soft);
  }

  .no-selection-icon {
    font-size: 2.5rem;
    margin-bottom: 8px;
  }

  /* Crystals Card */
  .crystals-card {
  }

  .crystals-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
    gap: 12px;
  }

  .crystal-item {
    padding: 12px;
    border-radius: 8px;
    border: 1px solid;
    text-align: center;
  }

  .crystal-item.placed {
    background: rgba(71, 85, 105, 0.2);
    border-color: rgba(148, 163, 184, 0.3);
  }

  .crystal-item.not-placed {
    background: rgba(30, 41, 59, 0.3);
    border-color: rgba(71, 85, 105, 0.3);
    opacity: 0.5;
  }

  .crystal-icon {
    font-size: 1.8rem;
    margin-bottom: 4px;
  }

  .crystal-name {
    font-size: 0.8rem;
    font-weight: 500;
    margin-bottom: 4px;
  }

  .crystal-status {
    font-size: 0.7rem;
    color: var(--theme-text-soft);
  }

  .crystal-count {
    font-size: 0.7rem;
    color: var(--theme-text-soft);
    margin-top: 2px;
  }

  /* Table Card */
  .table-card {
  }

  .table-scroll {
    overflow-x: auto;
  }

  .perks-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.85rem;
  }

  .perks-table th {
    text-align: left;
    padding: 8px 12px;
    border-bottom: 1px solid rgba(148, 163, 184, 0.2);
    color: var(--theme-text-soft);
    font-weight: 600;
  }

  .perks-table td {
    padding: 8px 12px;
    border-bottom: 1px solid rgba(148, 163, 184, 0.1);
  }

  .perks-table tr.locked {
    opacity: 0.4;
  }

  .perk-name-col.maxed {
    color: #a855f7;
    font-weight: 500;
  }

  .perk-name-col.unlocked {
    color: #22c55e;
    font-weight: 500;
  }

  .perk-name-col.ability {
    color: #3b82f6;
    font-weight: 500;
  }

  .perk-name-col.special {
    color: #fbbf24;
    font-weight: 500;
  }

  .perk-name-col.locked {
    color: var(--theme-text-soft);
  }

  .maxed-text {
    color: #a855f7;
  }

  .check {
    color: #22c55e;
  }

  .cross {
    color: var(--theme-text-soft);
  }

  .type-col {
    font-size: 0.75rem;
  }

  .ability-text {
    color: #3b82f6;
  }

  .special-text {
    color: #fbbf24;
  }

  .effect-col {
    color: var(--theme-text-soft);
  }
</style>
