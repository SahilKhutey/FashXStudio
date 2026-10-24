export const palette = {
  white: "#FFFFFF",
  black: "#000000",

  neutral: {
    0: "#FFFFFF",
    50: "#F9FAFB",
    100: "#F3F4F6",
    200: "#E5E7EB",
    300: "#D1D5DB",
    400: "#9CA3AF",
    500: "#6B7280",
    600: "#4B5563",
    700: "#374151",
    800: "#1F2937",
    900: "#111827",
    950: "#030712",
  },

  brand: {
    50: "#EEF2FF",
    100: "#E0E7FF",
    200: "#C7D2FE",
    300: "#A5B4FC",
    400: "#818CF8",
    500: "#6366F1",
    600: "#4F46E5",
    700: "#4338CA",
    800: "#3730A3",
    900: "#312E81",
  },

  accent: {
    rose: "#E11D48",
    emerald: "#047857",
    amber: "#B45309",
    blue: "#1D4ED8",
  },
} as const;

export const spacing = {
  0: 0,
  0.5: 2,
  1: 4,
  1.5: 6,
  2: 8,
  3: 12,
  4: 16,
  5: 20,
  6: 24,
  8: 32,
  10: 40,
  12: 48,
  16: 64,
  20: 80,
} as const;

export const radius = {
  none: 0,
  xs: 4,
  sm: 6,
  md: 8,
  lg: 12,
  xl: 16,
  "2xl": 20,
  "3xl": 24,
  pill: 999,
} as const;

export const fontSize = {
  xs: 12,
  sm: 14,
  md: 16,
  lg: 18,
  xl: 20,
  "2xl": 24,
  "3xl": 30,
  "4xl": 36,
} as const;

export const lineHeight = {
  tight: 1.2,
  normal: 1.45,
  relaxed: 1.6,
} as const;

export const fontWeight = {
  regular: "400",
  medium: "500",
  semibold: "600",
  bold: "700",
  extrabold: "800",
} as const;

export const borderWidth = {
  none: 0,
  hairline: 0.5,
  thin: 1,
  thick: 2,
} as const;

export const opacity = {
  disabled: 0.45,
  subtle: 0.65,
  overlay: 0.85,
  opaque: 1,
} as const;

export const elevation = {
  none: 0,
  low: 1,
  medium: 3,
  high: 6,
} as const;

export const zIndex = {
  base: 0,
  card: 10,
  sticky: 20,
  dropdown: 30,
  overlay: 40,
  modal: 50,
  toast: 60,
} as const;
