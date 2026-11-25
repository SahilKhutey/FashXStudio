# Privacy & Consent Boundaries for Quality Feedback

> **Data protection, DPDP/GDPR alignment, and retention boundaries.**

## 1. Feedback Reporting vs. Model Training
Submitting a problem report does **NOT** grant FashXStudio permission to use a shopper's photograph for model training:

| Activity | User Authorization Required | Storage / Access Scope |
|---|---|---|
| **Store Report Metadata** | Basic service usage terms | Encrypted metadata in database |
| **Inspect Image for Defect** | Explicit `include_in_quality_review=true` | Access-controlled triage bucket |
| **Add to Benchmark Regression** | Explicit quality evaluation consent | Isolated internal test suite |
| **Use for Model Training** | **SEPARATE EXPLICIT CONSENT** | **PROHIBITED** without consent |

## 2. Retention Rules
- If `include_in_quality_review` is `false`, the review service records only structured metadata (reason code, timestamp, provider ID) and does NOT retain shopper photos in review queues.
- Image artifacts in the review pipeline are automatically expired after 30 days unless explicitly quarantined for high-severity defect resolution.
