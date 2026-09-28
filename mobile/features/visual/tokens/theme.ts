/**
 * FashXStudio Design System — Theme Engine (Phase 02)
 *
 * Provides typed theme containers for Light and Dark modes, plus
 * dot-notation token resolver for components (Section 2.33 & 2.37).
 */

import {
  lightSemanticSurfaces,
  lightSemanticContent,
  lightSemanticBorders,
  lightSemanticActions,
  darkSemanticSurfaces,
  darkSemanticContent,
  darkSemanticBorders,
  darkSemanticActions,
  semanticDomains,
  semanticStatus,
  semanticBrand,
  semanticSpacing,
  SemanticSurfaces,
  SemanticContent,
  SemanticBorders,
  SemanticActions,
} from './semantic';
import {
  typeScale,
  fontFamilies,
  radiusScale,
  elevationShadows,
  motionDurations,
  motionEasings,
  zIndexScale,
} from './primitives';
import { focusTokens } from './accessibility';

export type ThemeMode = 'light' | 'dark';

export interface Theme {
  mode: ThemeMode;
  surfaces: SemanticSurfaces;
  content: SemanticContent;
  borders: SemanticBorders;
  actions: SemanticActions;
  domains: typeof semanticDomains;
  status: typeof semanticStatus;
  brand: typeof semanticBrand;
  spacing: typeof semanticSpacing;
  typography: typeof typeScale;
  fonts: typeof fontFamilies;
  radius: typeof radiusScale;
  elevation: typeof elevationShadows;
  motion: typeof motionDurations;
  easing: typeof motionEasings;
  zIndex: typeof zIndexScale;
  focus: typeof focusTokens;
}

export const lightTheme: Theme = {
  mode: 'light',
  surfaces: lightSemanticSurfaces,
  content: lightSemanticContent,
  borders: lightSemanticBorders,
  actions: lightSemanticActions,
  domains: semanticDomains,
  status: semanticStatus,
  brand: semanticBrand,
  spacing: semanticSpacing,
  typography: typeScale,
  fonts: fontFamilies,
  radius: radiusScale,
  elevation: elevationShadows,
  motion: motionDurations,
  easing: motionEasings,
  zIndex: zIndexScale,
  focus: focusTokens,
};

export const darkTheme: Theme = {
  mode: 'dark',
  surfaces: darkSemanticSurfaces,
  content: darkSemanticContent,
  borders: darkSemanticBorders,
  actions: darkSemanticActions,
  domains: semanticDomains,
  status: semanticStatus,
  brand: semanticBrand,
  spacing: semanticSpacing,
  typography: typeScale,
  fonts: fontFamilies,
  radius: radiusScale,
  elevation: elevationShadows,
  motion: motionDurations,
  easing: motionEasings,
  zIndex: zIndexScale,
  focus: focusTokens,
};

export function getTheme(mode: ThemeMode = 'light'): Theme {
  return mode === 'dark' ? darkTheme : lightTheme;
}

/**
 * Resolves a dot-notated token string against a theme.
 * Example: resolveThemeToken('surfaces.secondary', theme) => '#F9FAFB'
 */
export function resolveThemeToken(tokenPath: string, theme: Theme = lightTheme): any {
  const parts = tokenPath.split('.');
  let current: any = theme;
  for (const part of parts) {
    if (current && typeof current === 'object' && part in current) {
      current = current[part];
    } else {
      return undefined;
    }
  }
  return current;
}
