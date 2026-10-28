import React from "react";
import { StatusBar } from "react-native";
import { useDesignTokens } from "../design-system";

export function AppStatusBar() {
  const { theme, colors } = useDesignTokens();
  const isDark = theme.mode === "dark";

  return (
    <StatusBar
      barStyle={isDark ? "light-content" : "dark-content"}
      backgroundColor={colors.surface}
      animated
    />
  );
}
