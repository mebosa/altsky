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
    margin: 64px auto;
    padding: 0 16px;
    display: flex;
    flex-direction: column;
    gap: 16px;
    color: var(--theme-text-primary);
  }

  .row {
    display: flex;
    gap: 8px;
    backdrop-filter: blur(16px);
  }

  input {
    flex: 1;
    padding: 12px 14px;
    font-size: 16px;
    border: 1px solid var(--theme-form-border);
    border-radius: 12px;
    background: var(--theme-form-bg);
    color: var(--theme-text-primary);
    transition: border-color 0.25s ease, box-shadow 0.25s ease;
    box-shadow: 0 12px 24px rgba(15, 23, 42, 0.18);
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
    padding: 12px 16px;
    border-radius: 12px;
    border: none;
    background: linear-gradient(135deg, var(--theme-accent), var(--theme-accent-secondary));
    color: #ffffff;
    cursor: pointer;
    font-weight: 600;
    letter-spacing: 0.01em;
    box-shadow: 0 18px 32px rgba(15, 23, 42, 0.32);
    transition: transform 0.25s ease, box-shadow 0.25s ease, opacity 0.25s ease;
  }

  button:hover {
    transform: translateY(-2px);
    box-shadow: 0 22px 36px rgba(15, 23, 42, 0.4);
  }

  button:focus-visible {
    outline: 3px solid rgba(255, 255, 255, 0.35);
    outline-offset: 2px;
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
    background: var(--theme-chip-bg);
    border: 1px solid var(--theme-chip-border);
    cursor: pointer;
    transition: background 0.25s ease, border 0.25s ease, transform 0.2s ease;
    color: var(--theme-chip-text);
    box-shadow: 0 12px 20px rgba(15, 23, 42, 0.18);
  }

  .chip:hover,
  .chip:focus-visible {
    transform: translateY(-2px);
    background: var(--theme-accent-alpha-22);
    border-color: var(--theme-accent);
    outline: none;
  }

  h1 {
    font-size: 42px;
    margin: 0 0 12px;
    letter-spacing: -0.03em;
    color: var(--theme-text-primary);
  }

  p.muted {
    color: var(--theme-text-soft);
    margin: 0 0 24px;
  }

  .error-message {
    padding: 12px 16px;
    background: rgba(239, 68, 68, 0.1);
    border: 1px solid rgba(239, 68, 68, 0.2);
    color: rgb(239, 68, 68);
    border-radius: 12px;
    font-size: 0.95rem;
  }

  @media (max-width: 640px) {
    .row {
      flex-direction: column;
    }

    button {
      width: 100%;
    }
  }
</style>

<div class="wrap">
  <h1>AltSky</h1>
  <p class="muted">Enter a Minecraft username to view Hypixel SkyBlock stats.</p>

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
