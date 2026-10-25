import type { ResolvedTheme } from "../design-system";

export type NavigationTheme = {
  dark: boolean;
  colors: {
    primary: string;
    background: string;
    card: string;
    text: string;
    border: string;
    notification: string;
  };
};

export function getNavigationTheme(theme: ResolvedTheme): NavigationTheme {
  const isDark = theme.mode === "dark";
  return {
    dark: isDark,
    colors: {
      primary: theme.colors.brand,
      background: theme.colors.background,
      card: theme.colors.surface,
      text: theme.colors.textPrimary,
      border: theme.colors.border,
      notification: theme.colors.danger,
    },
  };
}
