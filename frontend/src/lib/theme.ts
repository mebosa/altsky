import { writable } from 'svelte/store';

export type ThemeMode = 'light' | 'dark';

export type ThemeDefinition = {
  id: string;
  label: string;
  primary: string;
  secondary: string;
  mode: ThemeMode;
  background: string;
  backgroundMuted: string;
  surface: string;
  surfaceElevated: string;
  border: string;
  textPrimary: string;
  textSecondary: string;
  textSoft: string;
  chipBackground: string;
  chipBorder: string;
  chipText: string;
  headerGradient: string;
  featuredGradient: string;
  cardShadow: string;
  progressStart: string;
  progressEnd: string;
  controlBg: string;
  controlHover: string;
  controlBorder: string;
  formBg: string;
  formBorder: string;
  tagBg: string;
  tagBorder: string;
  glow: string;
  shadowLight: string;
  shadowDark: string;
  special?: boolean;
};

const STORAGE_KEY = 'altsky_theme';
const GRADIENT_STORAGE_KEY = 'altsky_gradient';

function rgba(hex: string, alpha: number) {
  const normalized = hex.replace('#', '');
  const expanded =
    normalized.length === 3
      ? normalized
          .split('')
          .map((char) => char + char)
          .join('')
      : normalized;
  const value = parseInt(expanded, 16);
  const r = (value >> 16) & 0xff;
  const g = (value >> 8) & 0xff;
  const b = value & 0xff;
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

const darkBase = {
  mode: 'dark' as ThemeMode,
  background: '#2e323b',
  backgroundMuted: '#252830',
  surface: '#2e323b',
  surfaceElevated: '#2e323b',
  border: 'rgba(255, 255, 255, 0.05)',
  textPrimary: '#e2e8f0',
  textSecondary: '#a0aec0',
  textSoft: '#718096',
  chipBackground: '#2e323b',
  chipBorder: 'rgba(255, 255, 255, 0.05)',
  chipText: '#e2e8f0',
  cardShadow: '8px 8px 16px #252830, -8px -8px 16px #373c46',
  controlBg: '#2e323b',
  controlHover: '#323640',
  controlBorder: 'rgba(255, 255, 255, 0.05)',
  formBg: '#2e323b',
  formBorder: 'rgba(255, 255, 255, 0.05)',
  tagBg: 'rgba(59, 130, 246, 0.2)',
  tagBorder: 'rgba(59, 130, 246, 0.35)',
  shadowLight: '#373c46',
  shadowDark: '#252830'
};

const lightBase = {
  mode: 'light' as ThemeMode,
  background: '#e0e5ec',
  backgroundMuted: '#d1d9e6',
  surface: '#e0e5ec',
  surfaceElevated: '#e0e5ec',
  border: 'rgba(255, 255, 255, 0.4)',
  textPrimary: '#4a5568',
  textSecondary: '#718096',
  textSoft: '#a0aec0',
  chipBackground: '#e0e5ec',
  chipBorder: 'rgba(255, 255, 255, 0.4)',
  chipText: '#4a5568',
  cardShadow: '9px 9px 16px #a3b1c6, -9px -9px 16px #ffffff',
  controlBg: '#e0e5ec',
  controlHover: '#e6ebf2',
  controlBorder: 'rgba(255, 255, 255, 0.4)',
  formBg: '#e0e5ec',
  formBorder: 'rgba(255, 255, 255, 0.4)',
  tagBg: 'rgba(99, 102, 241, 0.16)',
  tagBorder: 'rgba(99, 102, 241, 0.2)',
  shadowLight: '#ffffff',
  shadowDark: '#a3b1c6'

};

export const themeOptions: ThemeDefinition[] = [
  {
    id: 'ocean',
    label: 'Ocean Blue',
    primary: '#2563eb',
    secondary: '#9333ea',
    headerGradient: 'linear-gradient(135deg, rgba(37, 99, 235, 0.25), rgba(147, 51, 234, 0.25))',
    featuredGradient: 'linear-gradient(135deg, rgba(59, 130, 246, 0.28), rgba(147, 51, 234, 0.28))',
    progressStart: '#38bdf8',
    progressEnd: '#8b5cf6',
    glow: 'rgba(59, 130, 246, 0.34)',
    ...darkBase
  },
  {
    id: 'emerald',
    label: 'Emerald Tide',
    primary: '#10b981',
    secondary: '#14b8a6',
    headerGradient: 'linear-gradient(135deg, rgba(16, 185, 129, 0.2), rgba(20, 184, 166, 0.28))',
    featuredGradient: 'linear-gradient(135deg, rgba(16, 185, 129, 0.26), rgba(20, 184, 166, 0.32))',
    progressStart: '#34d399',
    progressEnd: '#2dd4bf',
    glow: 'rgba(16, 185, 129, 0.36)',
    ...darkBase,
    tagBg: 'rgba(16, 185, 129, 0.22)',
    tagBorder: 'rgba(16, 185, 129, 0.32)'
  },
  {
    id: 'daylight',
    label: 'Daylight',
    primary: '#1d4ed8',
    secondary: '#7c3aed',
    headerGradient: 'linear-gradient(135deg, rgba(29, 78, 216, 0.12), rgba(124, 58, 237, 0.12))',
    featuredGradient: 'linear-gradient(135deg, rgba(59, 130, 246, 0.18), rgba(124, 58, 237, 0.18))',
    progressStart: '#60a5fa',
    progressEnd: '#a855f7',
    glow: 'rgba(125, 133, 255, 0.24)',
    ...lightBase,
    chipBackground: '#e2e8f0',
    chipBorder: 'rgba(15, 23, 42, 0.1)',
    controlBg: '#e2e8f0',
    controlHover: '#cbd5f5'
  },

  {
    id: 'crimson',
    label: 'Crimson Nova',
    primary: '#ef4444',
    secondary: '#f97316',
    headerGradient: 'linear-gradient(135deg, rgba(239, 68, 68, 0.22), rgba(249, 115, 22, 0.24))',
    featuredGradient: 'linear-gradient(135deg, rgba(239, 68, 68, 0.28), rgba(249, 115, 22, 0.3))',
    progressStart: '#f87171',
    progressEnd: '#fb923c',
    glow: 'rgba(239, 68, 68, 0.33)',
    ...darkBase,
    tagBg: 'rgba(239, 68, 68, 0.24)',
    tagBorder: 'rgba(249, 115, 22, 0.32)'
  },
  {
    id: 'forest',
    label: 'Forest Emerald',
    primary: '#15803d',
    secondary: '#4ade80',
    headerGradient: 'linear-gradient(135deg, rgba(21, 128, 61, 0.24), rgba(74, 222, 128, 0.28))',
    featuredGradient: 'linear-gradient(135deg, rgba(21, 128, 61, 0.32), rgba(34, 197, 94, 0.32))',
    progressStart: '#34d399',
    progressEnd: '#bbf7d0',
    special: true,
    ...darkBase,
    // background: '#02140a',
    // backgroundMuted: '#042010',
    chipBorder: 'rgba(74, 222, 128, 0.28)',
    tagBg: 'rgba(34, 197, 94, 0.24)',
    tagBorder: 'rgba(34, 197, 94, 0.34)',
    glow: 'rgba(34, 197, 94, 0.36)'
  },
  {
    id: 'catgirl',
    label: 'Neon Bloom',
    primary: '#f472b6',
    secondary: '#a855f7',
    headerGradient: 'linear-gradient(135deg, rgba(244, 114, 182, 0.2), rgba(168, 85, 247, 0.25))',
    featuredGradient: 'linear-gradient(135deg, rgba(244, 114, 182, 0.25), rgba(168, 85, 247, 0.3))',
    progressStart: '#f9a8d4',
    progressEnd: '#c4b5fd',
    special: true,
    ...darkBase,
    // background: '#18041f',
    // backgroundMuted: '#24072d',
    // surface: 'rgba(39, 10, 52, 0.88)',
    // surfaceElevated: 'rgba(44, 12, 60, 0.82)',
    controlBg: 'rgba(79, 22, 104, 0.65)',
    controlHover: 'rgba(101, 32, 132, 0.78)',
    controlBorder: 'rgba(244, 114, 182, 0.38)',
    formBg: 'rgba(32, 8, 44, 0.85)',
    formBorder: 'rgba(244, 114, 182, 0.42)',
    chipBackground: 'rgba(244, 114, 182, 0.18)',
    chipBorder: 'rgba(244, 114, 182, 0.38)',
    chipText: '#fce7f3',
    tagBg: 'rgba(244, 114, 182, 0.28)',
    tagBorder: 'rgba(244, 114, 182, 0.4)',
    glow: 'rgba(244, 114, 182, 0.2)'
  },
  {
    id: 'starlight',
    label: 'Starlight',
    primary: '#0ea5e9',
    secondary: '#38bdf8',
    headerGradient: 'linear-gradient(135deg, rgba(14, 165, 233, 0.22), rgba(56, 189, 248, 0.28))',
    featuredGradient: 'linear-gradient(135deg, rgba(14, 165, 233, 0.31), rgba(56, 189, 248, 0.35))',
    progressStart: '#38bdf8',
    progressEnd: '#22d3ee',
    ...darkBase,
    // background: '#010b14',
    // backgroundMuted: '#021524',
    glow: 'rgba(56, 189, 248, 0.35)'
  }
];

type ThemeStore = {
  subscribe: ReturnType<typeof writable<ThemeDefinition>>['subscribe'];
  init: () => void;
  select: (id: string) => void;
};

let transitionHandle: number | undefined;

function animateThemeChange() {
  if (typeof document === 'undefined') return;
  const root = document.documentElement;
  root.classList.add('theme-animating');
  if (transitionHandle) clearTimeout(transitionHandle);
  transitionHandle = setTimeout(() => {
    root.classList.remove('theme-animating');
  }, 520) as unknown as number;
}

function setCssVariables(theme: ThemeDefinition) {
  if (typeof document === 'undefined') return;
  const root = document.documentElement;

  root.style.setProperty('--theme-accent', theme.primary);
  root.style.setProperty('--theme-accent-secondary', theme.secondary);
  root.style.setProperty('--theme-accent-alpha-20', rgba(theme.primary, 0.2));
  root.style.setProperty('--theme-accent-alpha-22', rgba(theme.primary, 0.22));
  root.style.setProperty('--theme-accent-alpha-25', rgba(theme.primary, 0.25));
  root.style.setProperty('--theme-accent-alpha-28', rgba(theme.primary, 0.28));
  root.style.setProperty('--theme-accent-alpha-32', rgba(theme.primary, 0.32));
  root.style.setProperty('--theme-accent-alpha-40', rgba(theme.primary, 0.4));
  root.style.setProperty('--theme-accent-alpha-50', rgba(theme.primary, 0.5));

  root.style.setProperty('--theme-secondary-alpha-25', rgba(theme.secondary, 0.25));
  root.style.setProperty('--theme-secondary-alpha-32', rgba(theme.secondary, 0.32));
  root.style.setProperty('--theme-secondary-alpha-40', rgba(theme.secondary, 0.4));

  root.style.setProperty('--theme-bg', theme.background);
  root.style.setProperty('--theme-bg-muted', theme.backgroundMuted);
  root.style.setProperty('--theme-surface', theme.surface);
  root.style.setProperty('--theme-surface-elevated', theme.surfaceElevated);
  root.style.setProperty('--theme-surface-border', theme.border);
  root.style.setProperty('--theme-text-primary', theme.textPrimary);
  root.style.setProperty('--theme-text-secondary', theme.textSecondary);
  root.style.setProperty('--theme-text-soft', theme.textSoft);
  root.style.setProperty('--theme-chip-bg', theme.chipBackground);
  root.style.setProperty('--theme-chip-border', theme.chipBorder);
  root.style.setProperty('--theme-chip-text', theme.chipText);
  root.style.setProperty('--theme-header-gradient', theme.headerGradient);
  root.style.setProperty('--theme-featured-gradient', theme.featuredGradient);
  root.style.setProperty('--theme-card-shadow', theme.cardShadow);
  root.style.setProperty('--theme-progress-start', theme.progressStart);
  root.style.setProperty('--theme-progress-end', theme.progressEnd);
  root.style.setProperty('--theme-control-bg', theme.controlBg);
  root.style.setProperty('--theme-control-hover', theme.controlHover);
  root.style.setProperty('--theme-control-border', theme.controlBorder);
  root.style.setProperty('--theme-form-bg', theme.formBg);
  root.style.setProperty('--theme-form-border', theme.formBorder);
  root.style.setProperty('--theme-tag-bg', theme.tagBg);
  root.style.setProperty('--theme-tag-border', theme.tagBorder);
  root.style.setProperty('--theme-glow', theme.glow);
  root.style.setProperty('--theme-shadow-light', theme.shadowLight);
  root.style.setProperty('--theme-shadow-dark', theme.shadowDark);

  document.body.dataset.themeMode = theme.mode;

  document.body.dataset.theme = theme.id;
  if (theme.special) document.body.dataset.themeSpecial = 'true';
  else delete document.body.dataset.themeSpecial;
}

function createThemeStore(): ThemeStore {
  const { subscribe, set } = writable<ThemeDefinition>(themeOptions[0]);
  let initialized = false;

  function apply(theme: ThemeDefinition, shouldAnimate = true) {
    set(theme);
    setCssVariables(theme);
    if (shouldAnimate) animateThemeChange();
  }

  function init() {
    if (initialized || typeof window === 'undefined') return;
    initialized = true;

    const storedId = window.localStorage.getItem(STORAGE_KEY);
    if (storedId) {
      const storedTheme = themeOptions.find((item) => item.id === storedId);
      if (storedTheme) {
        apply(storedTheme, false);
        return;
      }
    }

    apply(themeOptions[0], false);
  }

  function select(id: string) {
    const nextTheme = themeOptions.find((item) => item.id === id);
    if (!nextTheme) return;
    if (typeof window !== 'undefined') {
      window.localStorage.setItem(STORAGE_KEY, id);
    }
    apply(nextTheme, true);
  }

  return { subscribe, init, select };
}

export const theme = createThemeStore();

type GradientStore = {
  subscribe: ReturnType<typeof writable<boolean>>['subscribe'];
  init: () => void;
  toggle: () => void;
};

function createGradientStore(): GradientStore {
  const { subscribe, set } = writable<boolean>(true);
  let initialized = false;

  function init() {
    if (initialized || typeof window === 'undefined') return;
    initialized = true;

    const stored = window.localStorage.getItem(GRADIENT_STORAGE_KEY);
    const shouldEnableGradient = stored === null ? true : stored === 'true';
    set(shouldEnableGradient);
    applyGradientState(shouldEnableGradient);
  }

  function applyGradientState(enabled: boolean) {
    if (typeof document === 'undefined') return;
    if (enabled) {
      document.body.dataset.gradientEnabled = 'true';
    } else {
      delete document.body.dataset.gradientEnabled;
    }
  }

  function toggle() {
    let current = true;
    const unsubscribe = subscribe((value) => {
      current = value;
    });
    unsubscribe();

    const next = !current;
    set(next);
    applyGradientState(next);
    if (typeof window !== 'undefined') {
      window.localStorage.setItem(GRADIENT_STORAGE_KEY, String(next));
    }
  }

  return { subscribe, init, toggle };
}

export const gradient = createGradientStore();
