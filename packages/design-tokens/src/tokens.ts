import type { DesignTokens } from '../../contracts/generated/customization';

export const DEFAULT_DESIGN_TOKENS: DesignTokens = {
  color: {
    brand: {
      primary: '#18181b',
      secondary: '#71717a',
      accent: '#2563eb',
    },
    surface: {
      default: '#ffffff',
      subtle: '#f4f4f5',
      raised: '#ffffff',
      overlay: 'rgba(0, 0, 0, 0.5)',
    },
    text: {
      primary: '#09090b',
      secondary: '#71717a',
      inverse: '#ffffff',
      muted: '#a1a1aa',
    },
    border: {
      default: '#e4e4e7',
      subtle: '#f4f4f5',
      strong: '#a1a1aa',
    },
    status: {
      success: '#16a34a',
      warning: '#ca8a04',
      error: '#dc2626',
      info: '#2563eb',
    },
  },
  typography: {
    fontFamily: {
      body: 'Inter',
      heading: 'Inter',
      monospace: 'JetBrains Mono',
    },
    fontSize: {
      small: '0.875rem',
      body: '1rem',
      medium: '1.125rem',
      heading: '1.5rem',
      display: '2rem',
    },
    fontWeight: {
      normal: 400,
      medium: 500,
      bold: 700,
    },
    lineHeight: {
      tight: '1.25',
      normal: '1.5',
      relaxed: '1.75',
    },
    letterSpacing: {
      normal: '0',
      wide: '0.025em',
    },
  },
  spacing: {
    none: '0px',
    xs: '0.25rem',
    sm: '0.5rem',
    md: '1rem',
    lg: '1.5rem',
    xl: '2rem',
    '2xl': '3rem',
    '3xl': '4rem',
  },
  radius: {
    none: '0px',
    small: '0.25rem',
    medium: '0.5rem',
    large: '0.75rem',
    full: '9999px',
  },
  shadow: {
    none: 'none',
    small: '0 1px 2px rgba(0, 0, 0, 0.05)',
    medium: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
    large: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
    card: '0 1px 3px rgba(0, 0, 0, 0.05)',
  },
  border: {
    width: {
      thin: '1px',
      normal: '2px',
      thick: '4px',
    },
    style: {
      solid: 'solid',
      dashed: 'dashed',
      dotted: 'dotted',
    },
  },
  sizing: {
    containerMaxWidth: '1200px',
    cardMinWidth: '280px',
    imageAspectRatio: '4/3',
  },
  motion: {
    durationFast: '150ms',
    durationNormal: '250ms',
    durationSlow: '400ms',
    easingStandard: 'cubic-bezier(0.4, 0, 0.2, 1)',
    reduceMotion: false,
  },
  breakpoints: {
    mobileSmall: '320px',
    mobile: '375px',
    tablet: '768px',
    desktop: '1024px',
    desktopLarge: '1440px',
  },
  zIndex: {
    dropdown: 100,
    modal: 1000,
    tooltip: 2000,
    overlay: 500,
  },
  accessibility: {
    focusRingColor: '#2563eb',
    focusRingWidth: '2px',
    minTouchTarget: '44px',
  },
};
