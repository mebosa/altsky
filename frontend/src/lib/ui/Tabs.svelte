<script lang="ts">
  import { createEventDispatcher } from 'svelte';

  export let tabs: { id: string; label: string }[] = [];
  export let value: string;

  const dispatch = createEventDispatcher<{ change: string }>();

  function select(id: string) {
    if (id === value) return;
    value = id;
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
    border: 1px solid var(--theme-control-border);
    background: var(--theme-control-bg);
    color: var(--theme-text-secondary);
    cursor: pointer;
    font-size: 0.95rem;
    transition: background 0.25s ease, color 0.25s ease, border 0.25s ease, transform 0.2s ease;
    box-shadow: 0 8px 18px rgba(15, 23, 42, 0.18);
  }

  button:hover {
    background: var(--theme-control-hover);
    transform: translateY(-2px);
  }

  .value-active {
    background: linear-gradient(135deg, var(--theme-accent), var(--theme-accent-secondary));
    color: #ffffff;
    border-color: transparent;
    box-shadow: 0 14px 26px rgba(15, 23, 42, 0.28);
  }
</style>
