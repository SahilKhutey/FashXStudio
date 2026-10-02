# FashXStudio — Production Build Visual Design — 9
## Product & Fashion Detail Screens Experience Framework

**Subsystem:** Screens / Pages / Visual Design  
**Phase:** Visual Design — 9 (Product & Fashion Detail Screens)  
**Status:** **LOCKED & VERIFIED PRODUCTION BASELINE**  
**Date:** 2026-10-02  
**Verification Baseline:** 936 tests passed (100% green)

---

### 1. Phase Objective

Establish the production visual and interaction framework for the pivotal inflection point where a user transitions from broad discovery and search into deep content understanding and authoritative action.

Connecting the complete upstream and downstream systems:
$$\text{Discovery / Search} \longrightarrow \mathbf{Product\ /\ Fashion\ Detail} \longrightarrow \begin{cases} \text{Commerce (Shop / Buy / Add to Cart)} \\ \text{Styling (Outfit Builder / Complete the Look)} \\ \text{Related Products (Similar / Recommended)} \\ \text{Content Exploration (Stories / Brands / Collections)} \end{cases}$$

This phase builds directly upon:
* **VD-6 Fashion Content:** Entity visual semantics (Product, Look, Collection, Brand, Story, Editorial).
* **VD-7 Shopping UI:** Commerce transactional guarantees, availability, cart mutations, and checkout handoff.
* **VD-8 Discovery + Search:** Preserving search queries, active filter facets, and tab states across back-navigation loops.

---

### 2. Detail Experience Architecture & Flow Diagram (Section 9.1)

```
                         DETAIL EXPERIENCE
                                │
                ┌───────────────┴───────────────┐
                │                               │
             PRODUCT                          FASHION
                │                               │
       ┌────────┼────────┐             ┌────────┼────────┐
       ▼        ▼        ▼             ▼        ▼        ▼
     Media    Info    Commerce       Story     Look   Collection
       │        │        │             │        │        │
       └────────┼────────┘             └────────┼────────┘
                ▼                               ▼
             Actions                         Related
                │                               │
                └───────────────┬───────────────┘
                                ▼
                       Styling / Shopping
```

---

### 3. Detail Experience Principles (Section 9.3)

1. **Content First:** The primary garment or editorial asset dominates the visual hierarchy above all chrome.
2. **Action Clarity:** Users immediately discern *What is this?*, *Why is it relevant?*, and *What can I do next?*
3. **Progressive Disclosure:** Essential summary and purchase controls sit immediately accessible; exhaustive technical specifications, care guides, and review archives are disclosed on demand.
4. **Preserve Context:** Navigating $\text{Search} \rightarrow \text{Product} \rightarrow \text{Back}$ maintains exact result position, query, and filters.
5. **Separate Facts from Interpretation:**
   $$\text{Objective Product Facts} \longrightarrow \text{Editorial Context} \longrightarrow \text{System Recommendation} \longrightarrow \text{AI Explanation}$$
   Subjective stylist advice or algorithmic recommendations are never presented as immutable physical facts.

---

### 4. Detail Screen Inventory: P01–P10 & F01–F09 (Section 9.2)

#### Product Detail Screens (P01 – P10)
| Screen ID | Screen Name | Template Contract | Primary Purpose |
| :--- | :--- | :--- | :--- |
| **P01** | Product Listing | *Reused from VD-7/VD-8* | Catalog grid & search results gateway |
| **P02** | Product Detail | `ComprehensiveProductDetailTemplateSpecContract` | Primary product canvas with media, facts, variants, specs & actions |
| **P03** | Product Image Gallery | `ProductGalleryContract` | Fullscreen modal zoom, pan, and multi-angle inspection |
| **P04** | Product Variant Selection | `VariantGroupContract` | Size pills, color swatches with dependency constraints |
| **P05** | Product Reviews | `ProductReviewsTemplateSpecContract` | Rating summary, star distribution histogram, and verified buyer reviews |
| **P06** | Product Specifications | `SpecificationSectionContract` | Grouped technical specifications (fabric, weave, fit, origin, care) |
| **P07** | Similar Products | `RelatedProductItemContract` | Visually and aesthetically related garment suggestions |
| **P08** | Recommended Products | `RelatedProductItemContract` | Personalized suggestions with transparent explainability tags |
| **P09** | Product Comparison | `ProductComparisonTemplateSpecContract` | Data-driven side-by-side attribute comparison matrix |
| **P10** | Product Availability | `ProductAvailabilityTemplateSpecContract` | Real-time stock units, logistics fulfillment, and delivery estimates |

#### Fashion Detail Screens (F01 – F09)
| Screen ID | Screen Name | Template Contract | Primary Purpose |
| :--- | :--- | :--- | :--- |
| **F01** | Fashion Home | *Reused from VD-6/VD-8* | Curated editorial & discovery feed entry |
| **F02** | Fashion Feed | *Reused from VD-6* | Endless chronological stream of looks & stories |
| **F03** | Fashion Story | `FashionStoryDetailTemplateSpecContract` | Narrative editorial with author attribution and shoppable mentions |
| **F04** | Fashion Article | `FashionArticleDetailTemplateSpecContract` | In-depth textile journalism with inline media assets |
| **F05** | Fashion Collection | `FashionCollectionDetailTemplateSpecContract` | Seasonal capsule edits curated by guest guild stylists |
| **F06** | Fashion Look | `FashionLookDetailTemplateSpecContract` | Styled look canvas with interactive hotspot pins and constituent pieces |
| **F07** | Fashion Inspiration | `FashionInspirationDetailTemplateSpecContract` | Moodboards tagged with visual style keywords and linked garments |
| **F08** | Brand Story | `BrandStoryDetailTemplateSpecContract` | Designer ethos, artisanal sustainability values, and atelier catalog |
| **F09** | Editorial View | `EditorialViewTemplateSpecContract` | High visual rhythm canvas pairing text, pullquotes, and large media |

---

### 5. Desktop & Mobile Product Detail Architecture (Sections 9.4, 9.5, 9.9)

* **Breadcrumb Navigation:** Canonical trail ($\text{Home} \rightarrow \text{Catalog} \rightarrow \text{Outerwear} \rightarrow \text{Item Name}$).
* **Desktop 2-Column Split:** Left column dedicated to high-resolution 3:4 portrait media and thumbnail rail; right column hosts title, rating, pricing, variant pickers, quantity, and primary purchase CTA.
* **Information Hierarchy:**
  $$\text{Brand} \longrightarrow \text{Product Name} \longrightarrow \text{Rating} \longrightarrow \text{Price} \longrightarrow \text{Availability} \longrightarrow \text{Summary} \longrightarrow \text{Variants} \longrightarrow \text{Actions}$$
  Secondary technical specifications and reviews never visually compete with the primary purchase action.

---

### 6. Product Media & Interactive Gallery System (Sections 9.6 – 9.8)

* **Media Asset Types:** `image`, `thumbnail`, `detail`, `lifestyle`, `model`, `video`, `view_360`. Only formats supplied by the authoritative backend contract are rendered.
* **Gallery Interaction:**
  * Primary view standardizes on a high-resolution 3:4 portrait ratio.
  * Horizontally scrollable thumbnail strip with active selection ring.
  * Tap-to-zoom modal supporting pan and dismiss gestures.
  * Keyboard navigation: Arrow keys cycle images; `Enter` opens zoom; `Escape` closes modal.

---

### 7. Authoritative Pricing & Commerce Transparency (Section 9.10)

* **Displayed vs. Final Amount:** Displayed price ($\text{Current Price}$, $\text{Original Price}$, $\text{Discount \%}$) is rendered strictly from the backend commerce service.
* The visual system explicitly avoids promising price locks across multi-day sessions:
  $$\text{Displayed Price} \longrightarrow \text{Pre-Checkout Cart Validation} \longrightarrow \text{Final Payable Amount}$$

---

### 8. Product Availability & Logistics (Section 9.11)

Real-time inventory states:
* `● In Stock`: Green indicator; triggers normal Add to Cart flow.
* `● Low Stock`: Amber indicator with authoritative remaining unit count.
* `✕ Out of Stock`: Red indicator; disables primary purchase CTA.
* `⏳ Pre-Order`: Blue indicator; surfaces expected dispatch date and pre-order registration.
* `✕ Currently Unavailable`: Replaces commerce actions with a "Notify Me When Available" trigger.

---

### 9. Variant Selection Engine & Cross-Dependencies (Sections 9.12 – 9.14)

* **Variant Dimensions:** Color swatches with hex background preview, size pills, and custom fit options.
* **Multi-State Rules:**
  $$\text{Available (Selectable)} \mid \text{Selected (Active Accent)} \mid \text{Unavailable (Disabled + Strikethrough)} \mid \text{Loading}$$
* **Accessibility Rule:** State is never communicated by color alone (e.g. strikethrough text and accessible ARIA attributes are enforced).
* **Cross-Option Dependencies:** Selecting a specific color (e.g. *Raw Indigo*) dynamically recalculates available sizes (*S, M, L available; XL disabled*).

---

### 10. Quantity Controls & Pre-Purchase Validation (Section 9.15)

* Boundary-checked stepper ($1 \le q \le 10$) with decrement `[ − ]` and increment `[ + ]` triggers.
* Disables controls when inventory limit is reached or item is out of stock.
* Prevents client-side tampering through backend validation upon cart submission.

---

### 11. Primary & Sticky Purchase Actions on Mobile (Sections 9.16 & 9.17)

* **Dual Button Architecture:** High-contrast `Add to Cart` primary action paired with direct `Buy Now` trigger.
* **Optimistic Wishlist:** One-tap heart button toggles state instantly with rollback on network failure.
* **Mobile Sticky Bar:** On narrow viewports, a sticky bottom sheet displays total payable price and `Add to Cart` with safe-area padding for mobile home indicators.

---

### 12. Progressive Disclosure: Specifications & Care (Sections 9.18 – 9.20)

* **Overview:** 3-line truncated overview with interactive `Read More ▼` / `Show Less ▲` disclosure.
* **Grouped Specifications:**
  * *Fabric & Construction:* Material, weave, fiber count, dye method.
  * *Fit & Silhouette:* Cut profile, collar type, length, model measurements.
  * *Origin & Care:* Manufacturing origin mill, washing temperature, drying guidelines.
* Rows with missing data are cleanly suppressed rather than rendering empty placeholders.

---

### 13. Product Reviews & Rating Distribution (Sections 9.21 – 9.23)

* **Rating Summary:** Big score display ($4.7$) with 5-star graphical summary and total rating count.
* **Rating Histogram:** 5-star to 1-star percentage distribution bars visualizing satisfaction density.
* **Verified Buyer Cards:** Author name, verified purchase badge, date, review commentary, and helpfulness upvote counters.
* **State Resilience:** Distinguishes between "No reviews yet" (inviting first review) and "Reviews temporarily unavailable" (with retry trigger).

---

### 14. Content Relationship Architecture (Sections 9.24 – 9.27)

Strict semantic separation prevents confusing users with conflated recommendations:

| Relationship | Semantic Meaning | Recommendation Engine Source |
| :--- | :--- | :--- |
| **Similar Products** | Directly related to current product attributes | Content-based vector similarity (textiles, fit) |
| **Recommended for You** | Personalized to active user style preferences | Collaborative filtering + Style Tag matching |
| **Styled With** | Constituent garments forming a complete look | Curated ensemble relationship mapping |
| **Recently Viewed** | History of garments previously inspected | Client/Session navigation ledger |
| **Trending** | Popular across platform within current season | Real-time platform interaction velocity |

---

### 15. Product Comparison Engine (Sections 9.31 & 9.32)

* Multi-product comparison endpoint (`POST /detail/product/compare`).
* Side-by-side attribute alignment across Price, Brand, Availability, Customer Rating, and Technical Specifications.
* Responsive horizontal scroll on narrow mobile viewports preventing unreadable squished tables.

---

### 16. Content-Led Fashion Detail Canvas (Sections 9.33 – 9.44)

Fashion detail prioritizes editorial storytelling and cultural resonance over direct cart buttons:
* **F03 Fashion Story:** High-resolution hero header, author, publication date, markdown narrative, and mentioned garments.
* **F04 Fashion Article:** In-depth textile journalism with inline high-resolution gallery images.
* **F05 Fashion Collection:** Seasonal capsule edits curated by guild designers with constituent looks and garments.
* **F06 Fashion Look:** Full-ensemble photography featuring interactive hotspot coordinates ($x\%, y\%$) linking directly to constituent shoppable products.
* **F07 Fashion Inspiration:** Thematic moodboard tagged with aesthetic keywords (`Waxed Cotton`, `Flax Linen`).
* **F08 Brand Story:** Independent atelier ethos, sustainability certifications, verified badges, and collection drops.
* **F09 Editorial View:** Dynamic visual rhythm alternating full-bleed imagery, narrative paragraphs, pull quotes, and look rails.

---

### 17. Explainable AI Boundaries (Section 9.46)

* Algorithmic recommendation rationales are displayed in transparent callout pills (*"Recommended because you explored Japanese selvedge denim in Monsoon capsule"*).
* Recommendation interpretations are never presented as physical product facts.

---

### 18. Detail State Resilience & Error Isolation (Sections 9.47 – 9.50)

* **Partial Failure Isolation:** If secondary services (such as reviews or recommendations) fail to respond, the core product media, pricing, and purchase buttons remain fully operational.
* **Non-Destructive Retry:** Failed modules render localized retry triggers rather than failing the whole page.
* **Authoritative Error Mapping:** Distinguishes between `Not Found`, `Removed`, `Unavailable`, and `Restricted` items.

---

### 19. Mobile TypeScript Component & Template Architecture

Located under `mobile/features/visual/detail/`:

```
mobile/features/visual/detail/
├── types.ts                                  # Complete TypeScript interfaces mirroring Pydantic v2
├── components/
│   ├── ProductGallery.tsx                   # 3:4 media gallery with zoom modal & thumbnails
│   ├── ProductInfo.tsx                      # Header, breadcrumbs, price, and availability
│   ├── VariantSelector.tsx                  # Size pills and color swatches with dependencies
│   ├── QuantitySelector.tsx                 # Boundary-checked stepper controls
│   ├── ProductActions.tsx                   # Add to Cart, Buy Now, and sticky mobile purchase bar
│   ├── ProductSpecifications.tsx            # Progressive overview and grouped spec table
│   ├── ProductReviews.tsx                   # Review histogram and verified cards
│   ├── RelatedProductsRail.tsx              # Similar, Recommended, and Styled-With rails
│   └── LookDetailView.tsx                   # Look hero with interactive hotspot pins
├── templates/
│   ├── ProductDetailTemplate.tsx            # P02: Complete product detail screen
│   ├── FashionStoryTemplate.tsx             # F03: Editorial story detail screen
│   ├── FashionLookTemplate.tsx              # F06: Styled look detail screen
│   └── FashionCollectionTemplate.tsx        # F05: Curated capsule collection screen
└── index.ts                                 # Public module barrel export
```

---

### 20. Verification, Automated Test Metrics & Completion Gate

```powershell
pytest tests/unit/test_visual_detail.py tests/integration/test_visual_detail_router.py -v
============================= 23 passed in 2.05s ==============================

pytest -q
============================ 936 passed in 17.12s =============================
```

* **Unit Tests (PROD-001–PROD-020, FASH-001–FASH-011):** 13 comprehensive tests in `tests/unit/test_visual_detail.py`.
* **Integration Tests (Journeys, REST Endpoints, End-to-End Flows):** 10 tests in `tests/integration/test_visual_detail_router.py`.
* **Total Passing Tests:** 936 / 936 (100% green, 0 failures, 0 regressions across the entire FashXStudio suite).

```
==============================================================================
FASHXSTUDIO VISUAL DESIGN — PHASE 09: COMPLETION GATE
==============================================================================
[✓] P01 - P10 Product Detail Screen Contracts & Templates                     LOCKED
[✓] F01 - F09 Fashion Detail Screen Contracts & Templates                     LOCKED
[✓] Product Media Gallery with 3:4 Ratios and Zoom Modal                      LOCKED
[✓] Variant Selection Engine with Option Dependencies & States                 LOCKED
[✓] Boundary-Checked Quantity Selector with Pre-Purchase Constraints          LOCKED
[✓] Sticky Purchase Action Sheet for Mobile Environments                      LOCKED
[✓] Progressive Specifications & Disclosure Architecture                      LOCKED
[✓] Review Histogram Distribution & Verified Buyer Cards                      LOCKED
[✓] Distinct Semantic Relationship Rails (Similar vs Recommended vs Styled)   LOCKED
[✓] Look Canvas with Interactive Hotspot Pins & Constituent Pieces            LOCKED
[✓] Mobile TypeScript UI Components & Templates                               LOCKED
[✓] FastAPI REST Endpoints (/visual/detail/*)                                 LOCKED
[✓] Pydantic v2 BaseContractModel Schemas (extra="forbid" everywhere)         LOCKED
[✓] Automated Tests (23 new tests, 936 / 936 total passing)                   PASSED
==============================================================================
STATUS: READY FOR HANDOFF TO PHASE 10 (OUTFIT / STYLING / FASHION EXPERIENCE)
==============================================================================
```
