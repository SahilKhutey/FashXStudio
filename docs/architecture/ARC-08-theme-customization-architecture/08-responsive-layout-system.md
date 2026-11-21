# ARC-08: 08 — Responsive Layout System

## 1. Supported Breakpoints
The responsive layout system operates across 5 platform-controlled breakpoints:
- `mobileSmall`: 320px (Strictly 1 column to prevent horizontal scrolling)
- `mobile`: 375px (1 or 2 columns max)
- `tablet`: 768px (1 to 4 columns)
- `desktop`: 1024px (1 to 6 columns)
- `desktopLarge`: 1440px (1 to 6 columns)

## 2. Mobile Fallback Rule
If a tenant omits responsive overrides, the platform automatically applies default mobile constraints ensuring zero horizontal overflow on small devices.
