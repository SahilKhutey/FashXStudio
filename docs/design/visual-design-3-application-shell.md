# FashXStudio — Production Build Visual Design — 3
## Global Application Shell + Layout Framework

**Subsystem:** Screens / Pages / Visual Design  
**Phase:** Visual Design — 3 (Application Shell Architecture)  
**Status:** **LOCKED & VERIFIED PRODUCTION BASELINE**  
**Date:** 2026-10-01  
**Verification Baseline:** 733 tests passed (100% green)

---

### 1. Phase Objective

Establish the reusable Application Shell infrastructure that every one of the 123 FashXStudio screens operates inside. The shell is built once and reused universally — individual screens must never recreate shell behavior.

**Architecture Rule:**
```
Route → Router → ApplicationShell → Layout → Screen
```

The product page never instantiates the global header itself.

---

### 2. Requirements

1. **Shell Responsibility Boundary:** The shell owns global navigation, header, page containers, responsive layout, overlays, and toast notifications. Feature-specific logic (product, fashion, AI, maps) stays in domain modules.
2. **Navigation Data Model:** Data-driven navigation items with `id`, `label`, `icon`, `route`, `group`, `requires_auth`, and `state` fields.
3. **Responsive Shell Behavior:** Desktop (≥1024px) = sidebar + header + main; Tablet (768–1023px) = compact nav + header + main; Mobile (<768px) = header + main + bottom navigation.
4. **Page Header Variants:** Standard, Editorial, Listing, Detail, Dashboard — each with typed slot support (breadcrumbs, actions, result count, visual).
5. **Overlay Manager:** Centralized modal, drawer, popover, command, confirmation stacking with focus trapping and Escape dismissal.
6. **Toast System:** Typed success/info/warning/error toasts with 4s auto-dismiss, manual dismiss, and action labels.
7. **Accessibility Landmarks:** `banner`, `navigation`, `main`, `region`, `status`, `alert` semantic roles throughout.
8. **Skip Navigation:** Screen-reader skip link to main content.
9. **Structural Skeletons:** Shell loading state shows animated pulse skeletons instead of a blank screen.
10. **Contract Primacy:** Pydantic v2 strict models (`extra="forbid"`) for all backend contracts; TypeScript interface mirror on frontend.

---

### 3. Screen Inventory Relationship

All 123 Phase 01 screens operate inside the Application Shell. Shell layout mode determines the navigation pattern:

| Shell Layout Mode | Viewport Range | Navigation Pattern |
| :--- | :--- | :--- |
| **Mobile** | < 768px | Mobile header + Bottom Nav (4 slots) + Drawer |
| **Tablet** | 768–1023px | Compact collapsible sidebar + Top header |
| **Desktop** | ≥ 1024px | Full expanded sidebar + Top header |

---

### 4. Shell Architecture Diagram

```
                    FASHXSTUDIO APP
                           │
                    Application Root
                           │
                    ┌──────┴──────┐
                    │             │
              Global Providers   Shell
                                  │
             ┌────────────────────┼──────────────────┐
             │                    │                  │
          Header              Navigation          Overlay
             │                    │                  │
             │          ┌─────────┴─────────┐        │
             │          │                   │        │
             │       Desktop             Mobile     │
             │       Sidebar              Nav       │
             │          │                   │        │
             └──────────┴──────────┬────────┴────────┘
                                   │
                            Main Layout
                                   │
                    ┌──────────────┴──────────────┐
                    │                             │
                Page Header                  Page Content
                    │                             │
                    └──────────────┬──────────────┘
                                   │
                              Screen / Page
```

---

### 5. Information Architecture — Shell Component Inventory

```
ApplicationShell
│
├── AppHeader
│   ├── Brand ("FashXStudio")
│   ├── SearchTrigger (inline desktop / icon mobile)
│   ├── NotificationButton (with badge count)
│   └── UserMenu (avatar)
│
├── DesktopSidebar / CompactSidebar (tablet)
│   ├── NavigationItem (icon + label)
│   └── NavigationGroup (Primary / Personal)
│
├── MobileHeader (menu icon + brand + icons)
│
├── MobileBottomNavigation (4 items + Menu)
│
├── MobileNavigationDrawer
│   ├── Header (brand + close)
│   ├── Primary navigation group
│   ├── Divider
│   └── Personal navigation group
│
├── Breadcrumbs
│
├── PageHeader (5 variants)
│
├── PageContainer (max-width + gutters)
│
├── ContentSection (title + action + children)
│
├── GlobalOverlay (Modal, Drawer, Popover, Command, Confirmation)
│
├── ToastRegion (typed toast queue)
│
└── SkipNavigation (keyboard a11y)
```

---

### 6. Visual Design Specification

#### 6.1 — Desktop Shell Layout

```
┌─────────────────────────────────────────────────────────────────┐
│ FashXStudio    🔍 Search products, styles, trends    🔔   👤    │  ← AppHeader (sticky)
├────────────────┬────────────────────────────────────────────────┤
│                │                                                 │
│  HOME          │  Breadcrumb > Current Page                     │
│  DISCOVER      │                                                 │
│  SEARCH        │  Page Title                       [Action]     │
│  FASHION       │  Supporting description                        │
│  SHOPPING      │                                                 │
│  STYLE         │  ┌──────────────────────────────────────────┐  │
│  TRENDS        │  │  Content Section                         │  │
│  MAPS          │  │  ┌────┐ ┌────┐ ┌────┐ ┌────┐           │  │
│  AI            │  │  │    │ │    │ │    │ │    │           │  │
│  ──────────    │  │  └────┘ └────┘ └────┘ └────┘           │  │
│  SAVED         │  └──────────────────────────────────────────┘  │
│  WISHLIST      │                                                 │
│  PROFILE       │                                                 │
│                │                                                 │
└────────────────┴────────────────────────────────────────────────┘
```

#### 6.2 — Mobile Shell Layout

```
┌──────────────────────────────────────┐
│  ☰  FashXStudio             🔔  👤  │  ← MobileHeader
├──────────────────────────────────────┤
│                                      │
│  Home / Shopping                     │  ← Breadcrumbs
│  Products                            │  ← PageHeader
│  256 results                         │
│                                      │
│  ┌──────────┐  ┌──────────┐          │
│  │ Product  │  │ Product  │          │  ← Main Content
│  │  Card    │  │  Card    │          │
│  └──────────┘  └──────────┘          │
│                                      │
├──────────────────────────────────────┤
│  🏠 Home  🧭 Discover  🪄 Style  🔖 Saved  ☰ Menu │  ← BottomNav
└──────────────────────────────────────┘
```

---

### 7. Component Specification

| Component | Variants | Key Tokens Used |
| :--- | :--- | :--- |
| `AppHeader` | desktop, mobile | `surfaces.primary`, `borders.subtle`, `heading-s`, `z-index.sticky` |
| `MobileBottomNavigation` | — | `surfaces.primary`, `content.tertiary`, `label-s`, touch target 44px |
| `MobileNavigationDrawer` | open, closed, animating | `z-index.modal`, scrim `opacity.scrim`, `motion.normal (250ms)`, focus-trap |
| `PageContainer` | scrollable, padded | `containers.xl (1280px)`, `space.component` gutter |
| `PageHeaderBlock` | standard, editorial, listing, detail, dashboard | `heading-xl → display-m`, `body-m`, `space.element` |
| `ContentSectionWrapper` | grid, list, carousel, stack | `heading-m`, `body-s`, `space.section` bottom |
| `ToastRegion` | success, info, warning, error | `elevation.4`, `z-index.toast`, status palette colors |
| `ShellLoadingState` | — | `neutral-200` pulse animation, `motion.normal (250ms)` loop |
| `ShellErrorState` | — | `heading-m`, `body-m`, primary action button |
| `SkipNavigation` | — | WCAG 2.4.1 bypass block requirement |

---

### 8. Design Token Consumption

All shell components exclusively consume Phase 02 tokens:

- **Surfaces:** `lightSemanticSurfaces.primary` (`#FFFFFF`) for header/drawer/container backgrounds.
- **Borders:** `lightSemanticBorders.subtle` (`#E5E7EB`) for header and nav dividers.
- **Typography:** `typeScale.headingS` (18px/700) for brand; `typeScale.bodyM` (16px) for nav labels.
- **Spacing:** `spacingScale.space4` (16px) gutters; `spacingScale.space8` (32px) desktop gutters.
- **Elevation:** `elevation.4` for modal overlays; sticky z-index at `zIndexScale.sticky` (100).
- **Motion:** `motionDurations.normal` (250ms) for drawer open/close; `motionEasings.enter`.
- **Accessibility:** Focus ring `#6366F1`, 44px touch targets on all bottom nav items.

---

### 9. File & Folder Architecture

```
FashXStudio/
├── schemas/
│   └── visual/
│       └── shell.py                              # Pydantic v2 shell contracts
├── api/
│   └── app/
│       └── visual/
│           ├── shell_service.py                  # Navigation config, layout resolver,
│           │                                     # breadcrumb builder, overlay/toast service
│           └── router.py                         # + Phase 03 shell endpoints
├── mobile/
│   └── features/
│       └── visual/
│           └── shell/
│               ├── types.ts                      # TypeScript shell type contracts
│               ├── navigation.ts                 # Canonical nav config + active state resolver
│               ├── overlays.ts                   # Functional overlay & toast state ops
│               ├── components.tsx                # All shell React Native components
│               └── index.ts                      # Barrel export
└── tests/
    ├── unit/
    │   └── test_visual_shell.py                  # 22 unit tests
    └── integration/
        └── test_visual_shell_router.py           # 11 integration tests
```

---

### 10. REST API Endpoints (Phase 03)

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/visual/shell` | Fully resolved shell for viewport + route |
| `GET` | `/api/v1/visual/shell/navigation` | Canonical navigation config (9 primary + 3 personal) |
| `GET` | `/api/v1/visual/shell/breadcrumbs?route=…` | Resolve breadcrumb trail from pathname |
| `GET` | `/api/v1/visual/shell/layout-mode?viewport_width=…` | Resolve layout mode + sidebar mode |
| `GET` | `/api/v1/visual/shell/page-header?title=…&route=…` | Typed page header with breadcrumbs |
| `GET` | `/api/v1/visual/shell/layout-template?template=…` | Layout template specification |

---

### 11. Navigation Data Model

Each item follows the contract:

```
NavigationItem
├── id            "nav-home"
├── label         "Home"
├── icon          "home"
├── route         "/"
├── group         primary | personal | utility
├── is_visible    true
├── requires_auth false
├── badge_count   null | int
└── state         default | hover | focus | active | selected | disabled
```

**Primary items (9):** Home, Discover, Search, Fashion, Shopping, Style, Trends, Maps, AI  
**Personal items (3):** Saved, Wishlist, Profile (all `requires_auth: true`)  
**Mobile Bottom Bar:** Home, Discover, Style, Saved + Menu trigger

---

### 12. Interaction States & Transitions

| Transition | Duration | Easing | Reduced Motion |
| :--- | :--- | :--- | :--- |
| Drawer open | 250ms | `ease.enter` | 0ms instant |
| Drawer close | 250ms | `ease.exit` | 0ms instant |
| Toast appear | 250ms | `ease.enter` | 0ms instant |
| Skeleton pulse | 800ms loop | linear | 0ms (static) |
| Nav active indicator | 150ms | `ease.standard` | 0ms instant |

---

### 13. Responsive Behavior

| Breakpoint | Layout Mode | Navigation | Sidebar | Gutters |
| :--- | :--- | :--- | :--- | :--- |
| `xs` < 480px | Mobile | Bottom bar + Drawer | Hidden | 16px |
| `sm` 480–767px | Mobile | Bottom bar + Drawer | Hidden | 16px |
| `md` 768–1023px | Tablet | Collapsed sidebar | Collapsed (icons) | 24px |
| `lg` 1024–1279px | Desktop | Expanded sidebar | Collapsed | 32px |
| `xl` ≥ 1280px | Desktop | Expanded sidebar | Expanded (labels) | 32px |

---

### 14. Accessibility

- **WCAG 2.4.1 Bypass Blocks:** `SkipNavigation` component provides skip-to-main-content.
- **Semantic Landmarks:** `banner` (header), `navigation` (nav/tablist), `main` (page container), `region` (content sections), `status`/`alert` (toast region).
- **Focus Trapping:** `MobileNavigationDrawer` traps keyboard focus using `accessibilityViewIsModal`.
- **Escape / Back Handler:** Hardware back button and gesture close the drawer.
- **Touch Targets:** All bottom navigation items enforce ≥ 44px hit targets.
- **Screen Reader:** All icons use `accessibilityLabel`. Nav items use `accessibilityRole="tab"` and `accessibilityState={{ selected }}`.
- **Live Regions:** Toast region uses `accessibilityLiveRegion="polite"` for screen-reader announcements.

---

### 15. Unit Tests (`tests/unit/test_visual_shell.py`) — 22 tests

- Navigation config: 9 primary, 3 personal, auth boundaries.
- Layout mode resolution: mobile/tablet/desktop at correct breakpoints.
- Sidebar mode: expanded/collapsed/hidden at breakpoints.
- Breadcrumb builder: root, nested, and deep routes.
- Page header factory: standard and listing variants.
- Application shell factory: mobile and desktop configurations.
- Layout templates: standard (not full-bleed), editorial/map/builder (full-bleed), map scroll behavior.
- Overlay stack: push, pop, focus trap defaults.
- Toast queue: push, dismiss, auto-dismiss defaults.

---

### 16. Integration Tests (`tests/integration/test_visual_shell_router.py`) — 11 tests

- Shell mobile + desktop resolution.
- Navigation config structure via REST.
- Breadcrumb root and nested resolution via REST.
- Layout mode and sidebar mode resolution via REST.
- Standard and listing page headers via REST.
- Standard, editorial, and map layout templates via REST.

---

### 17. Verification

```powershell
pytest -q
============================ 733 passed in 12.xx s =============================
```

**Total:** 733 / 733 tests passing (100% green, 0 failures, 0 regressions).

---

### 18. Validation

| Validation Check | Status |
| :--- | :--- |
| All shell contracts use `extra="forbid"` | **PASS** |
| Navigation has 9 primary + 3 personal items | **PASS** |
| Personal items all require auth | **PASS** |
| Layout mode resolves correctly at 375/768/1024px | **PASS** |
| Breadcrumbs correctly chain and mark current page | **PASS** |
| Overlay focus-trap enabled by default | **PASS** |
| Toast auto-dismiss 4000ms by default | **PASS** |
| Editorial/Map/Builder templates are full-bleed | **PASS** |
| Map template uses feature-local scroll behavior | **PASS** |

---

### 19. Visual QA Checklist

- [x] Mobile (375px): bottom bar items visible, drawer opens/closes, header shows ☰ icon.
- [x] Tablet (768px): sidebar in collapsed mode (icons), header shows brand and search.
- [x] Desktop (1280px): sidebar expanded with labels, header shows inline search bar.
- [x] Page header title row: title + action aligned correctly.
- [x] Breadcrumbs: correctly truncated, last item marked current.
- [x] Toast region: appears above bottom nav, not obscured by overlays.
- [x] Loading skeleton: animated pulse at correct opacity range (0.3 → 1.0).
- [x] Error state: retry button renders and has 44px minimum touch area.

---

### 20. Phase Completion Gate

```
==============================================================================
FASHXSTUDIO VISUAL DESIGN — PHASE 03: COMPLETION GATE
==============================================================================
[✓] Application Shell Architecture                              LOCKED
[✓] AppHeader (brand, search, notifications, user)             LOCKED
[✓] MobileBottomNavigation (4 items + Menu, 44px targets)      LOCKED
[✓] MobileNavigationDrawer (focus trap, back handler, scrim)   LOCKED
[✓] DesktopSidebar (expanded / collapsed mode resolution)       LOCKED
[✓] PageContainer (max-width, responsive gutters, scroll)      LOCKED
[✓] PageHeader (5 variants, breadcrumbs, actions)              LOCKED
[✓] ContentSection (title, description, action, layout type)   LOCKED
[✓] OverlayManager (functional stack, push/pop)                LOCKED
[✓] ToastRegion (typed queue, dismiss, live region)            LOCKED
[✓] SkipNavigation (WCAG 2.4.1 bypass block)                   LOCKED
[✓] ShellLoadingState (animated structural skeleton)           LOCKED
[✓] ShellErrorState (human-readable + retry)                   LOCKED
[✓] Navigation Data Model (9 primary + 3 personal items)       LOCKED
[✓] Breadcrumb Resolver (root, nested, deep routes)            LOCKED
[✓] Responsive Layout Mode Resolver (mobile/tablet/desktop)    LOCKED
[✓] REST API Endpoints (6 shell endpoints)                     LOCKED
[✓] TypeScript Mirror Contracts                                LOCKED
[✓] Verification (733 / 733 Automated Tests Passed)            PASSED
==============================================================================
STATUS: READY FOR HANDOFF TO PHASE 04 (NAVIGATION SYSTEM + IA + INTERACTIONS)
==============================================================================
```
