# FashXStudio — Production Build Visual Design — 14
## Responsive / Adaptive Visual System Reference Manual

**Subsystem:** Screens / Pages / Visual Design  
**Phase:** Visual Design — 14 (Responsive / Adaptive Visual System)  
**Status:** **LOCKED & VERIFIED PRODUCTION BASELINE**  
**Date:** 2026-10-02  
**Verification Baseline:** 1197 tests passed (100% green)

---

### 1. Phase Objective & Core Operational Principle

Establish a production-grade responsive visual framework that ensures the entire FashXStudio platform adapts predictably and seamlessly across mobile, tablet, laptop, desktop, large desktop, touch, keyboard, mouse, portrait, landscape, and constrained viewports.

This phase is not simply a set of CSS media queries; it defines how FashXStudio adjusts:
* **Layout Structure:** Multi-column grids, split panels, stacked vertical flows.
* **Content Density:** Compact, comfortable, and spacious density modes.
* **Navigation Architecture:** Full desktop sidebar $\to$ compact tablet sidebar $\to$ mobile header + bottom navigation + navigation drawer.
* **Typography & Spacing:** Fluid semantic scale tokens and bounded line lengths.
* **Component Metadata Priority:** P0 $\to$ P1 $\to$ P2 $\to$ P3 progressive disclosure.
* **Interaction Paradigms:** Touch targets ($\ge 44\text{px}$), hover alternatives, keyboard focus traps, and modal/sheet transformations.
* **Accessibility & Safety:** Safe-area insets, zoom up to 200%, text scaling, and `prefers-reduced-motion`.

#### The Core Operational Principle:
$$\mathbf{Components\ respond\ to\ available\ space\ and\ content\ needs,\ not\ merely\ device\ names.}$$

#### The Responsive Decision Model:
$$\begin{aligned}
&\text{Available Width} + \text{Content Requirements} + \text{Interaction Mode} + \text{Accessibility Constraints} \\
&\quad\implies \mathbf{Responsive\ Decision} \implies \mathbf{Layout\ Variant}
\end{aligned}$$

#### The Final Architectural Paradigm:
```
                 ONE FASHXSTUDIO
                       │
                ONE DESIGN SYSTEM
                       │
                ONE COMPONENT MODEL
                       │
              RESPONSIVE ADAPTATION
                       │
       ┌───────────────┼───────────────┐
       ▼               ▼               ▼
    Compact         Adaptive        Expanded
       │               │               │
     Mobile          Tablet          Desktop
```

---

### 2. Responsive Architecture & 14-Layer Hierarchy (Sections 14.1 & 14.2)

```
                    FASHXSTUDIO
                         │
                 RESPONSIVE ENGINE
                         │
       ┌─────────────────┼─────────────────┐
       ▼                 ▼                 ▼
   VIEWPORT           CONTENT            INPUT
   SIZE               PRIORITY           MODE
       │                 │                 │
       ▼                 ▼                 ▼
   Breakpoints        Adaptation       Touch/Mouse
   Containers         Density          Keyboard
   Grid               Visibility       Pointer
       │                 │                 │
       └─────────────────┼─────────────────┘
                         ▼
                  ADAPTIVE COMPONENTS
                         │
                         ▼
                      SCREENS
```

#### The 14 Integrated Responsive Layers:
1. **Viewport:** Viewport dimension sensing and orientation detection.
2. **Breakpoints:** Layout thresholds (XS, SM, MD, LG, XL, 2XL).
3. **Containers:** Bounded widths, horizontal padding, and ultra-wide centering.
4. **Grid:** Fluid column calculation driven by item minimum widths and gutters.
5. **Spacing:** Semantic spacing tokens scaling from mobile to desktop.
6. **Typography:** Fluid typographic scales with natural line wrapping.
7. **Media:** Aspect-ratio-stable images, lazy loading, and object-fit rules.
8. **Navigation:** Viewport-governed navigation transformations (Sidebar, Bottom Nav, Drawer).
9. **Components:** Component priority pruning (P0-P3 metadata models).
10. **Templates:** 11 core page templates re-flowing content based on available space.
11. **Screen Composition:** Specialized studio canvases (Outfit Builder, Maps, Assistant).
12. **Interaction:** Touch targets ($\ge 44\text{px}$), hover decoupling, keyboard focus loops.
13. **Accessibility:** Zoom tolerance (up to 200%), reduced motion, and DOM order integrity.
14. **Performance:** Responsive image candidates, lazy map rendering, and deferred AI streams.

---

### 3. Breakpoint Baseline & Layout Thresholds (Section 14.3)

Layout thresholds represent spatial capacity breakpoints rather than device brand classifications:

| Token | Threshold | Visual Classification | Base Columns | Gutter | Page Padding |
| :--- | :--- | :--- | :---: | :---: | :---: |
| **`xs`** | $< 480\text{px}$ | Compact Mobile | 4 | $12\text{px}$ | $16\text{px}$ |
| **`sm`** | $\ge 480\text{px}$ | Large Mobile / Phablet | 4 | $16\text{px}$ | $16\text{px}$ |
| **`md`** | $\ge 768\text{px}$ | Tablet Portrait | 8 | $20\text{px}$ | $24\text{px}$ |
| **`lg`** | $\ge 1024\text{px}$ | Tablet Landscape / Laptop | 12 | $24\text{px}$ | $24\text{px}$ |
| **`xl`** | $\ge 1280\text{px}$ | Desktop | 12 | $24\text{px}$ | $32\text{px}$ |
| **`2xl`** | $\ge 1536\text{px}$ | Large Desktop / Ultra-Wide | 12 | $32\text{px}$ | $32\text{px}$ |

---

### 4. Container System, Margins & Page Padding (Sections 14.5 – 14.7)

```
Viewport
┌────────────────────────────────────────────┐
│                                            │
│       ┌────────────────────────────┐       │
│       │       CONTENT CONTAINER    │       │
│       │                            │       │
│       └────────────────────────────┘       │
│                                            │
└────────────────────────────────────────────┘
```

* **Mobile ($<768\text{px}$):** $100\%$ width minus $16\text{px}$ page padding.
* **Tablet ($768\text{px}-1023\text{px}$):** Fluid width with $24\text{px}$ page padding and max container width of $960\text{px}$.
* **Desktop ($1024\text{px}-1535\text{px}$):** Fluid container bounded up to $1440\text{px}$ max width.
* **Large Desktop / Ultra-Wide ($\ge 1536\text{px}$):** Centered max-width of $1600\text{px}$ with $32\text{px}$ page padding. Prevents excessive whitespace and unreadable line lengths.

---

### 5. Dynamic Fluid Grid Calculation Engine (Sections 14.8 – 14.10)

FashXStudio replaces static, breakpoint-heavy media query grids with a continuous mathematical calculation:

$$\text{computed\_columns} = \max\left(1, \min\left(\text{max\_columns},\, \left\lfloor\frac{\text{available\_width} + \text{gap}}{\text{card\_min\_width} + \text{gap}}\right\rfloor\right)\right)$$

$$\text{card\_width} = \frac{\text{available\_width} - ((\text{computed\_columns} - 1) \times \text{gap})}{\text{computed\_columns}}$$

This produces optimal layouts automatically:
* **$1200\text{px}$ Container:** 4 columns ($288\text{px}$ each at $16\text{px}$ gap).
* **$820\text{px}$ Container:** 3 columns ($252\text{px}$ each at $16\text{px}$ gap).
* **$360\text{px}$ Container:** 1 column ($360\text{px}$ full width).
* **Narrow constraint ($< \text{min\_width}$):** Clamped safely to 1 column without clipping.

---

### 6. Fashion Editorial & Detail Page Adaptation (Sections 14.11 & 14.12)

#### Editorial Stories (VD-06):
* **Desktop:** Hero image above a side-by-side 2-column layout (Editorial Story narrative on left, Supporting Products & Looks on right).
* **Mobile:** Linear single-column flow: Hero Image $\to$ Story Narrative $\to$ Supporting Items rail.

#### Product Detail Canvas (VD-09):
* **Desktop (`P02`):** Split layout ($55\%$ Image Gallery with zoom capability on left, $45\%$ Product Information, Variant Selectors, and Sticky Buy Box on right).
* **Mobile (`P02`):** Stacked vertical layout: Swipeable Image Gallery $\to$ Product Specifications $\to$ Variant Chips $\to$ Sticky Bottom Purchase Area.

---

### 7. Safe Areas, Notches & Sticky Actions (Sections 14.13 & 14.14)

Mobile experiences must accommodate hardware cutouts, home gesture indicators, and system navigation:
* **Safe-Area Inset Handling:**
  $$\text{ContainerPaddingBottom} = \max(16\text{px},\, \text{safe\_area\_insets.bottom\_px})$$
* **Sticky Purchase Area (`ResponsiveStickyAction`):** Pins the primary commercial action (Price + `Add to Bag`) to the bottom of the screen on mobile without obscuring validation notices or content.
* **Desktop Suppression:** Automatically transitions to an inline button on expanded desktop viewports where sticky bottom bars would be intrusive.

---

### 8. Navigation Adaptation Architecture (Sections 14.15 – 14.18)

| Viewport | Primary Navigation | Header Composition | Secondary Navigation |
| :--- | :--- | :--- | :--- |
| **Desktop** | Fixed Left Sidebar | `Logo \| Global Search \| Nav Links \| Alerts \| Profile` | Top Menu Drops |
| **Tablet** | Compact Icon Sidebar | `Logo \| Global Search \| Alerts \| Profile` | Right Drawer |
| **Mobile** | Fixed 5-Item Bottom Bar | `Menu (Drawer) \| Logo \| Search Trigger \| Profile` | Navigation Drawer (Focus Trapped) |

#### Mobile Navigation Drawer (Section 14.18):
* Full-height slide-out drawer accessible via hamburger menu.
* Contains complete platform hierarchy (Home, Discover, Fashion, Shopping, Style, Trends, Maps, AI, Saved, Wishlist, Profile).
* Enforces strict accessibility: focus trap within drawer, escape key dismissal, visible close button, and backdrop tap dismissal.

---

### 9. Typography & Fluid Spacing Adaptation (Sections 14.19 – 14.22)

Typography scales exclusively through semantic tokens rather than arbitrary pixel sizes:
* **`display_xl`:** $48\text{px}$ on Desktop $\to$ $36\text{px}$ on Mobile.
* **`display_l`:** $36\text{px}$ on Desktop $\to$ $28\text{px}$ on Mobile.
* **`heading_xl`:** $30\text{px}$ on Desktop $\to$ $24\text{px}$ on Mobile.
* **Natural Flow Rule (Section 14.20):** Headings never use fixed container heights (`height: 40px`), allowing natural multi-line wrapping for localized and long titles.
* **Reading Length Control (Section 14.21):** Body text containers on desktop are bounded to a maximum reading width of $680\text{px}$ (60–75 characters per line).

---

### 10. Image Responsiveness & Aspect Ratio Stability (Sections 14.23 – 14.26)

* **Aspect Ratio Reservation:** Containers enforce fixed ratios (`3:4` Product, `2:3` Editorial, `16:9` Lifestyle, `1:1` Square) prior to image download, eliminating Cumulative Layout Shift (CLS).
* **Object-Fit Taxonomy:**
  * `product` $\implies$ `contain` (garment silhouette must not be cropped).
  * `lifestyle` $\implies$ `cover` (ambient imagery fills viewport).
  * `editorial` $\implies$ `cover` (curated magazine photography).
  * `detail` $\implies$ `contain + zoom` (fabric weave and stitching inspection).

---

### 11. Card Adaptation & Content Priority Framework P0–P3 (Sections 14.27 & 14.28)

Every fashion card implements deterministic metadata pruning based on available spatial capacity:

```
┌──────────────────────────────────────────────────────────┐
│ P0: Image, Title, Primary CTA (Always Rendered)          │
├──────────────────────────────────────────────────────────┤
│ P1: Brand, Price, Availability Status (All Viewports)    │
├──────────────────────────────────────────────────────────┤
│ P2: Secondary Specs (Material, Fit) [Tablet & Desktop]   │
├──────────────────────────────────────────────────────────┤
│ P3: Style Tags, Extended Badges [Desktop Only]           │
└──────────────────────────────────────────────────────────┘
```

* **Compact Mobile:** Renders P0 + P1. P2 and P3 are pruned to maintain clean scanning.
* **Adaptive Tablet:** Renders P0 + P1 + P2.
* **Expanded Desktop:** Renders all metadata P0 + P1 + P2 + P3.
* **Touch Target Baseline:** Minimum $44\text{px}$ height on all action triggers across all viewports.

---

### 12. Search, Filters & Bottom Sheet Drawers (Sections 14.29 – 14.32)

* **Desktop:** Faceted filter sidebar alongside results grid with live badge counters.
* **Tablet:** Filter button opening an off-canvas drawer with apply/reset actions.
* **Mobile:** Filter & Sort pills opening accessible Bottom Sheets (`ResponsiveSheet`). The background is locked, and dismiss triggers include backdrop tap, swipe-down handle, close icon, or system back gesture.

---

### 13. Discovery Layout & Horizontal Content Rails (Sections 14.33 & 14.34)

* **Horizontal Rails (`ResponsiveRail`):** Used for Recommended Looks, Trending Silhouettes, and Recently Viewed items.
* **Continuation Cue:** The trailing card on mobile is partially cut off at the edge of the viewport ($85\%$ width visibility), providing a visual affordance for horizontal scrolling.
* **Accessibility Guarantee:** Supports keyboard arrow navigation and touch fling snapping without causing an inaccessible horizontal trap.

---

### 14. Outfit Builder 3-Way Responsive Architecture (Sections 14.35 & 14.36)

```
Desktop (3-Column):
┌──────────────┬────────────────────────┬──────────────┐
│ Item Browser │ Outfit Studio Canvas   │ Inspector    │
└──────────────┴────────────────────────┴──────────────┘

Tablet (2-Column):
┌──────────────┬────────────────────────┐
│ Item Browser │ Outfit Studio Canvas   │
├──────────────┴────────────────────────┤
│ Bottom Inspector & Compatibility Rail  │
└────────────────────────────────────────┘

Mobile (Canvas Primary):
┌───────────────────────────────────────┐
│ Canvas (Active Layered Outfit)        │
├───────────────────────────────────────┤
│ Bottom Sheet Drawer (Candidate Items) │
├───────────────────────────────────────┤
│ Sticky Bottom Actions (Save / Shop)   │
└───────────────────────────────────────┘
```

The canvas remains the primary focus across all viewports, ensuring composition tasks are never compromised.

---

### 15. AI & Conversational Experience Adaptation (Sections 14.37 – 14.39)

* **Desktop:** 2-column layout (Context chips, style taxonomy, and suggestions on left; multi-turn conversation and recommendation cards on right).
* **Mobile:** Sequential vertical conversation stream with sticky bottom prompt composer.
* **Scanning Comfort:** AI messages are bounded to a maximum width of $680\text{px}$ on desktop, preventing wide-line reading fatigue.
* **Fact Separation:** Factual catalog cards and subjective AI guidance maintain distinct visual containers across all viewport sizes.

---

### 16. Regional Maps Responsive Architecture (Sections 14.40 – 14.42)

* **Desktop:** Side-by-side layout (Left sidebar with region search, cultural movements, and results list; Right panel with interactive vector map).
* **Mobile:** Full-bleed interactive map with floating filter chips and an expandable bottom sheet listing regional fashion locations.

---

### 17. Shopping Checkout, Forms & Data Tables (Sections 14.44 – 14.47, 14.60)

* **Checkout:**
  * **Desktop:** 2-column layout (Checkout form steps on left, sticky Order Summary on right).
  * **Mobile:** Sequential accordion flow (Contact $\to$ Delivery $\to$ Payment $\to$ Review) with sticky total summary bar.
* **Forms:** Desktop 2-column input grid collapses into a clean single-column vertical stack on mobile with full-width submit controls.
* **Comparison Tables:** Desktop multi-column grid adapts on mobile by stacking attributes vertically or providing horizontal column scrolling with locked product headers.

---

### 18. Interaction, Pointer & Accessibility Adaptation (Sections 14.48 – 14.52, 14.75 – 14.78)

* **Touch Targets:** All interactive controls maintain $\ge 44\text{px} \times 44\text{px}$ touch targets.
* **Hover Decoupling:** Desktop hover previews (e.g. secondary garment angles) have explicit tap equivalents on touch devices.
* **Keyboard Navigation:** Tab, Shift+Tab, Enter, Space, and Escape work across all responsive variants. Focus is preserved when switching views.
* **Zoom Support:** Interfaces tolerate up to $200\%$ browser zoom without text clipping or overlapping containers.
* **Reduced Motion:** When `prefers-reduced-motion` is active, layout transitions and carousel animations are instant or minimized.

---

### 19. Mobile TypeScript Architecture & Layout Utilities

Located under `mobile/features/visual/responsive/`:

```
mobile/features/visual/responsive/
├── types.ts                                   # Complete TypeScript interfaces mirroring Pydantic v2
├── hooks/
│   └── useResponsive.ts                       # Semantic responsive query hook (isCompact, isAdaptive, etc.)
├── components/
│   ├── ResponsiveContainer.tsx                # Max-width bounded content container with page padding
│   ├── ResponsiveGrid.tsx                     # Dynamic fluid grid calculating columns from min width
│   ├── ResponsiveStack.tsx                    # Linear stack switching between row and column
│   ├── ResponsiveSplit.tsx                    # 2-column desktop split collapsing to mobile stack
│   ├── ResponsiveVisibility.tsx               # Semantic conditional rendering wrapper
│   ├── ResponsiveRail.tsx                     # Horizontal content carousel with continuation cues
│   ├── ResponsiveSheet.tsx                    # Adaptive bottom sheet (mobile) / modal (desktop)
│   ├── ResponsiveStickyAction.tsx             # Safe-area aware fixed bottom action bar
│   └── ResponsiveCard.tsx                     # P0-P3 metadata adaptive product/look card
└── index.ts                                  # Public module barrel export
```

---

### 20. Verification, Automated Test Metrics & Completion Gate

```powershell
pytest tests/unit/test_visual_responsive.py tests/integration/test_visual_responsive_router.py -v
============================= 39 passed in 2.06s ==============================

pytest -q
=========================== 1197 passed in 12.65s ============================
```

* **Unit Tests (`tests/unit/test_visual_responsive.py` — 24 tests):**
  * `RESP-001`: Breakpoint resolution across layout thresholds (XS, SM, MD, LG, XL, 2XL) and 3-way layout mode resolution.
  * `RESP-002`: Container sizing, padding, and bounded widths.
  * `RESP-003`: Dynamic fluid grid column calculations and boundary conditions.
  * `RESP-004`: Typography adaptation semantic token mappings.
  * `RESP-005`: Spacing adaptation and padding resolution.
  * `RESP-006` & `RESP-008`: Card adaptation and P0–P3 content priority pruning.
  * `RESP-007`: Navigation adaptation (Sidebar vs Compact Sidebar vs BottomNav/Drawer).
  * `RESP-009` & `RESP-010`: Filter and modal bottom sheet transformations.
  * `RESP-011`: Specialized canvas layouts (Outfit Builder, Map, Checkout).
  * `RESP-012`: Safe area boundaries and sticky action preservation.
  * `RESP-013`: Extreme viewports (320px small mobile, 2560px ultra-wide containment).
  * `RESP-014`: Orientation handling (Portrait vs Landscape).
  * `FORBID-001` to `FORBID-008`: Strict `extra="forbid"` rejection across all Responsive contracts (Rule I02).
* **Integration Tests (`tests/integration/test_visual_responsive_router.py` — 15 tests):**
  * All 6 REST endpoints under `/api/v1/visual/responsive/*`.
  * 6 Cross-System Integration Flows:
    1. Flow 1: Responsive Grid $\to$ Shopping Product Listing (`VD-07` P01).
    2. Flow 2: Responsive Split $\to$ Product Detail Canvas (`VD-09` P02).
    3. Flow 3: Responsive Outfit Builder $\to$ Styling Studio (`VD-10` ST02).
    4. Flow 4: Responsive Regional Map $\to$ Geography Visuals (`VD-11` M02).
    5. Flow 5: Responsive AI Assistant $\to$ Intelligence Composer (`VD-12` AI02).
    6. Flow 6: Responsive Preferences $\to$ Personal Settings (`VD-13` PR08).
* **Total Project Tests:** **1197 passed (100% green, 0 failures, 0 regressions)**.

```
==============================================================================
FASHXSTUDIO VISUAL DESIGN — PHASE 14: COMPLETION GATE
==============================================================================
[✓] Breakpoint Baseline & Layout Thresholds (XS, SM, MD, LG, XL, 2XL)         LOCKED
[✓] Core Decision Model: Space + Content + Input -> Responsive Decision      LOCKED
[✓] Bounded Container System with Ultra-Wide Centering & Page Padding         LOCKED
[✓] Mathematical Fluid Grid Calculation (Card Min Width + Gap)                LOCKED
[✓] Content Priority Framework (P0, P1, P2, P3 Metadata Pruning)              LOCKED
[✓] Safe Area Insets & Mobile Sticky Bottom Action Bar                        LOCKED
[✓] Navigation Transformation (Sidebar, Compact Sidebar, Bottom Nav + Drawer) LOCKED
[✓] Fluid Typography Scaling Tokens with Natural Content Flow                 LOCKED
[✓] Aspect-Ratio-Stable Responsive Media & Image Loading Strategy             LOCKED
[✓] Specialized Canvas Adaptation (Outfit Builder, Regional Map, AI Studio)   LOCKED
[✓] Modal & Filter Transformation (Bottom Sheets vs Centered Modals)          LOCKED
[✓] Touch Target Baseline (>= 44px) & Hover vs Tap Decoupling                 LOCKED
[✓] Orientation & Extreme Viewport Handling (320px mobile to 2560px ultra-wide) LOCKED
[✓] Mobile TypeScript Utilities & useResponsive Hook (React Native / Expo)    LOCKED
[✓] FastAPI REST Endpoints (/visual/responsive/*)                             LOCKED
[✓] Pydantic v2 BaseContractModel Schemas (extra="forbid" everywhere)         LOCKED
[✓] Automated Tests (39 new tests, 1197 / 1197 total passing)                PASSED
==============================================================================
STATUS: PHASE 14 (RESPONSIVE / ADAPTIVE VISUAL SYSTEM) COMPLETED & VERIFIED
==============================================================================
```
