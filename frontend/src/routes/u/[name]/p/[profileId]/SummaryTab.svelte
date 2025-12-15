<script lang="ts">
  import StatChip from '$lib/components/StatChip.svelte';
  import { StarIcon, DungeonIcon, SkullIcon } from '$lib/icons';
  import { formatNumber, formatPercent, formatLargeNumber } from '$lib/utils';
  import type { ProfileSummaryResponse, Player } from './profileTypes';

  export let summary: ProfileSummaryResponse;
  export let statLabels: Record<string, string>;
  export let player: Player | null = null;
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
    <h3>Character</h3>
    {#if player}
      <div class="model-container">
        <img 
          src={`https://visage.surgeplay.com/full/384/${player.uuid}`} 
          alt={player.name} 
          class="player-model"
          loading="lazy"
        />
      </div>
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

  .model-card {
    display: flex;
    flex-direction: column;
    align-items: center;
    overflow: hidden;
    min-height: 400px;
  }

  .model-container {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    width: 100%;
    margin-top: -20px;
  }

  .player-model {
    max-height: 360px;
    filter: drop-shadow(0 10px 20px rgba(0, 0, 0, 0.4));
    transition: transform 0.3s ease;
  }
  
  .player-model:hover {
    transform: scale(1.05) translateY(-5px);
  }
</style>
