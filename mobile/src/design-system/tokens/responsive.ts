export const breakpoints = {
  compact: 360,
  phone: 480,
  tablet: 768,
  desktop: 1024,
} as const;

export type ScreenSize =
  | "compact"
  | "phone"
  | "tablet"
  | "desktop";

export function getScreenSize(width: number): ScreenSize {
  if (width < breakpoints.compact) return "compact";
  if (width < breakpoints.tablet) return "phone";
  if (width < breakpoints.desktop) return "tablet";
  return "desktop";
}

export function getScreenGutter(width: number): number {
  if (width < breakpoints.compact) return 12;
  if (width < breakpoints.tablet) return 16;
  if (width < breakpoints.desktop) return 24;
  return 32;
}

export function getProductGridColumns(width: number): number {
  if (width < breakpoints.compact) return 1;
  if (width < breakpoints.tablet) return 2;
  if (width < breakpoints.desktop) return 3;
  return 4;
}

export function getContentWidth(
  screenWidth: number,
  maxWidth: number,
): number {
  return Math.min(screenWidth, maxWidth);
}
