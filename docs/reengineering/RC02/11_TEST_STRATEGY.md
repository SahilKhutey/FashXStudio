# RC-02 — Test Strategy & Automated Verification Matrix

## Testing Layers
1. **TypeScript Type Safety**: Strict type validation across all screens, hooks, and design system components.
2. **Component & Unit Testing**: Component behavior, props, and user events using Jest and `@testing-library/react-native`.
3. **Navigation & Route Policy Testing**: Route protection rules, onboarding redirections, and session guards.
4. **Integration & API Contract Testing**: Error handling, token refresh, and wardrobe mutations.

## Verification Matrix

| Test Suite | File Path | Focus | Status |
| :--- | :--- | :--- | :--- |
| **TypeScript Typecheck** | `npm run --prefix mobile typecheck` | Strict compilation across all `.tsx` and `.ts` files | 🟢 0 errors |
| **ESLint Quality Check** | `npx --prefix mobile eslint -c mobile/eslint.config.js mobile/` | Code formatting and styling standards | 🟢 0 errors |
| **Button Component Tests** | `src/design-system/components/__tests__/Button.test.tsx` | Button render, onPress, disabled, and loading states | 🟢 4 passed in 1.81s |
| **Design System Tests** | `src/design-system/__tests__/design-system.test.ts` | Design tokens, color palette, responsive breakpoints | 🟢 17 passed |
| **Route Policy Tests** | `src/navigation/__tests__/route-policy.test.ts` | Route guards, auth redirects, onboarding steps | 🟢 14 passed |
| **Wardrobe & Commerce API** | `src/features/wardrobe/__tests__/commerceApi.test.ts` | Buy click validation, offer selection | 🟢 8 passed |
| **Closet & Offers Tests** | `__tests__/closet_and_offers.test.tsx` | Retailer offers selection and wardrobe integration | 🟢 6 passed |
| **Try-On Polling & Lifecycle** | `__tests__/tryon_polling.test.ts` | Exponential backoff, terminal status detection | 🟢 5 passed |
| **Try-On Screen Logic** | `__tests__/tryon_screen.test.tsx` | Provider classification (mock vs real) | 🟢 4 passed |
| **API Client & Refresh** | `src/api/client.test.ts` | 401 retry, token attachment, timeout handling | 🟢 9 passed |
| **Full Jest Suite Total** | `npm --prefix mobile test -- --ci` | Complete mobile test suite coverage | 🟢 19 suites passed, 137 tests passed in 8.46s |
| **Backend Recommendation Suite** | `pytest tests/unit/test_recommendation_use_case.py` | Feed cold-start, empty reason, backend stability | 🟢 3 passed in 2.90s |
