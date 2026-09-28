/**
 * FashXStudio Design System — Semantic Tokens (Phase 02)
 *
 * Tier 2 Semantic abstractions that map meaning (roles, contexts, surfaces)
 * to underlying primitive values. Allows dynamic re-theming without component refactors.
 */

import {
  neutralPrimitives,
  brandPalette,
  statusPalette,
  domainColorPalette,
  spacingScale,
} from './primitives';

export interface SemanticSurfaces {
  primary: string;
  secondary: string;
  tertiary: string;
  inverse: string;
  elevated: string;
}

export interface SemanticContent {
  primary: string;
  secondary: string;
  tertiary: string;
  inverse: string;
  disabled: string;
}

export interface SemanticBorders {
  default: string;
  subtle: string;
  strong: string;
  focus: string;
  error: string;
}

export interface SemanticActions {
  primary: string;
  primaryHover: string;
  primaryText: string;
  secondary: string;
  secondaryHover: string;
  secondaryText: string;
  destructive: string;
  ghost: string;
}

export const lightSemanticSurfaces: SemanticSurfaces = {
  primary: neutralPrimitives.neutral0,
  secondary: neutralPrimitives.neutral50,
  tertiary: neutralPrimitives.neutral100,
  inverse: neutralPrimitives.neutral900,
  elevated: neutralPrimitives.neutral0,
};

export const lightSemanticContent: SemanticContent = {
  primary: neutralPrimitives.neutral900,
  secondary: neutralPrimitives.neutral600,
  tertiary: neutralPrimitives.neutral500,
  inverse: neutralPrimitives.neutral0,
  disabled: neutralPrimitives.neutral400,
};

export const lightSemanticBorders: SemanticBorders = {
  default: neutralPrimitives.neutral300,
  subtle: neutralPrimitives.neutral200,
  strong: neutralPrimitives.neutral700,
  focus: brandPalette.secondary,
  error: statusPalette.error,
};

export const lightSemanticActions: SemanticActions = {
  primary: neutralPrimitives.neutral900,
  primaryHover: neutralPrimitives.neutral800,
  primaryText: neutralPrimitives.neutral0,
  secondary: neutralPrimitives.neutral100,
  secondaryHover: neutralPrimitives.neutral200,
  secondaryText: neutralPrimitives.neutral900,
  destructive: statusPalette.error,
  ghost: 'transparent',
};

// Dark theme semantics
export const darkSemanticSurfaces: SemanticSurfaces = {
  primary: neutralPrimitives.neutral950,
  secondary: neutralPrimitives.neutral900,
  tertiary: neutralPrimitives.neutral800,
  inverse: neutralPrimitives.neutral50,
  elevated: neutralPrimitives.neutral900,
};

export const darkSemanticContent: SemanticContent = {
  primary: neutralPrimitives.neutral50,
  secondary: neutralPrimitives.neutral300,
  tertiary: neutralPrimitives.neutral400,
  inverse: neutralPrimitives.neutral950,
  disabled: neutralPrimitives.neutral600,
};

export const darkSemanticBorders: SemanticBorders = {
  default: neutralPrimitives.neutral800,
  subtle: neutralPrimitives.neutral800,
  strong: neutralPrimitives.neutral500,
  focus: brandPalette.secondary,
  error: statusPalette.error,
};

export const darkSemanticActions: SemanticActions = {
  primary: neutralPrimitives.neutral50,
  primaryHover: neutralPrimitives.neutral200,
  primaryText: neutralPrimitives.neutral950,
  secondary: neutralPrimitives.neutral800,
  secondaryHover: neutralPrimitives.neutral700,
  secondaryText: neutralPrimitives.neutral50,
  destructive: statusPalette.error,
  ghost: 'transparent',
};

export const semanticSpacing = {
  inline: spacingScale.space2,       // 8px between text and icons
  element: spacingScale.space3,      // 12px within a card
  component: spacingScale.space4,    // 16px between cards
  section: spacingScale.space8,      // 32px between sections
  page: spacingScale.space12,        // 48px outer page gutter
} as const;

export const semanticDomains = domainColorPalette;
export const semanticStatus = statusPalette;
export const semanticBrand = brandPalette;
