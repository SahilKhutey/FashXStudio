import { darkTheme, lightTheme } from "./tokens/semantic";

export type ThemeMode = "light" | "dark" | "system";
export type ResolvedTheme = typeof lightTheme | typeof darkTheme;

export function resolveTheme(
  mode: ThemeMode,
  systemScheme: "light" | "dark" | "unspecified" | null | undefined,
): ResolvedTheme {
  const resolvedMode =
    mode === "system"
      ? systemScheme === "dark"
        ? "dark"
        : "light"
      : mode;

  return resolvedMode === "dark" ? darkTheme : lightTheme;
}
