<script lang="ts">
  export let label: string;
  export let value: string | number | undefined = '-';
  // Svelte component constructor typing differs across Svelte versions; keep this permissive.
  export let icon: any = null;
</script>

<span class="chip">
  {#if icon}
    <span class="icon">
      <svelte:component this={icon} />
    </span>
  {/if}
  <strong>{label}</strong>
  <span class="value">{value ?? '-'}</span>
</span>

<style>
  .chip {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.35rem 0.8rem;
    border-radius: 9999px;
    background: var(--theme-surface);
    border: 1px solid transparent;
    color: var(--theme-text-primary);
    font-size: 0.9rem;
    font-weight: 500;
    box-shadow: var(--neu-elevated);
    backdrop-filter: blur(12px);
    transition: background 0.4s ease, border-color 0.4s ease, box-shadow 0.4s ease,
      transform 0.3s ease;
  }

  .chip:hover {
    transform: translateY(-2px);
    box-shadow: var(--neu-elevated);
  }

  strong {
    font-weight: 600;
    color: var(--theme-text-secondary);
  }

  .value {
    color: var(--theme-text-soft);
  }

  .icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 1.15rem;
    height: 1.15rem;
  }

  .icon :global(svg) {
    width: 100%;
    height: 100%;
    fill: currentColor;
    stroke: currentColor;
    stroke-width: 1.5;
    color: var(--theme-text-secondary);
  }
</style>
