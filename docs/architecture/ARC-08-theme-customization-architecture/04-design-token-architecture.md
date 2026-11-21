# ARC-08: 04 — Design Token Architecture

## 1. Token Categories
Tokens represent the atomic design values of ModularMenu:
- **Color**: `brand` (primary, secondary, accent), `surface` (default, subtle, raised, overlay), `text` (primary, secondary, inverse, muted), `border` (default, subtle, strong), `status` (success, warning, error, info).
- **Typography**: `fontFamily` (body, heading, monospace allowlists), `fontSize` (small, body, medium, heading, display), `fontWeight` (normal, medium, bold), `lineHeight`, `letterSpacing`.
- **Spacing**: `none`, `xs`, `sm`, `md`, `lg`, `xl`, `2xl`, `3xl` (in rem or px).
- **Radius**: `none`, `small`, `medium`, `large`, `full`.
- **Shadow**: `none`, `small`, `medium`, `large`, `card`.
- **Border**: `width` (thin, normal, thick), `style` (solid, dashed, dotted).
- **Sizing**: `containerMaxWidth`, `cardMinWidth`, `imageAspectRatio`.
- **Motion**: `durationFast`, `durationNormal`, `durationSlow`, `easingStandard`, `reduceMotion`.
- **Breakpoints**: `mobileSmall` (320px), `mobile` (375px), `tablet` (768px), `desktop` (1024px), `desktopLarge` (1440px).
- **Accessibility**: `focusRingColor`, `focusRingWidth`, `minTouchTarget` (min 44px).

## 2. Deterministic CSS Variable Mapping
Tokens generate standardized CSS custom properties prefixed with `--mm-*`:
- `--mm-color-brand-primary`
- `--mm-color-surface-default`
- `--mm-color-text-primary`
- `--mm-font-family-body`
- `--mm-spacing-md`
- `--mm-radius-medium`
