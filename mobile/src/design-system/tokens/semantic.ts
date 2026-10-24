import { palette } from "./primitives";

export const lightTheme = {
  mode: "light" as const,

  colors: {
    background: palette.neutral[50],
    surface: palette.white,
    surfaceSecondary: palette.neutral[100],
    surfaceElevated: palette.white,

    textPrimary: palette.neutral[900],
    textSecondary: palette.neutral[600],
    textMuted: palette.neutral[500],
    textOnBrand: palette.white,

    border: palette.neutral[200],
    borderStrong: palette.neutral[300],

    brand: palette.brand[600],
    brandPressed: palette.brand[700],
    brandSubtle: palette.brand[50],

    success: palette.accent.emerald,
    warning: palette.accent.amber,
    danger: palette.accent.rose,
    info: palette.accent.blue,

    overlay: "rgba(17, 24, 39, 0.55)",
    skeleton: palette.neutral[200],
  },
} as const;

export const darkTheme = {
  mode: "dark" as const,

  colors: {
    background: palette.neutral[950],
    surface: palette.neutral[900],
    surfaceSecondary: palette.neutral[800],
    surfaceElevated: palette.neutral[800],

    textPrimary: palette.neutral[50],
    textSecondary: palette.neutral[300],
    textMuted: palette.neutral[400],
    textOnBrand: palette.white,

    border: palette.neutral[700],
    borderStrong: palette.neutral[600],

    brand: palette.brand[400],
    brandPressed: palette.brand[300],
    brandSubtle: palette.brand[900],

    success: "#34D399",
    warning: "#FBBF24",
    danger: "#FB7185",
    info: "#60A5FA",

    overlay: "rgba(0, 0, 0, 0.72)",
    skeleton: palette.neutral[700],
  },
} as const;

export type ThemeTokens =
  | typeof lightTheme
  | typeof darkTheme;
