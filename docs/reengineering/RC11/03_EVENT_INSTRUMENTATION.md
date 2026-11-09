# RC11: Event Instrumentation & Telemetry

## 1. Analytics Architecture
RC11 builds upon the existing versioned event contract defined in [`backend/fashx/api/v1/analytics.py`](file:///c:/Users/ASUS/Documents/FashXStudio/backend/fashx/api/v1/analytics.py), extending `ProductJourneyEvent` and `SessionEventType`.

## 2. Pilot Event Taxonomy
| Event Name | Trigger Point | Required Attributes |
| :--- | :--- | :--- |
| `pilot_invite_accepted` | Invite code redeemed | `cohort_id`, `app_version` |
| `consent_started` | Privacy/consent screen rendered | `consent_version` |
| `consent_accepted` | Explicit consent confirmed | `consent_version`, `timestamp` |
| `consent_declined` | Consent declined | `consent_version` |
| `photo_quality_accepted` | Upload passes quality validation | `mode` (no image bytes) |
| `onboarding_completed` | Profile setup finished | `app_version` |
| `feed_viewed` | Personalized feed loaded | `ranker_version` |
| `garment_opened` | Product detail viewed | `garment_id` |
| `tryon_submitted` | VTO request dispatched | `tryon_job_id`, `provider` |
| `tryon_completed` | VTO output ready | `tryon_job_id`, `duration_ms` |
| `tryon_failed` | VTO job fails or times out | `tryon_job_id`, `error_code` |
| `tryon_result_rated` | Visual realism rating submitted | `tryon_job_id`, `rating` (1–5) |
| `garment_saved` | Item added to closet | `garment_id` |
| `retailer_opened` | "Buy on Store" clicked | `merchant_id`, `garment_id` |
| `feedback_submitted` | Survey questionnaire submitted | `survey_version` |
| `pilot_withdrawn` | User requests pilot exit | `timestamp` (no reason text) |

## 3. Telemetry Privacy Invariants
1. **Zero Personal Data in Payloads**:
   Events must not contain names, email addresses, phone numbers, raw body photos, facial crops, skin-tone hex codes, or exact measurements.
2. **Server-Side Attribution**:
   `cohort_id` (`Alpha`, `Wave1`, `Wave2`), `ranker_version`, and `app_version` are validated server-side by authenticated session tokens—never trusted from arbitrary client headers.
3. **Idempotency & Deduplication**:
   Events enforce unique `event_id` UUID primary keys to eliminate duplicate telemetry under erratic mobile network retries.
4. **Time Invariant**:
   All timestamps are ISO-8601 UTC validated against server clock skew limits.
