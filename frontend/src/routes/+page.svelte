<script lang="ts">
  import { goto } from '$app/navigation';
  import { loadRecent, saveRecent } from '$lib/utils';

  let name = '';
  let recent: string[] = [];
  let searchError = '';
  let isLoading = false;

  // Debounce function to prevent rapid consecutive calls
  function debounce(func: Function, wait: number) {
    let timeout: NodeJS.Timeout;
    return function executedFunction(...args: any[]) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  }

  // Debounced `toUser` - validates input, saves recent, and navigates.
  const toUser = debounce(async (raw: string) => {
    if (isLoading) return;
    isLoading = true;
    try {
      const value = raw.trim();
      if (!value) return;

      searchError = '';
      // 마인크래프트 유저네임 검증 (영문, 숫자, _만 허용)
      const sanitizedValue = value.replace(/[^a-zA-Z0-9_]/g, '');
      if (!sanitizedValue) {
        searchError = 'Invalid username format. Only letters, numbers, and underscores are allowed.';
        return;
      }

      if (sanitizedValue.length > 16) {
        searchError = 'Username is too long. Maximum length is 16 characters.';
        return;
      }

      // Save recent and update local list
      await saveRecent(sanitizedValue);
      recent = loadRecent();

      const targetPath = `/u/${encodeURIComponent(sanitizedValue)}`;
      try {
        if (typeof window !== 'undefined' && window.location.pathname === targetPath) {
          // full reload to guarantee the player route re-initializes
          window.location.href = targetPath;
        } else {
          await goto(targetPath, { replaceState: false });
        }
      } catch (err) {
        // Fallback to location change on any navigation error
        console.error('Navigation error:', err);
        if (typeof window !== 'undefined') window.location.href = targetPath;
      }
    } catch (error) {
      console.error('Navigation error:', error);
      searchError = 'An unexpected error occurred';
    } finally {
      isLoading = false;
    }
  }, 200);

  function handleSearch() {
    if (name.trim()) {
      toUser(name);
    }
  }

  function onKey(event: KeyboardEvent) {
    if (event.key === 'Enter') {
      handleSearch();
    }
  }

  $: recent = loadRecent();
</script>

<style>
  .wrap {
    max-width: 720px;
    margin: 88px auto 64px;
    padding: 0 18px;
    display: flex;
    flex-direction: column;
    gap: 20px;
    color: var(--theme-text-primary);
  }

  .hero {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
  }

  .eyebrow {
    font-size: 12px;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--theme-text-soft);
    margin: 0 0 6px;
  }

  .row {
    display: flex;
    gap: 10px;
    align-items: center;
  }

  input {
    flex: 1;
    padding: 14px 16px;
    font-size: 17px;
    border: 1px solid color-mix(in srgb, var(--theme-form-border) 90%, transparent);
    border-radius: 12px;
    background: color-mix(in srgb, var(--theme-form-bg) 90%, #040915 10%);
    color: var(--theme-text-primary);
    transition: border-color 0.25s ease, box-shadow 0.25s ease;
    box-shadow: none;
  }

  input::placeholder {
    color: var(--theme-text-soft);
  }

  input:focus {
    outline: none;
    border-color: var(--theme-accent);
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.25);
  }

  button {
    padding: 13px 18px;
    border-radius: 12px;
    border: 1px solid color-mix(in srgb, var(--theme-accent) 70%, #ffffff 10%);
    background: var(--theme-accent);
    color: #0b1020;
    cursor: pointer;
    font-weight: 600;
    letter-spacing: 0.01em;
    box-shadow: 0 12px 26px rgba(5, 7, 14, 0.3);
    transition: transform 0.2s ease, box-shadow 0.2s ease, opacity 0.2s ease;
  }

  button:hover {
    transform: translateY(-1px);
    box-shadow: 0 14px 28px rgba(5, 7, 14, 0.35);
  }

  button:focus-visible {
    outline: 2px solid color-mix(in srgb, var(--theme-accent) 80%, #ffffff 20%);
    outline-offset: 3px;
  }

  .chips {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 12px;
  }

  .chip {
    padding: 8px 12px;
    border-radius: 14px;
    background: color-mix(in srgb, var(--theme-chip-bg) 80%, transparent);
    border: 1px solid color-mix(in srgb, var(--theme-chip-border) 90%, transparent);
    cursor: pointer;
    transition: background 0.25s ease, border 0.25s ease, transform 0.2s ease;
    color: var(--theme-chip-text);
    box-shadow: none;
  }

  .chip:hover,
  .chip:focus-visible {
    transform: translateY(-1px);
    background: color-mix(in srgb, var(--theme-accent-alpha-25) 70%, transparent);
    border-color: color-mix(in srgb, var(--theme-accent) 60%, #ffffff 10%);
    outline: none;
  }

  h1 {
    font-size: clamp(40px, 6vw, 52px);
    margin: 0 0 10px;
    letter-spacing: -0.03em;
    color: var(--theme-text-primary);
  }

  p.muted {
    color: var(--theme-text-soft);
    margin: 0;
  }

  .error-message {
    padding: 12px 14px;
    background: rgba(239, 68, 68, 0.12);
    border: 1px solid rgba(239, 68, 68, 0.24);
    color: rgb(248, 180, 180);
    border-radius: 10px;
    font-size: 0.94rem;
  }

  .panel {
    border: 1px solid color-mix(in srgb, var(--theme-surface-border) 90%, transparent);
    border-radius: 16px;
    background: color-mix(in srgb, var(--theme-surface) 92%, transparent);
    padding: 20px;
    box-shadow: 0 10px 26px rgba(4, 7, 14, 0.32);
    backdrop-filter: blur(10px);
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 10px 14px;
    border-radius: 12px;
    border: 1px solid color-mix(in srgb, var(--theme-accent) 40%, #ffffff 10%);
    color: var(--theme-text-primary);
    background: color-mix(in srgb, var(--theme-accent-alpha-22) 60%, transparent);
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 0.01em;
  }

  .badge::before {
    content: '';
    width: 8px;
    height: 8px;
    border-radius: 999px;
    background: var(--theme-accent);
    box-shadow: 0 0 0 6px color-mix(in srgb, var(--theme-accent) 24%, transparent);
  }

  .recent {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  @media (max-width: 640px) {
    .row {
      flex-direction: column;
    }

    button {
      width: 100%;
    }

    .hero {
      flex-direction: column;
      align-items: flex-start;
    }
  }
</style>

<div class="wrap">
  <div class="hero">
    <div>
      <p class="eyebrow">Hypixel SkyBlock companion</p>
      <h1>AltSky</h1>
      <p class="muted">Enter a Minecraft username to view Hypixel SkyBlock stats.</p>
    </div>
    <span class="badge">Faster lookups, calmer UI</span>
  </div>

  <div class="panel">
    <div class="row">
      <input
        placeholder="e.g. Technoblade"
        bind:value={name}
        on:input={() => (searchError = '')}
        on:keydown={onKey}
      />
      <button type="button" on:click={handleSearch}>Search</button>
    </div>
    
    {#if searchError}
      <div class="error-message">
        {searchError}
      </div>
    {/if}

    {#if recent.length}
      <div class="recent">
        <span class="eyebrow" style="margin-bottom:0;">Recent</span>
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
      </div>
    {/if}
  </div>
</div>
