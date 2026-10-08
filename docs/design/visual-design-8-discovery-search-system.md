# FashXStudio — Production Build Visual Design — 8
## Discovery + Search Screens + Exploration Experience Framework

**Subsystem:** Screens / Pages / Visual Design  
**Phase:** Visual Design — 8 (Discovery + Search Screens + Exploration Experience Framework)  
**Status:** **LOCKED & VERIFIED PRODUCTION BASELINE**  
**Date:** 2026-10-02  
**Verification Baseline:** 913 tests passed (100% green)

---

### 1. Phase Objective

Establish the production visual and interaction architecture connecting search, exploration, fashion discovery, catalog products, styled looks, curated collections, brand directories, aesthetic styles, trend radar signals, and explainable personalization into one cohesive experience.

Building on the foundation of VD-0 through VD-7:
$$\text{VD-0 (Master Baseline)} \longrightarrow \text{VD-1 (Screen Architecture)} \longrightarrow \text{VD-2 (Tokens)} \longrightarrow \text{VD-3 (App Shell)} \longrightarrow \text{VD-4 (Navigation)} \longrightarrow \text{VD-5 (Primitives/Components)} \longrightarrow \text{VD-6 (Fashion Content)} \longrightarrow \text{VD-7 (Shopping UI)} \longrightarrow \mathbf{VD\text{-}8\ (Discovery\ +\ Search)}$$

This phase delivers:
* Discovery Architecture & Multi-Taxonomy exploration rails.
* Complete screen inventory across Discovery (D01–D10) and Search (S01–S10).
* Unified multi-type search results engine navigating across Products, Looks, Brands, Styles, and Trends.
* Debounced autocomplete suggestions categorized by domain type.
* Recent search history with granular removal and clear-all capabilities.
* Structured advanced search query builder with interactive criteria and live result preview.
* Explainable personalization with transparent user style tags.
* Graceful zero-state handling with actionable query suggestions and category pivots.
* Cross-platform mobile TypeScript components and screen templates.

---

### 2. Discovery Architecture & Flow Diagram (Section 8.1)

FashXStudio Discovery is not merely a tabular search index. It operates as a layered exploration ecosystem:

```
                         DISCOVERY
                            │
            ┌───────────────┼────────────────┐
            │               │                │
         Explore          Search           Trends
            │               │                │
     ┌──────┼──────┐    ┌───┼────┐      ┌────┼────┐
     ▼      ▼      ▼    ▼   ▼    ▼      ▼    ▼    ▼
  Fashion Products Looks Query Filters Styles Trends
  Brands   Collections    │
                          ▼
                    Search Results
                          │
                          ▼
                 Product / Fashion /
                 Brand / Style / Trend
```

---

### 3. Discovery Principles (Section 8.2)

1. **Explore before committing:** Allow users to browse and uncover aesthetic themes without requiring an initial keyword query.
2. **Search must remain direct:** For directed intent ($\text{Query} \rightarrow \text{Results} \rightarrow \text{Product}$), interaction latency and visual friction are strictly minimized.
3. **Content types must remain distinguishable:**
   $$\text{Product} \neq \text{Look} \neq \text{Collection} \neq \text{Brand} \neq \text{Style} \neq \text{Trend}$$
   Visual cards, badges, metadata, and action affordances reflect distinct semantic roles.
4. **Preserve context during navigation:** When navigating $\text{Search} \rightarrow \text{Product Detail} \rightarrow \text{Back}$, active tab, scroll offset, and filter facets remain preserved.
5. **Personalization must remain explainable:** Curated or AI-recommended recommendations clearly communicate *why* they were surfaced.

---

### 4. Screen Inventory: D01-D10 & S01-S10 (Section 8.3)

#### Discovery Screens (D01 – D10)
| Screen ID | Screen Name | Template Contract | Primary Purpose |
| :--- | :--- | :--- | :--- |
| **D01** | Discovery Home | `DiscoveryHomeTemplateSpecContract` | Primary discovery gateway with Hero, chips, and modular rails |
| **D02** | Explore Fashion | `ExploreTemplateSpecContract` | Mixed editorial stories, styled looks, and handloom highlights |
| **D03** | Explore Products | `ExploreTemplateSpecContract` | Catalog-focused luxury product exploration grid |
| **D04** | Explore Looks | `ExploreTemplateSpecContract` | Complete fashion ensembles with shoppable constituent garments |
| **D05** | Explore Collections | `ExploreTemplateSpecContract` | Thematic seasonal capsules, capsule drops, and festival edits |
| **D06** | Explore Brands | `ExploreTemplateSpecContract` | Verified merchant directory and artisanal ateliers |
| **D07** | Explore Styles | `ExploreTemplateSpecContract` | Aesthetic style taxonomy (Streetwear, Minimalist, Handloom) |
| **D08** | Explore Trends | `ExploreTemplateSpecContract` | Data-driven trend radar tracking runway-to-street momentum |
| **D09** | Personalized Discovery | `PersonalizedDiscoveryTemplateSpecContract` | Tailored recommendations with user style tag explainability |
| **D10** | Discovery Results | `DiscoveryResultsTemplateSpecContract` | Mixed cross-entity discovery search results matrix |

#### Search Screens (S01 – S10)
| Screen ID | Screen Name | Template Contract | Primary Purpose |
| :--- | :--- | :--- | :--- |
| **S01** | Search Home | `SearchHomeTemplateSpecContract` | Search entry gateway with recent queries & trending keywords |
| **S02** | Search Suggestions | `list[SearchSuggestionContract]` | Real-time debounced autocomplete with type categorizations |
| **S03** | Product Search Results | `SearchResultsTemplateSpecContract` | Commerce product listing with pricing, badges, and filters |
| **S04** | Fashion / Look Results | `SearchResultsTemplateSpecContract` | Complete styled look results with outfit composition tags |
| **S05** | Brand Search Results | `SearchResultsTemplateSpecContract` | Brand cards with verification badges and product counts |
| **S06** | Style Search Results | `SearchResultsTemplateSpecContract` | Style aesthetic collections with visual mood imagery |
| **S07** | Trend Search Results | `SearchResultsTemplateSpecContract` | Trend signal cards with momentum velocity indicators |
| **S08** | Search Filters | `FilterStateContract` | Faceted drawer filters (sizes, brands, price range, color) |
| **S09** | Advanced Search | `AdvancedSearchTemplateSpecContract` | Structured multi-attribute query builder with live preview |
| **S10** | Search Empty State | `SearchResultsTemplateSpecContract` | Zero-result recovery screen with suggested alternative terms |

---

### 5. Discovery Home Experience: D01 (Sections 8.5 & 8.6)

`DiscoveryHomeTemplateSpecContract` orchestrates the top-level discovery surface:
* **Search Access Bar:** High-contrast search input acting as an immediate trigger to S01 / S02.
* **Discovery Hero Banner:** High-impact editorial hero (`Monsoon Transitional '26`) with primary CTA (`Explore Collection`) and secondary action (`View Lookbook`).
* **Exploration Chips:** Quick-pivot horizontal chip rail navigating into `Products`, `Looks`, `Collections`, `Styles`, `Brands`, and `Trends`.
* **Modular Content Feed:** Priority-sorted horizontal rails delivering `Featured Collections`, `Trending Products`, and `Curated Looks`.

---

### 6. Focused Exploration Screens: D02 – D08 (Sections 8.7 – 8.13)

Each `ExploreTemplateSpecContract` focuses on a distinct fashion taxonomy dimension:
* **D02 (Explore Fashion):** Blends editorial narratives, stories, and runway looks.
* **D03 (Explore Products):** High-density product listing showcasing luxury textiles and garments.
* **D04 (Explore Looks):** Styled outfits with clickable constituent garments (`Complete the Look`).
* **D05 (Explore Collections):** Editorial capsules organized by season, climate, and festival themes.
* **D06 (Explore Brands):** Verified merchant profiles featuring artisanal heritage and brand backstories.
* **D07 (Explore Styles):** Aesthetic taxonomy enabling navigation by visual identity (e.g. `Relaxed Tailoring`, `Boxy Streetwear`).
* **D08 (Explore Trends):** Trend momentum signals tracking adoption stages (`Runway emergence` $\rightarrow$ `Street adoption` $\rightarrow$ `Retail proliferation`).

---

### 7. Mixed Discovery Results: D10 (Section 8.14)

When exploration queries cross multiple domains, `DiscoveryResultsTemplateSpecContract` organizes results into partitioned sections:
* Top matching products (3:4 portrait cards with pricing)
* Matching styled looks (full-bleed ensemble cards)
* Designer brands & artisanal collectives
* Associated style tags and active trend signals

---

### 8. Search Home & Gateway Architecture: S01 (Sections 8.15 – 8.17)

The `SearchHomeTemplateSpecContract` screen provides an intentional entry point before typing:
* **Recent Searches:** Horizontally scrollable pill history with individual deletion and a "Clear All" action.
* **Trending Searches:** Popular keyword tags curated from real-time platform velocity (e.g. `Raw Denim`, `Camp Collar`, `Liquid Metallics`).
* **Curated Categories:** Instant entry chips routing directly to category search results.

---

### 9. Suggestions Engine, Autocomplete & Typo Resilience: S02 (Sections 8.18 – 8.20)

`SearchSuggestionContract` powers real-time autocomplete suggestions:
* **Categorized Types:** `query`, `product`, `brand`, `style`, `trend`, `category`.
* **Visual Distinction:** Distinct type badges allow users to differentiate between executing a broad query vs. jumping directly to a brand or product.
* **Empty Fallback:** When the input is blank, the engine surfaces platform trending suggestions.

---

### 10. Unified Search Results & Multi-Type Tabs: S03 – S07 (Sections 8.21 – 8.23)

Unified search evaluates user queries across all fashion entities simultaneously:
* **Multi-Type Tab Bar:** `All`, `Products`, `Looks`, `Brands`, `Styles`, `Trends`.
* **Count Indicators:** Badges communicate entity density (e.g. `Products (14)`, `Looks (4)`, `Brands (2)`).
* **Dynamic Screen ID Resolution:** Selecting a tab updates the screen ID dynamically (`S03` for Products, `S04` for Looks, `S05` for Brands, `S06` for Styles, `S07` for Trends).

---

### 11. Search Filtering & Facet Drawers: S08 (Section 8.24)

Integrates the faceted filtering architecture established in Phase 07:
* Multi-select facets: Category, Brand, Price Range, Size, Color, Stock Availability.
* Active filter pills with individual dismissal and one-tap "Clear All".
* Instant result count recomputation on facet mutation.

---

### 12. Advanced Structured Search: S09 (Section 8.25)

`AdvancedSearchTemplateSpecContract` provides a dedicated query builder for precision shopping:
* Structured fields: `keywords`, `category`, `brand`, `style`, `price_min`, `price_max`, `color`, `size`, `region`.
* Live preview grid: Dynamically displays matching items and matching count without leaving the builder.
* Direct handoff into unified results on execution.

---

### 13. Zero-State & Empty Search Handling: S10 (Sections 8.26 – 8.30)

When a query yields 0 results, the system activates `S10_SEARCH_EMPTY_STATE`:
* Clear explanation indicating no exact matches were found.
* Actionable alternative keyword suggestions (e.g. `Try 'denim'`, `Try 'linen'`).
* One-click "Reset Search" to return to S01 Search Home.

---

### 14. Explainable Personalization: D09 (Sections 8.31 – 8.33)

`PersonalizedDiscoveryTemplateSpecContract` ensures user trust by providing explainable AI suggestions:
* **User Style Tags:** Visual chip row displaying active user aesthetic preferences (`Contemporary Streetwear`, `Relaxed Boxy Fit`, `Natural Flax Linen`).
* **Explicit Explanations:** Explanations paired with recommendations (e.g. *"Recommended because you explored Japanese selvedge denim in Monsoon capsule"*).

---

### 15. Modular Content Blocks & Discovery Rails (Sections 8.34 – 8.39)

Discovery screens are constructed using modular blocks:
* `DiscoveryRail`: Horizontal scrolling carousel with title, subtitle, "View All" action, and typed card items.
* `DiscoveryGrid`: Responsive 2-to-4 column grid balancing visual density across mobile, tablet, and desktop viewports.
* Priority-based ordering ensuring sponsored, trending, or high-affinity modules appear above the fold.

---

### 16. Content Type Differentiation System

To prevent visual conflation between disparate fashion entities, cards enforce distinct presentation rules:

| Content Type | Primary Image Ratio | Metadata Displayed | Primary Action |
| :--- | :--- | :--- | :--- |
| **Product** | 3:4 Portrait | Brand, Title, Price, Discount, Stock Badge | View Product / Quick Add |
| **Look** | 16:9 / Full Ensembles | Look Title, Scene Location, Garment Piece Count | View Styled Look |
| **Collection** | 16:9 Banner | Collection Name, Season Tag, Story Teaser | Explore Collection |
| **Brand** | Square Logo / Banner | Brand Name, Origin, Verified Badge, Catalog Size | View Brand Profile |
| **Style** | 1:1 Aesthetic Mood | Style Name, Aesthetic Description | Browse Style Edit |
| **Trend** | Data Chart / Signal | Trend Name, Signal Intensity, Momentum Tag | Inspect Trend Radar |

---

### 17. State Machine, Async Debounce & Navigation Transitions (Sections 8.49 – 8.56)

* **Debounce Architecture:** 250ms debouncing on search input preventing excessive backend load while maintaining perceived real-time responsiveness.
* **Unified Lifecycle States:** `loading`, `ready`, `empty`, `partial`, `error`, `unavailable`.
* **State Preservation:** Search query, scroll positions, and selected result tab persist when returning from downstream detail screens.

---

### 18. Mobile TypeScript Component & Template Architecture

Located under `mobile/features/visual/discovery/`:

```
mobile/features/visual/discovery/
├── types.ts                     # Type definitions mirroring Pydantic v2 schemas
├── DiscoveryHero.tsx            # Full-bleed editorial hero banner with actions
├── DiscoveryRail.tsx            # Horizontal scrolling content rail
├── SearchInputBar.tsx           # Search bar with debouncing, clear, and loading states
├── SearchSuggestionsList.tsx    # Categorized autocomplete list with type badges
├── RecentSearchesList.tsx       # Search history pill list with deletion controls
├── SearchResultTabs.tsx         # Multi-type tab bar (All, Products, Looks, etc.) with counts
├── templates/
│   ├── DiscoveryHomeTemplate.tsx   # D01: Discovery Home assembly
│   ├── SearchHomeTemplate.tsx      # S01: Search Home entry gateway
│   ├── SearchResultsTemplate.tsx   # S03-S07, S10: Unified results grid with tabs
│   └── AdvancedSearchTemplate.tsx  # S09: Multi-attribute query builder
└── index.ts                     # Public API barrel export
```

---

### 19. Verification & Automated Test Metrics

```powershell
pytest tests/unit/test_visual_discovery.py tests/integration/test_visual_discovery_router.py -v
============================= 26 passed in 2.20s ==============================

pytest -q
============================ 913 passed in 10.45s =============================
```

* **Unit Tests (DISC-001 through DISC-010, SEARCH-001 through SEARCH-015):** 16 tests in `tests/unit/test_visual_discovery.py`
* **Integration Tests (REST Endpoints & User Navigation Flows):** 10 tests in `tests/integration/test_visual_discovery_router.py`
* **Total Passing Tests:** 913 / 913 (100% green, 0 failures, 0 regressions across the entire FashXStudio suite).

---

### 20. Phase Completion Gate & Sign-Off Matrix

```
==============================================================================
FASHXSTUDIO VISUAL DESIGN — PHASE 08: COMPLETION GATE
==============================================================================
[✓] D01 - D10 Discovery Screen Contracts & Templates                          LOCKED
[✓] S01 - S10 Search Screen Contracts & Templates                             LOCKED
[✓] Unified Multi-Type Search Engine (Products, Looks, Brands, Styles, Trends) LOCKED
[✓] Categorized Autocomplete Suggestions Engine with Type Badges              LOCKED
[✓] Recent Search History State with Individual & Batch Removal                LOCKED
[✓] Structured Advanced Search Query Builder with Live Preview                LOCKED
[✓] Explainable Personalization with User Style Tags & Reasons                LOCKED
[✓] Zero-State & Empty Search Handling with Actionable Query Recovery         LOCKED
[✓] Mobile TypeScript UI Components, Rails, and Templates                     LOCKED
[✓] FastAPI REST Endpoints (/visual/discovery/*)                              LOCKED
[✓] Pydantic v2 BaseContractModel Schemas (extra="forbid" everywhere)         LOCKED
[✓] Automated Tests (26 new tests, 913 / 913 total passing)                   PASSED
==============================================================================
STATUS: READY FOR HANDOFF TO PHASE 09 (PROFILE, WARDROBE & SOCIAL DISCOVERY)
==============================================================================
```
