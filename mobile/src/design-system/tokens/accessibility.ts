import { palette } from "./primitives";

export const accessibility = {
  minimumTouchTarget: 44,
  recommendedTouchTarget: 48,

  focus: {
    width: 2,
    color: palette.brand[600],
    offset: 2,
  },

  // A minimum font size guideline, not a forced limit.
  minimumComfortableFontSize: 14,

  // Respect the user's system text scaling wherever possible.
  allowFontScaling: true,
} as const;
