<script lang="ts">
  import StatChip from '$lib/components/StatChip.svelte';
  import CharacterSkinViewer3D from '$lib/components/CharacterSkinViewer3D.svelte';
  import { StarIcon, DungeonIcon, SkullIcon } from '$lib/icons';
  import { formatNumber, formatPercent, formatLargeNumber } from '$lib/utils';
  import type { ProfileSummaryResponse, Player, WardrobeItem } from './profileTypes';

  export let summary: ProfileSummaryResponse;
  export let player: Player | null = null;

  type ModelMode = 'naked' | 'armor';
  let modelMode: ModelMode = 'armor';

  $: equippedArmor = (summary?.wardrobe?.equipped_items ?? []) as (WardrobeItem | null)[];
  $: helmet = equippedArmor?.[0] ?? null;
  $: chestplate = equippedArmor?.[1] ?? null;
  $: leggings = equippedArmor?.[2] ?? null;
  $: boots = equippedArmor?.[3] ?? null;
</script>

<section id="summary" class="grid summary-grid">
  <div class="card featured">
    <h2>SkyBlock Level</h2>
    <div class="level-number">{summary.skyblock_level.level}</div>
    <div class="progress">
      <div
        class="progress-bar"
        style={`width:${Math.min(100, summary.skyblock_level.progress * 100).toFixed(1)}%`}
      ></div>
    </div>
    <div class="progress-label">
      {formatPercent(summary.skyblock_level.progress * 100, 1)} | Total XP
      {formatNumber(summary.skyblock_level.experience)}
    </div>
    <div class="chips">
      <StatChip
        label="Avg Skill Level"
        value={summary.skills.average_level.toFixed(2)}
        icon={StarIcon}
      />
      <StatChip
        label="Catacombs"
        value={`Lv. ${summary.dungeons.catacombs.level}`}
        icon={DungeonIcon}
      />
      <StatChip
        label="Total Slayer XP"
        value={formatNumber(summary.slayer.total_xp)}
        icon={SkullIcon}
      />
    </div>
  </div>

  <div class="card">
    <h3>Coins & Networth</h3>
    <div class="stat-list">
      <div>
        <span class="label">Purse</span>
        <span class="value">{formatLargeNumber(summary.currencies.purse)}</span>
      </div>
      <div>
        <span class="label">Co-op Bank</span>
        <span class="value">{formatLargeNumber(summary.currencies.bank.coop)}</span>
      </div>
      <div>
        <span class="label">Personal Bank</span>
        <span class="value">{formatLargeNumber(summary.currencies.bank.personal)}</span>
      </div>
      <div>
        <span class="label">Total Coins</span>
        <span class="value accent">{formatLargeNumber(summary.currencies.total_coins)}</span>
      </div>
      {#if summary.networth}
        <div class="divider"></div>
        <div>
          <span class="label">Networth</span>
          <span class="value networth">{formatLargeNumber(summary.networth.total)}</span>
        </div>
        <div>
          <span class="label">Unsoulbound</span>
          <span class="value">{formatLargeNumber(summary.networth.unsoulbound)}</span>
        </div>
      {/if}
      <div class="divider"></div>
      <div>
        <span class="label">Motes</span>
        <span class="value">{formatLargeNumber(summary.currencies.motes)}</span>
      </div>
      <div>
        <span class="label">Essence Total</span>
        <span class="value">{summary.currencies.essence_total.toLocaleString()}</span>
      </div>
    </div>
  </div>

  <div class="card model-card">
    <div class="model-head">
      <h3>Character</h3>
      <div class="model-toggle" role="group" aria-label="Character view">
        <button
          type="button"
          class:selected={modelMode === 'naked'}
          on:click={() => (modelMode = 'naked')}
        >
          Skin
        </button>
        <button
          type="button"
          class:selected={modelMode === 'armor'}
          on:click={() => (modelMode = 'armor')}
        >
          Armor
        </button>
      </div>
    </div>

    {#if player}
      <div class="model-stage" data-mode={modelMode}>
        <div class="player-model">
          <CharacterSkinViewer3D 
            uuid={player.uuid} 
            armor={modelMode === 'armor' ? {
              helmet: helmet ? { id: helmet.id, color: helmet.leather_color, skin_url: helmet.skin_url } : null,
              chestplate: chestplate ? { id: chestplate.id, color: chestplate.leather_color, skin_url: chestplate.skin_url } : null,
              leggings: leggings ? { id: leggings.id, color: leggings.leather_color, skin_url: leggings.skin_url } : null,
              boots: boots ? { id: boots.id, color: boots.leather_color, skin_url: boots.skin_url } : null
            } : undefined}
          />
        </div>
      </div>

      {#if modelMode === 'armor' && !(helmet || chestplate || leggings || boots)}
        <p class="model-hint">No equipped armor found.</p>
      {/if}
    {:else}
      <p class="model-hint">Loading player info...</p>
    {/if}
  </div>
</section>

<style>
  .summary-grid {
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  }

  .level-number {
    font-size: 3.2rem;
    font-weight: 800;
    margin: 6px 0 8px;
    letter-spacing: -0.04em;
    color: var(--theme-text-primary);
  }

  .chips {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin-top: 14px;
  }

  .progress {
    height: 10px;
    background: rgba(148, 163, 184, 0.24);
    border-radius: 999px;
    overflow: hidden;
  }

  .progress-bar {
    height: 100%;
    background: linear-gradient(135deg, var(--theme-accent), var(--theme-accent-secondary));
    border-radius: 999px;
    transition: width 0.4s ease;
  }

  .progress-label {
    font-size: 0.9rem;
    color: var(--theme-text-soft);
  }

  .stat-list {
    display: flex;
    flex-direction: column;
    gap: 14px;
  }

  .stat-list .label {
    font-size: 0.85rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--theme-text-soft);
  }

  .stat-list .value {
    font-size: 1.15rem;
    font-weight: 600;
    color: var(--theme-text-primary);
  }

  .stat-list .value.accent {
    color: var(--theme-accent);
  }

  .stat-list .value.networth {
    color: #ffd700;
    font-weight: 700;
  }

  .stat-list .divider {
    height: 1px;
    background: var(--theme-secondary-alpha-32);
    margin: 4px 0;
  }

  .model-card {
    display: flex;
    flex-direction: column;
    overflow: hidden;
    min-height: 400px;
  }

  .model-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
  }

  .model-toggle {
    display: inline-flex;
    border-radius: 999px;
    border: 1px solid transparent;
    background: var(--theme-surface);
    box-shadow: var(--neu-elevated);
    overflow: hidden;
  }

  .model-toggle button {
    appearance: none;
    border: 0;
    background: transparent;
    color: var(--theme-text-soft);
    padding: 8px 12px;
    font-size: 0.9rem;
    cursor: pointer;
    line-height: 1;
  }

  .model-toggle button.selected {
    box-shadow: var(--neu-inset);
    color: var(--theme-accent);
  }

  .model-stage {
    position: relative;
    display: grid;
    place-items: center;
    width: 100%;
    padding: 16px 0 8px;
    margin-top: 6px;
  }

  .player-model {
    width: min(360px, 100%);
    height: 360px;
    display: block;
  }

  .model-hint {
    margin-top: 10px;
    color: var(--theme-text-soft);
    font-size: 0.95rem;
  }
</style>
