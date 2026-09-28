/**
 * FashXStudio Design System — Primitive Tokens (Phase 02)
 *
 * Immutable base primitives for color, typography, spacing, sizing, radius,
 * borders, shadows, opacity, z-index, and motion.
 * Rule: Components NEVER consume primitives directly; they consume semantic or component tokens.
 */

// ---------------------------------------------------------------------------
// 1. Color Primitives
// ---------------------------------------------------------------------------

export const neutralPrimitives = {
  neutral0: '#FFFFFF',
  neutral50: '#F9FAFB',
  neutral100: '#F3F4F6',
  neutral200: '#E5E7EB',
  neutral300: '#D1D5DB',
  neutral400: '#9CA3AF',
  neutral500: '#6B7280',
  neutral600: '#4B5563',
  neutral700: '#374151',
  neutral800: '#1F2937',
  neutral900: '#111827',
  neutral950: '#030712',
} as const;

export const monkSkinTonePalette = {
  mst01: '#F6EDE4',
  mst02: '#F3E7DB',
  mst03: '#F7DAD0',
  mst04: '#EADABA',
  mst05: '#D7BD96',
  mst06: '#A07E56',
  mst07: '#825C43',
  mst08: '#604134',
  mst09: '#3A312A',
  mst10: '#292420',
  undertoneWarm: '#E0A96D',
  undertoneCool: '#D4AFCD',
  undertoneNeutral: '#C8B89E',
} as const;

export const brandPalette = {
  primary: '#0F172A',
  primaryHover: '#1E293B',
  primaryActive: '#020617',
  secondary: '#6366F1',
  accent: '#E11D48',
} as const;

export const statusPalette = {
  success: '#10B981',
  successSurface: '#ECFDF5',
  warning: '#F59E0B',
  warningSurface: '#FFFBEB',
  error: '#EF4444',
  errorSurface: '#FEF2F2',
  info: '#3B82F6',
  infoSurface: '#EFF6FF',
} as const;

export const domainColorPalette = {
  product: '#0F172A',
  fashion: '#8B5CF6',
  shopping: '#10B981',
  trend: '#EC4899',
  ai: '#6366F1',
  geography: '#0EA5E9',
} as const;

// ---------------------------------------------------------------------------
// 2. Typography Primitives
// ---------------------------------------------------------------------------

export interface TypeScaleEntry {
  fontSize: number;
  lineHeight: number;
  letterSpacing: number; // in em
  fontWeight: number;
}

export const typeScale = {
  displayXl: { fontSize: 48, lineHeight: 56, letterSpacing: -0.02, fontWeight: 700 },
  displayL: { fontSize: 40, lineHeight: 48, letterSpacing: -0.02, fontWeight: 700 },
  displayM: { fontSize: 32, lineHeight: 40, letterSpacing: -0.015, fontWeight: 600 },
  headingXl: { fontSize: 28, lineHeight: 36, letterSpacing: -0.01, fontWeight: 600 },
  headingL: { fontSize: 24, lineHeight: 32, letterSpacing: -0.01, fontWeight: 600 },
  headingM: { fontSize: 20, lineHeight: 28, letterSpacing: -0.005, fontWeight: 600 },
  headingS: { fontSize: 18, lineHeight: 24, letterSpacing: 0, fontWeight: 500 },
  bodyL: { fontSize: 17, lineHeight: 26, letterSpacing: 0, fontWeight: 400 },
  bodyM: { fontSize: 16, lineHeight: 24, letterSpacing: 0, fontWeight: 400 },
  bodyS: { fontSize: 14, lineHeight: 20, letterSpacing: 0.005, fontWeight: 400 },
  labelL: { fontSize: 14, lineHeight: 20, letterSpacing: 0.01, fontWeight: 600 },
  labelM: { fontSize: 12, lineHeight: 16, letterSpacing: 0.015, fontWeight: 500 },
  labelS: { fontSize: 11, lineHeight: 14, letterSpacing: 0.02, fontWeight: 500 },
  caption: { fontSize: 12, lineHeight: 16, letterSpacing: 0.01, fontWeight: 400 },
  overline: { fontSize: 11, lineHeight: 14, letterSpacing: 0.05, fontWeight: 600 },
} as const;

export const fontFamilies = {
  display: "'Playfair Display', 'Didot', serif",
  heading: "'Plus Jakarta Sans', 'Inter', sans-serif",
  body: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
  ui: "'Plus Jakarta Sans', 'Inter', sans-serif",
  mono: "'JetBrains Mono', 'Fira Code', monospace",
} as const;

export const fontWeights = {
  regular: 400,
  medium: 500,
  semibold: 600,
  bold: 700,
} as const;

export const lineHeights = {
  tight: 1.15,
  snug: 1.25,
  normal: 1.45,
  relaxed: 1.65,
} as const;

// ---------------------------------------------------------------------------
// 3. Spacing & Sizing Primitives (4px Base Unit)
// ---------------------------------------------------------------------------

export const spacingScale = {
  space1: 4,
  space2: 8,
  space3: 12,
  space4: 16,
  space5: 20,
  space6: 24,
  space8: 32,
  space10: 40,
  space12: 48,
  space16: 64,
  space20: 80,
  space24: 96,
} as const;

export const sizingScale = {
  xs: 24,
  sm: 32,
  md: 40,
  lg: 48,
  xl: 56,
} as const;

// ---------------------------------------------------------------------------
// 4. Geometry Primitives
// ---------------------------------------------------------------------------

export const borderWidths = {
  none: 0,
  thin: 1,
  medium: 2,
  strong: 3,
} as const;

export const radiusScale = {
  none: 0,
  xs: 4,
  sm: 6,
  md: 10,
  lg: 14,
  xl: 20,
  full: 9999,
} as const;

export const elevationShadows = {
  elevation0: 'none',
  elevation1: '0 1px 3px rgba(0, 0, 0, 0.08), 0 1px 2px rgba(0, 0, 0, 0.04)',
  elevation2: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
  elevation3: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
  elevation4: '0 20px 25px -5px rgba(0, 0, 0, 0.12), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
} as const;

export const opacityScale = {
  disabled: 0.38,
  muted: 0.60,
  overlay: 0.75,
  scrim: 0.85,
} as const;

export const zIndexScale = {
  base: 0,
  sticky: 100,
  dropdown: 200,
  overlay: 300,
  modal: 400,
  popover: 500,
  toast: 600,
  max: 9999,
} as const;

// ---------------------------------------------------------------------------
// 5. Motion Primitives
// ---------------------------------------------------------------------------

export const motionDurations = {
  instant: 50,
  fast: 150,
  normal: 250,
  slow: 400,
} as const;

export const motionEasings = {
  standard: 'cubic-bezier(0.4, 0.0, 0.2, 1)',
  enter: 'cubic-bezier(0.0, 0.0, 0.2, 1)',
  exit: 'cubic-bezier(0.4, 0.0, 1.0, 1)',
  emphasized: 'cubic-bezier(0.2, 0.0, 0.0, 1)',
} as const;
