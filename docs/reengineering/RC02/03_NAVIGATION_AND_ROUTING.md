# RC-02 — Navigation, Routing & Shell Architecture

## Primary Navigation Shell
The primary tab bar is defined in [`mobile/app/(tabs)/_layout.tsx`](file:///c:/Users/ASUS/Documents/FashXStudio/mobile/app/(tabs)/_layout.tsx) with four distinct destinations:

| Route Name | Tab Title | Tab Label | Icon | Destination File | Responsibility |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `feed` | Discover | Home | ✦ | `mobile/app/(tabs)/feed.tsx` | Personalized discovery feed |
| `explore` | Explore | Explore | ⌕ | `mobile/app/(tabs)/explore.tsx` | Search, catalog browsing & categories |
| `looks` | Your Looks | Looks | ▧ | `mobile/app/(tabs)/looks.tsx` | Try-on history and rendered looks |
| `closet` | My Closet | Closet | ♧ | `mobile/app/(tabs)/closet.tsx` | Saved garments & personal wardrobe |

## Header & Global Actions
- **Settings Access**: The tab layout includes a header button (`⚙`) in `headerRight` that navigates to `/settings` (`mobile/app/settings/index.tsx`), ensuring settings and privacy controls are accessible across all main tabs without taking up tab bar real estate.

## Explore Route Recovery (BP-03 Resolved)
- **Problem**: In RC-00 and RC-01 baseline, `mobile/app/(tabs)/closet.tsx` referenced `/(tabs)/explore` on empty states, but the route file did not exist in the repository, resulting in broken navigation and TypeScript compilation failures.
- **Resolution**: Implemented [`mobile/app/(tabs)/explore.tsx`](file:///c:/Users/ASUS/Documents/FashXStudio/mobile/app/(tabs)/explore.tsx), delivering a fully functional search, filter, and catalog grid interface.

## Route Policies & Guards
Defined in [`mobile/src/navigation/route-policy.ts`](file:///c:/Users/ASUS/Documents/FashXStudio/mobile/src/navigation/route-policy.ts):
- Unauthenticated users are redirected to `/(auth)/sign-in`.
- Users with incomplete onboarding are routed to their required step (`/onboarding/consent`, `/onboarding/profile`, `/onboarding/quiz`, `/onboarding/capture`).
- Authenticated users with completed onboarding are directed into `/(tabs)/feed`.
- All routes verified via [`src/navigation/__tests__/route-policy.test.ts`](file:///c:/Users/ASUS/Documents/FashXStudio/mobile/src/navigation/__tests__/route-policy.test.ts) (passing).
