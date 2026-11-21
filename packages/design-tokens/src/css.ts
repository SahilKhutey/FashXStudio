import type { DesignTokens } from '../../contracts/generated/customization';

export function toCssVariables(tokens: DesignTokens): Record<string, string> {
  const vars: Record<string, string> = {
    // Colors
    '--mm-color-brand-primary': tokens.color.brand.primary,
    '--mm-color-brand-secondary': tokens.color.brand.secondary || tokens.color.brand.primary,
    '--mm-color-brand-accent': tokens.color.brand.accent || tokens.color.brand.primary,
    '--mm-color-surface-default': tokens.color.surface.default,
    '--mm-color-surface-subtle': tokens.color.surface.subtle || tokens.color.surface.default,
    '--mm-color-surface-raised': tokens.color.surface.raised || tokens.color.surface.default,
    '--mm-color-text-primary': tokens.color.text.primary,
    '--mm-color-text-secondary': tokens.color.text.secondary || tokens.color.text.primary,
    '--mm-color-text-inverse': tokens.color.text.inverse || '#ffffff',
    '--mm-color-border-default': tokens.color.border.default,

    // Typography
    '--mm-font-family-body': tokens.typography.fontFamily.body,
    '--mm-font-family-heading': tokens.typography.fontFamily.heading,
    '--mm-font-size-small': tokens.typography.fontSize.small,
    '--mm-font-size-body': tokens.typography.fontSize.body,
    '--mm-font-size-heading': tokens.typography.fontSize.heading,
    '--mm-font-size-display': tokens.typography.fontSize.display || '2rem',
    '--mm-font-weight-normal': String(tokens.typography.fontWeight.normal),
    '--mm-font-weight-medium': String(tokens.typography.fontWeight.medium),
    '--mm-font-weight-bold': String(tokens.typography.fontWeight.bold),

    // Spacing
    '--mm-spacing-xs': tokens.spacing.xs,
    '--mm-spacing-sm': tokens.spacing.sm,
    '--mm-spacing-md': tokens.spacing.md,
    '--mm-spacing-lg': tokens.spacing.lg,
    '--mm-spacing-xl': tokens.spacing.xl,

    // Radius
    '--mm-radius-small': tokens.radius.small,
    '--mm-radius-medium': tokens.radius.medium,
    '--mm-radius-large': tokens.radius.large,

    // Shadow
    '--mm-shadow-card': tokens.shadow.card,

    // Accessibility
    '--mm-focus-ring-color': tokens.accessibility?.focusRingColor || tokens.color.brand.primary,
    '--mm-focus-ring-width': tokens.accessibility?.focusRingWidth || '2px',
    '--mm-min-touch-target': tokens.accessibility?.minTouchTarget || '44px',
  };

  return vars;
}
