<script lang="ts">
  import StatChip from './StatChip.svelte';
  import { ClockIcon, CoinIcon } from '$lib/icons';

  export let cuteName = '(unknown)';
  export let lastSave: number | undefined;
  export let purse: number | undefined;
  export let profileId: string | undefined;

  const formatTime = (timestamp?: number) => (timestamp ? new Date(timestamp).toLocaleString() : '-');
  const formatCoins = (value?: number) =>
    typeof value === 'number' ? value.toLocaleString(undefined, { maximumFractionDigits: 0 }) : '-';
</script>

<div class="card">
  <div class="header">
    <h3>{cuteName}</h3>
    {#if profileId}
      <code>{profileId.slice(0, 8)}...</code>
    {/if}
  </div>

  <div class="chips">
    <StatChip label="Last Saved" value={formatTime(lastSave)} icon={ClockIcon} />
    <StatChip label="Coins on Hand" value={formatCoins(purse)} icon={CoinIcon} />
  </div>
</div>

<style>
  .card {
    border: 1px solid var(--theme-surface-border);
    border-radius: 16px;
    padding: 16px;
    background: var(--theme-surface);
    color: var(--theme-text-primary);
    display: flex;
    flex-direction: column;
    gap: 12px;
    box-shadow: var(--theme-card-shadow);
    transition: background 0.4s ease, border-color 0.4s ease, box-shadow 0.4s ease;
  }

  .header {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    gap: 12px;
  }

  h3 {
    margin: 0;
    font-size: 1.1rem;
    color: var(--theme-text-primary);
  }

  code {
    font-size: 0.75rem;
    color: var(--theme-text-soft);
  }

  .chips {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
  }
</style>
