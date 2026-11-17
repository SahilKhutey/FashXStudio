# FashXStudio — Screen-by-Screen Interaction & State Specifications

**Document ID:** `FASHX-UX-001`  
**Version:** `1.0 — Execution Baseline`  
**Date:** `10 November 2026`  
**Scope:** `Phase 01.2 — UI/UX Error, Loading, Empty & Retry Contracts`  

---

## 1. Interaction Principles & Non-Negotiable UX Rules

1. **Deterministic State Modeling:** Every screen must implement four mutually exclusive states: `Loading`, `Empty`, `Failure`, and `Success/Populated`.
2. **Network Timeout Idempotency Rule:** If a client request times out during a state-changing operation (submitting a VTO job, creating a catalog import, saving a look), the UI **must not assume the operation failed**. The client must first check the status of the resource using its client-generated `idempotency_key`. A duplicate tap must never create double jobs or duplicate records.
3. **Transparent Progress:** When awaiting asynchronous ML inference, the UI displays real backend state milestones (`queued`, `preprocessing`, `processing`, `postprocessing`), not fabricated timer percentages.

---

## 2. Merchant Portal Screen State Matrix

| Screen Title | Loading State | Empty State | Failure / Error State | User Recovery & Retry Action |
| :--- | :--- | :--- | :--- | :--- |
| **M02: Registration** | Primary button spinner; fields disabled. | Clean input fields with inline validation hints. | Email/phone already registered; invalid domain. | Suggest login if existing; highlight invalid fields. |
| **M04: Business Profile** | Inline skeleton loaders across form fields. | Blank profile form prompting GSTIN & brand URL. | Verification API unreachable; invalid GST format. | Displays error toast; preserves entered text for resubmission. |
| **M05: Verification** | File upload progress bar with byte counts. | Upload dropzone prompting GST/Trademark PDF. | Unsupported MIME type; file exceeds 10 MB limit. | Rejects file instantly with red border; prompts valid PDF/JPG. |
| **M07–M08: Permissions** | Skeleton toggles with disabled checkboxes. | All permission scopes unchecked with warning banner.| Database commit error while saving permission grant. | Reverts toggle to prior state; shows "Failed to update, tap to retry". |
| **M09: Catalog Connect** | "Testing connection..." pulse animation. | Grid of supported connectors (Shopify, Feed, CSV). | Bad API key; feed URL returns HTTP 403 or 404. | Inline banner with exact error reason; allows editing credentials. |
| **M10: Import Config** | Fetching remote catalog schema columns. | Mapping table empty; "Select remote columns". | Missing required field mapping (SKU or Title unmapped).| Highlights unmapped required columns in red. |
| **M11: Import Status** | Live status polling spinner with item counter. | No active imports; shows "Start your first import". | Ingest worker timed out; feed parsing error. | Shows parsed error log with download link; button "Retry Failed Items". |
| **M12: Product Review** | Shimmer skeleton table rows. | "No products imported yet. Connect a catalog." | Server error fetching product records. | "Retry Fetch" button with exponential backoff. |
| **M13: Product Editor** | Saving indicator on top-right action button. | "Select a product to view and edit details." | Validation failure (e.g. invalid size format). | Field-level error message highlighting exact requirement. |
| **M14: Publish Review** | "Publishing products..." modal spinner. | "No approved products ready for publication." | Publication gate failed (missing image rights or SKU). | Displays blocked SKUs with direct links to resolve issues. |
| **M15: Live Analytics** | Shimmer charts and metric card skeletons. | "No data yet. Activity will appear once shoppers try items."| Analytics query timeout. | Date-picker dropdown with option to reload data. |

---

## 3. Consumer Mobile App Screen State Matrix

| Screen Title | Loading State | Empty State | Failure / Error State | User Recovery & Retry Action |
| :--- | :--- | :--- | :--- | :--- |
| **S01: Welcome / Splash** | Pulsing brand icon and animated gradient. | N/A (Static welcoming screen). | Network unreachable on app boot. | "Unable to connect. Tap to retry" with offline cache fallback. |
| **S02: Registration** | Button spinner; inputs locked. | Clean email/phone inputs with country code selector. | Phone number format error; rate-limited SMS. | Shows countdown timer before requesting next OTP. |
| **S03: OTP Verification**| Auto-submitting spinner on 6th digit entered. | 6 empty digit boxes with active cursor. | Invalid code; expired code challenge. | "Incorrect code. 2 attempts left." with "Resend Code" link. |
| **S04: DPDP Consent** | Shimmer placeholder for legal policy text. | Full policy loaded with unselected optional toggles.| Consent write API fails. | Shows toast "Unable to save preferences. Please check internet." |
| **S06: Body Profile** | Pulsing slider controls. | Form initialized with neutral defaults. | Out-of-bounds height/weight values entered. | Inline validation: "Height must be between 120 and 230 cm." |
| **S07: Style Profile** | Shimmer grid of style card tiles. | Category chips unselected. | Preferences sync error. | Saves locally to Zustand store; syncs in background. |
| **S09: Home Feed** | 6 shimmer skeleton product cards. | "No products match your selected styles." | Feed service HTTP 500 error. | "Pull to refresh" or "Reset filters to explore all garments". |
| **S10: Search & Filters** | Search input loading spinner. | "No matches found for '[query]'. Try different keywords."| Elastic/trigram search timeout. | Suggests popular categories (e.g., "Men's Kurtas", "Oversized Shirts").|
| **S11: Product Detail** | Full PDP skeleton shimmer. | "Item no longer available from merchant." | Failed to load product details. | "Return to Feed" button; preserves browse position. |
| **S12–S13: Photo Upload**| Upload percentage indicator with cancel button. | Camera viewfinder / gallery selection prompt. | File corrupted; camera permission denied. | Deep-link button: "Open Device Settings to Enable Camera". |
| **S14: Photo Validation**| Pulse scanline animation over uploaded photo. | Prompt: "Ensure photo shows full torso in good light." | Multiple people detected; severe occlusion. | Actionable guidance: "Single person required. Tap to retake." |
| **S15: VTO Submission** | "Initializing try-on engine..." spinner. | N/A (Transition screen). | Daily quota exceeded (5/5). | "Daily try-on limit reached. Quota resets at 12:00 AM IST." |
| **S16: VTO Progress** | Real-time status cards (`queued` ➔ `processing`).| N/A (Shows active job ID). | Worker timeout after 30 seconds. | "Processing took longer than expected. Tap to check result." |
| **S17: VTO Result** | High-res image progressive blur-up. | N/A (Renders synthesized result). | Failed to load generated image asset. | "Retry image download" using refreshed presigned S3 URL. |
| **S18: Save Look** | Heart icon bouncing loading animation. | N/A (Direct action). | Storage conflict or duplicate save. | Toast: "Look already saved in your wardrobe!" |
| **S19: Merchant Handoff**| "Redirecting to official brand store..." overlay. | N/A (Navigation transition). | Merchant product URL broken/unverified domain. | Fallback modal: "Store temporarily unavailable. Try again later." |
| **S20: Wardrobe** | Shimmer grid of saved outfits. | "Your wardrobe is empty. Try on clothes to save looks!" | Failed to fetch saved looks. | Pull-down refresh gesture; cached offline looks displayed. |
