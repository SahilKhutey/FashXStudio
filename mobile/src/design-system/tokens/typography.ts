import type { TextStyle } from "react-native";
import {
  fontSize,
  fontWeight,
  lineHeight,
} from "./primitives";

export const typography = {
  display: {
    fontSize: fontSize["4xl"],
    fontWeight: fontWeight.bold,
    lineHeight: Math.round(fontSize["4xl"] * lineHeight.tight),
  },

  heading1: {
    fontSize: fontSize["3xl"],
    fontWeight: fontWeight.bold,
    lineHeight: Math.round(fontSize["3xl"] * lineHeight.tight),
  },

  heading2: {
    fontSize: fontSize["2xl"],
    fontWeight: fontWeight.bold,
    lineHeight: Math.round(fontSize["2xl"] * lineHeight.tight),
  },

  heading3: {
    fontSize: fontSize.xl,
    fontWeight: fontWeight.semibold,
    lineHeight: Math.round(fontSize.xl * lineHeight.normal),
  },

  body: {
    fontSize: fontSize.md,
    fontWeight: fontWeight.regular,
    lineHeight: Math.round(fontSize.md * lineHeight.normal),
  },

  bodySmall: {
    fontSize: fontSize.sm,
    fontWeight: fontWeight.regular,
    lineHeight: Math.round(fontSize.sm * lineHeight.normal),
  },

  label: {
    fontSize: fontSize.sm,
    fontWeight: fontWeight.semibold,
    lineHeight: Math.round(fontSize.sm * lineHeight.normal),
  },

  caption: {
    fontSize: fontSize.xs,
    fontWeight: fontWeight.regular,
    lineHeight: Math.round(fontSize.xs * lineHeight.relaxed),
  },

  button: {
    fontSize: fontSize.md,
    fontWeight: fontWeight.semibold,
    lineHeight: Math.round(fontSize.md * lineHeight.normal),
  },
} satisfies Record<string, TextStyle>;
