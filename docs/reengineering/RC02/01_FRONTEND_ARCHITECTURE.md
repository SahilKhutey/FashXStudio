# RC-02 — Frontend Architecture & State Management

## Architecture Overview
The FashXStudio mobile application is built using React Native, TypeScript, and Expo Router. It separates client state, server state, presentation components, and domain business rules cleanly.

```mermaid
flowchart TD
    subgraph UI ["Presentation Layer"]
        Tabs["Tabs: Discover / Explore / Looks / Closet"]
        Modals["Modals: Settings / Garment Detail / Try-On Studio"]
        DS["Design System: Button, ProductCard, SearchBar, CategoryChip"]
    end

    subgraph State ["Client & Server State"]
        AuthStore["Zustand: AuthStore (Session, User, Token)"]
        QueryClient["TanStack React Query (Cache & Synchronizers)"]
    end

    subgraph Service ["API Services & Feature Hooks"]
        FeedHooks["useFeed / useSignal / useImpressionTracker"]
        WardrobeHooks["useUserWardrobe / useSaveToWardrobe / useRemoveFromWardrobe"]
        TryonHooks["useJob / useTryOnJobs / useStartTryOn / useTryOnFeedback"]
        CatalogHooks["useGarmentDetail / useBuy"]
    end

    subgraph Backend ["FastAPI Live Backend"]
        LiveAPI["/api/v1/feed, /wardrobe/items, /tryon/jobs, /garments/{id}"]
    end

    Tabs --> DS
    Modals --> DS
    Tabs --> Service
    Modals --> Service
    Service --> QueryClient
    Service --> AuthStore
    Service --> LiveAPI
```

## State Management Responsibilities

### 1. Global Authentication & Session State (`Zustand`)
- **File**: `mobile/src/features/auth/authStore.ts`
- **Scope**: Authenticated user session, `me` object, role, onboarding completion flags.
- **Security**: Token storage handled securely via `expo-secure-store` or dev token session. On sign-out or account erasure, queries are invalidated and cached tokens are cleared.

### 2. Server State & Remote Caching (`TanStack React Query`)
- **Feed Cache**: Stored under query key `["feed"]`. Invalidated upon recording negative interaction signals (`hide`, `not_interested`) or refreshing.
- **Wardrobe Cache**: Stored under query key `["wardrobe"]`. Invalidated upon saving or removing items.
- **Try-On Jobs**: Polled with exponential/adaptive intervals until reaching terminal status (`completed`, `failed`, `cancelled`).

### 3. Navigation State (`Expo Router`)
- File-based router using typed routes in `mobile/app/`.
- Deep linking support for `/garment/[id]` and `/tryon/[jobId]`.
