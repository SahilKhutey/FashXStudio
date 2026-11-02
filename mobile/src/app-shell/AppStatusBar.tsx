import React from "react";
import { StatusBar } from "expo-status-bar";
import { useDesignTokens } from "../design-system";

export function AppStatusBar() {
  const { theme } = useDesignTokens();
  const isDark = theme.mode === "dark";

  return (
    <StatusBar
      style={isDark ? "light" : "dark"}
      animated
    />
  );
}
