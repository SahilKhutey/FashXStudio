# FashXStudio — Production Build Visual Design — 15
## Interaction, State, Accessibility & Visual QA System Reference Manual

**Subsystem:** Screens / Pages / Visual Design  
**Phase:** Visual Design — 15 (Interaction, State, Accessibility & Visual QA System)  
**Status:** **LOCKED & VERIFIED PRODUCTION BASELINE**  
**Date:** 2026-10-02  
**Verification Baseline:** 1238 tests passed (100% green)

---

### 1. Phase Objective & Core Operational Principle

Phase VD-15 defines the production interaction, state lifecycle, accessibility audit, and visual quality assurance layer across the entire FashXStudio design system. Building on the foundations of tokens (`VD-00`), shell (`VD-01`), components (`VD-05`), fashion content (`VD-06`), shopping (`VD-07`), discovery (`VD-08`), product detail (`VD-09`), outfit styling (`VD-10`), regional maps (`VD-11`), AI intelligence (`VD-12`), personal profile (`VD-13`), and responsive layouts (`VD-14`), this phase establishes the unified behavioral rules for interactive feedback, error prevention, state transitions, accessibility compliance, and regression protection.

#### The Core Operational Principle:
$$\mathbf{Interactions\ must\ be\ predictable,\ visible,\ accessible,\ state\text{-}aware,\ reversible,\ and\ non\text{-}destructive\ by\ default.}$$

#### The Interaction Decision Model:
$$\begin{aligned}
&\text{User Input (Mouse/Touch/Key)} + \text{Component Current State} + \text{Validation/Network Constraints} \\
&\quad\implies \mathbf{State\ Precedence\ Machine} \implies \mathbf{Feedback\ Presentation} \implies \mathbf{Accessible\ Live\ Region}
\end{aligned}$$

#### The Final Architectural Paradigm:
```
                         USER
                          │
                          ▼
                     INTERACTION
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
        INPUT           STATE          FEEDBACK
          │               │               │
          ▼               ▼               ▼
       Mouse          Component       Visual
       Touch          Screen          Audio/Semantic
       Keyboard       Workflow        Feedback
                          │
                          ▼
                     UI RESPONSE
                          │
                          ▼
                  ACCESSIBILITY LAYER
                          │
                          ▼
                      VISUAL QA
```

---

### 2. Master Interaction Architecture & Hierarchy (Sections 15.1 & 15.2)

The FashXStudio interaction architecture unites input handling, state computation, feedback dispatch, accessibility guarantees, and visual regression testing across all platforms:

1. **Input Layer:** Multi-modal support covering standard mouse pointer events, capacitive touch gestures, full keyboard navigation, and semantic voice inputs where supported.
2. **State Engine:** Deterministic evaluation of component states following strict precedence ordering.
3. **Screen Lifecycle Controller:** Manages high-level screen states (`loading`, `empty`, `error`, `partial`, `offline`) ensuring users are never left in visual ambiguity.
4. **Feedback Router:** Governs appropriate communication channel selection (Toast, Inline Alert, Banner, Modal Dialog, Status Badge) based on message severity and reversibility.
5. **Accessibility Audit Engine:** Continuously verifies touch targets ($\ge 44\text{px}$), contrast ratios ($\ge 4.5:1$), keyboard focus loops, ARIA semantics, and non-color-only communication.
6. **Motion Engine:** Enforces duration limits (150ms–400ms) and respects system-level `prefers-reduced-motion` settings.
7. **Visual QA Gate:** Validates pixel-level regression specifications across 12 master interaction fixtures and 6 end-to-end user journeys.

---

### 3. The 10 Component States & Strict Precedence (Sections 15.3 – 15.14)

All interactive elements support up to 10 standard states. When multiple conditions are simultaneously true, the component resolves state according to a strict mathematical hierarchy:

$$\mathbf{Error} \succ \mathbf{Unavailable} \succ \mathbf{Disabled} \succ \mathbf{Loading} \succ \mathbf{Selected} \succ \mathbf{Pressed} \succ \mathbf{Focus} \succ \mathbf{Hover} \succ \mathbf{Rest}$$

| Precedence | State | Visual Treatment | Interactivity | ARIA Attribute |
| :--- | :--- | :--- | :--- | :--- |
| **P1 (Highest)** | `error` | Red border (`#EF4444`), inline error message, alert icon | Active (allows correction) | `aria-invalid="true"`, `aria-describedby` |
| **P2** | `unavailable` | Muted background, slash badge, out-of-stock tag | Inactive (`is_interactive=False`) | `aria-disabled="true"` |
| **P3** | `disabled` | 40% opacity, default cursor, no hover/press response | Inactive (`is_interactive=False`) | `aria-disabled="true"` |
| **P4** | `loading` | Spinner replaces/supplements content, cursor progress | Inactive (prevents double submits) | `aria-busy="true"` |
| **P5** | `selected` | Brand border (`#111827`), checkmark indicator, active tint | Active | `aria-selected="true"` or `aria-pressed="true"` |
| **P6** | `pressed` / `active` | Scaled down 98%, deeper background tint | Active | Native active |
| **P7** | `focus` | 2px high-contrast focus ring (`#111827`), 2px offset | Active | Focused element |
| **P8** | `hover` | Light tint transition, subtle elevation change | Active | Pointer hover |
| **P9** | `success` | Green accent (`#10B981`), checkmark icon | Active | `aria-live="polite"` |
| **P10 (Default)** | `rest` | Neutral baseline styling, standard contrast | Active | Default |

*Key Guarantee:* Form validation errors take absolute precedence over loading or disabled states, ensuring users immediately perceive submission failures and actionable fix guidance.

---

### 4. Focus Management, Focus Rings & Keyboard Navigation (Sections 15.15 – 15.22)

Keyboard navigation is a first-class operational mode across all FashXStudio interfaces:
* **Focus Rings:** All focusable elements display a clear, 2px solid ring with 2px offset (`ring-2 ring-neutral-900 ring-offset-2`), achieving at least $3:1$ contrast against adjacent surfaces.
* **Navigation Traversal:** `Tab` moves forward, `Shift+Tab` moves backward in intuitive logical reading order.
* **Activation:** `Enter` activates links and primary actions; `Space` toggles buttons, checkboxes, and modal dialogs.
* **Dismissal:** `Escape` immediately dismisses dropdown menus, filter sheets, floating panels, and modal dialogs, returning focus to the trigger element.
* **Modal Focus Trapping:** When modals or sheets open, focus is trapped within the container until dismissed; background elements are marked `aria-hidden="true"`.
* **Skip Links:** A skip-to-content link is provided at the very top of the DOM for immediate bypass of the global navigation bar.

---

### 5. Form Validation & Contextual Guidance (Sections 15.25 – 15.35)

Form inputs must provide real-time, actionable feedback rather than generic rejection:
* **Inline Validation:** Errors appear directly below the affected input field, coupled with an explicit error icon and red border styling.
* **Fix Guidance:** Every validation error must include actionable advice (e.g., *"Please include an '@' symbol in your email address (e.g. name@domain.com)"*).
* **ARIA Coupling:** Errored inputs are linked to their error descriptions via `aria-describedby="[field_id]-error"` and marked `aria-invalid="true"`.
* **Non-Blocking Exploration:** Form validation triggers on blur (`onBlur`) rather than on initial keypress (`onChange`), allowing users to complete typing before receiving feedback.

---

### 6. Feedback Decision Matrix (Sections 15.36 – 15.48)

System feedback is dispatched through 5 distinct visual channels based on permanence, urgency, and user workflow disruption:

```
                          FEEDBACK EVENT
                                │
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
   LOW SEVERITY            MEDIUM SEVERITY         HIGH SEVERITY
 (Non-blocking)         (Field / Contextual)    (System / Critical)
        │                       │                       │
        ▼                       ▼                       ▼
      TOAST                INLINE ALERT              BANNER
(Auto-dismiss 4-6s)      (Persistent beside      (Top of page/viewport,
                         affected element)        requires resolution)
                                                        │
                                                        ▼
                                                  MODAL DIALOG
                                              (Destructive confirmation)
```

| Feedback Type | Channel | Auto-Dismiss | Interaction Mode | ARIA Role | Primary Use Case |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Toast** | Floating Overlay | Yes (4–6s) | Non-blocking | `status` (`aria-live="polite"`) | Item saved, look copied, profile updated |
| **Inline Alert** | Adjacent to element | No (until fixed) | Contextual | `alert` (`aria-live="polite"`) | Invalid input, size unavailable, out of stock |
| **Banner** | Page / Container Top | No (dismissible) | Non-blocking | `alert` (`aria-live="assertive"`) | System maintenance, offline mode, partial outage |
| **Modal Dialog** | Screen Center | No (requires decision)| Blocking (modal)| `alertdialog` | Deleting look, resetting preferences, order cancel |
| **Status Badge** | Inline Chip | No | Information-only | `status` | Syncing, network status, beta feature flag |

---

### 7. Destructive Actions, Confirmation & Reversibility (Sections 15.49 – 15.54)

Destructive user operations (e.g., deleting saved looks, purging search history, resetting personalization preferences) must protect users from accidental data loss:
* **Explicit Consequence Wording:** The confirmation dialog must clearly explain what will be lost (e.g., *"Are you sure you want to delete 'Summer Streetwear'? This outfit and its 4 garment pairings cannot be recovered."*).
* **Two-Step Affirmation:** Two distinct buttons with clear visual hierarchy: a neutral "Cancel" button (focused by default) and a destructive "Delete Look" button in semantic red.
* **Undo Windows:** For non-destructive removals (e.g., removing a product from the shopping cart), provide a temporary Toast with an active "Undo" button (active for 8 seconds).

---

### 8. Screen Lifecycle States (Sections 15.55 – 15.65)

Screens adapt across 5 standard lifecycle states to provide visual continuity during asynchronous data fetching:

```
                         SCREEN REQUEST
                               │
                               ▼
                        [1] LOADING STATE
                    (Pulse Skeleton Shapes)
                               │
             ┌─────────────────┼─────────────────┐
             ▼                 ▼                 ▼
       [2] SUCCESS         [3] EMPTY         [4] ERROR
      (Full Content)    (Context + CTA)   (Reason + Retry)
                                                 │
                               ┌─────────────────┴─────────────────┐
                               ▼                                   ▼
                        [5] PARTIAL OUTAGE                  [6] OFFLINE
                     (Banner + Usable Data)             (Cached Data + Tag)
```

1. **Loading State:** Content-shaped skeleton loaders with subtle pulse animation (`animate-pulse`) match the geometry of the target cards, preventing layout shifts (CLS < 0.1).
2. **Empty State:** Illustrated empty placeholder featuring empathetic copy and a clear primary call-to-action (e.g., *"No saved looks yet — explore trending collections in Outfit Studio"*).
3. **Error State:** Friendly error illustration explaining what went wrong, accompanied by an immediate "Try Again" retry action button.
4. **Partial State:** When secondary services degrade (e.g., recommendations offline), display an informative banner at the top while rendering all available catalog items normally.
5. **Offline State:** Cached data is displayed alongside an offline status badge and timestamp indicating when the data was last synchronized.

---

### 9. WCAG 2.1 AA Accessibility Audit Engine (Sections 15.66 – 15.78)

The FashXStudio accessibility engine automates compliance verification against WCAG 2.1 Level AA standards:
* **Touch Target Size:** All touch targets must measure at least $44\text{px} \times 44\text{px}$ (or include sufficient transparent touch padding).
* **Contrast Ratios:** Text and essential visual icons achieve a contrast ratio $\ge 4.5:1$ against backgrounds ($3:1$ for large text $\ge 18\text{pt}$ / $24\text{px}$).
* **Non-Color Reliance:** Color is never the sole communicator of state; every status color is paired with text, icons, or distinctive border treatments.
* **Screen Reader Names:** All interactive elements without visible text provide explicit `aria-label` or `accessibilityLabel` properties.
* **Audit Endpoint:** Verified via `/api/v1/visual/interaction/accessibility-audit`.

---

### 10. Screen Reader Semantics & ARIA Live Regions (Sections 15.79 – 15.86)

Semantic screen reader markup ensures non-visual users experience complete parity:
* **Polite Announcements (`aria-live="polite"`):** Background updates (e.g., "3 items added to cart", "Filter applied: 14 results found") wait until the user stops interacting.
* **Assertive Announcements (`aria-live="assertive"`):** Critical alerts and errors (e.g., "Payment failed: Card expired", "Connection lost") interrupt immediately.
* **Dynamic Indicators:** Stateful controls update `aria-expanded` (accordion/drawers), `aria-selected` (tabs), and `aria-pressed` (toggle buttons) in real time.

---

### 11. Motion, Micro-Interactions & Reduced Motion (Sections 15.87 – 15.93)

Animations serve functional feedback rather than decorative distraction:
* **Micro-Interactions (150ms–250ms):** Button presses, checkbox toggles, heart bookmark animations use standard cubic-bezier easing (`ease-out`).
* **State Transitions (200ms–300ms):** Dropdowns, drawer slide-ins, and toast reveals.
* **Screen Transitions (300ms–400ms):** Page transitions and hero image zooms.
* **Prefers-Reduced-Motion:** When the user enables reduced motion, all position translations and scale transitions collapse to instant snap or gentle opacity fades (0–100ms).

---

### 12. Visual QA Regression Protection & Fixtures (Sections 15.94 – 15.97)

The automated Visual QA matrix tracks 12 canonical fixtures (`INT-01` through `INT-12`) with strict pixel-match thresholds ($\le 0.05$ difference):

| Fixture ID | Fixture Name | Category | Classification | Match Threshold |
| :--- | :--- | :--- | :--- | :--- |
| `INT-01` | Button State Progression (Rest $\to$ Hover $\to$ Focus $\to$ Pressed $\to$ Loading $\to$ Disabled) | Component | `pixel_perfect` | $\le 0.01$ |
| `INT-02` | Form Input Validation & Error Ring Transition | Component | `pixel_perfect` | $\le 0.01$ |
| `INT-03` | Feedback Toast Auto-Dismissal & Position Stack | Feedback | `perceptual` | $\le 0.05$ |
| `INT-04` | Destructive Action Modal Dialog & Focus Trap | Modal | `pixel_perfect` | $\le 0.01$ |
| `INT-05` | Screen Skeleton Loading Pulse Effect | Lifecycle | `perceptual` | $\le 0.05$ |
| `INT-06` | Screen Empty State with Illustration & CTA | Lifecycle | `pixel_perfect` | $\le 0.02$ |
| `INT-07` | Screen Error Recovery & Retry Button Interaction | Lifecycle | `pixel_perfect` | $\le 0.02$ |
| `INT-08` | Screen Partial Outage Banner with Usable Catalog | Lifecycle | `pixel_perfect` | $\le 0.02$ |
| `INT-09` | Screen Offline Banner with Cached Data Badge | Lifecycle | `pixel_perfect` | $\le 0.02$ |
| `INT-10` | High-Contrast Focus Ring 2px Ring Offset | A11y | `pixel_perfect` | $\le 0.00$ |
| `INT-11` | Touch Target Minimum Bounding Box ($\ge 44\text{px}$) | A11y | `pixel_perfect` | $\le 0.00$ |
| `INT-12` | Reduced Motion Fallback Mode Verification | Motion | `perceptual` | $\le 0.03$ |

---

### 13. End-to-End Visual Journey A: Discovery to Product Detail

* **Workflow:** User browses Discovery feed (`/api/v1/visual/fashion/feed`), activates product card `prod-denim-01`, tests hover/focus, and loads the Product Detail Screen (`/api/v1/visual/shopping/product/prod-denim-01`).
* **Interaction Verification:** Focus transitions smoothly to the product header; breadcrumbs update without layout jank; touch target for "Save to Wishlist" measures $48\text{px} \times 48\text{px}$.

---

### 14. End-to-End Visual Journey B: Product to Cart & Checkout Flow

* **Workflow:** User selects size "M", clicks "Add to Cart", triggers optimistic loading state on button, receives non-blocking feedback Toast, and views the updated Cart drawer.
* **Interaction Verification:** Button transitions: `Rest` $\to$ `Loading` (spinner) $\to$ `Success` (check) $\to$ `Rest`. Toast announces "Item added to cart" via `aria-live="polite"`. Cart counter increments with micro-bounce animation.

---

### 15. End-to-End Visual Journey C: Fashion Content to Outfit Builder

* **Workflow:** User views Editorial Story, selects "Open in Outfit Studio", loads Outfit Builder canvas (`/api/v1/visual/styling/builder`), swaps garment slots, and attempts to navigate away with unsaved changes.
* **Interaction Verification:** Confirmation dialog triggers: *"You have unsaved changes. Leave without saving?"*, trapping focus on "Cancel" button.

---

### 16. End-to-End Visual Journey D: AI Assistant to Styling Studio (Fact vs Guidance)

* **Workflow:** User interacts with AI Product Assistant (`/api/v1/visual/ai/product-assistant/prod-denim-01`), asking about fabric composition and styling recommendations.
* **Interaction Verification:** Hard catalog facts (`Material: 100% Selvedge Cotton`) are strictly separated from subjective AI guidance. AI prompt input maintains $\ge 48\text{px}$ touch target with accessible name.

---

### 17. End-to-End Visual Journey E: Regional Map to Local Products

* **Workflow:** User opens Fashion Map (`/api/v1/visual/geography/map`), switches to accessible structured list alternative, selects region `reg-mumbai`, and views local artisans.
* **Interaction Verification:** Non-visual users can navigate all regional data via keyboard tab list; map markers provide `aria-label` with localized descriptions.

---

### 18. End-to-End Visual Journey F: Profile to Personalization Controls

* **Workflow:** User visits Personal Preferences (`/api/v1/visual/personal/preferences`), toggles "Streetwear" preference, and initiates account privacy export.
* **Interaction Verification:** Preference toggles immediately dispatch `status_badge` feedback; destructive reset requests initiate modal confirmation.

---

### 19. Mobile TypeScript Architecture & Stateful Components

Located under `mobile/features/visual/interaction/`:

```
mobile/features/visual/interaction/
├── types.ts                                   # Complete TypeScript interfaces mirroring Pydantic v2
├── hooks/
│   └── useInteractionState.ts                 # State precedence machine and event handlers
├── components/
│   ├── StatefulButton.tsx                     # Precedence-aware button (loading, success, disabled)
│   ├── StatefulInput.tsx                      # Accessible input with inline validation and fix hints
│   ├── FeedbackToast.tsx                      # Auto-dismissing floating toast with a11y announcement
│   ├── ConfirmationDialog.tsx                 # Modal dialog for destructive operations with focus trap
│   ├── ScreenStateWrapper.tsx                 # Master lifecycle wrapper (skeleton, empty, error, offline)
│   └── LiveAnnouncement.tsx                   # Screen reader live region component
└── index.ts                                  # Public module barrel export
```

---

### 20. Verification, Automated Test Metrics & Completion Gate

```powershell
pytest tests/unit/test_visual_interaction.py tests/integration/test_visual_interaction_router.py -v
============================= 41 passed in 3.78s ==============================

pytest tests -q
=========================== 1238 passed in 24.59s ============================
```

* **Unit Tests (`tests/unit/test_visual_interaction.py` — 29 tests):**
  * `INT-UNIT-001`: Rest state defaults, interactivity, and ARIA attributes.
  * `INT-UNIT-002`: Mathematical state precedence hierarchy (`error` $\succ$ `unavailable` $\succ$ `disabled` $\succ$ `loading` $\succ$ `selected` $\succ$ `focus`).
  * `INT-UNIT-003`: Form validation rules, email format checking, and actionable fix guidance.
  * `INT-UNIT-004`: Feedback decision matrix resolution (Toast vs Alert vs Dialog).
  * `INT-UNIT-005` & `INT-UNIT-006`: Screen lifecycle states (Loading skeleton, Empty state, Error retry, Offline cache).
  * `INT-UNIT-008`: Accessibility audit engine (touch targets $\ge 44\text{px}$, contrast $\ge 4.5:1$).
  * `INT-UNIT-009`: Motion categories and durations (150ms–400ms).
  * `INT-UNIT-010`: Visual QA fixtures registry and threshold verification.
  * `FORBID-001` to `FORBID-008`: Strict `extra="forbid"` schema rejection across all Interaction contracts (Rule I02).
* **Integration Tests (`tests/integration/test_visual_interaction_router.py` — 12 tests):**
  * All 6 REST endpoints under `/api/v1/visual/interaction/*`.
  * 6 End-to-End User Journeys:
    1. Journey A: Discovery Feed $\to$ Product Detail Screen (`VD-08` $\to$ `VD-09`).
    2. Journey B: Product Detail $\to$ Size Selection $\to$ Add to Cart $\to$ Toast Feedback (`VD-09` $\to$ `VD-07`).
    3. Journey C: Fashion Content Story $\to$ Outfit Builder Studio $\to$ Unsaved Changes Confirmation (`VD-06` $\to$ `VD-10`).
    4. Journey D: AI Product Assistant $\to$ Fact vs Guidance Separation $\to$ Accessible Prompt Input (`VD-12` $\to$ `VD-10`).
    5. Journey E: Regional Map Canvas $\to$ Accessible Structured List $\to$ Local Products (`VD-11` $\to$ `VD-07`).
    6. Journey F: Personal Profile $\to$ Preferences Update $\to$ Confirmation Dialog (`VD-13`).
* **Total Project Tests:** **1238 passed (100% green, 0 failures, 0 regressions)**.

```
==============================================================================
FASHXSTUDIO VISUAL DESIGN — PHASE 15: COMPLETION GATE
==============================================================================
[✓] 10 Component States Defined & Governed by Precedence Machine               LOCKED
[✓] High-Contrast Focus Rings (>= 3:1) & Keyboard Traversal (Tab/Enter/Esc)   LOCKED
[✓] Contextual Form Validation with Actionable Fix Guidance & ARIA DescribedBy LOCKED
[✓] Global Feedback Decision Matrix (Toast, Inline Alert, Banner, Dialog)     LOCKED
[✓] Destructive Action Safeguards with Two-Step Dialog & Consequence Wording  LOCKED
[✓] Screen Lifecycle System (Skeleton Loading, Empty State, Error Recovery)   LOCKED
[✓] Partial Outage Banners & Offline Mode with Cached Data Indicators         LOCKED
[✓] WCAG 2.1 AA Accessibility Engine (Touch >= 44px, Contrast >= 4.5:1)       LOCKED
[✓] ARIA Live Region Announcements (Polite vs Assertive Modes)                LOCKED
[✓] Functional Motion System (150-400ms) with Prefers-Reduced-Motion Fallback LOCKED
[✓] Automated Visual QA Regression Matrix (12 Fixtures INT-01 to INT-12)      LOCKED
[✓] 6 End-to-End User Journeys (Journeys A through F) Fully Validated          LOCKED
[✓] Mobile TypeScript Hook & Stateful React Native / Expo UI Components       LOCKED
[✓] FastAPI REST Endpoints (/visual/interaction/*)                             LOCKED
[✓] Pydantic v2 BaseContractModel Schemas (extra="forbid" everywhere)         LOCKED
[✓] Automated Tests (41 new tests, 1238 / 1238 total passing)                 PASSED
==============================================================================
STATUS: PHASE 15 (INTERACTION, STATE, ACCESSIBILITY & QA) COMPLETED & VERIFIED
==============================================================================
```
