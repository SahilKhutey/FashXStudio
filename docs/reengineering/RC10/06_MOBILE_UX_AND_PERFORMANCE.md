# RC10-F: Mobile UX and Performance Optimization

## 1. Objectives
Eliminate frontend crashes, duplicate submissions, and inconsistent state transitions across the full shopping and try-on journey on Expo (React Native).

## 2. Core Mobile Invariants
1. **Empty, Loading & Error States**:
   - Every list, screen, and modal must provide explicit loading indicators (skeletons), informative empty states (e.g. Empty Wardrobe guidance), and actionable retry prompts on network failure.
2. **Duplicate Submission Guards**:
   - VTO submission buttons, wardrobe save actions, and buy-click triggers must disable immediately upon press and display activity spinners until acknowledgment.
3. **Session & Cache Isolation**:
   - On sign-out, all user tokens, cached photos, and transient wardrobe queries must be evicted from persistent device storage (`SecureStore` and AsyncStorage).
4. **Physical Device QA**:
   - Android APK and iOS builds must be verified on physical hardware for camera permissions, background app pausing/resuming, and intermittent network reconnects.

## 3. Automated Mobile Gate
Mobile verification script in CI runs:
```bash
cd mobile
npx tsc --noEmit
npx eslint . --max-warnings 0
npx jest --ci
```
Ensures zero type regressions and strict design-system component test adherence.
