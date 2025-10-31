<script lang="ts">
  import { goto } from '$app/navigation';
  import { debounce, loadRecent, saveRecent } from '$lib/utils';

  let name = '';
  let recent: string[] = [];

  function toUser(raw: string) {
    const value = raw.trim();
    if (!value) return;
    saveRecent(value);
    recent = loadRecent();
    goto(`/u/${encodeURIComponent(value)}`);
  }

  const debounced = debounce((value: string) => {
    name = value;
  }, 0);

  function onKey(event: KeyboardEvent) {
    if (event.key === 'Enter') {
      toUser(name);
    }
  }

  $: recent = loadRecent();
</script>

<style>
  .wrap {
    max-width: 720px;
    margin: 48px auto;
    padding: 0 16px;
  }

  .row {
    display: flex;
    gap: 8px;
  }

  input {
    flex: 1;
    padding: 12px 14px;
    font-size: 16px;
    border: 1px solid #d1d5db;
    border-radius: 10px;
  }

  button {
    padding: 12px 16px;
    border-radius: 10px;
    border: 1px solid #111827;
    background: #111827;
    color: white;
    cursor: pointer;
  }

  .chips {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 12px;
  }

  .chip {
    padding: 6px 12px;
    border-radius: 999px;
    background: #f3f4f6;
    border: 1px solid transparent;
    cursor: pointer;
    transition: background 0.15s ease, border 0.15s ease;
  }

  .chip:hover,
  .chip:focus-visible {
    background: #e0e7ff;
    border-color: #6366f1;
    outline: none;
  }

  h1 {
    font-size: 42px;
    margin: 0 0 12px;
  }

  p.muted {
    color: #6b7280;
    margin: 0 0 24px;
  }
</style>

<div class="wrap">
  <h1>AltSky</h1>
  <p class="muted">Enter a Minecraft username to view Hypixel SkyBlock stats.</p>

  <div class="row">
    <input
      placeholder="e.g. Technoblade"
      value={name}
      on:input={(event) => debounced((event.target as HTMLInputElement).value)}
      on:keydown={onKey}
    />
    <button type="button" on:click={() => toUser(name)}>Search</button>
  </div>

  {#if recent.length}
    <div class="chips">
      {#each recent as r}
        <button
          type="button"
          class="chip"
          on:click={() => toUser(r)}
        >
          {r}
        </button>
      {/each}
    </div>
  {/if}
</div>
