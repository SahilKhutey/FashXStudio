# FashXStudio — Production Build Visual Design — 0
## Visual Design Development Foundation / Master Baseline

**Subsystem:** Screens / Pages / Visual Design  
**Phase:** Visual Design — 0 (Pre-Phase-01 Foundation & Lock Document)  
**Status:** **LOCKED & VERIFIED BASELINE**  
**Date:** 2026-09-28  
**Verification Baseline:** 676 tests passed (100%)  

---

### 0.1 — Build Objective
We are transitioning the established FashXStudio subsystems into a unified, production-grade visual product system:

```
Existing FashXStudio Core Systems
        │
        ├── Foundation
        ├── Core
        ├── ML / AI
        ├── Product Systems
        ├── Shopping Systems
        └── Workflow Systems
                │
                ▼
─────────────────────────────────────────────
        VISUAL PRODUCT SYSTEM
─────────────────────────────────────────────
                │
        ├── Screens
        ├── Pages
        ├── Components
        ├── Content Templates
        ├── Shopping Interfaces
        ├── Regional Maps
        ├── AI Interfaces
        └── Responsive Experiences
```

The visual product layer is engineered to be:
* **Modular:** Fully composable from independent, reusable primitives.
* **Reusable:** Zero ad-hoc duplication of typography, colors, or controls.
* **Responsive:** Mathematically sound across mobile, tablet, and desktop.
* **Accessible:** WCAG 2.2 AAA compliant with full screen-reader and keyboard parity.
* **Data-Driven:** Strictly bound to Pydantic v2 domain schemas (`extra="forbid"`).
* **Fashion-Oriented:** Editorial imagery, silhouette presentation, and color harmony.
* **Shopping-Oriented:** Predictable placement of pricing, variants, and checkout handoffs.
* **Geography-Aware:** Multi-layered spatial context and localized fashion trends.
* **AI-Ready:** Explainable stylist insights without replacing user agency.
* **Production-Ready:** Hardened with unit tests, integration tests, and release gates.

---

### 0.2 — Visual Design Layered Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FASHXSTUDIO UI                           │
├─────────────────────────────────────────────────────────────────┤
│ Pages / Screens                                                 │
│ Discover, Fitting Canvas, Lookbook Studio, Cart, Profile...    │
├─────────────────────────────────────────────────────────────────┤
│ Feature Components                                              │
│ ProductGrid, FilterSheet, OutfitBuilder, MapExplorer, AIChat    │
├─────────────────────────────────────────────────────────────────┤
│ Design Components                                               │
│ ProductCard, FashionCard, LayerDrawer, ReviewModal, Tabs...     │
├─────────────────────────────────────────────────────────────────┤
│ Primitive Components                                            │
│ Button, Input, Text, Icon, Image, Badge, Divider, Spinner...    │
├─────────────────────────────────────────────────────────────────┤
│ Design Tokens                                                   │
│ Colors, Typography, Spacing, Sizing, Radius, Elevation, Motion │
├─────────────────────────────────────────────────────────────────┤
│ UI Foundation                                                   │
│ Accessibility, Responsive Geometry, State Engine, Safe Areas   │
└─────────────────────────────────────────────────────────────────┘
```

---

### 0.3 — Core Visual Philosophy
FashXStudio visually communicates six core pillars:

1. **Fashion:** High visual hierarchy, editorial typography, full-bleed imagery, and nuanced garment silhouette presentation.
2. **Discovery:** Uncluttered serendipity powered by Maximal Marginal Relevance (MMR $\lambda = 0.7$) diversity ranking.
3. **Shopping:** Absolute commercial clarity. Product title, current price, multi-merchant comparison, size availability, and checkout action must be instantaneously scannable.
4. **Intelligence:** Seamlessly integrated AI insights. Stylist reasoning appears as native chips, rationale drawers, and undertone tags—never as a detached chatbot overlay.
5. **Geography:** Spatial fashion data rendered through heatmaps, city clusters, and climate-adaptive wardrobe advisories.
6. **Trust & Transparency:** Absolute visual demarcation across information types:
$$\text{Product Information} \longrightarrow \text{System Recommendation} \longrightarrow \text{AI-Generated Insight} \longrightarrow \text{User Decision}$$

---

### 0.4 — Design Principles

#### Principle 01 — Visual First
Fashion is fundamentally visual. Interface design enforces:
$$\text{Image} \longrightarrow \text{Context} \longrightarrow \text{Information} \longrightarrow \text{Action}$$

#### Principle 02 — Progressive Disclosure
Interfaces expose data in three tiered levels of information density:
* **Level 1 (Essential Information):** Primary photograph, normalized product title, price, primary CTA ("Try On" / "Save").
* **Level 2 (Supporting Context):** Brand, Monk skin tone harmony chip, size availability, merchant count.
* **Level 3 (Advanced Intelligence):** Multimodal compatibility breakdown, size chart centimeter dimensions, community fit bias, C2PA synthetic watermark provenance.

---

### 0.5 — Visual Hierarchy
Every screen enforces an unambiguous visual priority stack:
$$\text{HERO / PRIMARY CONTENT} \longrightarrow \text{PRIMARY INFO} \longrightarrow \text{SECONDARY INFO} \longrightarrow \text{SUPPORTING CONTENT} \longrightarrow \text{ACTIONS}$$

No screen is permitted to present competing primary focal points unless explicitly executing a dual-garment or split-pane comparison.

---

### 0.6 — Design Token Foundation & Token Hierarchy
Tokens are organized into four strictly segregated tiers:
$$\text{Primitive Tokens} \longrightarrow \text{Semantic Tokens} \longrightarrow \text{Component Tokens} \longrightarrow \text{Screen Usage}$$

```text
tokens/
├── color/          # Primitives (neutral.900) -> Semantic (text.primary) -> Component (product-card.title)
├── typography/     # Font family, weight, line-height, letter-spacing
├── spacing/        # 4px base increment grid (4, 8, 12, 16, 24, 32, 48, 64)
├── sizing/         # Standard icon sizes, avatar radii, container bounds
├── radius/         # none(0), sm(4), md(8), lg(12), xl(16), full(9999)
├── border/         # Subtle hairline (1px), active focus (2px)
├── shadow/         # Soft diffuse elevation shadows
├── elevation/      # Levels 0 to 5
├── breakpoint/     # xs(0), sm(480), md(768), lg(1024), xl(1280)
├── z-index/        # 0 (Base), 10 (Cards), 100 (Header), 500 (Drawer), 1000 (Modal), 2000 (Toast)
├── motion/         # Easing curves, spring configs, transition durations
├── opacity/        # Hover (0.8), disabled (0.4), overlay (0.6)
└── accessibility/  # High contrast overrides, focus ring definitions
```

---

### 0.7 — Typography Architecture
Typography is categorized into five functional strata:

| Strata | Styles | Usage Context |
| :--- | :--- | :--- |
| **Display** | `Display-1`, `Display-2`, `Display-3` | Hero lookbooks, seasonal editorial banners, splash headers. |
| **Heading** | `H1`, `H2`, `H3`, `H4`, `H5`, `H6` | Page titles, drawer headers, section separators, modal titles. |
| **Body** | `Body Large`, `Body Regular`, `Body Small` | Stylist rationale text, product specifications, descriptions. |
| **UI** | `Label`, `Caption`, `Button`, `Navigation` | Tab labels, pill filters, badge indicators, CTA buttons. |
| **Data** | `Price`, `Rating`, `Metadata`, `Mono Numbers` | Monetary values, discount percentages, fit bias ratios, trace IDs. |

---

### 0.8 — Layout Architecture
The global layout model enforces strict container containment:
$$\text{Viewport} \longrightarrow \text{Container} \longrightarrow \text{Grid} \longrightarrow \text{Sections} \longrightarrow \text{Components}$$

```text
┌────────────────────────────────────────────────────────┐
│ Global Top Bar / App Shell Header                      │
├────────────────────────────────────────────────────────┤
│ Page Header / Breadcrumb Trail                         │
│ ┌────────────────────────────────────────────────────┐ │
│ │ Main Content Container (Max-Width 1440px)          │ │
│ │                                                    │ │
│ │  ┌──────────────┐ ┌──────────────┐ ┌─────────────┐ │ │
│ │  │ Section 1    │ │ Section 2    │ │ Section 3   │ │ │
│ │  └──────────────┘ └──────────────┘ └─────────────┘ │ │
│ └────────────────────────────────────────────────────┘ │
├────────────────────────────────────────────────────────┤
│ Bottom Tab Bar (Mobile) / Persistent Footer (Web)      │
└────────────────────────────────────────────────────────┘
```

---

### 0.9 — Grid System & Responsive Geometry

* **Desktop ($\ge 1024\text{px}$):** 12-column grid, 24–32px gutters, 32–48px outer margin, max content width 1440px.
* **Tablet ($768 - 1023\text{px}$):** 8-column grid, 20px gutters, 24px outer margin, max content width 960px.
* **Mobile ($0 - 767\text{px}$):** 4-to-6 column fluid grid, 12–16px gutters, 16–20px outer margin, full width.

---

### 0.10 — Component Taxonomy

* **Level 1 (Primitives):** `Text`, `Icon`, `Image`, `Button`, `Input`, `Link`, `Divider`, `Spinner`.
* **Level 2 (Common UI):** `Card`, `Badge`, `Avatar`, `Dropdown`, `Modal`, `Drawer`, `Tabs`, `Tooltip`, `Toast`, `Pagination`.
* **Level 3 (Domain Components):** `ProductCard`, `FashionCard`, `OutfitCard`, `TrendCard`, `BrandCard`, `MapCard`, `RecommendationCard`, `AIInsightCard`.
* **Level 4 (Feature Components):** `ProductGrid`, `FilterPanel`, `OutfitStudioCanvas`, `VirtualFittingRoom`, `MapExplorer`, `StylistConsole`, `ShoppingBagDrawer`.

---

### 0.11 — Component State Architecture

Every interactive component implements the 12 canonical interaction states:
$$\text{Default} \longrightarrow \{\text{Hover, Focus, Active, Selected, Disabled, Loading, Success, Warning, Error, Empty, Offline}\}$$

For asynchronous, data-dependent components:
$$\text{Loading} \longrightarrow \text{Loaded} \begin{cases} \text{Data State} \\ \text{Empty State} \end{cases} \Big| \longrightarrow \text{Error State}$$

---

### 0.12 — Fashion Content Visual Architecture
Fashion content is standardized into nine specialized content classes:
$$\text{Fashion} \longrightarrow \{\text{Product, Outfit, Look, Style, Trend, Collection, Brand, Editorial, Recommendation}\}$$

Every fashion content object encapsulates:
1. **Visual:** High-resolution optimized asset with focal-point awareness.
2. **Metadata:** Brand, category, normalized price, physical fabric/cut attributes.
3. **Context:** Seasonality, Monk skin tone harmony, occasion relevance.
4. **Actions:** Save to Closet, Try On in Fitting Room, Share Look, Purchase.
5. **Related Content:** Mix-and-match pairings, alternative colorways, stylist suggestions.

---

### 0.13 — Shopping Visual Architecture
Shopping workflows follow a deterministic funnel:
$$\text{Discover} \longrightarrow \text{Understand} \longrightarrow \text{Compare} \longrightarrow \text{Select} \longrightarrow \text{Save / Cart} \longrightarrow \text{Purchase Flow}$$

**Commercial Transparency Rule:** Commercial data (real-time price, merchant origin, stock status, delivery SLA) is never obscured, tucked behind hidden gestures, or subordinated to decorative aesthetics.

---

### 0.14 — AI Visual Architecture
AI experiences adhere to strict user-agency workflows:
$$\text{User Input} \longrightarrow \text{Processing Indicator} \longrightarrow \text{AI Result} \longrightarrow \text{Explanation / Context} \longrightarrow \text{User Controls} \longrightarrow \text{User Action}$$

* AI recommendations must always be visually accompanied by the "Why this recommendation?" explanation card.
* User controls (`[Apply]`, `[Modify]`, `[Dismiss]`) must remain prominent; AI output never forces automated cart additions.

---

### 0.15 — Geography & Maps Visual Architecture
Geographic interfaces employ three visual layers:
$$\text{Geographic Base Map} \longrightarrow \text{Regional Data Layer (Heatmaps)} \longrightarrow \text{Fashion \& Shopping Layer (Stores, Local Trends)}$$

Maps operate as primary interactive shopping surfaces, allowing pin selection, micro-cluster expansion, and local artisan discovery.

---

### 0.16 — Responsive Design Contract
Every screen must maintain complete fidelity across all 5 device tiers:
* Compact Mobile (`xs`: $< 480\text{px}$)
* Large Mobile (`sm`: $480 - 767\text{px}$)
* Tablet (`md`: $768 - 1023\text{px}$)
* Laptop (`lg`: $1024 - 1279\text{px}$)
* Desktop (`xl`: $\ge 1280\text{px}$)

---

### 0.17 — Accessibility Baseline (WCAG 2.2 AAA)
* **Semantic Roles:** Explicit ARIA and React Native accessibility roles on all controls.
* **Focus Visibility:** High-contrast 2px focus ring indicator on keyboard/accessibility focus.
* **Touch Targets:** Minimum $48 \times 48\text{ dp}$ bounding box for all interactive triggers.
* **Contrast:** Minimum $7:1$ contrast ratio for body text, $4.5:1$ for large headings.
* **Reduced Motion:** Automatic suppression of non-essential animations when `prefers-reduced-motion` is active.

---

### 0.18 — Visual States
Every page handles 4 mandatory state conditions:
1. **Loading:** Shimmer skeleton placeholders matching layout geometry (zero Cumulative Layout Shift).
2. **Empty:** Contextual illustration, clear explanation, and primary recovery action.
3. **Error:** RFC-7807 compliant error messaging, correlation trace ID, and retry CTA.
4. **Success:** Transient or persistent confirmation badge/toast.

---

### 0.19 — Standard Screen Specification Contract (17-Point Schema)
Every future screen in FashXStudio is specified and audited using the 17-point contract codified in [`schemas/visual/v1.py`](file:///c:/Users/ASUS/Documents/FashXStudio/schemas/visual/v1.py):
1. `SCREEN ID`: Unique identifier (`SCR-DOMAIN-NN`).
2. `SCREEN NAME`: Formal title.
3. `PURPOSE`: Business and user objective.
4. `USER`: Target persona.
5. `ENTRY POINT`: Inbound trigger/route.
6. `EXIT POINT`: Outbound destinations.
7. `PRIMARY ACTION`: Hero CTA.
8. `SECONDARY ACTIONS`: Supporting CTAs.
9. `DATA SOURCES`: Backing APIs & endpoints.
10. `COMPONENTS`: Required L1–L4 components.
11. `STATES`: Handled interaction states.
12. `RESPONSIVE RULES`: Viewport scaling behavior.
13. `ACCESSIBILITY`: WCAG criteria & labels.
14. `ERROR HANDLING`: Boundaries and retry paths.
15. `ANALYTICS EVENTS`: Emitted telemetry events.
16. `DEPENDENCIES`: Backing platform features (`FX-Fxx`).
17. `TEST CASES`: Validation test suite IDs.

---

### 0.20 — Visual File Architecture (Repository Alignment)

```text
mobile/
├── features/
│   └── visual/
│       ├── types.ts          # Contracts, enums, 17-point screen specification
│       ├── inventory.ts      # Canonical 54-screen inventory
│       ├── responsive.ts     # Breakpoint metrics and column math
│       ├── state.ts          # 12-state UI machine and envelope helpers
│       ├── navigation.ts     # Tabs, routes, breadcrumbs resolver
│       ├── shell.tsx         # AppShell, ScreenContainer, StateBoundary
│       └── index.ts          # Barrel export
schemas/
└── visual/
    ├── __init__.py           # Package exports
    └── v1.py                 # Pydantic v2 BaseContractModel schemas (extra="forbid")
api/app/
└── visual/
    ├── __init__.py           # Package exports
    ├── catalog.py            # Canonical screen inventory catalog
    └── router.py             # REST endpoints (/api/v1/visual/...)
```

---

### 0.21 — Screen Development Lifecycle
$$\text{Requirement} \to \text{Journey} \to \text{Wireframe} \to \text{Visual Spec} \to \text{Component Mapping} \to \text{Implementation} \to \text{Data Integration} \to \text{State Implementation} \to \text{Responsive} \to \text{A11y} \to \text{Tests} \to \text{Visual QA} \to \text{Gate Sign-Off}$$

---

### 0.22 — GitHub Branching & Release Model
Standardized branch naming for the visual design program:
`feature/ui-visual-foundation` $\to$ `feature/ui-design-tokens` $\to$ `feature/ui-shell` $\to$ `feature/ui-navigation` $\to$ `feature/ui-components` $\to$ `feature/ui-fashion` $\to$ `feature/ui-shopping` $\to$ `feature/ui-discovery` $\to$ `feature/ui-product` $\to$ `feature/ui-outfit` $\to$ `feature/ui-geography` $\to$ `feature/ui-ai` $\to$ `feature/ui-profile` $\to$ `feature/ui-responsive` $\to$ `feature/ui-qa` $\to$ `release/visual-v1.0`.

---

### 0.23 — Phase Gate: Visual Design — 0 Sign-Off Checklist
* [x] Visual architecture defined and layered.
* [x] Screen/page layer separated from system layer.
* [x] Design-token architecture established.
* [x] Component hierarchy established (L1 Primitives through L4 Features).
* [x] Fashion content visual architecture established.
* [x] Shopping visual architecture established.
* [x] AI visual architecture established with explainability.
* [x] Geography/map visual architecture established with 3-layer stack.
* [x] Responsive architecture established (5 breakpoints: `xs` to `xl`).
* [x] Accessibility baseline established (WCAG 2.2 AAA).
* [x] State architecture established (12 canonical interaction states).
* [x] 17-point Screen Specification Contract codified in Pydantic v2 & TypeScript.
* [x] Visual development lifecycle established.
* [x] GitHub development model established.

```
Status: FashXStudio Visual Design Foundation
Architecture:       ████████████████████ 100%
Design Rules:       ████████████████████ 100%
Component Strategy: ████████████████████ 100%
Screen Contract:    ████████████████████ 100%
Implementation:     ░░░░░░░░░░░░░░░░░░░░   0% (Ready for Phase 01 / Phase 02)
```
