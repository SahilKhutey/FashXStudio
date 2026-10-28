import { spacing } from "./primitives";

export const layout = {
  screenPadding: spacing[4],
  screenPaddingCompact: spacing[3],

  sectionGap: spacing[6],
  cardGap: spacing[4],
  inlineGap: spacing[2],

  controlHeight: {
    sm: 36,
    md: 44,
    lg: 52,
  },

  iconSize: {
    sm: 16,
    md: 20,
    lg: 24,
    xl: 32,
  },

  productImage: {
    aspectRatio: 3 / 4,
    thumbnailWidth: 68,
    thumbnailHeight: 80,
  },

  contentMaxWidth: 720,
} as const;
