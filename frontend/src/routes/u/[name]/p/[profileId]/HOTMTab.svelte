<script lang="ts">
  import type { ProfileSummaryResponse, HOTMData } from './profileTypes';
  import {
    HOTM_PERKS,
    HOTM_TIERS,
    HOTM_XP_REQUIREMENTS,
    TOKENS_PER_TIER,
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
    <div class="bg-surface-800 p-4 rounded-lg border border-surface-700">
      <div class="text-surface-400 text-sm">HOTM Tier</div>
      <div class="text-3xl font-bold text-purple-400">
        {tier}
        <span class="text-lg text-surface-500">/ {HOTM_TIERS}</span>
      </div>
      {#if tier < HOTM_TIERS}
        <div class="mt-2">
          <div class="text-xs text-surface-500 mb-1">
            {formatNumber(progress.current)} / {formatNumber(progress.next)} XP
          </div>
          <div class="w-full h-2 bg-surface-700 rounded-full overflow-hidden">
            <div
              class="h-full bg-gradient-to-r from-purple-600 to-purple-400 transition-all duration-300"
              style="width: {progress.progress}%"
            ></div>
          </div>
        </div>
      {:else}
        <div class="text-xs text-purple-400 mt-2">✧ Maximum Tier ✧</div>
      {/if}
    </div>

    <!-- Tokens -->
    <div class="bg-surface-800 p-4 rounded-lg border border-surface-700">
      <div class="text-surface-400 text-sm">Tokens of the Mountain</div>
      <div class="text-2xl font-bold text-yellow-400">
        {tokensSpent}
        <span class="text-lg text-surface-500">/ {totalTokens}</span>
      </div>
      <div class="text-xs text-surface-500 mt-1">
        {totalTokens - tokensSpent} available
      </div>
    </div>

    <!-- Powder (Mithril) -->
    <div class="bg-surface-800 p-4 rounded-lg border border-surface-700">
      <div class="text-surface-400 text-sm flex items-center gap-1">
        <span class="text-green-400">᠅</span> Mithril Powder
      </div>
      <div class="text-2xl font-bold" style="color: {POWDER_COLORS.mithril}">
        {formatPowder(powder.mithril)}
      </div>
      {#if powder.mithril_total}
        <div class="text-xs text-surface-500 mt-1">
          Total: {formatPowder(powder.mithril_total)}
        </div>
      {/if}
    </div>

    <!-- Powder (Gemstone) -->
    <div class="bg-surface-800 p-4 rounded-lg border border-surface-700">
      <div class="text-surface-400 text-sm flex items-center gap-1">
        <span class="text-pink-400">᠅</span> Gemstone Powder
      </div>
      <div class="text-2xl font-bold" style="color: {POWDER_COLORS.gemstone}">
        {formatPowder(powder.gemstone)}
      </div>
      {#if powder.gemstone_total}
        <div class="text-xs text-surface-500 mt-1">
          Total: {formatPowder(powder.gemstone_total)}
        </div>
      {/if}
    </div>
  </div>

  <!-- Glacite Powder (if available) -->
  {#if powder.glacite > 0 || (powder.glacite_total && powder.glacite_total > 0)}
    <div class="bg-surface-800 p-4 rounded-lg border border-surface-700 max-w-xs">
      <div class="text-surface-400 text-sm flex items-center gap-1">
        <span class="text-cyan-400">᠅</span> Glacite Powder
      </div>
      <div class="text-2xl font-bold" style="color: {POWDER_COLORS.glacite}">
        {formatPowder(powder.glacite)}
      </div>
      {#if powder.glacite_total}
        <div class="text-xs text-surface-500 mt-1">
          Total: {formatPowder(powder.glacite_total)}
        </div>
      {/if}
    </div>
  {/if}

  <!-- Main Content: Tree + Details -->
  <div class="flex flex-col lg:flex-row gap-6">
    <!-- HOTM Tree Grid -->
    <div class="flex-1 bg-surface-800/50 p-4 rounded-lg border border-surface-700">
      <h3 class="text-lg font-bold text-surface-200 mb-4 flex items-center gap-2">
        <span class="text-2xl">⛏️</span>
        Heart of the Mountain
      </h3>

      <!-- Legend -->
      <div class="flex flex-wrap gap-4 mb-4 text-xs">
        <div class="flex items-center gap-1">
          <div class="w-3 h-3 rounded bg-green-900/50 border border-green-500"></div>
          <span class="text-surface-400">Unlocked</span>
        </div>
        <div class="flex items-center gap-1">
          <div class="w-3 h-3 rounded bg-purple-900/50 border border-purple-500"></div>
          <span class="text-surface-400">Maxed</span>
        </div>
        <div class="flex items-center gap-1">
          <div class="w-3 h-3 rounded bg-blue-900/50 border border-blue-500"></div>
          <span class="text-surface-400">Ability</span>
        </div>
        <div class="flex items-center gap-1">
          <div class="w-3 h-3 rounded bg-yellow-900/50 border border-yellow-500"></div>
          <span class="text-surface-400">Special</span>
        </div>
        <div class="flex items-center gap-1">
          <div class="w-3 h-3 rounded bg-surface-800 border border-surface-600"></div>
          <span class="text-surface-400">Locked</span>
        </div>
      </div>

      <!-- Grid -->
      <div class="overflow-x-auto">
        <div class="min-w-[500px]">
          {#each gridData as row, rowIndex}
            {@const rowTier = getTierForRow(rowIndex)}
            {@const rowUnlocked = isRowUnlocked(rowIndex)}
            <div class="flex items-center gap-2 mb-2">
              <!-- Tier indicator -->
              <div
                class="w-10 h-10 flex items-center justify-center rounded-lg text-sm font-bold shrink-0
                  {rowUnlocked
                    ? 'bg-gradient-to-br from-purple-600 to-purple-800 text-white shadow-lg'
                    : 'bg-surface-700 text-surface-500'}"
              >
                {rowTier}
              </div>

              <!-- Perk cells -->
              <div class="perk-cells">
                {#each row as perk}
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
    <div class="lg:w-80 bg-surface-800 p-4 rounded-lg border border-surface-700">
      {#if selectedPerk}
        <div class="space-y-4">
          <!-- Perk Name -->
          <div>
            <h4 class="text-lg font-bold {
              selectedPerk.status === 'maxed' ? 'text-purple-400' :
              selectedPerk.status === 'unlocked' ? 'text-green-400' :
              selectedPerk.status === 'ability' ? 'text-blue-400' :
              selectedPerk.status === 'special' ? 'text-yellow-400' :
              'text-surface-400'
            }">
              {selectedPerk.name}
            </h4>
            {#if selectedPerk.maxLevel > 1}
              <div class="text-sm text-surface-400">
                Level {selectedPerk.level}/{selectedPerk.maxLevel}
              </div>
            {/if}
          </div>

          <!-- Level Progress Bar -->
          {#if selectedPerk.maxLevel > 1}
            <div>
              <div class="w-full h-2 bg-surface-700 rounded-full overflow-hidden">
                <div
                  class="h-full transition-all duration-300 {
                    selectedPerk.status === 'maxed' ? 'bg-purple-500' : 'bg-green-500'
                  }"
                  style="width: {(selectedPerk.level / selectedPerk.maxLevel) * 100}%"
                ></div>
              </div>
            </div>
          {/if}

          <!-- Perk Info -->
          <div class="space-y-2 text-sm">
            <div class="flex justify-between">
              <span class="text-surface-400">Required Tier:</span>
              <span class="text-surface-200">{selectedPerk.tier}</span>
            </div>
            {#if selectedPerk.powderType}
              <div class="flex justify-between">
                <span class="text-surface-400">Powder Type:</span>
                <span style="color: {POWDER_COLORS[selectedPerk.powderType]}">
                  {selectedPerk.powderType.charAt(0).toUpperCase() + selectedPerk.powderType.slice(1)}
                </span>
              </div>
            {/if}
            {#if selectedPerk.isAbility}
              <div class="text-blue-400 text-xs bg-blue-900/30 px-2 py-1 rounded">
                ⚡ Pickaxe Ability
              </div>
            {/if}
          </div>

          <!-- Effect -->
          <div class="bg-surface-900/50 p-3 rounded-lg">
            <div class="text-xs text-surface-400 mb-1">Current Effect:</div>
            <div class="text-sm text-surface-200">
              {#if selectedPerk.level > 0}
                {selectedPerk.description(selectedPerk.level)}
              {:else}
                {selectedPerk.description(1)}
                <span class="text-surface-500 text-xs">(at level 1)</span>
              {/if}
            </div>
          </div>

          <!-- Next Level Preview -->
          {#if selectedPerk.level > 0 && selectedPerk.level < selectedPerk.maxLevel}
            <div class="bg-green-900/20 p-3 rounded-lg border border-green-800/50">
              <div class="text-xs text-green-400 mb-1">Next Level ({selectedPerk.level + 1}):</div>
              <div class="text-sm text-surface-200">
                {selectedPerk.description(selectedPerk.level + 1)}
              </div>
            </div>
          {/if}

          <!-- Max Level Preview -->
          {#if selectedPerk.status !== 'maxed' && selectedPerk.maxLevel > 1}
            <div class="bg-purple-900/20 p-3 rounded-lg border border-purple-800/50">
              <div class="text-xs text-purple-400 mb-1">At Max Level ({selectedPerk.maxLevel}):</div>
              <div class="text-sm text-surface-200">
                {selectedPerk.description(selectedPerk.maxLevel)}
              </div>
            </div>
          {/if}
        </div>
      {:else}
        <div class="text-center text-surface-500 py-8">
          <div class="text-3xl mb-2">👆</div>
          <p>Click a perk to see details</p>
        </div>
      {/if}
    </div>
  </div>

  <!-- Crystal Hollows Crystals -->
  {#if crystals && Object.keys(crystals).length > 0}
    <div class="bg-surface-800 p-4 rounded-lg border border-surface-700">
      <h3 class="text-lg font-bold text-surface-200 mb-4 flex items-center gap-2">
        <span class="text-xl">💎</span>
        Crystal Hollows Crystals
      </h3>
      <div class="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-7 gap-3">
        {#each Object.entries(CRYSTALS) as [crystalId, crystalData]}
          {@const crystal = crystals[crystalId]}
          {@const isPlaced = crystal?.state === 'FOUND'}
          <div
            class="p-3 rounded-lg border text-center
              {isPlaced
                ? 'bg-surface-700 border-surface-500'
                : 'bg-surface-800/50 border-surface-700 opacity-50'}"
          >
            <div
              class="text-2xl mb-1"
              style="text-shadow: 0 0 10px {crystalData.color}"
            >
              💎
            </div>
            <div class="text-xs font-medium" style="color: {crystalData.color}">
              {crystalData.name}
            </div>
            <div class="text-xs text-surface-500 mt-1">
              {isPlaced ? '✓ Placed' : 'Not found'}
            </div>
            {#if crystal?.total_placed}
              <div class="text-xs text-surface-400">
                {crystal.total_placed}x placed
              </div>
            {/if}
          </div>
        {/each}
      </div>
    </div>
  {/if}

  <!-- Perk Summary Table -->
  <div class="bg-surface-800 p-4 rounded-lg border border-surface-700">
    <h3 class="text-lg font-bold text-surface-200 mb-4">All Perks Summary</h3>
    <div class="overflow-x-auto">
      <table class="w-full text-sm">
        <thead>
          <tr class="text-left text-surface-400 border-b border-surface-700">
            <th class="pb-2 pr-4">Perk</th>
            <th class="pb-2 pr-4">Tier</th>
            <th class="pb-2 pr-4">Level</th>
            <th class="pb-2 pr-4">Type</th>
            <th class="pb-2">Effect</th>
          </tr>
        </thead>
        <tbody>
          {#each Object.values(HOTM_PERKS).sort((a, b) => b.tier - a.tier || a.position - b.position) as perk}
            {@const level = perks[perk.id] ?? 0}
            {@const status = getPerkStatus(perk, level, tier)}
            <tr class="border-b border-surface-700/50 {status === 'locked' ? 'opacity-40' : ''}">
              <td class="py-2 pr-4 font-medium {
                status === 'maxed' ? 'text-purple-400' :
                status === 'unlocked' ? 'text-green-400' :
                status === 'ability' ? 'text-blue-400' :
                status === 'special' ? 'text-yellow-400' :
                'text-surface-500'
              }">
                {perk.name}
              </td>
              <td class="py-2 pr-4 text-surface-400">{perk.tier}</td>
              <td class="py-2 pr-4">
                {#if perk.maxLevel > 1}
                  <span class="{status === 'maxed' ? 'text-purple-400' : 'text-surface-300'}">
                    {level}/{perk.maxLevel}
                  </span>
                {:else}
                  <span class="{level > 0 ? 'text-green-400' : 'text-surface-500'}">
                    {level > 0 ? '✓' : '✗'}
                  </span>
                {/if}
              </td>
              <td class="py-2 pr-4 text-xs">
                {#if perk.powderType}
                  <span style="color: {POWDER_COLORS[perk.powderType]}">
                    {perk.powderType}
                  </span>
                {:else if perk.isAbility}
                  <span class="text-blue-400">ability</span>
                {:else}
                  <span class="text-yellow-400">special</span>
                {/if}
              </td>
              <td class="py-2 text-surface-400 text-xs">
                {#if level > 0}
                  {perk.effect(level)}
                {:else}
                  <span class="text-surface-500">{perk.effect(1)}</span>
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
