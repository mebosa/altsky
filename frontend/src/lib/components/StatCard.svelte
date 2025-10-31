<script lang="ts">
  export let label = '';
  export let value: string | number | null = null;
</script>

<div class="stat">
  <div class="v">{value ?? '-'}</div>
  <div class="l">{label}</div>
</div>

<style>
  .stat {
    padding: 14px 16px;
    border: 1px solid var(--theme-surface-border);
    border-radius: 14px;
    background: var(--theme-surface);
    color: var(--theme-text-primary);
    box-shadow: var(--theme-card-shadow);
    display: flex;
    flex-direction: column;
    gap: 4px;
    transition: background 0.35s ease, border-color 0.35s ease, box-shadow 0.35s ease;
  }

  .v {
    font-size: 22px;
    font-weight: 700;
    letter-spacing: -0.02em;
  }

  .l {
    font-size: 12px;
    color: var(--theme-text-soft);
    text-transform: uppercase;
    letter-spacing: 0.08em;
  }
</style>
