# Code Review Checklist

**Status:** Adopted
**Version:** 1.0
**Effective Date:** 2026-11-11
**Category:** Engineering Governance

---

## 1. Purpose and Philosophy

Code review in FashXStudio is a rigorous quality and safety gate. Reviews ensure correctness, architectural integrity, data privacy, security boundary enforcement, and maintainability.

Code reviews are collaborative, objective, and evidence-driven. Reviewers verify both the diff and the automated test evidence.

---

## 2. Reviewer Checklist (15 Dimensions)

Reviewers must inspect each pull request across the following 15 engineering categories:

| Category | Review Questions & Verification Criteria |
|---|---|
| **1. Correctness** | Does the implementation satisfy the stated product requirements and PRD? Are edge cases, null states, and boundary conditions handled properly? |
| **2. Architecture** | Are domain logic, application use cases, and infrastructure adapters cleanly separated? Are boundaries between modules preserved without leaky abstractions? |
| **3. Reuse** | Does the change leverage existing repository utilities, storage adapters, or core helpers instead of duplicating logic? |
| **4. API Contract** | Do new or modified endpoints adhere to the `/api/v1` URI prefix, standard error envelopes, and consistent snake_case schema conventions? |
| **5. Authentication** | Is every protected route guarded with valid JWT/JWKS authentication dependencies? Are public endpoints deliberately documented as such? |
| **6. Authorization** | Is resource ownership verified for every operation (`user_id == current_user.id`)? Are multi-tenant merchant boundaries strictly enforced? |
| **7. Privacy & Consent** | Is explicit user consent validated before processing photographs or biometric data? Are user erasure and deletion workflows honored across storage and database records? |
| **8. VTO Lifecycle** | Are provider timeouts, rate limits, failures, retries, and costs properly handled? Does the job status transition cleanly through its state machine? |
| **9. Catalog Integrity** | Are catalog source provenance, copyright/licensing permissions, and product deduplication rules maintained? |
| **10. Database & Migrations** | Is the Alembic migration non-destructive, backwards-compatible (expand-migrate-contract), and tested against PostgreSQL? Are locks avoided on large tables? |
| **11. Performance** | Are database queries indexed and free of N+1 patterns? Are image payloads, network requests, and async worker concurrency within acceptable thresholds? |
| **12. Logging & Redaction** | Are `request_id` and structured contextual fields present? Are all secrets, tokens, PII, and presigned URLs completely redacted? |
| **13. Test Coverage** | Are positive, negative, boundary, and failure scenarios covered? Are assertions meaningful rather than cosmetic? |
| **14. Mobile Experience** | Does the React Native/Expo UI handle loading spinners, network errors, offline states, and OS permission denials (camera, photo library)? |
| **15. Operations & Rollback** | Can this feature be disabled via an operational kill switch or feature flag? Is there an explicit rollback plan? |

---

## 3. Mandatory FashXStudio Security Checks

The following security assertions are non-negotiable and must be verified for any PR impacting auth, storage, profile, or VTO:

1. **Cross-User Photo Isolation:** A user must never be able to access, download, or inspect another user's uploaded photograph (`storage/` access strictly bounded by authenticated `user_id`).
2. **Cross-User VTO Isolation:** A user must never be able to view, query, or poll another user's generated try-on job or resulting imagery.
3. **Multi-Tenant Isolation:** Merchant A must never be able to read, update, or aggregate Merchant B's products, inventory, settings, or analytics.
4. **Enforced Consent Gate:** A VTO job must never be queued or submitted to a provider without active, verified user consent recorded in the database.
5. **Consent Revocation Enforcement:** When a user revokes consent or requests data deletion, cached jobs or stored reference images must immediately become inaccessible.
6. **Safe Redirects:** Product clickouts and affiliate redirects must strictly validate target URLs against an approved merchant domain allowlist.
7. **Complete Data Erasure:** When a user deletes their account, all associated photographs, fit profiles, measurements, and generated images must be deleted from object storage and purged from the database.
8. **No Secrets in Logs:** API keys, authorization tokens, bearer headers, passwords, and presigned URLs must never appear in application logs or Sentry breadcrumbs.

---

## 4. Reviewer Outcomes and Standards

Reviewers must submit one of three formal outcomes:

- **APPROVE:** All requirements and checklist items are verified, automated tests are green, and no material concerns remain.
- **REQUEST_CHANGES:** The PR contains defects, missing tests, security vulnerabilities, or violations of engineering standards. Clear, actionable remediation steps must be specified.
- **COMMENT:** General observations, non-blocking suggestions, or questions that do not block merging.

### Governance Constraints

- **No Self-Approval:** Authors may not approve their own pull requests.
- **Human Founder Merge Authority:** In accordance with repository rules (`AGENTS.md` Rule 12), pull requests are merged exclusively by the human founder on GitHub after all gates are verified green.
