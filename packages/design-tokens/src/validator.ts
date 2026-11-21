import { Draft202012Validator } from 'jsonschema';

export const ALLOWED_FONT_FAMILIES = new Set([
  'system',
  'sans-serif',
  'serif',
  'monospace',
  'Inter',
  'Playfair Display',
  'Merriweather',
  'Cinzel',
  'Outfit',
  'Lora',
  'JetBrains Mono',
  'Courier New',
]);

const HEX_COLOR_REGEX = /^#(?:[0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$/;
const SPACING_UNIT_REGEX = /^(?:0(?:px|rem)?|[0-9]+(?:\.[0-9]+)?(?:rem|px))$/;
const CSS_INJECTION_REGEX = /url\(|expression\(|javascript:|binding:|behavior:|<script|@import/i;

export interface TokenValidationResult {
  valid: boolean;
  errors: string[];
}

export function validateColor(value: unknown): boolean {
  if (typeof value !== 'string') return false;
  if (CSS_INJECTION_REGEX.test(value)) return false;
  return HEX_COLOR_REGEX.test(value);
}

export function validateSpacing(value: unknown): boolean {
  if (typeof value !== 'string') return false;
  if (CSS_INJECTION_REGEX.test(value)) return false;
  return SPACING_UNIT_REGEX.test(value);
}

export function validateFontFamily(value: unknown): boolean {
  if (typeof value !== 'string') return false;
  if (CSS_INJECTION_REGEX.test(value)) return false;
  return ALLOWED_FONT_FAMILIES.has(value);
}

export function validateTokenOverrides(overrides: Record<string, any>): TokenValidationResult {
  const errors: string[] = [];

  function traverse(obj: any, currentPath: string) {
    if (!obj || typeof obj !== 'object' || Array.isArray(obj)) {
      errors.push(`Invalid token override container at ${currentPath}`);
      return;
    }

    for (const [key, value] of Object.entries(obj)) {
      const nextPath = currentPath ? `${currentPath}.${key}` : key;

      // Reject arbitrary CSS expressions
      if (typeof value === 'string' && CSS_INJECTION_REGEX.test(value)) {
        errors.push(`Arbitrary CSS expression rejected at ${nextPath}: ${value}`);
        continue;
      }

      if (value !== null && typeof value === 'object' && !Array.isArray(value)) {
        traverse(value, nextPath);
      } else {
        // Leaf value validation
        if (nextPath.startsWith('color.')) {
          if (!validateColor(value)) {
            errors.push(`Invalid hex color at ${nextPath}: ${value}`);
          }
        } else if (nextPath.startsWith('typography.fontFamily.')) {
          if (!validateFontFamily(value)) {
            errors.push(`Unsupported font family at ${nextPath}: ${value}`);
          }
        } else if (nextPath.startsWith('spacing.')) {
          if (!validateSpacing(value)) {
            errors.push(`Invalid spacing unit at ${nextPath}: ${value}`);
          }
        } else if (
          !nextPath.startsWith('radius.') &&
          !nextPath.startsWith('shadow.') &&
          !nextPath.startsWith('border.') &&
          !nextPath.startsWith('sizing.') &&
          !nextPath.startsWith('motion.') &&
          !nextPath.startsWith('breakpoints.') &&
          !nextPath.startsWith('zIndex.') &&
          !nextPath.startsWith('accessibility.')
        ) {
          errors.push(`Unsupported token path: ${nextPath}`);
        }
      }
    }
  }

  traverse(overrides, '');
  return {
    valid: errors.length === 0,
    errors,
  };
}
