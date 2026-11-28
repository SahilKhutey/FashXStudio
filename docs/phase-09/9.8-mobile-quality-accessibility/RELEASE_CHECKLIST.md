# Release Checklist

- [x] Responsive layout hook & container (`useResponsiveLayout`, `ResponsiveContainer`)
- [x] Android back handler & keyboard-safe screen (`useAndroidBackHandler`, `KeyboardSafeScreen`)
- [x] Image fallback, network status & lifecycle hooks (`ImageWithFallback`, `useNetworkStatus`, `NetworkStatusBanner`, `useAppLifecycle`)
- [x] Accessible 48dp button & PII-redacted crash reporting (`AccessibleButton`, `crashReporting.ts`, `permissionPolicy.ts`)
- [x] `tsc --noEmit`, `eslint --max-warnings 0`, and Jest (`36/36` suites, `241/241` tests) pass locally
- [ ] Physical Android & iOS device QA (TalkBack, VoiceOver, interruptions, poor network)
- [ ] Staging crash-reporting event verification
