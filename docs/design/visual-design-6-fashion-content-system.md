# FashXStudio — Production Build Visual Design — 6
## Fashion Content Design System + Content Templates

**Subsystem:** Screens / Pages / Visual Design  
**Phase:** Visual Design — 6 (Fashion Content Design System + Content Templates)  
**Status:** **LOCKED & VERIFIED PRODUCTION BASELINE**  
**Date:** 2026-10-01  
**Verification Baseline:** 854 tests passed (100% green)

---

### 1. Phase Objective

Transform the generic UI component framework from Phase 05 into a fashion-native visual content system.

While Phase 05 established the reusable visual language (`Box`, `Stack`, `Grid`, `Card`, `Button`, `Badge`), Phase 06 infuses domain-specific visual meaning. It standardizes how FashXStudio visually structures and renders:
* Products
* Fashion Looks
* Outfits
* Collections
* Styles
* Trends
* Brands
* Fashion Stories & Editorials
* AI Recommendations
* Creators & Content Sources

**Core Principle (Section 6.1):**
$$\text{The UI component system provides the visual language; the Fashion Content System provides the visual meaning.}$$

---

### 2. Fashion Content Architecture (Section 6.1)

```
                    FASHXSTUDIO APP
                           │
                 Fashion Content Layer
                           │
       ┌───────────────────┼───────────────────┐
       │                   │                   │
    Commerce            Content           Intelligence
       │                   │                   │
   Product              Story            Recommendation
   Catalog              Editorial        AI Insight
   Availability         Collection       Personalization
       │                   │                   │
       └───────────────────┼───────────────────┘
                           │
                           ▼
                 Fashion Visual System
                           │
                           ▼
                  Screens / Templates
```

---

### 3. Content Object Model & Taxonomy (Sections 6.2 & 6.3)

The visual system defines and enforces contracts for 10 primary fashion objects:

| Object | Primary Purpose | Primary Visual Grammar | Key Metadata |
| :--- | :--- | :--- | :--- |
| **Product** | Commerce | 3:4 portrait product imagery | Brand, title, price, discount %, sizes, badges |
| **Look** | Styled inspiration | Full-body editorial composition | Style category, piece count, curator attribution |
| **Outfit** | Ensemble combo | Coordinated pieces breakdown | Constituent slots (outerwear, top, bottom, shoes) |
| **Collection** | Curated showcase | Wide landscape hero (16:9) | Season tag, item count, curated products |
| **Style** | Aesthetic categorization | Aesthetic mood image | Style name, look count, associated tags |
| **Trend** | Emerging market signal | High-contrast trend visual | Momentum badge, multi-stage timeline points |
| **Brand** | Merchant identity | Brand logo & storefront banner | Brand name, verified badge, product count |
| **Story** | Fashion editorial | Long-form hero & layout | Author, publication date, tagged looks/products |
| **Article** | Informational guidance | Editorial cover | Markdown content, reading time, category |
| **Recommendation**| Transparent AI suggestion| Focused item with explainability| Reason chip ("Why this appears"), confidence score |

---

### 4. Product System Specifications (Sections 6.4 - 6.7)

* **Media Aspect:** Standardized $3:4$ portrait aspect ratio.
* **Pricing Grammar:** Strict distinction between active price and strikethrough original price, plus automatic discount percentage computation.
* **Badges:** Semantically aligned badges (`BESTSELLER`, `ORGANIC`, `NEW_ARRIVAL`, `LIMITED_EDITION`).
* **Interactive Wishlist Toggle:** Instant optimistic wardrobe save interaction with accessible feedback.

---

### 5. Look System Specifications (Sections 6.8 - 6.10)

* **Visual Composition:** Portrays an entire styled outfit in context.
* **Item Tagging:** Links to each tagged product constituent within the look.
* **Curator Attribution:** Displays human stylist or editorial director attribution.
* **Look Metrics:** Displays total pieces included and community save counts.

---

### 6. Outfit System Specifications (Sections 6.11 & 6.12)

* **Slot Architecture:** Strict slot-based piece mapping (`outerwear`, `top`, `bottom`, `shoes`, `accessory`).
* **Bundle Pricing:** Dynamically aggregates individual piece prices into a coherent total ensemble price.
* **Slot Swapping:** Supports interchangeable pieces within the outfit canvas.

---

### 7. Collection System Specifications (Sections 6.13 & 6.14)

* **Hero Banner:** Immersive $16:9$ landscape media banner.
* **Seasonal Alignment:** Tagged with seasonal metadata (e.g., `Monsoon 2026`, `Festive 2026`).
* **Curated Products:** Displays preview thumbnails of constituent products with direct explore actions.

---

### 8. Style Category Specifications (Sections 6.15 & 6.16)

* **Aesthetic Identity:** Visual cards for styles like `Urban Relaxed`, `Contemporary Streetwear`, `Artisanal Handloom`.
* **Inventory Breadth:** Displays available look count within the style category.
* **Associated Tags:** Chip clusters representing sub-themes, materials, and silhouettes.

---

### 9. Trend System & Timeline Signals (Sections 6.17 - 6.19)

* **Momentum Classification:** Strict states (`emerging`, `peaking`, `stabilizing`, `cooling`).
* **Trajectory Timeline:** Multi-point trajectory array capturing signal evolution (Runway emergence $\rightarrow$ Street adoption $\rightarrow$ Retail proliferation) with intensity metrics ($0.0 \le i \le 1.0$).

---

### 10. Brand System Specifications (Sections 6.20 & 6.21)

* **Brand Authenticity:** Verified merchant indicator badge (`is_verified`).
* **Media Assets:** Dual asset representation featuring square brand mark logo and wide storefront cover.
* **Catalogue Reach:** Displays active product count and brand category specialization.

---

### 11. Editorial & Story System (Sections 6.22 - 6.24)

* **Narrative Depth:** Supports markdown-rendered editorial articles and trend dispatches.
* **Commerce Linking:** Bi-directional links connecting editorial prose directly to purchasable products and looks.
* **Editorial Bylines:** Full author credits and ISO publication dates.

---

### 12. Recommendation System & Transparent AI Explainability (Sections 6.31 & 6.32)

* **Transparent Explainability:** Enforces the inclusion of an `explanation_reason` chip answering "Why this appears" (e.g., *"Aligns with your explored interest in Japanese selvedge denim"*).
* **Confidence Bounds:** Strict Pydantic validation requiring $0.0 \le \text{confidence\_score} \le 1.0$.
* **Provenance:** Delineates `source_type` (`system_recommendation`, `ai_generated`, `collaborative_filter`).

---

### 13. Polymorphic Visual Content Model (`VisualContentModel`) (Sections 6.25 & 6.52)

A single polymorphic bridge contract that normalizes heterogeneous fashion content items for universal feed rendering:

```python
class VisualContentModel(BaseContractModel):
    id: str
    content_type: FashionContentType
    title: str
    subtitle: str | None
    media_uri: str
    category_label: str
    price: PriceSpecContract | None
    rating: RatingSpecContract | None
    labels: list[str]
    is_saved: bool
    state: ContentState
    source: ContentSourceType
    relationships: dict[str, list[str]]
```

---

### 14. Content State Machine & Lifecycle (Section 6.46)

Every content object implements a six-stage availability state machine:
* `LOADING`: Skeleton placeholder rendering.
* `LOADED`: Fully rendered content presentation.
* `EMPTY`: No items found matching query/category.
* `UNAVAILABLE`: Temporarily out of service or unlisted.
* `ERROR`: Network or retrieval failure with retry trigger.
* `PARTIAL`: Feed containing mixed loaded and degraded items.

---

### 15. Content Safety, Moderation & Inventory Availability (Sections 6.48 & 6.49)

* **Moderation Boundary:** Five safety tiers (`visible`, `restricted`, `unavailable`, `removed`, `pending`).
* **Inventory Real-Time Status:** Three commerce availability states (`in_stock`, `out_of_stock`, `preorder`).

---

### 16. Fashion Templates (Sections 6.35 - 6.40)

Five standardized screen templates organize fashion content into repeatable layouts:

1. **`DiscoveryTemplate` (Section 6.40):** Mixed-content discovery landing combining Hero Stories, Trending Radar, Curated Collections, AI Recommendations, and Featured Brands.
2. **`ListingTemplate` (Section 6.36):** High-density catalog grid with filter drawer triggers, sort controls, and pagination.
3. **`DetailTemplate` (Section 6.37):** Focused product/look examination with media gallery, breadcrumb trail, and contextual recommendations.
4. **`EditorialTemplate` (Section 6.38):** Long-form fashion story narrative with inline product callouts and related looks.
5. **`CollectionTemplate` (Section 6.39):** Curated showcase highlighting editorial seasonal themes with direct shoppable outfits.

---

### 17. Cross-Content Navigation & Relationships (Section 6.44)

The Fashion Content System maintains bi-directional relational graph edges:
* $\text{Story} \longleftrightarrow \text{Products} + \text{Looks}$
* $\text{Look} \longleftrightarrow \text{Products} + \text{Stylist}$
* $\text{Outfit} \longleftrightarrow \text{Product Slots}$
* $\text{Trend} \longleftrightarrow \text{Associated Products}$
* $\text{Collection} \longleftrightarrow \text{Featured Products}$

---

### 18. Save & Share Interactions (Sections 6.28 & 6.29)

Wardrobe save state interactions run through a deterministic state machine:
* Toggle requests execute via `POST /api/v1/visual/fashion/save-toggle`.
* Strict contracts return `SaveToggleResultContract` detailing updated state, optimistic feedback message, and synchronization status.

---

### 19. Verification & Test Metrics

Comprehensive test coverage across unit domain models, adapters, and FastAPI REST endpoints:

```powershell
pytest tests/unit/test_visual_fashion.py tests/integration/test_visual_fashion_router.py -v
============================= 32 passed in 1.72s ==============================

pytest -q
============================= 854 passed in 9.60s =============================
```

* **Unit Tests (FASH-001 through FASH-015):** 19 tests in `tests/unit/test_visual_fashion.py`
* **Integration Tests:** 13 tests in `tests/integration/test_visual_fashion_router.py`
* **Total Passing Tests:** 854 / 854 (100% green, 0 failures, 0 regressions across the entire FashXStudio suite).

---

### 20. Phase Completion Gate

```
==============================================================================
FASHXSTUDIO VISUAL DESIGN — PHASE 06: COMPLETION GATE
==============================================================================
[✓] 10 Fashion Content Domain Objects (Product, Look, Outfit, etc.)             LOCKED
[✓] Polymorphic VisualContentModel Adapter (Section 6.52)                      LOCKED
[✓] Content State Machine (Loading, Loaded, Empty, Unavailable, Error, Partial)LOCKED
[✓] Content Safety & Moderation States (Visible, Restricted, Removed, Pending) LOCKED
[✓] Transparent AI Recommendation Explainability ("Why this appears")          LOCKED
[✓] Trend Momentum & Multi-stage Signal Trajectory Timelines                   LOCKED
[✓] 5 Fashion Templates (Discovery, Listing, Detail, Editorial, Collection)     LOCKED
[✓] Mobile TypeScript Visual Content Components (Card ecosystem & templates)   LOCKED
[✓] FastAPI REST Endpoints (/visual/fashion/*)                                 LOCKED
[✓] Pydantic v2 BaseContractModel Schemas (extra="forbid" everywhere)          LOCKED
[✓] Automated Tests (32 new tests, 854 / 854 total passing)                    PASSED
==============================================================================
STATUS: READY FOR HANDOFF TO PHASE 07 (INTERACTION STATES & MICRO-EXPERIENCES)
==============================================================================
```
