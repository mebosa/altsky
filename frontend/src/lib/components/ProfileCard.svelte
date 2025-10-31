<script lang="ts">
  import StatChip from './StatChip.svelte';

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
    <StatChip label="Last Saved" value={formatTime(lastSave)} />
    <StatChip label="Coins on Hand" value={formatCoins(purse)} />
  </div>
</div>

<style>
  .card {
    border: 1px solid #1f2937;
    border-radius: 16px;
    padding: 16px;
    background: rgba(15, 23, 42, 0.8);
    color: #e2e8f0;
    display: flex;
    flex-direction: column;
    gap: 12px;
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
  }

  code {
    font-size: 0.75rem;
    color: #94a3b8;
  }

  .chips {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
  }
</style>
