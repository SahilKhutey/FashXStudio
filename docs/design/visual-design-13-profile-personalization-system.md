# FashXStudio — Production Build Visual Design — 13
## Profile, Personalization & Saved Experience System Reference Manual

**Subsystem:** Screens / Pages / Visual Design  
**Phase:** Visual Design — 13 (Profile, Personalization & Saved Experience System)  
**Status:** **LOCKED & VERIFIED PRODUCTION BASELINE**  
**Date:** 2026-10-02  
**Verification Baseline:** 1158 tests passed (100% green)

---

### 1. Phase Objective & Core Operational Principle

Establish a production-grade visual system for the user's personal FashXStudio space—where identity, preferences, saved fashion, saved products, outfits, activity, recommendations, regional context, and account controls are organized into one coherent, transparent, and user-governed experience.

This phase integrates all preceding visual design layers:
* **VD-6 Fashion Content:** Editorial stories, trends, and inspiration.
* **VD-7 Shopping UI:** Commercial catalog, stock reality, and shopping cart.
* **VD-8 Discovery + Search:** Faceted search, exploratory rails, and categories.
* **VD-9 Product & Fashion Detail:** Garment specifications and product detail screens.
* **VD-10 Outfit + Styling:** Outfit builder, look canvas, and styling studio.
* **VD-11 Regional Maps + Geography:** Territorial fashion movements and regional culture.
* **VD-12 AI / Intelligence:** Context-aware styling assistant and transparent explanations.
* $$\mathbf{\downarrow}$$
* **VD-13 Profile + Personalization:** User identity, saved items, history, and algorithmic governance.

#### The Core Operational Principle:
$$\mathbf{Personalization\ should\ be\ user\text{-}controlled,\ explainable,\ reversible,\ and\ clearly\ separated\ from\ authoritative\ product/content\ information.}$$

#### Strict Separation Rules:
$$\begin{aligned}
\mathbf{Saved} &\neq \mathbf{Purchased} && \text{Saving an item expresses interest; commerce truth resides in the order ledger.} \\
\mathbf{Viewed} &\neq \mathbf{Liked} && \text{Browsing history records activity; it is never an endorsement or like.} \\
\mathbf{Recommended} &\neq \mathbf{Selected} && \text{Algorithmic output proposes; the user remains in control.} \\
\mathbf{AI\ Suggested} &\neq \mathbf{User\ Approved} && \text{AI styling advice is separate from explicit user preferences.} \\
\mathbf{Preferred\ Region} &\neq \mathbf{Current\ Location} && \text{Regional context is user-chosen and strictly decoupled from device GPS.} \\
\mathbf{Profile\ UI} &\neq \mathbf{Authorization} && \text{Visual display does not grant access; backend guards enforce authorization.} \\
\mathbf{Frontend\ State} &\neq \mathbf{Commerce\ Truth} && \text{Prices, stock, and cart states are verified against catalog domain models.}
\end{aligned}$$

---

### 2. Personal Experience Architecture & Flow Diagram (Section 13.1)

```
                         PERSONAL SPACE
                              │
       ┌──────────────────────┼──────────────────────┐
       ▼                      ▼                      ▼
    PROFILE               ACTIVITY                SAVED
       │                      │                      │
       ▼                      ▼                      ▼
   Identity              Recently Viewed        Products
   Preferences           Interactions           Looks
   Settings              History                Fashion
   Regions               Discovery              Collections
   AI                     Shopping
       │                      │
       └──────────────┬───────┘
                      ▼
                PERSONALIZATION
                      │
          ┌───────────┼───────────┐
          ▼           ▼           ▼
      Discovery     Styling      AI
          │           │           │
          └───────────┼───────────┘
                      ▼
                 SHOPPING
```

---

### 3. Personal Space Core Principles (Section 13.3)

1. **User In Control:** The user explicitly decides what is saved, what is remembered, and what influences recommendations.
2. **Transparent & Explainable:** Every recommendation displays the factors and signals that generated it.
3. **Reversible & Editable:** Users can edit preferences, remove items, clear history, or reset personalization signals at any time.
4. **Clear Information Boundaries:** Explicit choices are never conflated with inferred observations.
5. **Cross-Subsystem Continuity:** Saved items seamlessly transition into Detail, Styling, Shopping, and Discovery canvases.
6. **Graceful Degradation:** A failure in the recommendation engine never prevents users from accessing their saved products, looks, or profile settings.
7. **Privacy-Preserving:** Browsing history has granular clear triggers; regional preferences do not track or leak GPS coordinates.
8. **Commercial Reality Respected:** Saved products and wishlist items reflect real-time stock availability, restock dates, and out-of-stock alternative suggestions.

---

### 4. Personal Screen Inventory: PR01–PR11 (Section 13.2)

| Screen ID | Screen Name | Template Contract | Primary Purpose |
| :--- | :--- | :--- | :--- |
| **PR01** | Profile | `ProfileTemplateSpecContract` | Main personal space overview with identity, activity, and shortcuts |
| **PR02** | Personal Dashboard | `PersonalDashboardTemplateSpecContract` | Action-oriented home prioritizing Continue $\to$ Saved $\to$ Recommendations |
| **PR03** | Saved Products | `SavedProductsTemplateSpecContract` | Saved catalog items with category filters and multiple sort modes |
| **PR04** | Saved Looks | `SavedLooksTemplateSpecContract` | Outfits organized by collection with direct Outfit Builder editing bridge |
| **PR05** | Saved Fashion | `SavedFashionTemplateSpecContract` | Saved editorial stories, fashion trends, collections, and brand archives |
| **PR06** | Wishlist | `WishlistTemplateSpecContract` | Commercial shopping wishlist with live stock availability and alternatives |
| **PR07** | Recently Viewed | `RecentlyViewedTemplateSpecContract` | Chronological browsing activity with granular history purging controls |
| **PR08** | Preferences | `PreferencesTemplateSpecContract` | Explicit user styles and categories strictly decoupled from inferred signals |
| **PR09** | Recommendation Preferences | `RecommendationPreferencesTemplateSpecContract` | Algorithmic tuning switches and one-tap personalization signal reset |
| **PR10** | Regional Preferences | `RegionalPreferencesTemplateSpecContract` | User-chosen regional fashion context decoupled from device GPS |
| **PR11** | Account Settings | `AccountSettingsTemplateSpecContract` | Categorized account controls, 2FA status, notifications, and privacy retention |

---

### 5. Personal Information Architecture & State Modeling (Sections 13.4 & 13.5)

The personal system is governed by deterministic states defined in `PersonalState`:

$$\text{PersonalState} \in \{\mathbf{LOADING},\, \mathbf{LOADED},\, \mathbf{EMPTY},\, \mathbf{ERROR},\, \mathbf{SAVING},\, \mathbf{SAVED},\, \mathbf{UNSAVED\_CHANGES}\}$$

#### Explicit vs. Inferred Preferences Boundary:
```
                       PREFERENCES SYSTEM
                               │
            ┌──────────────────┴──────────────────┐
            ▼                                     ▼
   EXPLICIT PREFERENCES                  INFERRED PREFERENCES
   (User-Declared Truth)                 (System-Observed Signals)
            │                                     │
   • Selected Styles                     • Frequently Viewed Categories
   • Preferred Brands                    • Explored Silhouettes
   • Favorite Colors                     • Browsing Frequency
   • Fit Preferences                     • Recency Weights
            │                                     │
            └──────────────┬──────────────────────┘
                           ▼
                  TRANSPARENT REASONS
                           │
                           ▼
                ALGORITHMIC SUGGESTIONS
```

* **Explicit Preferences (`ExplicitPreferencesContract`):** Declared directly by the user via interactive selectors. Modifiable and persistent until user alters them.
* **Inferred Preferences (`InferredPreferencesContract`):** Derived from aggregate activity. Completely purged when the user triggers `Reset Personalization Signals` (`PR09`).

---

### 6. User Profile Canvas: PR01 (Sections 13.6 – 13.9)

Screen `PR01` acts as the main personal hub:
* **`ProfileHeader`:** Avatar, display name, handle (`@alexandra.chen`), member since badge (`September 2024`), and direct `Edit Profile` action.
* **`ProfileSummary`:** High-level metrics counters:
  $$\text{Saved Products: } 12 \quad\vert\quad \text{Saved Looks: } 6 \quad\vert\quad \text{Wishlist: } 3 \quad\vert\quad \text{Collections: } 2$$
* **`Recent Activity Preview`:** Displays the top 3 chronological browsing actions with timestamps.
* **`Saved Items Preview`:** Horizontal scroll rail of recently saved garments and looks.
* **`Explicit Preference Tags`:** Chip rail showing active style identities (`Minimalist`, `Contemporary Streetwear`, `Heritage Workwear`).

---

### 7. Personal Dashboard: PR02 (Sections 13.10 – 13.12)

Screen `PR02` is structured around a strict action-oriented vertical hierarchy:

$$\mathbf{Continue\ Exploring} \longrightarrow \mathbf{Saved\ Items\ Quick\ Access} \longrightarrow \mathbf{Personalized\ Recommendations} \longrightarrow \mathbf{Recent\ Activity}$$

#### Graceful Module Degradation Guarantee (Section 13.12):
If downstream recommendation microservices fail or time out:
1. `PersonalDashboardTemplateSpecContract.recommendation_error` is populated with an explainable fallback notice (*"Recommendations temporarily unavailable"*).
2. The `recommendations` list safely degrades to an empty list.
3. The dashboard screen **still renders successfully** with `state = loaded`, allowing unhindered access to Continue Exploring, Saved Products, Wishlist, and Profile Settings.

---

### 8. Saved Products Canvas: PR03 (Sections 13.13 & 13.14)

Screen `PR03` manages the user's saved garment archive:
* **Non-Color-Only Saved Indicators:** Every card utilizes an explicit bookmark icon plus a visible text badge (`SAVED`), adhering to WCAG 2.1 AA accessibility guidelines.
* **Filter Rail:** Category filtering (`All`, `Outerwear`, `Tops`, `Bottoms`, `Footwear`, `Accessories`).
* **Sorting Modes:**
  * `recently_saved` (Default)
  * `price_asc` (Low to High)
  * `price_desc` (High to Low)
* **Quick Actions:** Remove from saved (immediate state toggle), View Product Detail (`P02`), or Add to Cart (`VD-07`).

---

### 9. Saved Looks & Outfit Collections: PR04 (Sections 13.15 & 13.16)

Screen `PR04` manages composed ensembles and collections:
* **Collection Filter Bar:** Tabs for user-defined collections (`All`, `Summer Capsule`, `Workwear Edit`).
* **`SavedLookCard`:** Renders multi-item outfit thumbnail previews, total item count, constituent tags, and collection affiliation.
* **Outfit Studio Bridge:** High-contrast `Edit in Builder` button transitions directly into the interactive Outfit Builder (`ST02`) with all outfit slots populated.

---

### 10. Saved Fashion Content: PR05 (Sections 13.17 & 13.18)

Screen `PR05` organizes non-commercial editorial inspiration:
* **Content Tabs:** `All`, `Stories` (editorial articles), `Collections` (runway lookbooks), `Trends` (forecast reports), `Brands` (designer profiles).
* **`SavedFashionCard`:** Image banner, publication/curator metadata, reading time, and direct link to the full editorial canvas.

---

### 11. Wishlist Experience: PR06 (Sections 13.19 – 13.21)

Screen `PR06` is the commercially-aware shopping wishlist:
* **Stock Availability Badges:** Real-time inventory status (`in_stock`, `low_stock`, `out_of_stock`).
* **Out of Stock Notices:** Explicit restock timeline notifications (*"Out of stock - Restock expected in November"*).
* **Alternative Suggestions:** When an item is out of stock, a direct reference link to an in-stock alternative product is rendered (`alternative_product_id`).
* **Direct Commerce Action:** Active `Add to Cart` button for in-stock items.

---

### 12. Recently Viewed Activity: PR07 (Sections 13.22 – 13.25)

Screen `PR07` maintains browsing history with strict privacy protections:
* **Viewing $\neq$ Endorsement:** Merely opening a product or lookbook never marks it as "Liked" or automatically adds it to recommendations without user consent.
* **Descending Chronology:** Items are strictly ordered with the most recent interaction at index 0.
* **Granular History Clear:**
  * One-tap `Clear All History` action.
  * Category-specific clear action (`POST /personal/recent/clear?entity_type=product`).

---

### 13. User Preferences Studio: PR08 (Sections 13.26 – 13.28)

Screen `PR08` is the master configuration studio for explicit user tastes:
* **Style Multi-Selector:** `Minimalist`, `Streetwear`, `Heritage Workwear`, `Avant-Garde`, `Casual Tailored`.
* **Category Preferences:** `Outerwear`, `Denim`, `Knitwear`, `Tailoring`, `Footwear`.
* **Fit Preferences:** `Relaxed / Oversized`, `Regular`, `Slim / Tailored`.
* **Interaction State Engine:** Visual pill indicator cycling through `saved` $\to$ `unsaved_changes` $\to$ `saving` $\to$ `saved` (or `error`).
* **Discard & Save:** Explicit buttons to commit changes or revert to previously saved preferences.

---

### 14. Recommendation Preferences & Algorithmic Governance: PR09 (Sections 13.29 – 13.31)

Screen `PR09` gives the user transparent algorithmic control:
* **Granular Toggles:**
  * `Personalized Recommendations` (Master switch)
  * `Style Inspiration Feed`
  * `Trend Suggestions`
  * `Similar Products`
* **Signal Transparency Breakdown:** Explains active signals consumed by recommendation rankers (browsing frequency, preferred categories, recent searches).
* **Reset Personalization Signals:**
  * `POST /api/v1/visual/personal/preferences/recommendations/reset`
  * Instantly clears all inferred browsing weights while preserving explicit user preferences.

---

### 15. Regional Preferences & Geography Decoupling: PR10 (Sections 13.32 – 13.34)

Screen `PR10` establishes regional fashion identity without invasive location tracking:
* **GPS Decoupling Notice:** Displays prominent banner:
  > *"Your regional fashion context is user-chosen and not derived from your device GPS location."*
* **Selectable Hierarchy:** Preferred Country (`Japan`), Preferred State/Prefecture (`Tokyo-to`), Preferred City (`Tokyo`).
* **Curated Regional Movement:** Links into local textile hubs and regional street fashion feeds (`VD-11`).

---

### 16. Account Settings & Privacy Retention: PR11 (Sections 13.35 – 13.37)

Screen `PR11` centralizes administrative controls and security:
* **Categorized Settings Navigation:**
  * `Profile & Identity` (Display name, email, avatar)
  * `Notifications` (Push, email, restock alerts)
  * `Security` (Password, Two-Factor Authentication status)
  * `Privacy & Data Retention` (`standard`, `enhanced`, `minimal`)
* **Data Deletion:** Triggers compliant with GDPR/CCPA privacy retention policies.

---

### 17. Multi-Action Saved Item Toggle & Persistence Engine (Sections 13.38 – 13.40)

The backend provides a unified, idempotent save/unsave toggle engine:
* **Toggle Endpoint:** `POST /api/v1/visual/personal/saved/toggle`
  ```json
  {
    "item_type": "product",
    "item_id": "prd_new_item"
  }
  ```
* **Explicit Delete Endpoint:** `DELETE /api/v1/visual/personal/saved/{item_type}/{item_id}`
* **Response Contract (`SavedItemToggleResultContract`):**
  * `item_id`: Target entity ID.
  * `item_type`: `product`, `look`, `fashion`, or `wishlist`.
  * `is_saved`: Boolean state after operation.
  * `saved_summary`: Updated live totals across all saved entity types.

---

### 18. Cross-System Architectural Bridges (Sections 13.50 – 13.56)

Phase 13 establishes verified bidirectional bridges across the visual ecosystem:

1. **Profile $\longrightarrow$ Discovery (PR01 $\to$ VD-08 D01):**
   * Tapping "Explore New Arrivals" on the profile routes to the Discovery Home screen (`D01`).
2. **Profile $\longrightarrow$ Styling Studio (PR01 $\to$ VD-10 ST01):**
   * Tapping "Style Studio" routes to the Styling Home canvas (`ST01`) with recommended looks.
3. **Profile Preferences $\longrightarrow$ AI Style Assistant (PR08 $\to$ VD-12 AI04):**
   * Explicit preferences (`Minimalist`, `Streetwear`) configure the AI Style Assistant without leaking private data.
4. **Saved Product $\longrightarrow$ Product Detail (PR03 $\to$ VD-09 P02):**
   * Selecting a saved product opens the canonical Product Detail screen with full specifications.
5. **Saved Look $\longrightarrow$ Outfit Builder (PR04 $\to$ VD-10 ST02):**
   * Selecting a saved look loads its constituent slots into the Outfit Studio for interactive editing.
6. **Wishlist $\longrightarrow$ Shopping Cart Handoff (PR06 $\to$ VD-07 Cart):**
   * Available wishlist items transfer into the commercial shopping cart with selected variants.

---

### 19. Mobile TypeScript Component & Template Architecture

Located under `mobile/features/visual/personal/`:

```
mobile/features/visual/personal/
├── types.ts                                   # Complete TypeScript interfaces mirroring Pydantic v2
├── components/
│   ├── ProfileHeader.tsx                      # Identity header with avatar, handle, and edit trigger
│   ├── ProfileSummary.tsx                     # 4-column metric counters for saved entities
│   ├── PersonalDashboard.tsx                  # Dashboard layout prioritizing Continue -> Saved -> Recs
│   ├── PersonalSection.tsx                    # Accessible container wrapper with section headers
│   ├── SavedProductCard.tsx                   # Product card with non-color-only saved badge & actions
│   ├── SavedLookCard.tsx                      # Outfit card with multi-piece previews and builder trigger
│   ├── SavedFashionCard.tsx                   # Editorial card with tags, curator, and reading time
│   ├── WishlistItem.tsx                       # Wishlist item with stock status and alternative links
│   ├── RecentItem.tsx                         # Chronological browsing activity list item
│   ├── PreferenceGroup.tsx                    # Multi-option preference category container
│   ├── PreferenceSelector.tsx                 # Interactive selectable preference chips
│   ├── PreferenceSwitch.tsx                   # Accessible toggle switch with explanatory subtitle
│   ├── RecommendationPreferences.tsx          # Algorithmic switches and signal transparency list
│   ├── RegionalPreferences.tsx                # Regional fashion picker with GPS decoupling disclaimer
│   ├── AIPreferences.tsx                      # AI styling guidance customization switches
│   ├── SettingsNavigation.tsx                 # Category-based account settings menu
│   └── SettingsSection.tsx                    # Form field container for account configuration
├── templates/
│   ├── ProfileTemplate.tsx                    # PR01: Profile main overview template
│   ├── PersonalDashboardTemplate.tsx          # PR02: Personal dashboard template
│   ├── SavedProductsTemplate.tsx              # PR03: Saved products catalog template
│   ├── SavedLooksTemplate.tsx                 # PR04: Saved outfit collections template
│   ├── SavedFashionTemplate.tsx               # PR05: Saved editorial & fashion trends template
│   ├── WishlistTemplate.tsx                   # PR06: Shopping wishlist template
│   ├── RecentlyViewedTemplate.tsx             # PR07: Browsing activity history template
│   ├── PreferencesTemplate.tsx                # PR08: User preferences studio template
│   ├── RecommendationPreferencesTemplate.tsx  # PR09: Recommendation governance template
│   ├── RegionalPreferencesTemplate.tsx        # PR10: Regional fashion preferences template
│   └── AccountSettingsTemplate.tsx            # PR11: Account settings & privacy template
└── index.ts                                  # Public module barrel export
```

---

### 20. Verification, Automated Test Metrics & Completion Gate

```powershell
pytest tests/unit/test_visual_personal.py tests/integration/test_visual_personal_router.py -v
============================= 69 passed in 4.88s ==============================

pytest -q
=========================== 1158 passed in 12.12s ============================
```

* **Unit Tests (`tests/unit/test_visual_personal.py` — 45 tests):**
  * `PROFILE-001`–`PROFILE-006`: Profile identity, stats, activity preview, and saved preview.
  * `DASH-001`–`DASH-007`: Dashboard priority ordering, partial loading, and recommendation degradation.
  * `SAVE-001`–`SAVE-009`: Saved products, looks, fashion, filtering, sorting, removal, and wishlist realities.
  * `PREF-001`–`PREF-009`: Preferences selection, saving state cycle, error handling, and discard.
  * `REG-001`–`REG-003`: Regional preferences and GPS decoupling.
  * `REC-001`–`REC-003`: Recommendation preferences, transparency signals, and reset personalization.
  * `SET-001`–`SET-003`: Account settings, notifications, and privacy retention.
  * `FORBID-001`–`FORBID-008`: Strict `extra="forbid"` rejection on unauthorized fields across all contracts (Rule I02).
* **Integration Tests (`tests/integration/test_visual_personal_router.py` — 24 tests):**
  * All 19 REST endpoints under `/api/v1/visual/personal/*`.
  * 6 Cross-System Integration Flows:
    1. Profile $\to$ Discovery (`PR01` $\to$ VD-08 `D01`).
    2. Profile $\to$ Styling Studio (`PR01` $\to$ VD-10 `ST01`).
    3. Profile Preferences $\to$ AI Style Assistant (`PR08` $\to$ VD-12 `AI04`).
    4. Saved Product $\to$ Product Detail Canvas (`PR03` $\to$ VD-09 `P02`).
    5. Saved Look $\to$ Outfit Builder Canvas (`PR04` $\to$ VD-10 `ST02`).
    6. Wishlist $\to$ Shopping Cart Handoff (`PR06` $\to$ VD-07 Cart).
* **Total Project Tests:** **1158 passed (100% green, 0 failures, 0 regressions)**.

```
==============================================================================
FASHXSTUDIO VISUAL DESIGN — PHASE 13: COMPLETION GATE
==============================================================================
[✓] PR01 - PR11 Personal Screen Contracts & Templates                        LOCKED
[✓] Core Principle: User-Controlled, Explainable & Reversible Personal Space  LOCKED
[✓] Strict Separation Rules (Saved≠Purchased, Viewed≠Liked, Region≠GPS, etc.)  LOCKED
[✓] Personal Dashboard Hierarchy & Graceful Recommendation Degradation        LOCKED
[✓] Saved Products with Category Filters & Non-Color-Only Saved Indicators   LOCKED
[✓] Saved Looks with Collections & Outfit Builder Bridge                      LOCKED
[✓] Wishlist with Real-Time Stock Availability & Out-of-Stock Alternatives    LOCKED
[✓] Recently Viewed Activity with Granular History Purging Controls           LOCKED
[✓] Explicit Preferences Strictly Segregated from Inferred System Signals     LOCKED
[✓] Recommendation Preferences & One-Tap Personalization Signal Reset         LOCKED
[✓] Regional Preferences Decoupled from Physical Device GPS Location          LOCKED
[✓] Account Settings with Privacy Retention Controls                          LOCKED
[✓] Multi-Action Saved Item Toggle & Persistence Engine (Products/Looks/etc.)  LOCKED
[✓] Cross-System Bridges (Profile -> Discovery, Styling, AI, Detail, Cart)    LOCKED
[✓] Mobile TypeScript UI Components & Templates (React Native / Expo SDK 57)  LOCKED
[✓] FastAPI REST Endpoints (/visual/personal/*)                               LOCKED
[✓] Pydantic v2 BaseContractModel Schemas (extra="forbid" everywhere)         LOCKED
[✓] Automated Tests (69 new tests, 1158 / 1158 total passing)                PASSED
==============================================================================
STATUS: PHASE 13 (PROFILE, PERSONALIZATION & SAVED EXPERIENCE) COMPLETED & VERIFIED
==============================================================================
```
