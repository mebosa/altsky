<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import ThemePicker from '$lib/components/ThemePicker.svelte';
  import { theme } from '$lib/theme';
  import { iconPack } from '$lib/iconPack';

  let teardownBackground: (() => void) | undefined;
  let teardownIconPack: (() => void) | undefined;

  onMount(() => {
    theme.init();
    iconPack.init();
    teardownIconPack = iconPack.subscribe((pack) => {
      if (typeof document !== 'undefined') {
        document.body.dataset.iconPack = pack.id;
      }
    });
    teardownBackground = initDynamicBackground();
  });

  onDestroy(() => {
    teardownBackground?.();
    teardownIconPack?.();
  });

  function initDynamicBackground() {
    if (typeof window === 'undefined') return () => {};

    const root = document.documentElement;
    const pointerQuery = window.matchMedia('(pointer: coarse)');

    let frame = 0;
    let intervalId: ReturnType<typeof setInterval> | null = null;
    let idleTimeout: ReturnType<typeof setTimeout> | null = null;
    let pointerActive = false;

    const clamp = (value: number, min: number, max: number) => Math.min(Math.max(value, min), max);

    const setPositions = (x: number, y: number) => {
      const primaryX = clamp(x, 0, 100);
      const primaryY = clamp(y, 0, 100);
      const secondaryX = clamp(primaryX + 26, 0, 100);
      const secondaryY = clamp(primaryY - 18, 0, 100);
      const tertiaryX = clamp(primaryX + (primaryX > 50 ? -18 : 18), 0, 100);
      const tertiaryY = clamp(primaryY + 28, 0, 100);

      root.style.setProperty('--cursor-x', `${primaryX}%`);
      root.style.setProperty('--cursor-y', `${primaryY}%`);
      root.style.setProperty('--cursor-secondary-x', `${secondaryX}%`);
      root.style.setProperty('--cursor-secondary-y', `${secondaryY}%`);
      root.style.setProperty('--cursor-tertiary-x', `${tertiaryX}%`);
      root.style.setProperty('--cursor-tertiary-y', `${tertiaryY}%`);
    };

    const animateTo = (x: number, y: number) => {
      if (frame) window.cancelAnimationFrame(frame);
      frame = window.requestAnimationFrame(() => setPositions(x, y));
    };

    const randomize = () => {
      const x = 18 + Math.random() * 64;
      const y = 14 + Math.random() * 60;
      animateTo(x, y);
    };

    const startRandom = () => {
      if (intervalId) return;
      clearIdle();
      randomize();
      intervalId = window.setInterval(() => randomize(), 2600 + Math.random() * 1600);
    };

    const stopRandom = () => {
      if (!intervalId) return;
      window.clearInterval(intervalId);
      intervalId = null;
    };

    const applyMode = (coarse: boolean) => {
      if (coarse) {
        enablePointer(); // Enable pointermove for touch devices
        startRandom();    // Also start random movement when idle
      } else {
        stopRandom();
        enablePointer();
        scheduleIdle();
      }
    };

    const handlePointerPreferenceChange = (event?: MediaQueryListEvent) => {
      applyMode(event ? event.matches : pointerQuery.matches);
    };

    if (pointerQuery.addEventListener) {
      pointerQuery.addEventListener('change', handlePointerPreferenceChange);
    } else {
      // Safari
      pointerQuery.addListener(handlePointerPreferenceChange);
    }

    const handleVisibility = () => {
      if (document.hidden) {
        stopRandom();
        clearIdle();
      } else if (pointerQuery.matches) {
        startRandom();
      } else {
        scheduleIdle();
        enablePointer();
      }
    };

    document.addEventListener('visibilitychange', handleVisibility);

    applyMode(pointerQuery.matches);
    if (!pointerQuery.matches) {
      animateTo(32, 28);
      scheduleIdle();
    }

    return () => {
      disablePointer();
      stopRandom();
      clearIdle();
      if (pointerQuery.removeEventListener) {
        pointerQuery.removeEventListener('change', handlePointerPreferenceChange);
      } else {
        pointerQuery.removeListener(handlePointerPreferenceChange);
      }
      document.removeEventListener('visibilitychange', handleVisibility);
      if (frame) window.cancelAnimationFrame(frame);
    };
  }
</script>

<div class="container">
  <ThemePicker />
  <slot />
</div>

<style>
  :global(:root) {
    --theme-accent: #2563eb;
    --theme-accent-secondary: #9333ea;
    --theme-accent-alpha-20: rgba(37, 99, 235, 0.2);
    --theme-accent-alpha-22: rgba(37, 99, 235, 0.22);
    --theme-accent-alpha-25: rgba(37, 99, 235, 0.25);
    --theme-accent-alpha-28: rgba(37, 99, 235, 0.28);
    --theme-accent-alpha-32: rgba(37, 99, 235, 0.32);
    --theme-accent-alpha-40: rgba(37, 99, 235, 0.4);
    --theme-accent-alpha-50: rgba(37, 99, 235, 0.5);
    --theme-secondary-alpha-25: rgba(147, 51, 234, 0.25);
    --theme-secondary-alpha-32: rgba(147, 51, 234, 0.32);
    --theme-secondary-alpha-40: rgba(147, 51, 234, 0.4);
    --theme-bg: #020617;
    --theme-bg-muted: #0f172a;
    --theme-surface: rgba(15, 23, 42, 0.85);
    --theme-surface-elevated: rgba(15, 23, 42, 0.75);
    --theme-surface-border: rgba(148, 163, 184, 0.25);
    --theme-text-primary: #e2e8f0;
    --theme-text-secondary: #cbd5f5;
    --theme-text-soft: #cbd5f5;
    --theme-chip-bg: rgba(15, 23, 42, 0.65);
    --theme-chip-border: rgba(148, 163, 184, 0.25);
    --theme-chip-text: #e2e8f0;
    --theme-header-gradient: linear-gradient(135deg, rgba(37, 99, 235, 0.25), rgba(147, 51, 234, 0.25));
    --theme-featured-gradient: linear-gradient(135deg, rgba(59, 130, 246, 0.28), rgba(147, 51, 234, 0.28));
    --theme-card-shadow: 0 16px 40px rgba(15, 23, 42, 0.45);
    --theme-progress-start: #38bdf8;
    --theme-progress-end: #8b5cf6;
    --theme-control-bg: rgba(15, 23, 42, 0.75);
    --theme-control-hover: rgba(30, 41, 59, 0.85);
    --theme-control-border: rgba(148, 163, 184, 0.35);
    --theme-form-bg: rgba(15, 23, 42, 0.85);
    --theme-form-border: rgba(148, 163, 184, 0.4);
    --theme-tag-bg: rgba(59, 130, 246, 0.2);
    --theme-tag-border: rgba(59, 130, 246, 0.35);
    --theme-glow: rgba(59, 130, 246, 0.34);
    --cursor-x: 40%;
    --cursor-y: 32%;
    --cursor-secondary-x: 68%;
    --cursor-secondary-y: 20%;
    --cursor-tertiary-x: 24%;
    --cursor-tertiary-y: 70%;
    --bg-radial-1: rgba(37, 99, 235, 0.32);
    --bg-radial-2: rgba(147, 51, 234, 0.26);
    --bg-radial-3: rgba(14, 165, 233, 0.2);
  }

  :global(html),
  :global(body) {
    min-height: 100%;
  }

  :global(body) {
    margin: 0;
    background:
      radial-gradient(circle at var(--cursor-x) var(--cursor-y), var(--bg-radial-1), transparent 58%),
      radial-gradient(circle at var(--cursor-secondary-x) var(--cursor-secondary-y), var(--bg-radial-2), transparent 64%),
      radial-gradient(circle at var(--cursor-tertiary-x) var(--cursor-tertiary-y), var(--bg-radial-3), transparent 72%),
      var(--theme-bg);
    color: var(--theme-text-primary);
    font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    transition: background 0.6s cubic-bezier(0.16, 1, 0.3, 1), color 0.6s ease, background-position 0.8s ease-in-out;
    position: relative;
  }

  :global(body)::before {
    content: '';
    position: fixed;
    inset: 0;
    pointer-events: none;
    background:
      radial-gradient(circle at 12% 18%, rgba(255, 255, 255, 0.08), transparent 58%),
      radial-gradient(circle at 82% 28%, rgba(255, 255, 255, 0.05), transparent 60%);
    opacity: 0.65;
    mix-blend-mode: screen;
    transition: opacity 0.6s ease;
  }

  :global(body[data-theme-mode='light']) {
    background:
      radial-gradient(circle at var(--cursor-x) var(--cursor-y), rgba(96, 165, 250, 0.28), transparent 58%),
      radial-gradient(circle at var(--cursor-secondary-x) var(--cursor-secondary-y), rgba(148, 163, 184, 0.22), transparent 64%),
      radial-gradient(circle at var(--cursor-tertiary-x) var(--cursor-tertiary-y), rgba(167, 139, 250, 0.2), transparent 70%),
      linear-gradient(135deg, rgba(248, 250, 252, 0.92), rgba(241, 245, 249, 0.92)),
      #f8fafc;
  }

  :global(body[data-theme-mode='light'])::before {
    opacity: 0.3;
    mix-blend-mode: normal;
  }

  :global(body[data-theme='catgirl']) {
    background:
      radial-gradient(circle at var(--cursor-x) var(--cursor-y), rgba(244, 114, 182, 0.42), transparent 58%),
      radial-gradient(circle at var(--cursor-secondary-x) var(--cursor-secondary-y), rgba(168, 85, 247, 0.34), transparent 64%),
      radial-gradient(circle at var(--cursor-tertiary-x) var(--cursor-tertiary-y), rgba(59, 130, 246, 0.18), transparent 72%),
      linear-gradient(135deg, rgba(24, 4, 31, 0.94), rgba(37, 8, 52, 0.92)),
      var(--theme-bg);
  }

  :global(body[data-theme='catgirl'])::before {
    background:
      radial-gradient(circle at 16% 20%, rgba(255, 176, 222, 0.6), transparent 52%),
      radial-gradient(circle at 84% 26%, rgba(178, 102, 255, 0.38), transparent 60%);
    opacity: 0.85;
    mix-blend-mode: lighten;
  }



  :global(html.theme-animating *),
  :global(html.theme-animating *::before),
  :global(html.theme-animating *::after) {
    transition-property: background-color, color, border-color, box-shadow, transform, fill, stroke;
    transition-duration: 0.6s;
    transition-timing-function: cubic-bezier(0.16, 1, 0.3, 1);
  }

  .container {
    max-width: 960px;
    margin: 28px auto;
    padding: 0 16px;
  }
</style>
