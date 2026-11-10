# FashXStudio — Complete KPI & Metric Definitions

**Document ID:** `FASHX-KPI-001`  
**Version:** `1.0 — Execution Baseline`  
**Date:** `10 November 2026`  
**Status:** `Proposed Baseline — Not Yet Measured`  
**Scope:** `Phase 01.4 — Product & Engineering Measurement Framework`  

---

## 1. Measurement Architecture & Principles

FashXStudio defines strict mathematical definitions, explicit denominators, and server-confirmed events for every key performance indicator across five categories:
1. **Acquisition & Onboarding:** Can shoppers enter and set up the product?
2. **Discovery & Engagement:** Can shoppers find products and interact meaningfully?
3. **Virtual Try-On Experience:** Does the AI pipeline produce realistic, prompt, and reliable results?
4. **Retention & Commerce Intent:** Do users return and demonstrate outbound purchase intent?
5. **Merchant & Unit Economics:** Can merchants activate successfully and can we serve VTO sustainably?

### Core Measurement Units & Distinct Denominators
To avoid misleading metrics, the following units are **never** combined in the same denominator:
- **Shopper:** A unique, registered individual identity (`user_id`).
- **Session:** A continuous interaction session bounded by 30 minutes of user inactivity (`session_id`).
- **Product Impression:** A product card rendered within the device's visible viewport for $\ge 1.0$ second (`impression_id`).
- **VTO Attempt:** A single execution of the try-on pipeline, including retries (`vto_attempt_id`).
- **VTO Job:** A logical user request to try on a specific garment, which may contain 1 or more attempts (`vto_job_id`).
- **Successful VTO:** A completed job returning a valid, non-corrupted, accessible result image.
- **Saved Look:** A persisted record linking a user, product, variant, and VTO result asset.
- **Merchant:** A verified business organization tenant (`merchant_id`).
- **Merchant Activation:** A merchant completing legal agreements, permission grants, catalog ingestion, and publishing $\ge 1$ live product.

### Core Measurement Principles
1. **Server-Confirmed Authority:** Successful actions are logged from backend database commits, never solely client-side optimistic UI clicks.
2. **Strict UTC Timestamps:** All events record microsecond-precision UTC timestamps (`occurred_at`); client displays format to local Indian Standard Time (IST).
3. **Synthetic / Test Isolation:** All automated end-to-end tests, internal developer runs, and synthetic load tests emit `is_internal: true` and are strictly excluded from production metrics.
4. **Failure Preservation:** Failed requests and timeouts are preserved with explicit error categories rather than dropped.
5. **Privacy Safeguard:** Telemetry payloads never contain raw biometric images, full names, emails, phone numbers, or exact body measurements.

---

## 2. Complete Metric Specifications (1.4.1 – 1.4.14)

### 1.4.1: Registration Completion Rate
- **Purpose:** Measure onboarding friction from initial signup intent to an authenticated account.
- **Formula:**
  $$\text{Registration Completion Rate} = \frac{\text{Unique Users with } \texttt{registration\_completed}}{\text{Unique Users with } \texttt{registration\_started}} \times 100$$
- **Start Event:** `registration_started` (`session_id`, `acquisition_source`)
- **Success Event:** `registration_completed` (`user_id`, `auth_provider`)
- **Failure Events:** `registration_failed`, `verification_failed` (`error_code`)
- **Measurement Window:** Same session; secondary report within 24 hours.
- **Initial Target Hypothesis:** $\ge 70\%$.

### 1.4.2: Profile Completion Rate
- **Purpose:** Measure the percentage of authenticated shoppers who complete the minimum viable profile (MVP) needed for personalized discovery.
- **Minimum Viable Profile Definition:** Preferred style archetype(s), tops/kurtas size range, and DPDP consent grant. (Height and weight remain optional).
- **Formula:**
  $$\text{Profile Completion Rate} = \frac{\text{Unique Users with } \texttt{profile\_completed}}{\text{Unique Users with } \texttt{profile\_setup\_started}} \times 100$$
- **Start Event:** `profile_setup_started` (`user_id`)
- **Success Event:** `profile_completed` (`user_id`, `completion_score`, `has_optional_measurements`)
- **Measurement Window:** Same session and within 24 hours.
- **Initial Target Hypothesis:** $\ge 65\%$.

### 1.4.3: Product Discovery Success Rate
- **Purpose:** Measure whether shoppers actively find and engage with relevant, VTO-eligible garments.
- **Definition:** A discovery session where the shopper opens an eligible garment PDP and subsequently initiates VTO or saves the look.
- **Formula:**
  $$\text{Discovery Success Rate} = \frac{\text{Sessions with (}\texttt{vto\_started} \lor \texttt{look\_saved}\text{)}}{\text{Total Sessions with } \ge 1 \text{ } \texttt{product\_viewed}} \times 100$$
- **Start Event:** `discovery_session_started`
- **Qualifying Actions:** `vto_started`, `look_saved`
- **Measurement Window:** Within the same session.
- **Initial Target Hypothesis:** $\ge 30\%$.

### 1.4.4: VTO Job Success Rate (Core Technical KPI)
- **Purpose:** Measure the end-to-end technical reliability of the AI try-on pipeline.
- **Criteria for Success:** Request accepted, input validation passed, GPU inference completed, quality check cleared, and result stored securely in S3.
- **Formula:**
  $$\text{VTO Job Success Rate} = \frac{\text{Count of VTO Jobs with terminal state } \texttt{completed}}{\text{Total VTO Jobs with state } \texttt{queued}} \times 100$$
- **Terminal States:** `completed` (Success), `failed` (Error), `cancelled` (Aborted), `expired` (TTL Purged).
- **Reporting Split:** First-attempt success rate vs. eventual success rate after permitted single retry.
- **Initial Target Hypothesis:** $\ge 90\%$.

### 1.4.5: VTO Completion Time (Latency P95)
- **Purpose:** Quantify the total duration a shopper waits between submitting an image and viewing the try-on result.
- **Formula:**
  $$T_{\text{VTO}} = T_{\text{result\_available}} - T_{\text{job\_accepted}}$$
- **Decomposition:**
  $$T_{\text{total}} = T_{\text{queue}} + T_{\text{preprocess}} + T_{\text{provider}} + T_{\text{postprocess}} + T_{\text{storage}}$$
- **Measurement:** Server-side microsecond timestamps recorded in `vto_jobs`.
- **Initial Target Hypothesis:** P95 latency $< 45$ seconds (Median target $< 20$ seconds).

### 1.4.6: Visual Realism Rating
- **Purpose:** Determine whether synthesized images appear photorealistic to human observers.
- **Human Review Question:** *"How realistic does the generated try-on look compared with an actual photograph?"* (1 = Very unrealistic, 5 = Highly realistic).
- **Formula:**
  $$\text{Average Realism Score} = \frac{\sum \text{Valid Realism Scores}}{\text{Count of Valid Reviews}}$$
  $$\text{Positive Realism Rate} = \frac{\text{Reviews with Score } \ge 4}{\text{Total Valid Reviews}} \times 100$$
- **Initial Target Hypothesis:** Average score $\ge 3.8 / 5.0$ (Positive rate $\ge 70\%$).

### 1.4.7: Garment Preservation Rating
- **Purpose:** Measure visual fidelity of the synthesized garment against the original merchant product.
- **Evaluated Dimensions:** Color accuracy, print/pattern fidelity, collar/neckline shape, sleeve length, garment silhouette, logos/branding, and fabric texture appearance.
- **Scale:** 1 = Major alteration/unrecognizable, 5 = Highly faithful reproduction.
- **Formula:**
  $$\text{Average Garment Preservation Score} = \frac{\sum \text{Preservation Scores}}{\text{Count of Valid Reviews}}$$
- **Initial Target Hypothesis:** Average score $\ge 3.8 / 5.0$.

### 1.4.8: Image Failure Rates
- **Purpose:** Differentiate user-input photo issues from infrastructure/AI provider failures.
- **Formula A (Input Rejection Rate):**
  $$\text{Input Rejection Rate} = \frac{\text{Uploads rejected by validation (lighting, multi-person, pose)}}{\text{Total uploaded image assets}} \times 100$$
- **Formula B (Pipeline Failure Rate):**
  $$\text{Pipeline Image Failure Rate} = \frac{\text{Queued jobs failing due to segmentation, GPU timeout, or corruption}}{\text{Total accepted VTO jobs}} \times 100$$
- **Initial Target Hypothesis:** Pipeline Image Failure Rate $\le 5\%$. (Input rejection observed without hard threshold initially).

### 1.4.9: Product Click-Through Rate (CTR)
- **Purpose:** Measure the visual attractiveness of catalog presentation.
- **Formula:**
  $$\text{Product CTR} = \frac{\text{Unique } \texttt{product\_clicked} \text{ events}}{\text{Unique } \texttt{product\_impression} \text{ events}} \times 100$$
- **Impression Criteria:** Garment card visible $\ge 1.0$s with $> 50\%$ card area in viewport.
- **Initial Target Hypothesis:** $\ge 10\%$.

### 1.4.10: Saved-Look Rate
- **Purpose:** Measure post-try-on satisfaction and digital wardrobe curation.
- **Formula:**
  $$\text{Saved-Look Rate} = \frac{\text{Unique Shoppers with } \ge 1 \text{ } \texttt{look\_saved}}{\text{Unique Shoppers receiving } \ge 1 \text{ } \texttt{vto\_completed}} \times 100$$
- **Initial Target Hypothesis:** $\ge 20\%$.

### 1.4.11: Shopper Cohort Retention (D7 & D30)
- **Purpose:** Measure repeat engagement over a 7-day and 30-day window.
- **Qualifying Activity:** Logging in and viewing a product, running a try-on, or viewing saved wardrobe looks.
- **Formula (D7):**
  $$\text{D7 Retention} = \frac{\text{Users active between Day 7 and Day 13 post-signup}}{\text{Total eligible signups in cohort}} \times 100$$
- **Initial Directional Hypothesis:** D7: 15–25%; D30: 8–15% (Observational metric for pilot).

### 1.4.12: Merchant Activation Rate
- **Purpose:** Quantify B2B onboarding efficiency.
- **Definition:** Merchant signs agreement, grants data/image permissions, connects catalog feed, passes product validation, and publishes $\ge 50$ live SKUs.
- **Formula:**
  $$\text{Merchant Activation Rate} = \frac{\text{Merchants with status } \texttt{ACTIVE\_PUBLISHED}}{\text{Merchants initiating registration}} \times 100$$
- **Pilot Target:** Exactly 1 real D2C merchant activated.

### 1.4.13: Merchant Dashboard Engagement
- **Purpose:** Verify whether the merchant interacts with provided funnel analytics.
- **Qualifying Actions:** Viewing product catalog health, inspecting try-on counts, or exporting conversion reports.
- **Pilot Target:** 1 active weekly session during the 4-week pilot.

### 1.4.14: Cost Per Successful Try-On (Unit Economics)
- **Purpose:** Verify commercial viability and gross margin sustainability.
- **Direct Variable Cost Formula:**
  $$C_{\text{VTO}} = C_{\text{provider}} + C_{\text{storage}} + C_{\text{compute}} + C_{\text{infrastructure}}$$
- **Fully Loaded Pilot Cost Formula:**
  $$C_{\text{loaded}} = \frac{\text{Direct Costs} + \text{Attributable Fixed Cloud \& Monitoring Costs}}{\text{Total Completed VTO Jobs}}$$
- **Initial Target Hypothesis:** Direct variable cost $C_{\text{VTO}} \le ₹12.00$ per generation (Target gross margin $\ge 65\%$).
