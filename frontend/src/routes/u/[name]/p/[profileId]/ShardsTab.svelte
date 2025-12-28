<script lang="ts">
  import type { ProfileSummaryResponse, ShardsData } from './profileTypes';
  import { formatNumber } from '$lib/utils';

  export let summary: ProfileSummaryResponse;

  $: shardsData = summary.shards as ShardsData | null;
  $: stats = shardsData?.stats;
  $: allShards = shardsData?.shards || [];

  let searchQuery = '';
  let showOwnedOnly = false;

  $: filteredShards = allShards.filter(shard => {
    if (showOwnedOnly && !shard.owned) return false;
    if (searchQuery) {
      return shard.name.toLowerCase().includes(searchQuery.toLowerCase());
    }
    return true;
  });
  
  // Calculate progress
  $: totalShards = allShards.length;
  $: ownedCount = allShards.filter(s => s.owned).length;
  $: progress = totalShards > 0 ? (ownedCount / totalShards) * 100 : 0;
</script>

<div class="space-y-6">
  <!-- Stats Header -->
  {#if stats}
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
      <div class="bg-surface-800 p-4 rounded-lg border border-surface-700">
        <div class="text-surface-400 text-sm">Applied Shards</div>
        <div class="text-2xl font-bold text-primary-400">{stats.unique_shards}</div>
        <div class="text-xs text-surface-500 mt-1">Consumed on profile</div>
      </div>
      
      <div class="bg-surface-800 p-4 rounded-lg border border-surface-700">
        <div class="text-surface-400 text-sm">Shard Charm</div>
        <div class="text-2xl font-bold text-yellow-400">
            {#if stats.shard_charm_level}
                Lvl {stats.shard_charm_level}
            {:else}
                -
            {/if}
        </div>
      </div>

      <div class="bg-surface-800 p-4 rounded-lg border border-surface-700">
        <div class="text-surface-400 text-sm">Total Hunts</div>
        <div class="text-2xl font-bold text-secondary-400">{formatNumber(stats.total_hunts)}</div>
      </div>
      
      <div class="bg-surface-800 p-4 rounded-lg border border-surface-700">
        <div class="text-surface-400 text-sm">Inventory Shards</div>
        <div class="text-2xl font-bold text-green-400">{ownedCount}</div>
        <div class="text-xs text-surface-500 mt-1">Found in storage</div>
      </div>
    </div>
  {/if}

  <!-- Info Alert -->
  <div class="bg-surface-800/50 border border-surface-700 p-4 rounded-lg flex items-start gap-3 text-sm text-surface-300">
    <div class="text-xl">ℹ️</div>
    <div>
      <p class="font-bold text-surface-200 mb-1">About Shard Tracking</p>
      <p>
        Hypixel's API only reports the <strong>total count</strong> of applied shards, not the specific ones you've used. 
        The grid below shows shards found in your inventory/storage, which are likely duplicates or unapplied extras.
      </p>
    </div>
  </div>

  <!-- Controls -->
  <div class="flex flex-wrap gap-4 items-center bg-surface-800 p-4 rounded-lg border border-surface-700">
    <input 
      type="text" 
      placeholder="Search shards..." 
      bind:value={searchQuery}
      class="input px-4 py-2 rounded bg-surface-900 border border-surface-600 focus:border-primary-500 outline-none"
    />
    
    <label class="flex items-center gap-2 cursor-pointer select-none">
      <input type="checkbox" bind:checked={showOwnedOnly} class="checkbox" />
      <span>Show Owned Only</span>
    </label>
  </div>

  <!-- Grid -->
  <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
    {#each filteredShards as shard (shard.id)}
      <div 
        class="relative group bg-surface-800 rounded-lg p-4 flex flex-col items-center text-center transition-all duration-200 hover:-translate-y-1
        {shard.owned ? 'border-2 border-green-500/50 shadow-[0_0_15px_rgba(34,197,94,0.2)]' : 'border border-surface-700 opacity-70 hover:opacity-100'}"
      >
        <!-- Status Indicator -->
        <div class="absolute top-2 right-2">
            {#if shard.owned}
                <div class="w-3 h-3 rounded-full bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.8)]"></div>
            {:else}
                <div class="w-3 h-3 rounded-full bg-red-500/50"></div>
            {/if}
        </div>

        <!-- Icon Placeholder -->
        <div class="w-12 h-12 mb-3 rounded bg-surface-700 flex items-center justify-center text-2xl">
            💎
        <div class="font-medium text-sm line-clamp-2 h-10 flex items-center justify-center">
            {shard.name}
        </div>
        
        <div class="text-xs text-surface-400 mt-2 uppercase tracking-wider">
            {shard.rarity}
        </div>
      </div>
    {/each}
  </div>
  
  {#if filteredShards.length === 0}
    <div class="text-center py-12 text-surface-400">
        No shards found matching your criteria.
    </div>
  {/if}
</div>
