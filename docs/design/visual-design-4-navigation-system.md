# FashXStudio — Production Build Visual Design — 4
## Navigation System + Information Architecture + Interaction Framework

**Subsystem:** Screens / Pages / Visual Design  
**Phase:** Visual Design — 4 (Navigation System Architecture)  
**Status:** **LOCKED & VERIFIED PRODUCTION BASELINE**  
**Date:** 2026-10-01  
**Verification Baseline:** 778 tests passed (100% green)

---

### 1. Phase Objective

Convert the Global Application Shell (Phase 03) into a production-grade, unified navigation and information-architecture framework that supports the complete FashXStudio 123-screen ecosystem across all devices and platforms.

> **Architecture Rule (Section 4.2 — Rule 01):** One navigation model feeds all surfaces. Desktop, tablet, and mobile consume the same registry. Only the visual presentation changes.

---

### 2. Core Architecture Rules

| Rule | Statement |
|---|---|
| **Rule 01 — One Navigation Model** | Desktop and mobile never maintain separate route definitions. |
| **Rule 02 — Route is Source of Location** | Active navigation state is _derived_ from the current route/URL — never maintained as a parallel "current page" variable. |
| **Rule 03 — UI Visibility ≠ Authorization** | Items can be hidden for feature availability, platform, or user preference, but backend auth remains the authoritative gate. |

---

### 3. Navigation Architecture

```
                      APPLICATION
                           │
                      ROUTE REGISTRY
                           │
                  NAVIGATION RESOLVER
                           │
           ┌───────────────┼───────────────┐
           │               │               │
        Desktop          Tablet          Mobile
           │               │               │
        Sidebar       Compact Nav      Header / Drawer
           │               │               │
           └───────────────┼───────────────┘
                           │
                  CONTEXT NAVIGATION
                           │
          ┌────────────────┼────────────────┐
          │                │                │
      Breadcrumbs        Tabs         Local Actions
                           │
                           ▼
                        SCREEN
```

---

### 4. Information Architecture — Navigation Levels

| Level | Name | Example |
|---|---|---|
| **1** | Global Navigation | Sidebar / Bottom Nav / Drawer |
| **2** | Section Navigation | Shopping sub-nav |
| **3** | Context Navigation | Profile: Overview / Saved / Settings |
| **4** | Local Tabs | Product: Overview / Reviews / Specs / Styling |
| **5** | Actions | Page-level primary/secondary buttons |

---

### 5. Route Registry

**12 top-level routes + nested children:**

```
FASHXSTUDIO ROUTE REGISTRY
│
├── PRIMARY (9 top-level)
│   ├── nav-home      /
│   ├── nav-discover  /discover
│   ├── nav-search    /search
│   ├── nav-fashion   /fashion
│   ├── nav-shopping  /shopping
│   │   ├── nav-shopping-products   /shopping/products
│   │   ├── nav-shopping-categories /shopping/categories
│   │   ├── nav-shopping-cart       /shopping/cart         [auth]
│   │   └── nav-shopping-orders     /shopping/orders       [auth]
│   ├── nav-style     /style
│   │   ├── nav-style-home    /style
│   │   ├── nav-style-outfits /style/outfits
│   │   ├── nav-style-looks   /style/looks
│   │   ├── nav-style-saved   /style/saved               [auth]
│   │   └── nav-style-prefs   /style/preferences         [auth]
│   ├── nav-trends    /trends
│   ├── nav-maps      /maps
│   └── nav-ai        /ai
│
└── PERSONAL (3 top-level)           [all require auth]
    ├── nav-saved     /saved
    ├── nav-wishlist  /wishlist
    └── nav-profile   /profile
        ├── nav-profile-overview  /profile
        ├── nav-profile-saved     /profile/saved
        ├── nav-profile-wishlist  /profile/wishlist
        ├── nav-profile-prefs     /profile/preferences
        └── nav-profile-settings  /profile/settings
```

**Total:** 9 primary + 3 personal top-level = **12 root routes**  
With nested children: **26 total registered routes**

---

### 6. Navigation Item Contract

```python
NavigationRouteContract:
  id           : str          # "nav-discover"
  label        : str          # "Discover"
  icon         : str          # "compass"
  route        : str          # "/discover"
  group        : PRIMARY | PERSONAL | UTILITY
  order        : int          # Display order within group
  visibility   : visible | hidden | disabled | restricted
  active_match : list[str]    # Additional activating prefixes
  is_external  : bool         # External URL
  requires_auth: bool         # Must be authenticated
  feature_flag : str | None   # Feature flag key gating this item
  children     : list[...]    # Nested sub-navigation
  metadata     : dict
```

---

### 7. Responsive Navigation Matrix

| Capability | Desktop | Tablet | Mobile |
|---|---|---|---|
| Global header | ✓ | ✓ | ✓ |
| Sidebar | Expanded (≥1280px) / Collapsed (1024–1279px) | Compact | Drawer |
| Bottom navigation | — | Optional | ✓ (4 items + Menu) |
| Breadcrumb | Full chain | Full chain | Parent label only (`‹ Parent`) |
| Tabs | Full | Full | Scrollable |
| Search | Inline full | Compact | Dedicated `/search` |
| Context nav | ✓ | ✓ | Drawer / Tabs |
| Keyboard navigation | ✓ | ✓ | External keyboard support |
| Touch | ✓ | ✓ | Primary |

---

### 8. Navigation Item Visibility Rules

```
User Context
     ↓
Navigation Resolver
     ↓
┌────────────────────────────────┐
│ Item checks (in order):        │
│ 1. Feature flag enabled?       │  → hidden if not enabled
│ 2. Requires auth + is auth'd?  │  → restricted if not authenticated
│ 3. Explicit visibility field   │  → visible / disabled / hidden
└────────────────────────────────┘
     ↓
Resolved NavigationGuardResult
```

> Backend authorization remains authoritative. Guards are UI-only.

---

### 9. Breadcrumb System

**Full chain (desktop/tablet):**
```
Home / Shopping / Products / Jacket
```
**Mobile adaptation:**
```
‹ Products
```
**Truncation** (> 4 levels): intermediate entries are collapsed.

**Contract:**
```
BreadcrumbChainContract:
  entries     : [BreadcrumbEntryContract]
  mobile_label: str       # Parent label for mobile back link
  is_truncated: bool      # True when intermediate entries collapsed
```

**Entry:**
```
BreadcrumbEntryContract:
  label        : str
  route        : str
  position     : int       # 1-based
  is_current   : bool
  is_interactive: bool     # Current entry is NOT interactive (Section 4.14)
```

---

### 10. Tab System

**Route-based tabs** (drives URL, supports deep linking):
```
/products/123
/products/123/reviews
/products/123/specifications
/products/123/styling
```

**State-based tabs** (local view switching, no URL change):
```
ProductDetailView → Overview | Reviews | Specs | Styling
(all at same route, state managed locally)
```

**Well-known tab groups:**
- `product-detail-tabs`: Overview, Reviews, Specs, Styling
- Profile context nav: Overview, Saved, Wishlist, Preferences, Settings

---

### 11. Navigation Error States

| Error | Code | Primary Recovery | Secondary Recovery |
|---|---|---|---|
| Not Found | `not_found` | Go Home `/` | Explore Discover `/discover` |
| Data Failure | `data_failure` | Try Again (same route) | Return to Discover `/discover` |
| Forbidden | `forbidden` | Go Home `/` | Explore Discover `/discover` |
| Feature Disabled | `feature_disabled` | Go Home `/` | Explore Discover `/discover` |

---

### 12. Navigation Analytics Events

| Event | Trigger |
|---|---|
| `navigation_view` | Route is rendered |
| `navigation_click` | Nav item is tapped/clicked |
| `navigation_open` | Drawer/sidebar opens |
| `navigation_close` | Drawer/sidebar closes |
| `breadcrumb_click` | Breadcrumb segment clicked |
| `tab_change` | Tab switches |
| `back_navigation` | Back action triggered |
| `external_navigation` | External URL opened |
| `search_navigation` | Search query submitted |
| `deep_link_entry` | Application entered via deep link |
| `navigation_error` | Navigation failure (404, forbidden, etc.) |

---

### 13. File & Folder Architecture

```
FashXStudio/
├── schemas/
│   └── visual/
│       └── navigation.py                        # Pydantic v2 navigation contracts
├── api/
│   └── app/
│       └── visual/
│           ├── navigation_service.py            # Registry, resolver, breadcrumbs,
│           │                                    # guards, tabs, analytics, errors
│           └── router.py                        # + 9 Phase 04 navigation endpoints
├── mobile/
│   └── features/
│       └── visual/
│           └── navigation/
│               ├── types.ts                     # TypeScript mirror contracts
│               ├── registry.ts                  # Route registry + guard evaluator
│               ├── resolver.ts                  # Breadcrumb, state, full resolver
│               ├── state.ts                     # Functional nav state operations
│               ├── analytics.ts                 # Typed event builders
│               ├── tabs.ts                      # Tab/context navigation builders
│               └── index.ts                     # Barrel export
└── tests/
    ├── unit/
    │   └── test_visual_navigation.py            # 31 unit tests (NAV-001→NAV-027+)
    └── integration/
        └── test_visual_navigation_router.py     # 14 integration tests
```

---

### 14. REST API Endpoints (Phase 04)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/visual/navigation/registry` | Full route registry |
| `GET` | `/api/v1/visual/navigation/resolve` | Full navigation resolver result |
| `GET` | `/api/v1/visual/navigation/breadcrumbs` | Typed breadcrumb chain |
| `GET` | `/api/v1/visual/navigation/guards` | All item visibility guard results |
| `GET` | `/api/v1/visual/navigation/tabs/product` | Product detail tab group |
| `GET` | `/api/v1/visual/navigation/context` | Context navigation for a page section |
| `GET` | `/api/v1/visual/navigation/error/404` | 404 error contract |
| `GET` | `/api/v1/visual/navigation/error/data-failure` | Data failure error contract |

---

### 15. Unit Tests (`tests/unit/test_visual_navigation.py`) — 31 tests

- **NAV-001–005:** Registry loads, IDs unique, routes valid, groups correct, nested routes
- **NAV-006–010:** Route resolver, active item, parent section, invalid route, feature flags
- **NAV-011–014:** Desktop expanded/collapsed presentation, sidebar toggle, active item in state
- **NAV-016–018:** Drawer open, closes on navigation
- **NAV-020:** Mobile presentation resolution
- **NAV-021–023:** Breadcrumb hierarchy, non-interactive current, mobile label
- **NAV-024–027:** Active tab, disabled tab, tab mode
- **Guards:** Unauthenticated restricts auth items; authenticated shows all
- **Errors:** 404, data-failure, forbidden contracts
- **Analytics:** Event structure validation
- **Context Nav:** Profile active item; unknown ID returns None

---

### 16. Integration Tests (`tests/integration/test_visual_navigation_router.py`) — 14 tests

- Registry structure (9 primary, 3 personal, nested children)
- Resolver mobile → `mobile_header` presentation
- Resolver desktop → `desktop_expanded` presentation
- Resolver nested child → active + parent set
- Breadcrumbs shallow (2 entries) and deep (3 entries)
- Guards unauthenticated → restricted; authenticated → all visible
- Product tabs with active route
- Profile context nav with active item
- Unknown context nav → 404
- 404 and data-failure error contracts

---

### 17. Verification

```powershell
pytest -q
============================ 778 passed in 12.xx s =============================
```

**Total:** 778 / 778 tests passing (100% green, 0 failures, 0 regressions).

---

### 18. Accessibility Checklist (Section 4.41)

- [x] Navigation landmarks: `banner`, `navigation`, `tablist`, `menuitem` semantic roles
- [x] Keyboard navigation: Tab → item, Enter/Space → navigate, Arrow → within list, Escape → close
- [x] Focus visibility: 2px Electric Indigo (#6366F1) focus ring (Phase 02 token)
- [x] Drawer focus trap: `accessibilityViewIsModal` on drawer modal
- [x] Focus restoration: Back handler restores focus to drawer trigger
- [x] Screen reader labels: All nav items have `accessibilityLabel`
- [x] Current-page indication: `accessibilityState={{ selected: true }}` on active item
- [x] Escape behavior: `BackHandler` closes mobile drawer
- [x] Touch targets: All items ≥ 44px (`minHeight: 44`)
- [x] No color-only active state: Active items use background + weight + indicator
- [x] Reduced motion: Motion timing can be zeroed via `ReducedMotionTokens`

---

### 19. Performance Principles (Section 4.43)

- Navigation registry is a **singleton** built at module load — never rebuilt on each route change
- Active item resolution is **O(n)** flat scan across ≤ 26 routes — no expensive tree traversal
- Navigation state is **derived from route** — no manual sync required
- Feature flag evaluation is **pure function** — safe to memoize
- Guard results are computed once per resolution — not re-evaluated on every render

---

### 20. Phase Completion Gate

```
==============================================================================
FASHXSTUDIO VISUAL DESIGN — PHASE 04: COMPLETION GATE
==============================================================================
[✓] Unified Navigation Model (Rule 01 — one registry, multiple surfaces)   LOCKED
[✓] Route Registry (12 root + 14 nested = 26 total routes)                 LOCKED
[✓] Navigation Resolver (active item, parent, state from route)            LOCKED
[✓] Navigation State Contract (currentRoute, expandedGroups, etc.)         LOCKED
[✓] Breadcrumb System (full chain, mobile_label, truncation)               LOCKED
[✓] Tab System (route-based + state-based, product tabs)                   LOCKED
[✓] Context Navigation (profile context nav + builder)                      LOCKED
[✓] Navigation Visibility Guards (visible/hidden/disabled/restricted)       LOCKED
[✓] Feature Flag Navigation (Section 4.29)                                  LOCKED
[✓] Navigation Analytics Events (11 event types, Section 4.30)             LOCKED
[✓] Navigation Error Contracts (404, data-failure, forbidden)               LOCKED
[✓] TypeScript Navigation Package (types, registry, resolver, state, tabs) LOCKED
[✓] REST API Endpoints (8 navigation endpoints)                             LOCKED
[✓] Verification (778 / 778 Automated Tests Passed)                        PASSED
==============================================================================
STATUS: READY FOR HANDOFF TO PHASE 05 (PRIMITIVE + CORE UI COMPONENT FRAMEWORK)
==============================================================================
```
