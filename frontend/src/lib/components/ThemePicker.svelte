<script lang="ts">
  import { onMount, createEventDispatcher } from 'svelte';
  import CaretDownIcon from '$lib/icons/CaretDownIcon.svelte';
  import { theme, themeOptions } from '$lib/theme';
  import { iconPack, iconPackOptions } from '$lib/iconPack';

  let expanded = false;
  let pointerCoarse = false;
  let mediaQuery: MediaQueryList | null = null;

  const dispatch = createEventDispatcher();

  function clickOutside(node: HTMLElement) {
    const handleClick = (event: MouseEvent) => {
      if (!node.contains(event.target as Node)) {
        setTimeout(() => {
          expanded = false;
        }, 0);
      }
    };

    document.addEventListener('click', handleClick);

    return {
      destroy() {
        document.removeEventListener('click', handleClick);
      }
    };
  }

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

  function showFromToggle() {
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

  function selectPack(id: string) {
    iconPack.select(id);
  }
</script>

<aside
  class="palette-shell"
  class:expanded
  data-mode={$theme.mode}
  on:mouseleave={hidePalette}
  on:focusin={() => (expanded = true)}
  on:focusout={handleFocusOut}
  use:clickOutside
  style={`pointer-events: ${expanded ? 'auto' : 'none'}`}>
  <button
    type="button"
    class="toggle"
    on:click={togglePalette}
    on:mouseenter={showFromToggle}
    aria-label={expanded ? 'Hide theme palette' : 'Show theme palette'}
    aria-expanded={expanded}>
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
    <div class="icon-pack">
      <span class="subtitle">Item Style</span>
      <div class="pack-options">
        {#each iconPackOptions as pack}
          <button
            type="button"
            class:active={$iconPack.id === pack.id}
            on:click={() => selectPack(pack.id)}
            aria-pressed={$iconPack.id === pack.id}
          >
            {pack.label}
          </button>
        {/each}
      </div>
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
    pointer-events: auto;
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

  .swatches button {
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

  .swatches button.light {
    background: rgba(255, 255, 255, 0.78);
    color: var(--theme-text-secondary);
  }

  .swatches button.special {
    background: rgba(244, 114, 182, 0.22);
  }

  .swatches button:hover,
  .swatches button:focus-visible {
    transform: translateY(-2px);
    outline: none;
  }

  .swatches button.selected {
    border-color: var(--theme-accent);
    box-shadow: 0 12px 26px var(--theme-glow);
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.16), rgba(255, 255, 255, 0.05));
  }

  .swatches button.light.selected {
    box-shadow: 0 12px 22px rgba(15, 23, 42, 0.16);
    border-color: rgba(15, 23, 42, 0.2);
  }

  .swatches button.special.selected {
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
    isolation: isolate;
  }

  .swatches button.selected .chip {
    box-shadow: 0 8px 18px var(--theme-glow);
  }

  .face {
    display: none;
    font-size: 0.55rem;
    color: #fff7fb;
    text-shadow: 0 2px 6px rgba(15, 23, 42, 0.45);
    pointer-events: none;
  }

  .swatches button[data-theme='catgirl'] .chip::before,
  .swatches button[data-theme='catgirl'] .chip::after {
    content: '';
    position: absolute;
    width: 9px;
    height: 9px;
    top: -6px;
    background: var(--swatch-primary);
    clip-path: polygon(50% 0, 0 100%, 100% 100%);
    filter: drop-shadow(0 2px 6px rgba(244, 114, 182, 0.45));
    z-index: -1;
  }

  .swatches button[data-theme='catgirl'] .chip::before {
    left: 5px;
    transform: rotate(-8deg);
  }

  .swatches button[data-theme='catgirl'] .chip::after {
    right: 5px;
    transform: rotate(8deg);
    background: var(--swatch-secondary);
  }

  .swatches button[data-theme='catgirl'] .face {
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

  .swatches button:hover .name,
  .swatches button:focus-visible .name {
    opacity: 0.45;
    transform: translateY(0);
  }

  .swatches button.selected .name {
    opacity: 1;
    transform: translateY(0);
  }

  .marker {
    font-size: 0.65rem;
    color: #fde68a;
    opacity: 0;
    transition: opacity 0.2s ease;
  }

  .swatches button.special.selected .marker {
    opacity: 1;
  }

  .icon-pack {
    margin-top: 12px;
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .subtitle {
    font-size: 0.62rem;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    font-weight: 600;
    opacity: 0.6;
  }

  .pack-options {
    display: inline-flex;
    gap: 6px;
    background: rgba(15, 23, 42, 0.4);
    padding: 4px;
    border-radius: 10px;
    border: 1px solid rgba(148, 163, 184, 0.25);
  }

  .pack-options button {
    border: none;
    border-radius: 8px;
    padding: 4px 10px;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.04em;
    color: var(--theme-text-soft);
    background: transparent;
    cursor: pointer;
    transition: background 0.2s ease, color 0.2s ease, transform 0.2s ease;
  }

  .pack-options button:hover,
  .pack-options button:focus-visible {
    color: var(--theme-text-secondary);
    background: rgba(59, 130, 246, 0.18);
    transform: translateY(-1px);
    outline: none;
  }

  .pack-options button.active {
    background: rgba(59, 130, 246, 0.26);
    color: #fff;
    box-shadow: 0 10px 18px rgba(59, 130, 246, 0.32);
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
