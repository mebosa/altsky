<script lang="ts">
  import { onMount, createEventDispatcher } from 'svelte';
  import CaretDownIcon from '$lib/icons/CaretDownIcon.svelte';
  import { theme, themeOptions } from '$lib/theme';
  import { iconPack, iconPackOptions } from '$lib/iconPack';

  let expanded = false;
  let pointerCoarse = false;
  let paletteShell: HTMLElement | null = null;
  let idleFrame: number | null = null;
  let idleTimeout: number | null = null;
  let mediaQuery: MediaQueryList | null = null;
  let detachMedia: (() => void) | null = null;

  const dispatch = createEventDispatcher();

  function clamp(value: number) {
    return Math.max(0, Math.min(100, value));
  }

  function applyGlow(xPercent: number, yPercent: number) {
    if (!paletteShell) return;
    paletteShell.style.setProperty('--glow-x', `${clamp(xPercent)}%`);
    paletteShell.style.setProperty('--glow-y', `${clamp(yPercent)}%`);
  }

  function cancelIdleAnimation() {
    if (idleTimeout !== null) {
      clearTimeout(idleTimeout);
      idleTimeout = null;
    }
    if (idleFrame !== null) {
      cancelAnimationFrame(idleFrame);
      idleFrame = null;
    }
  }

  function startIdleAnimation(delay = 1200) {
    if (pointerCoarse) return;
    cancelIdleAnimation();
    idleTimeout = window.setTimeout(() => {
      const loop = (time: number) => {
        const t = time / 1000;
        const x = 50 + Math.cos(t * 0.4) * 18;
        const y = 46 + Math.sin(t * 0.32) * 20;
        applyGlow(x, y);
        idleFrame = requestAnimationFrame(loop);
      };
      idleFrame = requestAnimationFrame(loop);
    }, delay);
  }

  function openPalette() {
    if (expanded) return;
    expanded = true;
    cancelIdleAnimation();
  }

  function closePalette() {
    if (!expanded) return;
    expanded = false;
    startIdleAnimation();
  }

  function togglePalette() {
    if (expanded) {
      closePalette();
    } else {
      openPalette();
    }
  }

  function handleToggleKey(event: KeyboardEvent) {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      togglePalette();
    }
  }

  function handlePointerMove(event: MouseEvent) {
    if (pointerCoarse || !paletteShell) return;
    cancelIdleAnimation();
    const rect = paletteShell.getBoundingClientRect();
    const x = ((event.clientX - rect.left) / rect.width) * 100;
    const y = ((event.clientY - rect.top) / rect.height) * 100;
    applyGlow(x, y);
    startIdleAnimation();
  }

  function handleMouseEnter() {
    if (pointerCoarse) return;
    openPalette();
    cancelIdleAnimation();
  }

  function handleMouseLeave(event: MouseEvent) {
    if (pointerCoarse) return;
    const next = event.relatedTarget as Node | null;
    if (next && paletteShell?.contains(next)) return;
    closePalette();
  }

  function handleFocusOut(event: FocusEvent) {
    if (!expanded) return;
    const next = event.relatedTarget as Node | null;
    if (next && paletteShell?.contains(next)) return;
    closePalette();
  }

  function selectTheme(id: string) {
    theme.select(id);
    dispatch('theme', { id });
  }

  function selectPack(id: string) {
    iconPack.select(id);
  }

  function clickOutside(node: HTMLElement) {
    const handle = (event: MouseEvent) => {
      if (!expanded) return;
      if (!node.contains(event.target as Node)) {
        closePalette();
      }
    };
    document.addEventListener('click', handle);
    return {
      destroy() {
        document.removeEventListener('click', handle);
      }
    };
  }

  onMount(() => {
    if (typeof window === 'undefined') return;
    applyGlow(50, 45);
    startIdleAnimation(0);

    const coarseQuery = window.matchMedia('(pointer: coarse)');
    const fineQuery = window.matchMedia('(pointer: fine)');

    const computePointerMode = () => {
      const coarse = coarseQuery.matches;
      const fine = fineQuery.matches;
      return coarse && !fine;
    };

    const updatePointerMode = (_event?: MediaQueryListEvent) => {
      pointerCoarse = computePointerMode();
      if (pointerCoarse) closePalette();
    };

    updatePointerMode();

    const attachListener = (mq: MediaQueryList, handler: (event: MediaQueryListEvent) => void) => {
      if (mq.addEventListener) {
        mq.addEventListener('change', handler);
        return () => mq.removeEventListener('change', handler);
      }
      // @ts-ignore addListener fallback for older browsers
      mq.addListener(handler);
      return () => {
        // @ts-ignore removeListener fallback
        mq.removeListener(handler);
      };
    };

    const detachCoarse = attachListener(coarseQuery, updatePointerMode);
    const detachFine = attachListener(fineQuery, updatePointerMode);
    detachMedia = () => {
      detachCoarse();
      detachFine();
    };

    return () => {
      detachMedia?.();
      cancelIdleAnimation();
    };
  });
</script>


<aside
  bind:this={paletteShell}
  class="palette-shell"
  class:expanded
  data-mode={$theme.mode}
  on:mouseenter={handleMouseEnter}
  on:mouseleave={handleMouseLeave}
  on:mousemove={handlePointerMove}
  on:focusin={() => {
    if (!pointerCoarse) openPalette();
  }}
  on:focusout={handleFocusOut}
  use:clickOutside>
  <button
    type="button"
    class="toggle"
    on:click|stopPropagation={togglePalette}
    on:keydown={handleToggleKey}
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
          <span class="chip" aria-hidden="true">
            <span class="grain"></span>
          </span>
          <span class="name">{option.label}</span>
          {#if option.special}
            <span class="marker" aria-hidden="true">*</span>
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
    align-items: flex-start;
    gap: 8px;
    z-index: 20;
    color: var(--theme-text-secondary);
    pointer-events: auto;
    --glow-x: 50%;
    --glow-y: 45%;
  }

  .palette-shell:not(.expanded) {
    gap: 0;
  }

  .palette-shell:not(.expanded) .panel {
    max-width: 0;
    padding: 0;
    margin: 0;
    border-width: 0;
    height: 0;
  }

  .toggle {
    position: relative;
    width: 34px;
    height: 34px;
    border-radius: 10px;
    border: 1px solid rgba(148, 163, 184, 0.28);
    background: rgba(9, 13, 24, 0.8);
    color: var(--theme-text-secondary);
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    backdrop-filter: blur(8px);
    pointer-events: auto;
    overflow: hidden;
    transition: background 0.25s ease, transform 0.25s ease, border-color 0.25s ease, box-shadow 0.25s ease;
  }

  .toggle:hover,
  .toggle:focus-visible {
    background: rgba(95, 113, 245, 0.2);
    border-color: rgba(95, 113, 245, 0.6);
    box-shadow: 0 6px 16px rgba(5, 7, 14, 0.4);
    outline: none;
  }

  .toggle::after {
    content: '';
    position: absolute;
    inset: -20%;
    background: radial-gradient(
      60% 60% at var(--glow-x) var(--glow-y),
      rgba(59, 130, 246, 0.38),
      transparent 70%
    );
    opacity: 0;
    transition: opacity 0.35s ease;
    pointer-events: none;
  }

  .toggle:hover::after,
  .palette-shell.expanded .toggle::after {
    opacity: 0.85;
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
    border: 1px solid rgba(148, 163, 184, 0.24);
    background: rgba(7, 11, 20, 0.88);
    backdrop-filter: blur(12px);
    box-shadow: 0 14px 28px rgba(5, 7, 14, 0.38);
    max-width: 280px;
    opacity: 0;
    transform: translateX(-12px) scale(0.96);
    pointer-events: none;
    transition: opacity 0.25s ease, transform 0.25s ease;
    overflow: hidden;
  }

  .panel::before {
    content: '';
    position: absolute;
    inset: -35%;
    background: radial-gradient(
      45% 45% at var(--glow-x) var(--glow-y),
      rgba(95, 113, 245, 0.28),
      rgba(99, 102, 241, 0.18),
      transparent 70%
    );
    opacity: 0;
    transition: opacity 0.4s ease;
    pointer-events: none;
  }

  .palette-shell.expanded .panel {
    opacity: 1;
    transform: translateX(0) scale(1);
    pointer-events: auto;
  }

  .palette-shell.expanded .panel::before {
    opacity: 0.95;
  }

  .title {
    font-size: 0.64rem;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    font-weight: 600;
    opacity: 0.72;
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
    padding: 8px 4px 10px;
    border-radius: 12px;
    border: 1px solid rgba(148, 163, 184, 0.16);
    background: rgba(12, 18, 32, 0.6);
    color: var(--theme-text-secondary);
    cursor: pointer;
    transition: transform 0.25s ease, box-shadow 0.25s ease, border-color 0.25s ease,
      background 0.25s ease;
  }

  .swatches button.light {
    background: rgba(255, 255, 255, 0.78);
    color: var(--theme-text-secondary);
  }

  .swatches button.special {
    border-color: rgba(95, 113, 245, 0.3);
  }

  .swatches button:hover,
  .swatches button:focus-visible {
    transform: translateY(-2px);
    border-color: var(--theme-accent-alpha-32);
    background: rgba(12, 18, 32, 0.72);
    outline: none;
  }

  .swatches button.selected {
    border-color: var(--theme-accent);
    box-shadow: 0 10px 18px var(--theme-glow);
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0.02));
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
    box-shadow: 0 6px 14px rgba(5, 7, 14, 0.35);
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
    isolation: isolate;
  }

  .swatches button.selected .chip {
    box-shadow: 0 8px 16px var(--theme-glow);
  }

  .grain {
    position: absolute;
    inset: 0;
    background: radial-gradient(circle at 30% 30%, rgba(255, 255, 255, 0.24), transparent 48%),
      radial-gradient(circle at 70% 70%, rgba(255, 255, 255, 0.16), transparent 46%);
    opacity: 0.5;
    mix-blend-mode: screen;
  }

  .name {
    font-size: 0.66rem;
    font-weight: 600;
    color: var(--theme-text-secondary);
    opacity: 0.65;
    transform: translateY(0);
    transition: opacity 0.18s ease;
    text-align: center;
  }

  .swatches button.selected .name {
    opacity: 1;
  }

  .marker {
    font-size: 0.65rem;
    color: #fde68a;
    opacity: 0.45;
    transition: opacity 0.18s ease;
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

    .palette-shell:not(.expanded) {
      gap: 0;
    }

    .panel {
      max-width: min(260px, calc(100vw - 80px));
    }
  }
</style>

