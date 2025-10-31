<script lang="ts">
  import { onMount } from 'svelte';
  import CaretDownIcon from '$lib/icons/CaretDownIcon.svelte';
  import { theme, themeOptions } from '$lib/theme';

  let expanded = false;
  let pointerCoarse = false;
  let mediaQuery: MediaQueryList | null = null;

  onMount(() => {
    if (typeof window === 'undefined') return;

    const setMode = (matches: boolean) => {
      pointerCoarse = matches;
      if (!pointerCoarse) {
        expanded = false;
      }
    };

    mediaQuery = window.matchMedia('(pointer: coarse)');
    setMode(mediaQuery.matches);

    const handler = (event: MediaQueryListEvent) => setMode(event.matches);
    if (mediaQuery.addEventListener) {
      mediaQuery.addEventListener('change', handler);
      return () => mediaQuery?.removeEventListener('change', handler);
    }

    mediaQuery.addListener(handler);
    return () => mediaQuery?.removeListener(handler);
  });

  function selectTheme(id: string) {
    theme.select(id);
  }

  function showPalette() {
    if (!pointerCoarse) {
      expanded = true;
    }
  }

  function hidePalette() {
    if (!pointerCoarse) {
      expanded = false;
    }
  }

  function handleFocusOut(event: FocusEvent) {
    if (pointerCoarse) return;
    const target = event.relatedTarget as HTMLElement | null;
    const current = event.currentTarget as HTMLElement;
    if (target && current.contains(target)) {
      return;
    }
    expanded = false;
  }

  function togglePalette() {
    if (pointerCoarse) {
      expanded = !expanded;
    }
  }
</script>

<aside
  class="palette-shell"
  class:expanded={expanded}
  data-mode={$theme.mode}
  on:mouseenter={showPalette}
  on:mouseleave={hidePalette}
  on:focusin={() => (expanded = true)}
  on:focusout={handleFocusOut}
>
  <button
    type="button"
    class="toggle"
    on:click={togglePalette}
    aria-label={expanded ? 'Hide theme palette' : 'Show theme palette'}
    aria-expanded={expanded}
  >
    <CaretDownIcon />
  </button>
  <div class="panel" aria-hidden={!expanded}>
    <span class="title">Palette</span>
    <div class="swatches">
      {#each themeOptions as option}
        <button
          type="button"
          class:selected={$theme.id === option.id}
          class:light={option.mode === 'light'}
          class:special={option.special}
          style={`--swatch-primary:${option.primary};--swatch-secondary:${option.secondary}`}
          data-theme={option.id}
          on:click={() => selectTheme(option.id)}
          aria-label={`Activate ${option.label} theme`}
          aria-pressed={$theme.id === option.id}
        >
          <span class="chip">
            <span class="face" aria-hidden="true">=^._.^=</span>
          </span>
          <span class="name">{option.label}</span>
          {#if option.special}
            <span class="marker" aria-hidden="true">★</span>
          {/if}
        </button>
      {/each}
    </div>
  </div>
</aside>

<style>
  .palette-shell {
    position: fixed;
    top: 20px;
    left: 20px;
    display: flex;
    align-items: stretch;
    gap: 8px;
    z-index: 20;
    color: var(--theme-text-secondary);
    pointer-events: auto;
  }

  .toggle {
    width: 34px;
    height: 34px;
    border-radius: 10px;
    border: 1px solid rgba(148, 163, 184, 0.35);
    background: rgba(15, 23, 42, 0.55);
    color: var(--theme-text-secondary);
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    backdrop-filter: blur(10px);
    transition: background 0.25s ease, transform 0.25s ease, border-color 0.25s ease;
  }

  .toggle:hover,
  .toggle:focus-visible {
    background: rgba(37, 99, 235, 0.35);
    border-color: var(--theme-accent);
    outline: none;
  }

  .toggle :global(svg) {
    width: 16px;
    height: 16px;
    transition: transform 0.25s ease;
  }

  .palette-shell.expanded .toggle :global(svg) {
    transform: rotate(180deg);
  }

  .panel {
    position: relative;
    display: flex;
    flex-direction: column;
    gap: 10px;
    padding: 14px 16px;
    border-radius: 16px;
    border: 1px solid rgba(148, 163, 184, 0.28);
    background: rgba(15, 23, 42, 0.72);
    backdrop-filter: blur(14px);
    box-shadow: 0 18px 32px rgba(15, 23, 42, 0.4);
    max-width: 280px;
    opacity: 0;
    transform: translateX(-12px) scale(0.96);
    pointer-events: none;
    transition: opacity 0.25s ease, transform 0.25s ease;
  }

  .palette-shell.expanded .panel {
    opacity: 1;
    transform: translateX(0) scale(1);
    pointer-events: auto;
  }

  .title {
    font-size: 0.64rem;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    font-weight: 600;
    opacity: 0.7;
  }

  .swatches {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(52px, 1fr));
    gap: 6px;
  }

  button {
    position: relative;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
    padding: 6px 4px 10px;
    border-radius: 12px;
    border: 1px solid transparent;
    background: rgba(15, 23, 42, 0.22);
    color: var(--theme-text-soft);
    cursor: pointer;
    transition: transform 0.25s ease, box-shadow 0.25s ease, border-color 0.25s ease,
      background 0.25s ease;
  }

  button.light {
    background: rgba(255, 255, 255, 0.78);
    color: var(--theme-text-secondary);
  }

  button.special {
    background: rgba(244, 114, 182, 0.22);
  }

  button:hover,
  button:focus-visible {
    transform: translateY(-2px);
    outline: none;
  }

  button.selected {
    border-color: var(--theme-accent);
    box-shadow: 0 12px 26px var(--theme-glow);
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.16), rgba(255, 255, 255, 0.05));
  }

  button.light.selected {
    box-shadow: 0 12px 22px rgba(15, 23, 42, 0.16);
    border-color: rgba(15, 23, 42, 0.2);
  }

  button.special.selected {
    box-shadow: 0 14px 30px rgba(244, 114, 182, 0.4);
  }

  .chip {
    position: relative;
    width: 30px;
    height: 14px;
    border-radius: 999px;
    background: linear-gradient(135deg, var(--swatch-primary), var(--swatch-secondary));
    box-shadow: 0 6px 14px rgba(15, 23, 42, 0.22);
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
  }

  button.selected .chip {
    box-shadow: 0 8px 18px var(--theme-glow);
  }

  .face {
    display: none;
    font-size: 0.55rem;
    color: #fff7fb;
    text-shadow: 0 2px 6px rgba(15, 23, 42, 0.45);
    pointer-events: none;
  }

  button[data-theme='catgirl'] .chip::before,
  button[data-theme='catgirl'] .chip::after {
    content: '';
    position: absolute;
    width: 9px;
    height: 9px;
    top: -6px;
    background: var(--swatch-primary);
    clip-path: polygon(50% 0, 0 100%, 100% 100%);
    filter: drop-shadow(0 2px 6px rgba(244, 114, 182, 0.45));
  }

  button[data-theme='catgirl'] .chip::before {
    left: 5px;
    transform: rotate(-8deg);
  }

  button[data-theme='catgirl'] .chip::after {
    right: 5px;
    transform: rotate(8deg);
    background: var(--swatch-secondary);
  }

  button[data-theme='catgirl'] .face {
    display: block;
  }

  .name {
    font-size: 0.66rem;
    font-weight: 600;
    color: inherit;
    opacity: 0;
    transform: translateY(2px);
    transition: opacity 0.2s ease, transform 0.2s ease;
    text-align: center;
  }

  button:hover .name,
  button:focus-visible .name {
    opacity: 0.45;
    transform: translateY(0);
  }

  button.selected .name {
    opacity: 1;
    transform: translateY(0);
  }

  .marker {
    font-size: 0.65rem;
    color: #fde68a;
    opacity: 0;
    transition: opacity 0.2s ease;
  }

  button.special.selected .marker {
    opacity: 1;
  }

  @media (max-width: 720px) {
    .palette-shell {
      top: 14px;
      left: 14px;
      gap: 6px;
    }

    .panel {
      max-width: min(260px, calc(100vw - 80px));
    }
  }
</style>
