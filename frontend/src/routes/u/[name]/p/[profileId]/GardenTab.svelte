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
</script>

<div class="space-y-6">
  <!-- Overview Stats -->
  <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
    <!-- Garden Stats Card -->
    <div class="bg-surface-800 rounded-xl p-5 border border-surface-700 shadow-lg relative overflow-hidden group">
      <div class="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
        <img src="/api/vanilla/item/wheat.png" alt="Garden" class="w-16 h-16 pixelated" />
      </div>
      <h3 class="text-lg font-bold mb-4 text-primary-400 flex items-center gap-2">
        <span class="text-2xl">🌾</span> Garden Stats
      </h3>
      <div class="space-y-3 relative z-10">
        <div class="flex justify-between items-center p-2 bg-surface-900/50 rounded-lg">
          <span class="text-surface-300 font-medium">Level</span>
          <span class="font-mono text-lg text-white">{garden.level}</span>
        </div>
        <div class="flex justify-between items-center p-2 bg-surface-900/50 rounded-lg">
          <span class="text-surface-300 font-medium">XP</span>
          <span class="font-mono text-lg text-white">{formatNumber(garden.xp)}</span>
        </div>
        <div class="flex justify-between items-center p-2 bg-surface-900/50 rounded-lg">
          <span class="text-surface-300 font-medium">Copper</span>
          <span class="font-mono text-lg text-yellow-500">{formatNumber(garden.copper)}</span>
        </div>
        <div class="flex justify-between items-center p-2 bg-surface-900/50 rounded-lg">
          <span class="text-surface-300 font-medium">Visitors</span>
          <span class="font-mono text-lg text-white">{formatNumber(garden.visitors_served)}</span>
        </div>
      </div>
    </div>

    <!-- Jacob's Medals Card -->
    <div class="bg-surface-800 rounded-xl p-5 border border-surface-700 shadow-lg relative overflow-hidden group">
      <div class="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
        <img src="/api/vanilla/item/gold_ingot.png" alt="Medals" class="w-16 h-16 pixelated" />
      </div>
      <h3 class="text-lg font-bold mb-4 text-yellow-400 flex items-center gap-2">
        <span class="text-2xl">🏅</span> Jacob's Medals
      </h3>
      <div class="space-y-3 relative z-10">
        <div class="flex justify-between items-center p-2 bg-surface-900/50 rounded-lg border-l-4 border-yellow-500">
          <span class="text-surface-300 font-medium">Gold</span>
          <div class="flex flex-col items-end">
            <span class="font-mono text-lg text-yellow-400 font-bold">{garden.medals.gold}</span>
            <span class="text-xs text-surface-400">{garden.unique_golds.length} unique</span>
          </div>
        </div>
        <div class="flex justify-between items-center p-2 bg-surface-900/50 rounded-lg border-l-4 border-gray-400">
          <span class="text-surface-300 font-medium">Silver</span>
          <div class="flex flex-col items-end">
            <span class="font-mono text-lg text-gray-300 font-bold">{garden.medals.silver}</span>
            <span class="text-xs text-surface-400">{garden.unique_silvers.length} unique</span>
          </div>
        </div>
        <div class="flex justify-between items-center p-2 bg-surface-900/50 rounded-lg border-l-4 border-orange-600">
          <span class="text-surface-300 font-medium">Bronze</span>
          <div class="flex flex-col items-end">
            <span class="font-mono text-lg text-orange-400 font-bold">{garden.medals.bronze}</span>
            <span class="text-xs text-surface-400">{garden.unique_bronzes.length} unique</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Perks Card -->
    <div class="bg-surface-800 rounded-xl p-5 border border-surface-700 shadow-lg relative overflow-hidden group">
      <div class="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
        <img src="/api/vanilla/item/emerald.png" alt="Perks" class="w-16 h-16 pixelated" />
      </div>
      <h3 class="text-lg font-bold mb-4 text-green-400 flex items-center gap-2">
        <span class="text-2xl">✨</span> Perks
      </h3>
      <div class="space-y-3 relative z-10">
        <div class="flex justify-between items-center p-2 bg-surface-900/50 rounded-lg">
          <span class="text-surface-300 font-medium">Double Drops</span>
          <span class="font-mono text-lg text-green-400">{garden.perks.double_drops || 0}%</span>
        </div>
        <div class="flex justify-between items-center p-2 bg-surface-900/50 rounded-lg">
          <span class="text-surface-300 font-medium">Farming Cap</span>
          <span class="font-mono text-lg text-green-400">+{garden.perks.farming_level_cap || 0}</span>
        </div>
      </div>
    </div>
  </div>

  <!-- Recent Contests -->
  <div class="bg-surface-800 rounded-xl border border-surface-700 shadow-lg overflow-hidden">
    <div class="p-5 border-b border-surface-700 bg-surface-800/50">
      <h3 class="text-lg font-bold text-primary-400 flex items-center gap-2">
        <span class="text-2xl">📊</span> Recent Contests
      </h3>
    </div>
    <div class="overflow-x-auto">
      <table class="w-full text-left text-sm">
        <thead class="bg-surface-900/80 text-surface-300 uppercase text-xs font-bold tracking-wider">
          <tr>
            <th class="p-4">Crop</th>
            <th class="p-4 text-right">Collected</th>
            <th class="p-4 text-center">Medal</th>
            <th class="p-4 text-right">Position</th>
            <th class="p-4 text-right">Participants</th>
            <th class="p-4 text-right">Top %</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-surface-700/50">
          {#each garden.contests.slice(0, 20) as contest}
            <tr class="hover:bg-surface-700/30 transition-colors group">
              <td class="p-4 flex items-center gap-3">
                <div class="w-10 h-10 bg-surface-700/50 rounded-lg flex items-center justify-center border border-surface-600 group-hover:border-surface-500 transition-colors">
                  <img src={getCropIcon(contest.crop)} alt={contest.crop} class="w-6 h-6 pixelated" />
                </div>
                <span class="font-medium text-surface-100">{formatCropName(contest.crop)}</span>
              </td>
              <td class="p-4 text-right font-mono text-surface-200">{formatNumber(contest.collected)}</td>
              <td class="p-4 text-center">
                {#if contest.medal === 'gold'}
                  <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-yellow-500/10 text-yellow-400 border border-yellow-500/20">GOLD</span>
                {:else if contest.medal === 'silver'}
                  <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-gray-500/10 text-gray-300 border border-gray-500/20">SILVER</span>
                {:else if contest.medal === 'bronze'}
                  <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-orange-500/10 text-orange-400 border border-orange-500/20">BRONZE</span>
                {:else}
                  <span class="text-surface-600">-</span>
                {/if}
              </td>
              <td class="p-4 text-right font-mono text-surface-300">
                {#if contest.position > 0}
                  #{formatNumber(contest.position)}
                {:else}
                  -
                {/if}
              </td>
              <td class="p-4 text-right font-mono text-surface-300">{formatNumber(contest.participants)}</td>
              <td class="p-4 text-right font-mono">
                {#if contest.participants > 0}
                  <span class="text-surface-200">{((contest.position / contest.participants) * 100).toFixed(1)}%</span>
                {:else}
                  <span class="text-surface-600">-</span>
                {/if}
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
    {#if garden.contests.length > 20}
      <div class="p-4 text-center border-t border-surface-700 bg-surface-800/30">
        <span class="text-surface-400 text-sm">Showing 20 of {garden.contests.length} contests</span>
      </div>
    {/if}
  </div>
</div>

<style>
  .pixelated {
    image-rendering: pixelated;
  }
</style>
