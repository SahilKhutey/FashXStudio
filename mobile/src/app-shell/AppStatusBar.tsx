import React, { useEffect } from "react";
import { Platform, StatusBar } from "react-native";
import { useDesignTokens } from "../design-system";

export function AppStatusBar() {
  const { theme, colors } = useDesignTokens();
  const isDark = theme.mode === "dark";

  useEffect(() => {
    if (Platform.OS === "android") {
      (StatusBar as any).setBackgroundColor?.(colors.surface, true);
    }
  }, [colors.surface]);

  return (
    <StatusBar
      barStyle={isDark ? "light-content" : "dark-content"}
      animated
    />
  );
}
