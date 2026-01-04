<script lang="ts">
  import { createEventDispatcher } from 'svelte';

  export let tabs: { id: string; label: string }[] = [];
  export let value: string;

  const dispatch = createEventDispatcher<{ change: string; select: string }>();

  function select(id: string) {
    if (id === value) return;
    value = id;
    dispatch('select', id);
    dispatch('change', id);
  }
</script>

<div class="tabs">
  {#each tabs as tab}
    <button
      class:value-active={value === tab.id}
      on:click={() => select(tab.id)}
      type="button"
    >
      {tab.label}
    </button>
  {/each}
</div>

<style>
  .tabs {
    display: flex;
    gap: 8px;
    margin: 16px 0;
    flex-wrap: wrap;
  }

  button {
    padding: 8px 16px;
    border-radius: 999px;
    border: 1px solid transparent;
    background: var(--theme-surface);
    color: var(--theme-text-secondary);
    cursor: pointer;
    font-size: 0.95rem;
    transition: all 0.25s ease;
    box-shadow: var(--neu-elevated);
  }

  button:hover {
    color: var(--theme-accent);
    transform: translateY(-2px);
  }

  button.value-active {
    box-shadow: var(--neu-inset);
    color: var(--theme-accent);
    font-weight: 600;
  }

  .value-active {
    /* Removed gradient to maintain neumorphic surface */
    border-color: transparent;
  }
</style>
