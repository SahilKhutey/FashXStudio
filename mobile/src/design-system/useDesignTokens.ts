import { useColorScheme } from "react-native";
import { resolveTheme, type ThemeMode } from "./theme";
import {
  spacing,
  radius,
  fontSize,
  fontWeight,
  elevation,
  opacity,
  zIndex,
  borderWidth,
} from "./tokens/primitives";
import { typography } from "./tokens/typography";
import { layout } from "./tokens/layout";
import { motion } from "./tokens/motion";
import { accessibility } from "./tokens/accessibility";

export function useDesignTokens(mode: ThemeMode = "system") {
  const systemScheme = useColorScheme();

  const theme = resolveTheme(mode, systemScheme);

  return {
    theme,
    colors: theme.colors,
    spacing,
    radius,
    fontSize,
    fontWeight,
    typography,
    layout,
    motion,
    accessibility,
    elevation,
    opacity,
    zIndex,
    borderWidth,
  };
}
