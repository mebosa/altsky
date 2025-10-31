<script lang="ts">
  import { theme, themeOptions } from '$lib/theme';

  function selectTheme(id: string) {
    theme.select(id);
  }
</script>

<div class="theme-picker" data-mode={$theme.mode}>
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

<style>
  .theme-picker {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 8px 0;
    margin: 12px 0 20px;
    color: var(--theme-text-secondary);
  }

  .title {
    font-size: 0.7rem;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    font-weight: 600;
  }

  .swatches {
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
  }

  button {
    position: relative;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
    padding: 4px 6px 8px;
    min-width: 48px;
    border-radius: 12px;
    border: 1px solid transparent;
    background: rgba(15, 23, 42, 0.16);
    color: var(--theme-text-soft);
    cursor: pointer;
    transition: transform 0.25s ease, box-shadow 0.25s ease, border-color 0.25s ease,
      background 0.25s ease;
  }

  button.light {
    background: rgba(255, 255, 255, 0.75);
    color: var(--theme-text-secondary);
  }

  button.special {
    background: rgba(244, 114, 182, 0.18);
  }

  button:hover {
    transform: translateY(-2px);
  }

  button.selected {
    border-color: var(--theme-accent);
    box-shadow: 0 10px 24px var(--theme-glow);
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.12), rgba(255, 255, 255, 0.04));
  }

  button.light.selected {
    box-shadow: 0 10px 20px rgba(15, 23, 42, 0.12);
    border-color: rgba(15, 23, 42, 0.18);
  }

  button.special.selected {
    box-shadow: 0 12px 28px rgba(244, 114, 182, 0.35);
  }

  .chip {
    position: relative;
    width: 32px;
    height: 16px;
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
    width: 11px;
    height: 11px;
    top: -8px;
    background: var(--swatch-primary);
    clip-path: polygon(50% 0, 0 100%, 100% 100%);
    filter: drop-shadow(0 2px 6px rgba(244, 114, 182, 0.45));
  }

  button[data-theme='catgirl'] .chip::before {
    left: 6px;
    transform: rotate(-8deg);
  }

  button[data-theme='catgirl'] .chip::after {
    right: 6px;
    transform: rotate(8deg);
    background: var(--swatch-secondary);
  }

  button[data-theme='catgirl'] .face {
    display: block;
  }

  .name {
    font-size: 0.7rem;
    font-weight: 600;
    color: inherit;
    opacity: 0;
    transform: translateY(2px);
    transition: opacity 0.2s ease, transform 0.2s ease;
    text-align: center;
  }

  button:hover .name {
    opacity: 0.45;
    transform: translateY(0);
  }

  button.selected .name {
    opacity: 1;
    transform: translateY(0);
  }

  .marker {
    font-size: 0.7rem;
    color: #fde68a;
    opacity: 0;
    transition: opacity 0.2s ease;
  }

  button.special.selected .marker {
    opacity: 1;
  }

  @media (max-width: 720px) {
    .theme-picker {
      flex-wrap: wrap;
      gap: 8px;
    }

    .title {
      width: 100%;
    }
  }
</style>
