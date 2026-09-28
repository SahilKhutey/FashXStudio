/**
 * FashXStudio Design System — Component Tokens (Phase 02)
 *
 * Tier 3 Component-level tokens binding semantic styles to specific UI components
 * (Section 2.34 & 2.41). Prevents hard-coding hex colors or pixel numbers in components.
 */

export interface ComponentTokenMap {
  [componentKey: string]: Record<string, string>;
}

export const productCardTokens = {
  surface: 'surfaces.secondary',
  border: 'borders.subtle',
  borderRadius: 'radius.md',
  aspectRatio: '3 / 4',
  titleTypography: 'typography.bodyM',
  priceTypography: 'typography.headingS',
  merchantTypography: 'typography.caption',
  padding: 'spacing.component',
  hoverElevation: 'elevation.elevation2',
  focusRing: 'focus.ringColor',
} as const;

export const fashionCardTokens = {
  surface: 'surfaces.secondary',
  border: 'borders.default',
  borderRadius: 'radius.lg',
  aspectRatio: '2 / 3',
  headlineTypography: 'typography.headingM',
  captionTypography: 'typography.bodyS',
  padding: 'spacing.component',
  hoverElevation: 'elevation.elevation3',
  badgeBackground: 'domains.fashion',
} as const;

export const buttonTokens = {
  primaryBg: 'actions.primary',
  primaryText: 'actions.primaryText',
  primaryHover: 'actions.primaryHover',
  secondaryBg: 'actions.secondary',
  secondaryText: 'actions.secondaryText',
  secondaryHover: 'actions.secondaryHover',
  destructiveBg: 'actions.destructive',
  destructiveText: 'actions.primaryText',
  borderRadius: 'radius.sm',
  heightSm: 'sizing.sm',
  heightMd: 'sizing.md',
  heightLg: 'sizing.lg',
  paddingInlineSm: 'spacing.inline',
  paddingInlineMd: 'spacing.element',
  paddingInlineLg: 'spacing.component',
  focusRing: 'focus.ringColor',
} as const;

export const inputTokens = {
  bg: 'surfaces.primary',
  borderDefault: 'borders.default',
  borderFocus: 'borders.focus',
  borderError: 'borders.error',
  text: 'content.primary',
  placeholder: 'content.tertiary',
  borderRadius: 'radius.sm',
  heightMd: 'sizing.md',
  paddingInline: 'spacing.element',
} as const;

export const aiInsightTokens = {
  surface: 'surfaces.tertiary',
  border: 'domains.ai',
  badgeText: 'domains.ai',
  titleTypography: 'typography.headingS',
  bodyTypography: 'typography.bodyS',
  borderRadius: 'radius.md',
  padding: 'spacing.component',
} as const;

export const componentTokensRegistry = {
  productCard: productCardTokens,
  fashionCard: fashionCardTokens,
  button: buttonTokens,
  input: inputTokens,
  aiInsight: aiInsightTokens,
};
