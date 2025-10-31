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
    border: 1px solid #1f2933;
    background: #0f172a;
    color: #e2e8f0;
    cursor: pointer;
    font-size: 0.95rem;
    transition: background 0.15s ease, color 0.15s ease, border 0.15s ease;
  }

  button:hover {
    background: #1f2a44;
  }

  .value-active {
    background: linear-gradient(135deg, #2563eb, #9333ea);
    color: white;
    border-color: transparent;
  }
</style>
