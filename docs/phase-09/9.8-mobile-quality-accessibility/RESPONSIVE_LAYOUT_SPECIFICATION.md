# Responsive Layout Specification

- `getLayoutMetrics()` (`mobile/src/hooks/useResponsiveLayout.ts`) adapts `columns` (`1` compact `<360`, `2` phone `<768`, `3` tablet `<1024`, `4` desktop `>=1024`), `horizontalPadding` (`12` / `16` / `24` / `32`), and `contentMaxWidth: 1120`.
- `ResponsiveContainer` (`mobile/src/components/ResponsiveContainer.tsx`) centers content within `maxWidth` with optional `SafeAreaView`.
