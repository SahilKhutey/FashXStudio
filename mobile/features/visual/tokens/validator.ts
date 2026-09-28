/**
 * FashXStudio Design System — Token Validation Engine (Phase 02)
 *
 * Implements Section 2.40 automated token validation:
 * - Verifies contrast ratios against WCAG 2.2 AAA/AA
 * - Checks for unresolved component token references
 * - Enforces minimum touch target constraints
 */

import { lightTheme, darkTheme, resolveThemeToken, Theme } from './theme';
import { getContrastRatio, passesWcagAA, passesWcagAAA, targetSizes } from './accessibility';
import { componentTokensRegistry } from './components';

export interface ValidationIssue {
  type: 'CONTRAST' | 'DANGLING_REFERENCE' | 'TOUCH_TARGET' | 'MISSING_SCALE';
  severity: 'ERROR' | 'WARNING';
  message: string;
}

export interface ClientValidationReport {
  isValid: boolean;
  issues: ValidationIssue[];
  totalChecked: number;
}

export function validateTokens(theme: Theme = lightTheme): ClientValidationReport {
  const issues: ValidationIssue[] = [];
  let totalChecked = 0;

  // 1. Check Primary Content Contrast
  totalChecked++;
  const primaryRatio = getContrastRatio(theme.content.primary, theme.surfaces.primary);
  if (!passesWcagAAA(primaryRatio)) {
    issues.push({
      type: 'CONTRAST',
      severity: 'WARNING',
      message: `Primary text contrast ratio ${primaryRatio} is below WCAG AAA (7.0). Passes AA: ${passesWcagAA(primaryRatio)}`,
    });
  }

  // 2. Check Action Button Contrast
  totalChecked++;
  const actionRatio = getContrastRatio(theme.actions.primaryText, theme.actions.primary);
  if (!passesWcagAA(actionRatio)) {
    issues.push({
      type: 'CONTRAST',
      severity: 'ERROR',
      message: `Primary button text contrast ratio ${actionRatio} fails WCAG AA (4.5).`,
    });
  }

  // 3. Check Component Token References
  for (const [componentName, tokenMap] of Object.entries(componentTokensRegistry)) {
    for (const [property, tokenRef] of Object.entries(tokenMap)) {
      totalChecked++;
      const resolved = resolveThemeToken(tokenRef, theme);
      if (resolved === undefined) {
        issues.push({
          type: 'DANGLING_REFERENCE',
          severity: 'ERROR',
          message: `Unresolved token reference '${tokenRef}' in component '${componentName}.${property}'`,
        });
      }
    }
  }

  // 4. Verify Touch Target Geometries
  totalChecked++;
  if (targetSizes.touchTargetMinPx < 44) {
    issues.push({
      type: 'TOUCH_TARGET',
      severity: 'ERROR',
      message: `Mobile touch target minimum ${targetSizes.touchTargetMinPx}px is below WCAG 44px minimum.`,
    });
  }

  const hasErrors = issues.some((i) => i.severity === 'ERROR');
  return {
    isValid: !hasErrors,
    issues,
    totalChecked,
  };
}
