# FashXStudio — Production Build Visual Design — 7
## Shopping UI System + Commerce Experience Framework

**Subsystem:** Screens / Pages / Visual Design  
**Phase:** Visual Design — 7 (Shopping UI System + Commerce Experience Framework)  
**Status:** **LOCKED & VERIFIED PRODUCTION BASELINE**  
**Date:** 2026-10-01  
**Verification Baseline:** 887 tests passed (100% green)

---

### 1. Phase Objective

Build the complete fashion shopping visual and interaction system on top of VD-0 $\rightarrow$ VD-6.

This phase transforms FashXStudio from a fashion-discovery interface into an end-to-end fashion-commerce experience covering:
* Catalog discovery and category hierarchy
* Search integration and keyword suggestions
* Filter facet drawers and multi-attribute sorting
* Product grids and responsive listings
* Product details, 3:4 portrait galleries, specifications, and delivery estimates
* Variant selection (size, color, material) with strict pre-purchase validation
* Real-time availability system (In Stock, Low Stock, Out of Stock, Pre-order)
* Wishlist management with optimistic save/remove transitions
* Side-by-side product attribute comparison
* Shopping cart with line-item quantity controls and pre-checkout stock/price validation
* Progressive multi-step checkout (Contact, Address, Delivery, Payment, Review)
* Post-purchase order confirmation, order history, and tracking details
* Complete-the-look cross-selling bridging fashion inspiration to purchasable items

---

### 2. Shopping Architecture & Flow Diagram (Section 7.1)

```
                         SHOPPING EXPERIENCE
                                  │
             ┌────────────────────┼────────────────────┐
             │                    │                    │
          Discovery            Product              Purchase
             │                    │                    │
      ┌──────┼──────┐      ┌──────┼──────┐       ┌────┼────┐
      ▼      ▼      ▼      ▼      ▼      ▼       ▼    ▼    ▼
    Search  Category Grid  Detail Variant Reviews Cart Checkout
      │      │      │       │       │       │       │
      └──────┴──────┴───────┴───────┴───────┴───────┘
                                  │
                                  ▼
                         Shopping State System
                                  │
                                  ▼
                           Commerce Services
```

---

### 3. Shopping Design Principles (Section 7.2)

1. **Product First:** The physical/visual garment remains dominant across all screens.
2. **Information Clarity:** Pricing, discounts, sizes, inventory availability, shipping fees, and fabric specs are presented unambiguously.
3. **Low Friction:** Unnecessary hurdles between $\text{Discover} \rightarrow \text{Product} \rightarrow \text{Purchase}$ are minimized.
4. **Visual Consistency:** Products maintain coherent typography, badges, and pricing grammar across Search, Listing, Recommendations, Detail, Wishlist, Cart, and Orders.
5. **No Hidden Commerce State:** Out-of-stock items, price shifts, and cart validation failures are explicitly communicated before transaction finalization.

---

### 4. Shopping Screen Architecture: SH01 - SH12 (Section 7.3)

The Phase-1 shopping screen ecosystem maps directly to 12 production screen templates:

| Screen ID | Screen Name | Template Contract | Primary Purpose |
| :--- | :--- | :--- | :--- |
| **SH01** | Shopping Home | `ShoppingHomeTemplateSpecContract` | Combined discovery and commerce entry point |
| **SH02** | Category | `CategoryTemplateSpecContract` | Taxonomical hierarchy and subcategory navigation |
| **SH03** | Filter | `FilterStateContract` | Faceted drawer filters (sizes, brands, prices, colors) |
| **SH04** | Sort | `SortOption` | Multi-dimensional sorting (relevance, newest, price) |
| **SH05** | Wishlist | `WishlistTemplateSpecContract` | Saved items collection with empty state & cart transfer |
| **SH06** | Cart | `CartTemplateSpecContract` | Line-item review, quantity adjustments, order summary |
| **SH07** | Cart Detail / Product Detail | `ProductDetailTemplateSpecContract` | Comprehensive garment inspection & purchase action |
| **SH08** | Checkout | `CheckoutTemplateSpecContract` | Progressive checkout steps (address, logistics, payment) |
| **SH09** | Order Review | `OrderReviewTemplateSpecContract` | Final pre-submission verification of all order terms |
| **SH10** | Order Confirmation | `ConfirmationTemplateSpecContract` | Success confirmation, order number, and delivery date |
| **SH11** | Orders | `OrdersTemplateSpecContract` | Customer order history list with status badges |
| **SH12** | Order Detail | `OrderDetailTemplateSpecContract` | Granular order tracking timeline and constituent items |

---

### 5. Shopping Journey: Primary & Secondary (Section 7.5)

**Primary Commerce Journey:**
$$\text{Home} \longrightarrow \text{Discover / Search} \longrightarrow \text{Category / Results} \longrightarrow \text{Product Detail} \longrightarrow \text{Select Variant} \longrightarrow \text{Add to Cart} \longrightarrow \text{Cart} \longrightarrow \text{Checkout} \longrightarrow \text{Review} \longrightarrow \text{Confirmation} \longrightarrow \text{Order Detail}$$

**Secondary Wishlist Journey:**
$$\text{Product Detail} \longrightarrow \text{Save to Wishlist} \longrightarrow \text{Wishlist} \longrightarrow \text{Transfer to Cart} \longrightarrow \text{Checkout}$$

---

### 6. Catalog & Category Experience (Sections 7.6 & 7.7)

* **Shopping Home:** Balances editorial fashion discovery with commercial utility. Integrates search entry, featured collections (`Monsoon 2026`), category shortcut chips (`Outerwear`, `Tops`, `Bottoms`, `Footwear`), and trending products.
* **Category Hierarchy:** Driven dynamically by catalog taxonomy rather than hard-coded component states:
  $$\text{Shopping} \longrightarrow \text{Outerwear} \longrightarrow \text{Jackets \& Overshirts} \longrightarrow \text{Results}$$

---

### 7. Product Listing Layout & Responsive Architecture (Sections 7.8 & 7.9)

* **Desktop (12-column grid):** Persistent left-hand filter sidebar, active filter pill row, and 3-to-4 column product grid.
* **Tablet (8-column grid):** Horizontal filter & sort toolbar, summary count, and 3-column product grid.
* **Mobile (4-column grid):** Sticky category header, filter/sort button bar, full-width modal filter drawer, and 2-column portrait grid.

---

### 8. Product Grid & Product Card Integration (Sections 7.10 - 7.12)

Extends the Phase 06 fashion `ProductCard` into an active commercial driver:
* **Product Media:** Standardized 3:4 portrait aspect ratio.
* **Commercial Badges:** `BESTSELLER`, `ORGANIC`, `NEW_ARRIVAL`, `LIMITED_EDITION`.
* **Price Display:** Active price in bold, strikethrough original price, and automated discount percentage tag.
* **Actions:** View product detail on card tap, instant optimistic wishlist heart toggle.

---

### 9. Filter & Sort System Architecture (Sections 7.13 - 7.18)

* **Faceted Dimensions:** Category, Brand, Price Range, Size, Color Swatch, Material, and Stock Availability.
* **Active Filter Pills:** Individually dismissible filter pills with "Clear All" batch reset.
* **Sort Options:** `Relevance`, `Newest`, `Price: Low to High`, `Price: High to Low`, `Popularity`.

---

### 10. Search-to-Shopping Flow & Result States (Sections 7.19 & 7.20)

* **Global Query Integration:** `/shopping/search?q=denim`
* **Zero Results State:** Displays friendly guidance and automated suggestions (`Linen shirts`, `Selvedge denim`, `Summer jackets`) with a one-click "Clear Filters" recovery action.

---

### 11. Product Detail Experience & Gallery (Sections 7.21 - 7.24)

* **Portrait Gallery:** Primary 3:4 high-resolution media with responsive thumbnail strip navigation.
* **Authoritative Attributes:** Brand attribution, title, star rating, verified review count, comprehensive markdown description.
* **Delivery Information:** Real-time shipping duration estimates, postal code checking, and free delivery thresholds.
* **Technical Specifications:** Structured table detailing fabric composition, fit, care instructions, and manufacturing origin.

---

### 12. Variant Selection, Validation & States (Sections 7.25 - 7.27)

* **Variant Dimensions:** Color swatches with hex background previews, size pills, and material choices.
* **State Spectrum:** `Available`, `Selected`, `Unavailable` (strikethrough), `Disabled`, `Loading`.
* **Strict Pre-Purchase Validation:** Prevents adding to cart or checking out without required variant selection; displays explicit inline feedback rather than silent failures.

---

### 13. Authoritative Pricing, Price Change & Availability Systems (Sections 7.28 - 7.30)

* **Authoritative Source:** All currency formatting and pricing originate from the core commerce service.
* **Real-time Inventory Signals:**
  - `● In Stock` (green indicator)
  - `● Low Stock` (amber indicator with remaining unit count)
  - `× Out of Stock` (red indicator, disables purchase trigger)
  - `Pre-order` (accent indicator with expected dispatch date)
* **Price Change Transparency:** Pre-checkout cart verification detects price shifts and prompts the user before proceeding.

---

### 14. Cart Architecture & Quantity Control (Sections 7.36 - 7.40)

* **Line Items:** Thumbnail, title, brand, selected variant tags, unit price, and line total.
* **Quantity Controls:** Boundary-checked stepper ($1 \le q \le 10$) with automatic line and subtotal recomputation. Setting quantity to zero prompts item removal.
* **Pre-Checkout Validation:** Evaluates inventory and pricing integrity before enabling checkout progression.

---

### 15. Progressive Multi-Step Checkout Architecture (Sections 7.41 - 7.44)

* **Progress Indicator:** Breadcrumb trail tracking $\text{Contact} \rightarrow \text{Address} \rightarrow \text{Delivery} \rightarrow \text{Payment} \rightarrow \text{Review}$.
* **Address Management:** Default address selection with edit/change modal trigger.
* **Logistics Options:** Express Courier vs. Standard Ground with clear fee displays.
* **Payment Methods:** Support for UPI instant payments, Saved Credit/Debit Cards, Netbanking, and Cash on Delivery.

---

### 16. Order Review, Confirmation & Orders History (Sections 7.45 - 7.50)

* **Order Review (SH09):** Final verification displaying complete delivery, payment, line items, and financial summary.
* **Order Confirmation (SH10):** Displays generated order number (e.g. `FXS-2026-98210`), estimated delivery date, and dual CTAs ("View Order Details", "Continue Shopping").
* **Order History (SH11):** Chronological list of orders with visual status badges (`PLACED`, `PROCESSING`, `SHIPPED`, `OUT_FOR_DELIVERY`, `DELIVERED`, `CANCELLED`).
* **Order Detail (SH12):** 4-step tracking progression timeline and full item breakdown.

---

### 17. Shopping State Architecture & Error Recovery (Sections 7.51 - 7.55)

Universal 8-state machine:
$$\text{Loading} \mid \text{Ready} \mid \text{Empty} \mid \text{Partial} \mid \text{Validation Error} \mid \text{Service Error} \mid \text{Unavailable} \mid \text{Success}$$

* **Empty States:** Custom empty views for Wishlist, Cart, and Search Results with explicit discovery CTAs.
* **Error States:** Human-readable error explanations paired with non-destructive retry triggers.

---

### 18. Complete-the-Look & Comparison Systems (Sections 7.60 - 7.63)

* **Complete-the-Look (Section 7.62):** Integrates fashion ensembles directly on the product detail page, allowing one-tap inspection and cart addition of coordinating pieces.
* **Product Comparison Matrix (Section 7.60):** Data-driven side-by-side comparison across Price, Availability, Rating, and Fabric specifications.

---

### 19. Verification & Test Metrics

Comprehensive automated test coverage across unit domain logic, validation engines, and integration REST endpoints:

```powershell
pytest tests/unit/test_visual_shopping.py tests/integration/test_visual_shopping_router.py -v
============================= 33 passed in 1.67s ==============================

pytest -q
============================ 887 passed in 10.23s =============================
```

* **Unit Tests (SHOP-001 through SHOP-061):** 25 tests in `tests/unit/test_visual_shopping.py`
* **Integration Tests (Flows A, B, C, D & Endpoints):** 8 tests in `tests/integration/test_visual_shopping_router.py`
* **Total Passing Tests:** 887 / 887 (100% green, 0 failures, 0 regressions across the entire FashXStudio suite).

---

### 20. Phase Completion Gate

```
==============================================================================
FASHXSTUDIO VISUAL DESIGN — PHASE 07: COMPLETION GATE
==============================================================================
[✓] SH01 - SH12 Shopping Screen Contracts & Models                             LOCKED
[✓] Variant Selector Engine with Strict Pre-Purchase Validation                LOCKED
[✓] Real-time Availability & Inventory State Indicators                        LOCKED
[✓] Wishlist State Machine & Optimistic Transitions                            LOCKED
[✓] Shopping Cart with Quantity Controls & Pre-Checkout Validation             LOCKED
[✓] Progressive Multi-Step Checkout Architecture                               LOCKED
[✓] Order Review, Confirmation, History, and Tracking Progression              LOCKED
[✓] Complete-the-Look Cross-Selling & Side-by-Side Comparison Matrix           LOCKED
[✓] Mobile TypeScript Shopping UI Components & Templates                       LOCKED
[✓] FastAPI REST Endpoints (/visual/shopping/*)                                LOCKED
[✓] Pydantic v2 BaseContractModel Schemas (extra="forbid" everywhere)          LOCKED
[✓] Automated Tests (33 new tests, 887 / 887 total passing)                    PASSED
==============================================================================
STATUS: READY FOR HANDOFF TO PHASE 08 (DISCOVERY + SEARCH SCREENS)
==============================================================================
```
