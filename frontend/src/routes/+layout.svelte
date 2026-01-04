<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import ThemePicker from '$lib/components/ThemePicker.svelte';
  import GoogleAnalytics from '$lib/components/GoogleAnalytics.svelte';
  import { theme, gradient } from '$lib/theme';

  const gaId = import.meta.env.VITE_GA_ID;
  import { iconPack } from '$lib/iconPack';

  let teardownBackground: (() => void) | undefined;
  let teardownIconPack: (() => void) | undefined;

  onMount(() => {
    theme.init();
    gradient.init();
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
    let currentX = 50;
    let currentY = 50;
    let targetX = 50;
    let targetY = 50;
    let isIdle = false;

    const clamp = (value: number, min: number, max: number) => Math.min(Math.max(value, min), max);

    const setPositions = (x: number, y: number) => {
      const primaryX = clamp(x, 0, 100);
      const primaryY = clamp(y, 0, 100);
      const secondaryX = clamp(primaryX + 26, 0, 100);
      const secondaryY = clamp(primaryY - 18, 0, 100);
      // 부드러운 전환을 위해 sin 함수 사용
      const offsetMultiplier = Math.sin((primaryX / 100) * Math.PI) * 18;
      const tertiaryX = clamp(primaryX + offsetMultiplier, 0, 100);
      const tertiaryY = clamp(primaryY + 28, 0, 100);

      root.style.setProperty('--cursor-x', `${primaryX}%`);
      root.style.setProperty('--cursor-y', `${primaryY}%`);
      root.style.setProperty('--cursor-secondary-x', `${secondaryX}%`);
      root.style.setProperty('--cursor-secondary-y', `${secondaryY}%`);
      root.style.setProperty('--cursor-tertiary-x', `${tertiaryX}%`);
      root.style.setProperty('--cursor-tertiary-y', `${tertiaryY}%`);
    };

    const lerp = (start: number, end: number, t: number) => {
      return start * (1 - t) + end * t;
    };

    const animateTo = (x: number, y: number) => {
      targetX = x;
      targetY = y;
      
      if (!frame) {
        const animate = () => {
          // 상태 전환 시 더 부드러운 속도 조정
          const speed = isIdle ? 0.02 : 0.08;  // 양쪽 모두 속도를 낮춰서 부드럽게
          currentX = lerp(currentX, targetX, speed);
          currentY = lerp(currentY, targetY, speed);
          setPositions(currentX, currentY);

          // 항상 애니메이션 지속
          frame = requestAnimationFrame(animate);
        };
        frame = requestAnimationFrame(animate);
      }
    };

    let lastTime = Date.now();
    let lastX = 50;
    let lastY = 50;
    
    const randomize = () => {
      const currentTime = Date.now();
      const deltaTime = (currentTime - lastTime) * 0.0003;
      lastTime = currentTime;
      
      // 이전 위치를 기반으로 부드럽게 다음 위치 계산
      const time = currentTime * 0.0003;
      const newX = 50 + Math.cos(time) * 25 + Math.sin(time * 0.5) * 15;
      const newY = 50 + Math.sin(time * 0.7) * 25 + Math.cos(time * 0.3) * 15;
      
      // 이전 위치와 새로운 위치를 보간하여 부드러운 전환
      lastX = lerp(lastX, newX, 0.1);
      lastY = lerp(lastY, newY, 0.1);
      
      animateTo(lastX, lastY);
    };

    const startRandom = () => {
      if (intervalId) return;
      lastTime = Date.now();
      // 현재 위치에서 시작
      lastX = currentX;
      lastY = currentY;
      randomize();
      // 부드러운 움직임을 위한 빈번한 업데이트
      intervalId = window.setInterval(() => randomize(), 16);
    };

    const stopRandom = () => {
      if (!intervalId) return;
      window.clearInterval(intervalId);
      intervalId = null;
    };

    const idleDelay = 2000;

    const clearIdle = () => {
      if (idleTimeout !== null) {
        clearTimeout(idleTimeout);
        idleTimeout = null;
      }
    };

    const scheduleIdle = () => {
      clearIdle();
      idleTimeout = window.setTimeout(() => {
        currentX = targetX;
        currentY = targetY;
        lastX = currentX;
        lastY = currentY;
        isIdle = true;
        startRandom();
      }, idleDelay);
    };

    let lastMouseX = 50;
    let lastMouseY = 50;
    let isTransitioning = false;
    let transitionStartTime = 0;
    const TRANSITION_DURATION = 500; // 전환 시간 (밀리초)

    const handlePointerMove = (event: PointerEvent) => {
      if (!pointerActive) return;
      const { clientX, clientY } = event;
      const x = (clientX / window.innerWidth) * 100;
      const y = (clientY / window.innerHeight) * 100;
      
      // 마우스 위치 업데이트
      lastMouseX = x;
      lastMouseY = y;
      
      // 마우스 움직임에 따른 부드러운 전환
      if (isIdle) {
        // idle 상태에서 마우스 움직임으로 전환할 때
        isTransitioning = true;
        transitionStartTime = Date.now();
        isIdle = false;
        // 자동 움직임은 전환이 완료된 후에 중지
      }
      
      if (isTransitioning) {
        const progress = Math.min((Date.now() - transitionStartTime) / TRANSITION_DURATION, 1);
        if (progress >= 1) {
          isTransitioning = false;
          stopRandom();
        }
        // 전환 중에는 현재 자동 위치와 마우스 위치를 보간
        const transitionX = lerp(currentX, x, progress);
        const transitionY = lerp(currentY, y, progress);
        animateTo(transitionX, transitionY);
      } else {
        animateTo(x, y);
      }

      // Reset idle timer with gradual transition
      scheduleIdle();
    };

    const enablePointer = () => {
      if (pointerActive) return;
      pointerActive = true;
      window.addEventListener('pointermove', handlePointerMove);
    };

    const disablePointer = () => {
      if (!pointerActive) return;
      pointerActive = false;
      window.removeEventListener('pointermove', handlePointerMove);
    };

    const applyMode = (coarse: boolean) => {
      if (coarse) {
        enablePointer();
        startRandom();
      } else {
        stopRandom();
        enablePointer();
      }
    };

    const handlePointerPreferenceChange = (event?: MediaQueryListEvent) => {
      applyMode(event ? event.matches : pointerQuery.matches);
    };

    if (pointerQuery.addEventListener) {
      pointerQuery.addEventListener('change', handlePointerPreferenceChange);
    } else {
      pointerQuery.addListener(handlePointerPreferenceChange);
    }

    const handleVisibility = () => {
      if (document.hidden) {
        stopRandom();
        isIdle = false;
      } else if (pointerQuery.matches) {
        startRandom();
      } else {
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

<div class="app-shell">
  {#if gaId}
    <GoogleAnalytics id={gaId} />
  {/if}
  <ThemePicker />
  <div class="container">
    <slot />
  </div>
</div>

<style>
  .app-shell {
    display: flex;
    flex-direction: column;
    min-height: 100vh;
  }

  :global(:root) {
    --theme-accent: #5f71f5;
    --theme-accent-secondary: #1fb6a6;
    --theme-accent-alpha-20: rgba(95, 113, 245, 0.2);
    --theme-accent-alpha-22: rgba(95, 113, 245, 0.22);
    --theme-accent-alpha-25: rgba(95, 113, 245, 0.25);
    --theme-accent-alpha-28: rgba(95, 113, 245, 0.28);
    --theme-accent-alpha-32: rgba(95, 113, 245, 0.32);
    --theme-accent-alpha-40: rgba(95, 113, 245, 0.4);
    --theme-accent-alpha-50: rgba(95, 113, 245, 0.5);
    --theme-secondary-alpha-25: rgba(31, 182, 166, 0.25);
    --theme-secondary-alpha-32: rgba(31, 182, 166, 0.32);
    --theme-secondary-alpha-40: rgba(31, 182, 166, 0.4);
    --theme-bg: #050914;
    --theme-bg-muted: #0b1225;
    --theme-surface: rgba(9, 14, 25, 0.9);
    --theme-surface-elevated: rgba(10, 16, 30, 0.82);
    --theme-surface-border: rgba(148, 163, 184, 0.22);
    --theme-text-primary: #e5e7eb;
    --theme-text-secondary: #d2d7e0;
    --theme-text-soft: #c0c7d6;
    --theme-chip-bg: rgba(9, 14, 25, 0.7);
    --theme-chip-border: rgba(148, 163, 184, 0.22);
    --theme-chip-text: #e5e7eb;
    --theme-header-gradient: linear-gradient(135deg, rgba(95, 113, 245, 0.16), rgba(31, 182, 166, 0.16));
    --theme-featured-gradient: linear-gradient(135deg, rgba(95, 113, 245, 0.2), rgba(31, 182, 166, 0.2));
    --theme-card-shadow: 0 12px 32px rgba(5, 9, 20, 0.38);
    --theme-progress-start: #7ab3ff;
    --theme-progress-end: #5be0c8;
    --theme-control-bg: rgba(12, 18, 32, 0.86);
    --theme-control-hover: rgba(19, 27, 43, 0.9);
    --theme-control-border: rgba(148, 163, 184, 0.32);
    --theme-form-bg: rgba(12, 18, 32, 0.92);
    --theme-form-border: rgba(148, 163, 184, 0.34);
    --theme-tag-bg: rgba(95, 113, 245, 0.16);
    --theme-tag-border: rgba(95, 113, 245, 0.26);
    --theme-glow: rgba(95, 113, 245, 0.28);
    --cursor-x: 40%;
    --cursor-y: 32%;
    --cursor-secondary-x: 68%;
    --cursor-secondary-y: 20%;
    --cursor-tertiary-x: 24%;
    --cursor-tertiary-y: 70%;
    --bg-radial-1: rgba(95, 113, 245, 0.18);
    --bg-radial-2: rgba(31, 182, 166, 0.12);
    --bg-radial-3: rgba(148, 163, 184, 0.12);
    --neu-elevated: 12px 12px 28px rgba(0, 0, 0, 0.35), -12px -12px 28px rgba(80, 110, 160, 0.14);
    --neu-soft: 8px 8px 18px rgba(0, 0, 0, 0.32), -8px -8px 18px rgba(80, 110, 160, 0.12);
    --neu-inset: inset 6px 6px 14px rgba(0, 0, 0, 0.28), inset -6px -6px 14px rgba(80, 110, 160, 0.16);
  }

  :global(html),
  :global(body) {
    min-height: 100%;
  }

  :global(body) {
    margin: 0;
    background: var(--theme-bg);
    color: var(--theme-text-primary);
    font-family: 'Space Grotesk', 'Inter', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    font-variant-numeric: lining-nums tabular-nums;
    transition: background 0.6s cubic-bezier(0.16, 1, 0.3, 1), color 0.6s ease, background-position 0.8s ease-in-out;
    position: relative;
  }

  /* Gradients removed: solid background only */



  :global(html.theme-animating *),
  :global(html.theme-animating *::before),
  :global(html.theme-animating *::after) {
    transition-property: background-color, color, border-color, box-shadow, transform, fill, stroke;
    transition-duration: 0.6s;
    transition-timing-function: cubic-bezier(0.16, 1, 0.3, 1);
  }

  .container {
    flex: 1;
    width: 100%;
    max-width: 960px;
    margin: 40px auto;
    padding: 0 18px;
    box-sizing: border-box;
  }
</style>
