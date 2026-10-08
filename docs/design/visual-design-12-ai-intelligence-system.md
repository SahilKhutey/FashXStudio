# FashXStudio — Production Build Visual Design — 12
## AI / Intelligence Screens & Interaction System Reference Manual

**Subsystem:** Screens / Pages / Visual Design  
**Phase:** Visual Design — 12 (AI / Intelligence Screens & Interaction System)  
**Status:** **LOCKED & VERIFIED PRODUCTION BASELINE**  
**Date:** 2026-10-02  
**Verification Baseline:** 1089 tests passed (100% green)

---

### 1. Phase Objective

Establish a production-grade visual system for FashXStudio AI experiences where AI understands, searches, recommends, explains, assists, and helps users create, while strictly separating:
1. **Factual product data** (price, stock, fabric, origin).
2. **System-generated recommendations** (catalog matching).
3. **AI-generated guidance** (styling advice and rationale).
4. **User decisions** (saving, editing, adding to bag).

The core operational principle:
$$\mathbf{AI\ proposes\ and\ assists;\ the\ user\ remains\ in\ control.}$$

Connecting intelligence to visual discovery, styling, and commerce:
$$\text{USER REQUEST} \longrightarrow \text{INTENT UNDERSTANDING} \longrightarrow \text{CATALOG / STYLE RETRIEVAL} \longrightarrow \mathbf{AI\ RECOMMENDATION} \longrightarrow \mathbf{TRANSPARENT\ EXPLANATION} \longrightarrow \begin{cases} \text{User Edits in Outfit Studio} \\ \text{User Explores in Discovery} \\ \text{User Adds to Shopping Bag} \\ \text{User Provides Quality Feedback} \end{cases}$$

This phase builds upon:
* **VD-8 Discovery + Search:** Natural language search, query refinement, and autocomplete rails.
* **VD-9 Product & Fashion Detail:** Garment specifications, craft provenance, and hotspot coordinators.
* **VD-10 Outfit + Styling:** Configurable slot architecture, mix-and-match matrix, and look composition.
* **VD-11 Regional Maps + Geography:** Territorial fashion movements, climate context, and local textile craft.

---

### 2. AI Experience Architecture & Flow Diagram (Section 12.1)

```
                         FASHXSTUDIO AI
                               │
          ┌────────────────────┼────────────────────┐
          ▼                    ▼                    ▼
       DISCOVER              CREATE              DECIDE
          │                    │                    │
          ▼                    ▼                    ▼
      AI Search          Style Assistant       AI Explanation
      AI Explore         Outfit Assistant      Recommendation
      AI Product         Look Assistant        Comparison
          │                    │                    │
          └────────────────────┼────────────────────┘
                               ▼
                         AI Intelligence
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
            Search       Recommendation      Generation
              │                │                │
              └────────────────┼────────────────┘
                               ▼
                         User Decision
                               │
           ┌───────────────────┼───────────────────┐
           ▼                   ▼                   ▼
        Product             Styling             Shopping
```

---

### 3. AI Design Principles (Section 12.3)

1. **Useful:** Focus on real user tasks (finding matching pieces, understanding drape/fit, building capsules).
2. **Understandable:** Every recommendation clearly articulates *why* it was selected using plain language.
3. **Controllable:** The user can edit any AI-generated outfit, swap any slot item, and override suggestions.
4. **Transparent:** No fake numerical certainty (e.g. no "98.7% match"); qualitative confidence levels (`Strong`, `Possible`, `Limited`) are backed by observable factors.
5. **Reversible:** Low friction to undo, discard, or restart an AI conversation session.
6. **Contextual:** Only active, verifiable parameters (current location, season, budget) are passed into prompts.
7. **Accessible:** Compliant with WCAG 2.1 AA (screen-reader announcements, 44px touch targets, reduced motion).
8. **Non-intrusive:** AI enhances the fashion experience without visually overpowering catalog items or styling canvases.

---

### 4. AI Screen Inventory: AI01–AI09 (Section 12.2)

| Screen ID | Screen Name | Template Contract | Primary Purpose |
| :--- | :--- | :--- | :--- |
| **AI01** | AI Home | `AIHomeTemplateSpecContract` | Central intelligence entry point with quick prompts, tasks, and recent sessions |
| **AI02** | AI Fashion Assistant | `AIAssistantTemplateSpecContract` | Multi-turn conversational interface with transparent context chips and actions |
| **AI03** | AI Product Assistant | `AIProductAssistantTemplateSpecContract` | Product Q&A enforcing strict boundary between catalog facts and AI styling advice |
| **AI04** | AI Style Assistant | `AIStyleAssistantTemplateSpecContract` | Aesthetic direction suggestions with verified factors and matching look rails |
| **AI05** | AI Outfit Recommendation | `AIOutfitRecommendationTemplateSpecContract` | Complete ensemble suggestion with constituent pieces, alternatives, and edit controls |
| **AI06** | AI Search | `AISearchTemplateSpecContract` | Natural language query search with intent interpretation and observable steps |
| **AI07** | AI Recommendation Detail | `AIRecommendationDetailTemplateSpecContract` | Deep dive into an individual recommendation with supporting items and alternatives |
| **AI08** | AI Result Explanation | `AIResultExplanationTemplateSpecContract` | Dedicated canvas explaining why a specific item was suggested with feedback capture |
| **AI09** | AI Preferences | `AIPreferencesTemplateSpecContract` | User-controlled AI customization, privacy switches, and budget tier tuning |

---

### 5. AI Trust Architecture & Information Classification (Sections 12.4 & 12.5)

```
                    INFORMATION
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
     Product Facts   System Data     AI Output
          │              │              │
          ▼              ▼              ▼
      Catalog/API     Services       AI Model
          │              │              │
          └──────────────┼──────────────┘
                         ▼
                       USER
```

#### Information Classification Hierarchy:
* **`product_fact`:** Authoritative catalog attributes (price, size, stock, fabric, origin). *Never generated or guessed by AI.*
* **`fashion_content`:** Curated editorial lookbooks, styling notes, and brand stories.
* **`system_recommendation`:** Algorithmic catalog match based on multi-stage ranking.
* **`ai_explanation`:** Transparent reasoning articulating why an item fits the current context.
* **`ai_generated_content`:** Conversational text clearly tagged as AI guidance.
* **`user_input`:** User prompts, selected context tags, and explicit preferences.
* **`user_decision`:** Authoritative user actions (edit in builder, save to lookbook, add to cart).

---

### 6. Product Fact Boundary (Section 12.16)

The system enforces a strict programmatic and visual boundary between physical catalog facts and subjective AI styling guidance:

$$\begin{aligned}
\text{Authoritative Catalog Data} &\implies \begin{cases} \text{Price: ₹4,999.00} \\ \text{Availability: In Stock (Ships in 24 hrs)} \\ \text{Fabric: 14oz Japanese Selvedge Cotton} \\ \text{Origin: Kojima, Okayama} \end{cases} \\
\text{AI Styling Guidance} &\implies \text{"This structured boxy silhouette pairs best with relaxed hemp trousers."}
\end{aligned}$$

AI guidance is visually isolated in dedicated containers with explicit badges (`AI STYLING GUIDANCE`), preventing users from mistaking algorithmic suggestions for physical product specifications.

---

### 7. AI Home Modules & Capabilities (Sections 12.6 – 12.8)

* **Hero Module (`AIHero`):** Communicates concrete platform capabilities without vague claims or false certainty:
  > *"Discover fashion. Find products. Build looks. Understand recommendations."*
* **Natural Language Composer (`AIPromptInput`):** Touch-friendly input with curated prompt chips (*"Find relaxed summer outfits under ₹3,000"*, *"How would I style an oversized selvedge denim jacket?"*).
* **Suggested Tasks Grid:** Direct shortcuts to dedicated assistants (`AI03 Product Assistant`, `AI04 Style Assistant`, `AI05 Outfit Ideas`, `AI06 Fashion Search`).
* **Recent Sessions Module:** Resumable conversation history with message counts.
* **Curated Recommendations Rail:** Live recommendations displaying qualitative confidence badges.

---

### 8. Multi-Turn Conversational Fashion Assistant (Sections 12.9 – 12.11)

The conversation interface (`AI02`) is structured around deterministic, inspectable message objects:
* **`UserMessage`:** High-contrast dark bubbles clearly labeled with `YOU`.
* **`AIMessage`:** Clean light-surface bubbles labeled with `AI FASHION ASSISTANT`.
* **Citations Rail (`AICitationContract`):** Backed by verified catalog records and fabric guides.
* **Action Buttons (`AIActionContract`):** Explicit next steps (*"Refine Style"*, *"Open Outfit Studio"*, *"View Look"*).

---

### 9. Transparent AI Context System (Sections 12.12 & 12.13)

AI responses visibly declare active contextual parameters:
$$\text{ActiveContext} = \{\text{Destination: Coastal}, \text{Season: Summer}, \text{Style: Streetwear}, \text{Region: India}\}$$

* **Tappable Context Chips (`AIContextChips`):** Displayed prominently at the top of the session.
* **User Control:** Users can remove individual context items (tapping `×`) or edit context parameters directly.

---

### 10. AI Product Assistant Canvas (Sections 12.15 – 12.17)

Screen `AI03` is focused entirely on a single catalog garment:
1. **Catalog Truth Summary:** Table of verified facts (`Price`, `Availability`, `Material`, `Fit`, `Origin`).
2. **Styling Advice:** Dropped-shoulder silhouette balance, color pairing rules, and drape notes.
3. **Frequently Asked Questions:** One-tap inquiry chips (*"How does this jacket fit across shoulders?"*, *"What color trousers pair best?"*).
4. **Styled Ensembles Rail:** Looks featuring the garment.
5. **Similar Catalog Pieces Rail:** Alternative products in the same aesthetic tier.

---

### 11. AI Style Assistant (Sections 12.18 & 12.19)

Screen `AI04` guides users toward cohesive aesthetic themes:
* **Recommended Direction:** Hero card presenting the style taxonomy (`Contemporary Streetwear`, `Minimalist`, `Heritage Workwear`).
* **Why It Fits:** Explainable matching breakdown (silhouette harmony, versatility, climate suitability).
* **Cross-Subsystem Studio Bridge:** High-contrast button linking directly into the Outfit Builder (`ST02`).

---

### 12. AI Outfit Recommendations & User Control (Sections 12.20 & 12.21)

Screen `AI05` presents complete ensembles with user control guarantees:
* **`can_edit = True`:** Recommended outfits are never locked; users can swap any item, adjust variants, or replace layers.
* **Constituent Garments Breakdown:** Direct inspectable list of top, bottom, outerwear, and footwear pieces.
* **Alternative Looks Rail:** Multiple alternative styling directions for the same context.
* **Sticky Bottom Bar:** Independent triggers for `Edit Outfit`, `Save Look`, and `Shop Pieces`.

---

### 13. Natural Language AI Search & Intent Extraction (Sections 12.27 – 12.31)

Screen `AI06` transforms conversational natural language queries into structured searches:
$$\text{"Find relaxed summer outfits under ₹3,000"} \implies \begin{cases} \text{Interpreted Style:} & \text{Relaxed / Streetwear} \\ \text{Interpreted Context:} & \text{Summer} \\ \text{Interpreted Budget:} & \text{Under ₹3,000} \end{cases}$$

* **Observable Steps:** Granular progress indicators (`Understanding query ✓`, `Extracting constraints ✓`, `Searching catalog ✓`).
* **Direct Result Card:** Reuses standard catalog product cards with a dedicated `Why this result?` trigger.

---

### 14. AI Result Explanation & Factor Transparency (Sections 12.32 – 12.34)

Screen `AI08` provides explainability without confusing technical jargon:
* **Primary Reason:** Concise 1-sentence explanation (*"Matches your explored preference for relaxed silhouettes and monsoon-resistant fabrics."*).
* **Detailed Narrative:** In-depth styling logic explaining proportions, color palette, and drape.
* **Verified Contributing Factors:** Green checkmark list of factual contributors (`Style Direction`, `Climate Suitability`, `Palette Harmony`).
* **Context Applied:** List of active constraints used in the recommendation.

---

### 15. Qualitative Confidence Presentation (Section 12.26)

FashXStudio explicitly rejects deceptive numerical certainty (e.g. *"98.4% match"*). Instead, the system uses qualitative match confidence levels:

$$\text{AIConfidenceLevel} \in \{\mathbf{STRONG},\, \mathbf{POSSIBLE},\, \mathbf{LIMITED}\}$$

* **`STRONG`:** All primary factors (style, climate, silhouette, budget) match verified user preferences.
* **`POSSIBLE`:** Matches core aesthetic but differs in secondary factors (e.g. brand or price tier).
* **`LIMITED`:** Exploratory suggestion based on tangential style associations.

---

### 16. Multi-Tier User Feedback Engine (Sections 12.37 & 12.38)

Users evaluate recommendations via `AIFeedbackModal`:
* **Sentiment:** `Helpful` (👍) vs `Not Helpful` (👎).
* **Structured Rationale:**
  * `Wrong Style Direction`
  * `Irrelevant Product`
  * `Too Expensive`
  * `Already Own Similar`
  * `Other`
* **Safety Boundary:** Submitting feedback tunes future recommendation weights without unexpectedly deleting or altering user profile preferences.

---

### 17. AI Preferences & Personalization Controls (Sections 12.35 & 12.36)

Screen `AI09` provides full user governance over AI behavior:
* **Aesthetic Multi-Chip Selectors:** `Minimalist`, `Streetwear`, `Heritage Workwear`, `Formal Tailored`, `Casual Relaxed`.
* **Occasion Contexts:** `Casual Everyday`, `Summer Travel`, `Evening Dinner`, `Office Professional`.
* **Budget Tier:** `budget`, `medium`, `premium`, `luxury`.
* **Privacy Switches:** `Allow AI Personalization` and `Automatic Outfit Suggestions`.

---

### 18. Cross-System Architectural Bridges (Sections 12.50 – 12.55)

The AI subsystem seamlessly interconnects all prior visual subsystems:

1. **AI $\longrightarrow$ Product Detail (VD-09):** Inquiring about a piece seamlessly transitions to the official product canvas.
2. **AI $\longrightarrow$ Outfit Builder (VD-10):** Recommended ensembles transfer into the Outfit Studio canvas for slot editing.
3. **AI $\longrightarrow$ Shopping Cart (VD-07):** Recommended pieces transfer directly into the commerce cart with variant selection.
4. **AI $\longrightarrow$ Discovery Search (VD-08):** AI Search links into faceted category exploration and filter rails.
5. **AI $\longrightarrow$ Regional Geography (VD-11):** Geographic context chips bridge into regional city and textile maps.

---

### 19. Mobile TypeScript Component & Template Architecture

Located under `mobile/features/visual/ai/`:

```
mobile/features/visual/ai/
├── types.ts                                  # Complete TypeScript interfaces mirroring Pydantic v2
├── components/
│   ├── AIHero.tsx                            # Visual header communicating capabilities clearly
│   ├── AIPromptInput.tsx                     # Natural language composer with quick prompt chips
│   ├── AIMessageView.tsx                     # Chat message renderer with citations and actions
│   ├── AIContextChips.tsx                    # Active context tags with remove and edit triggers
│   ├── AIRecommendationCard.tsx              # Recommendation card with confidence badges
│   ├── AIExplanationCard.tsx                 # Structured reasoning card with verified factors
│   └── AIFeedbackModal.tsx                   # User evaluation modal with structured reasons
├── templates/
│   ├── AIHomeTemplate.tsx                    # AI01: AI Home central intelligence entry point
│   ├── AIAssistantTemplate.tsx               # AI02: Multi-turn conversational fashion assistant
│   ├── AIProductAssistantTemplate.tsx        # AI03: Product-specific Q&A canvas
│   ├── AIStyleAssistantTemplate.tsx          # AI04: Aesthetic recommendation canvas
│   ├── AIOutfitRecommendationTemplate.tsx    # AI05: AI outfit recommendation with user editing
│   ├── AISearchTemplate.tsx                  # AI06: Natural language query search canvas
│   ├── AIRecommendationDetailTemplate.tsx    # AI07: Recommendation deep dive canvas
│   ├── AIExplanationTemplate.tsx             # AI08: Dedicated result explanation canvas
│   └── AIPreferencesTemplate.tsx             # AI09: AI tuning preferences control canvas
└── index.ts                                 # Public module barrel export
```

---

### 20. Verification, Automated Test Metrics & Completion Gate

```powershell
pytest tests/unit/test_visual_ai.py tests/integration/test_visual_ai_router.py -v
============================= 62 passed in 4.38s ==============================

pytest -q
=========================== 1089 passed in 15.58s ============================
```

* **Unit Tests (`tests/unit/test_visual_ai.py` — 44 tests):**
  * `AI-001`–`AI-005`: AI Home specifications, hero claims, tasks, and sessions.
  * `AI-010`–`AI-017`: Conversation sessions, citations, explicit actions, and ordering.
  * `AI-020`–`AI-023`: Context items, active context preservation, and explanation linkage.
  * `AI-030`–`AI-036`: Recommendations, verified factors, qualitative confidence, and feedback.
  * `AI-040`–`AI-046`: AI Search intent extraction and observable progress steps.
  * `AI-050`–`AI-055`: Product Assistant and Section 12.16 Product Fact Boundary.
  * `AI-060`–`AI-066`: Style & Outfit recommendations with user edit controls.
  * `FORBID-001`–`FORBID-008`: Strict `extra="forbid"` rejection on unauthorized fields (Rule I02).
* **Integration Tests (`tests/integration/test_visual_ai_router.py` — 18 tests):**
  * All 14 REST endpoints under `/api/v1/visual/ai/*`.
  * 5 Cross-System Integration Flows:
    1. AI Product Assistant $\to$ Shopping Product Detail (`AI03` $\to$ VD-07 Product).
    2. AI Outfit Recommendation $\to$ Outfit Builder Studio (`AI05` $\to$ VD-10 Styling).
    3. AI Recommendation $\to$ Commerce Shopping Cart Handoff (`AI07` $\to$ VD-07 Cart).
    4. AI Search $\to$ Discovery Faceted Search (`AI06` $\to$ VD-08 Discovery).
    5. AI Session Context $\to$ Regional Geography Profile (`AI02` $\to$ VD-11 Geography).
* **Total Project Tests:** **1089 passed (100% green, 0 failures, 0 regressions)**.

```
==============================================================================
FASHXSTUDIO VISUAL DESIGN — PHASE 12: COMPLETION GATE
==============================================================================
[✓] AI01 - AI09 Intelligence Screen Contracts & Templates                    LOCKED
[✓] AI Trust Architecture & Information Classification Boundary              LOCKED
[✓] Section 12.16 Product Fact Boundary (Catalog Facts vs AI Guidance)        LOCKED
[✓] Multi-Turn Conversation & Session Architecture with Citations            LOCKED
[✓] Transparent Context System with User Removal & Editing Controls          LOCKED
[✓] Natural Language AI Search with Style, Context, and Budget Extraction    LOCKED
[✓] Qualitative Match Confidence Presentation (Strong, Possible, Limited)     LOCKED
[✓] Multi-Tier User Feedback Engine (Helpful, Not Helpful + Reasons)         LOCKED
[✓] AI Preferences & Privacy Governance Switches                             LOCKED
[✓] Cross-System Bridges (AI -> Product, Styling, Cart, Discovery, Maps)      LOCKED
[✓] Mobile TypeScript UI Components & Templates (React Native / Expo SDK 57)  LOCKED
[✓] FastAPI REST Endpoints (/visual/ai/*)                                    LOCKED
[✓] Pydantic v2 BaseContractModel Schemas (extra="forbid" everywhere)         LOCKED
[✓] Automated Tests (62 new tests, 1089 / 1089 total passing)                 PASSED
==============================================================================
STATUS: PHASE 12 (AI / INTELLIGENCE SCREENS & INTERACTION SYSTEM) COMPLETED & VERIFIED
==============================================================================
```
