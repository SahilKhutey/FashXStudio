# Dataset Governance, Consent & Retention

## 1. Principles of Evaluation Data Governance

The Virtual Try-On (VTO) evaluation benchmark relies on real human portraits and authentic apparel imagery.

**Non-Negotiable Governance Invariants**:
1. **Consent Specificity**: General consent to use a photo in a customer VTO session does **not** grant permission to store that photo in a research benchmark dataset or distribute it to third-party human evaluators.
2. **Explicit Reviewer Permission**: Participants must explicitly consent to human evaluation review.
3. **Traceable Permissions**: Every image pair in the evaluation manifest must cite a verifiable `permission_record_id`.
4. **Zero Training Without Separate Authorization**: Evaluation photographs must **never** be used for model training or fine-tuning without explicit, standalone training consent.
5. **Immediate Propagation of Withdrawal**: If a participant revokes consent or requests account deletion under GDPR/CCPA, their assets are immediately quarantined, blocked from all active evaluation runs, and scheduled for permanent purge.

---

## 2. Participant Consent Model

For every participating individual in the benchmark dataset, the system records:

| Field | Description |
|---|---|
| `participant_id` | Opaque, pseudonymous UUID (e.g. `participant-pseudo-001`). No real names or contact details. |
| `consent_version` | Active version of the VTO Evaluation Informed Consent agreement. |
| `consented_at` | UTC timestamp of consent acquisition. |
| `approved_purposes` | Array of authorized activities: `[AI_PROCESSING, HUMAN_EVALUATION, RETENTION, BENCHMARK_REPORTING]`. |
| `third_party_processor` | Named provider cleared for inference (e.g. `fashn`). |
| `retention_period_days` | Approved retention lifespan (default: 180 days). |
| `revocation_status` | `ACTIVE`, `WITHDRAWN`, or `PURGED`. |

---

## 3. Merchant Garment Permissions

Catalog garment photos are intellectual property. Prior to inclusion in the benchmark:
- The merchant's catalog authorization record (`CatalogSourcePermission`) must confirm derivative AI rendering rights (`AI_PROCESSING_ALLOWED`).
- Images under active takedown notices (`TakedownStatus.ACCEPTED`) or delisted offers are immediately purged from evaluation candidate pairs.
