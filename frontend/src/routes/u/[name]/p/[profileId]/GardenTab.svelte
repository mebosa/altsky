<script lang="ts">
  import { formatNumber } from '$lib/utils';
  import type { GardenData } from './profileTypes';

  export let garden: GardenData;

  const CROP_ICONS: Record<string, string> = {
    'WHEAT': 'https://mc-heads.net/head/88cb8783131c034652e277e5e3c72453c578663974300320207d189d7526973a',
    'CARROT_ITEM': 'https://mc-heads.net/head/f9136514f3d86c77c21762b19847a14027827304475b413a0286087213d6',
    'POTATO_ITEM': 'https://mc-heads.net/head/48580312698b4f2029b4866321b9a78a8f5a74655c88d8f976893f2850711',
    'PUMPKIN': 'https://mc-heads.net/head/56fc854bb84cf4b7697297973e02b79bc10698460b51a639c60e5e417734e11',
    'MELON': 'https://mc-heads.net/head/c57bda623f659fc14d578e6031621130c6a88bf48259536348f7356f6776f77',
    'MUSHROOM_COLLECTION': 'https://mc-heads.net/head/d7623747183ef858474256e843f03192d381255353e9226324c0454550d55f',
    'CACTUS': 'https://mc-heads.net/head/4192254d379e885238f16d741962416736a027e9515f9d8a5d339941436051',
    'SUGAR_CANE': 'https://mc-heads.net/head/951e8861592a47af57648d82e28994e654b5924e81253199a6a28711675c',
    'NETHER_STALK': 'https://mc-heads.net/head/724a3a102d1f98a6992497633491646752c58728c845a84d5c0a1e69451',
    'INK_SACK:3': 'https://mc-heads.net/head/400c50177e2c60562c398f63147e7115815a934778a3e8dc5f1c652c0891e',
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
  <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
    <div class="bg-surface-600/30 rounded-lg p-4 border border-surface-600">
      <h3 class="text-lg font-bold mb-2 text-primary-400">Garden Stats</h3>
      <div class="space-y-2">
        <div class="flex justify-between">
          <span class="text-surface-300">Level</span>
          <span class="font-mono">{garden.level}</span>
        </div>
        <div class="flex justify-between">
          <span class="text-surface-300">XP</span>
          <span class="font-mono">{formatNumber(garden.xp)}</span>
        </div>
        <div class="flex justify-between">
          <span class="text-surface-300">Copper</span>
          <span class="font-mono text-yellow-500">{formatNumber(garden.copper)}</span>
        </div>
        <div class="flex justify-between">
          <span class="text-surface-300">Visitors Served</span>
          <span class="font-mono">{formatNumber(garden.visitors_served)}</span>
        </div>
      </div>
    </div>

    <div class="bg-surface-600/30 rounded-lg p-4 border border-surface-600">
      <h3 class="text-lg font-bold mb-2 text-yellow-400">Jacob's Medals</h3>
      <div class="space-y-2">
        <div class="flex justify-between items-center">
          <span class="text-surface-300">Gold</span>
          <div class="flex items-center gap-2">
            <span class="font-mono text-yellow-400">{garden.medals.gold}</span>
            <span class="text-xs text-surface-400">({garden.unique_golds.length} unique)</span>
          </div>
        </div>
        <div class="flex justify-between items-center">
          <span class="text-surface-300">Silver</span>
          <div class="flex items-center gap-2">
            <span class="font-mono text-gray-300">{garden.medals.silver}</span>
            <span class="text-xs text-surface-400">({garden.unique_silvers.length} unique)</span>
          </div>
        </div>
        <div class="flex justify-between items-center">
          <span class="text-surface-300">Bronze</span>
          <div class="flex items-center gap-2">
            <span class="font-mono text-orange-400">{garden.medals.bronze}</span>
            <span class="text-xs text-surface-400">({garden.unique_bronzes.length} unique)</span>
          </div>
        </div>
      </div>
    </div>

    <div class="bg-surface-600/30 rounded-lg p-4 border border-surface-600">
      <h3 class="text-lg font-bold mb-2 text-green-400">Perks</h3>
      <div class="space-y-2">
        <div class="flex justify-between">
          <span class="text-surface-300">Double Drops</span>
          <span class="font-mono">{garden.perks.double_drops || 0}%</span>
        </div>
        <div class="flex justify-between">
          <span class="text-surface-300">Farming Level Cap</span>
          <span class="font-mono">+{garden.perks.farming_level_cap || 0}</span>
        </div>
      </div>
    </div>
  </div>

  <!-- Recent Contests -->
  <div class="bg-surface-600/30 rounded-lg p-4 border border-surface-600">
    <h3 class="text-lg font-bold mb-4 text-primary-400">Recent Contests</h3>
    <div class="overflow-x-auto">
      <table class="w-full text-left text-sm">
        <thead class="bg-surface-700/50 text-surface-200 uppercase font-semibold">
          <tr>
            <th class="p-3">Crop</th>
            <th class="p-3 text-right">Collected</th>
            <th class="p-3 text-center">Medal</th>
            <th class="p-3 text-right">Position</th>
            <th class="p-3 text-right">Participants</th>
            <th class="p-3 text-right">Top %</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-surface-700">
          {#each garden.contests.slice(0, 20) as contest}
            <tr class="hover:bg-surface-700/30 transition-colors">
              <td class="p-3 flex items-center gap-3">
                <img src={getCropIcon(contest.crop)} alt={contest.crop} class="w-6 h-6 rounded-sm" />
                <span>{formatCropName(contest.crop)}</span>
              </td>
              <td class="p-3 text-right font-mono">{formatNumber(contest.collected)}</td>
              <td class="p-3 text-center">
                {#if contest.medal === 'gold'}
                  <span class="text-yellow-400 font-bold">GOLD</span>
                {:else if contest.medal === 'silver'}
                  <span class="text-gray-300 font-bold">SILVER</span>
                {:else if contest.medal === 'bronze'}
                  <span class="text-orange-400 font-bold">BRONZE</span>
                {:else}
                  <span class="text-surface-500">-</span>
                {/if}
              </td>
              <td class="p-3 text-right font-mono">#{formatNumber(contest.position)}</td>
              <td class="p-3 text-right font-mono">{formatNumber(contest.participants)}</td>
              <td class="p-3 text-right font-mono">
                {#if contest.participants > 0}
                  {((contest.position / contest.participants) * 100).toFixed(1)}%
                {:else}
                  -
                {/if}
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
    {#if garden.contests.length > 20}
      <div class="mt-4 text-center text-surface-400 text-sm">
        Showing 20 of {garden.contests.length} contests
      </div>
    {/if}
  </div>
</div>
