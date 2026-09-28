/**
 * FashXStudio Design System — Accessibility Tokens & Contrast Engine (Phase 02)
 *
 * Implements WCAG 2.2 AAA/AA contrast calculation, keyboard focus rings,
 * touch-target geometry baselines (44px mobile, 40px primary, 36px desktop),
 * and reduced-motion overrides (Sections 2.16, 2.30, 2.31, 2.32).
 */

export const targetSizes = {
  compactDesktopMinPx: 36,
  primaryControlMinPx: 40,
  touchTargetMinPx: 44, // WCAG 2.5.5 / 2.5.8 touch target minimum
} as const;

export const focusTokens = {
  ringColor: '#6366F1', // Electric Indigo
  ringWidthPx: 2,
  ringOffsetPx: 2,
  ringStyle: 'solid',
} as const;

export const reducedMotionTokens = {
  durationMs: 0,
  easing: 'linear',
} as const;

/**
 * Calculates WCAG 2.2 relative luminance for an sRGB hex code.
 */
export function calculateLuminance(hexColor: string): number {
  const clean = hexColor.replace('#', '');
  const r = parseInt(clean.substring(0, 2), 16) / 255;
  const g = parseInt(clean.substring(2, 4), 16) / 255;
  const b = parseInt(clean.substring(4, 6), 16) / 255;

  const toLinear = (c: number) => (c <= 0.04045 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4));
  return 0.2126 * toLinear(r) + 0.7152 * toLinear(g) + 0.0722 * toLinear(b);
}

/**
 * Calculates the contrast ratio between two hex colors (e.g. 7.0 for AAA, 4.5 for AA).
 */
export function getContrastRatio(hex1: string, hex2: string): number {
  const lum1 = calculateLuminance(hex1);
  const lum2 = calculateLuminance(hex2);
  const lighter = Math.max(lum1, lum2);
  const darker = Math.min(lum1, lum2);
  return Number(((lighter + 0.05) / (darker + 0.05)).toFixed(2));
}

export function passesWcagAA(ratio: number, isLargeText: boolean = false): boolean {
  return ratio >= (isLargeText ? 3.0 : 4.5);
}

export function passesWcagAAA(ratio: number, isLargeText: boolean = false): boolean {
  return ratio >= (isLargeText ? 4.5 : 7.0);
}
