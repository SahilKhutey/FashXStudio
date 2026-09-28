/**
 * FashXStudio Design System — Responsive & Grid Tokens (Phase 02)
 *
 * Mathematical grid specifications, container boundaries, and dynamic
 * adaptive product grid calculation engine (Section 2.22 - 2.25).
 */

export const breakpoints = {
  xs: 0,
  sm: 480,
  md: 768,
  lg: 1024,
  xl: 1280,
  twoXl: 1536,
} as const;

export const containers = {
  sm: 640,
  md: 768,
  lg: 1024,
  xl: 1280,
  twoXl: 1536,
  full: '100%',
} as const;

export const gridTokens = {
  desktopColumns: 12,
  tabletColumns: 8,
  mobileColumns: 4,
  gutterMobile: 16,
  gutterTablet: 24,
  gutterDesktop: 32,
  productMinCardWidth: 240,
} as const;

export const imageAspectRatios = {
  square: '1 / 1',
  portrait: '3 / 4',
  landscape: '16 / 9',
  editorial: '2 / 3',
  product: '3 / 4',
} as const;

export const imageFits = {
  cover: 'cover',
  contain: 'contain',
} as const;

/**
 * Section 2.25: Adaptive Product Grid Engine
 * Dynamically computes column count from available container width and minimum card width.
 * Available Width -> Minimum Card Width -> Calculate Columns -> Render Grid
 */
export function calculateAdaptiveColumns(
  containerWidthPx: number,
  minCardWidthPx: number = 240,
  gutterPx: number = 16,
  maxColumns: number = 12
): number {
  if (containerWidthPx <= 0) return 1;
  const cols = Math.floor((containerWidthPx + gutterPx) / (minCardWidthPx + gutterPx));
  return Math.max(1, Math.min(cols, maxColumns));
}
