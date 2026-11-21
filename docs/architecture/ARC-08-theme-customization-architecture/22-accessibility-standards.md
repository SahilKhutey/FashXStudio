# ARC-08: 22 — Accessibility Standards

## 1. Compliance Requirements
- **Color Contrast**: Minimum 4.5:1 for normal text and 3:1 for large headings (WCAG 2.1 Level AA / AAA).
- **Keyboard Navigation**: All interactive elements (categories, item cards, modals) must be navigable via Tab and Enter keys.
- **Focus Rings**: Standardized `--mm-focus-ring-color` and `--mm-focus-ring-width` (min 2px) for visible keyboard focus.
- **Reduced Motion**: Respects `prefers-reduced-motion` media queries via motion tokens.
- **Minimum Touch Target**: 44x44px minimum for mobile interactive controls.
