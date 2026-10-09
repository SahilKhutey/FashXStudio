# Persistence Matrix (MVP)

_Source of truth for repository adapters and storage persistence across the 12 phases._  
_Audited in Step 4.1 ([phase4-persistence-audit.txt](../logs/phase4-persistence-audit.txt))._

Legend: **SQL** = SQLAlchemy repo on Postgres; **MEM** = stays in-memory (tests/frozen only).

| Domain | Port(s) | Table(s) | Exists? | Status now | Target | User data? | Erasure class | Notes |
|---|---|---|---|---|---|---|---|---|
| **Identity & Auth** | `IdentityRepo` | `auth_identities`, `users` | Yes (Phase 3) | SQL | SQL | Yes | Account | Mapped via `SqlIdentityRepo`, `User` + `AuthIdentity` |
| **Profile & Body** | `BodyProfileRepository`, `UserMeasurementRepository` | `body_profiles`, `user_measurements` | Yes | SQL | SQL | Yes | Biometric | `ProfileUnitOfWork`. Measurements & body profile erased on biometric revoke |
| **Preferences & Onboarding** | `UserPreferenceRepository`, `OnboardingProfileRepository` | `user_preferences`, `onboarding_profiles` | Yes | SQL | SQL | Yes | Account | Kept on biometric revoke; erased on account deletion |
| **Consent & Governance** | `UserConsentRepository` | `consent_records` | Yes | SQL | SQL | Yes | Account | Tracks `body_photo`, `measurements` grants |
| **Photos & Media Metadata** | `UserPhotoRepository`, `MediaRepository` | `user_photos`, `media_objects` (4C) | Yes (`user_photos`) / New (`media_objects`) | SQL | SQL | Yes | Biometric | Object keys only; hard-deleted and files purged from bucket on revoke |
| **Capture Quality & Calibration** | Calibration services | `user_photos.reject_reason`, `user_style_profiles` | Yes | SQL | SQL | Yes | Biometric | Output embedded in photo record and style profile |
| **Catalog (Merchants & Garments)** | `MerchantRepository`, `MerchantProductRepository`, `CanonicalGarmentRepository`, `MerchantOfferRepository`, `BrandRepository`, `SizeChartRepository` | `merchants`, `merchant_products`, `canonical_garments`, `merchant_offers`, `brands`, `size_charts`, `size_measurements` | Yes | SQL | SQL | No | None | `CatalogUnitOfWork`. Canonical dedup key enforces Rule I09 |
| **Enrichment & Embeddings** | `GarmentEnrichmentRepository` | `garment_enrichments` | Yes | SQL | SQL | No | None | Vector(512) pgvector embeddings for cosine similarity |
| **Discovery & Recommendations** | `RecommendationCandidateRepository`, feed exclusions | `feed_exclusions`, `canonical_garments` | Yes | SQL | SQL | Yes | Account | Exclusions tied to `user_id` |
| **Try-On Jobs & Artifacts** | `TryOnJobRepository`, `TryOnArtifactRepository` | `tryon_jobs`, `tryon_artifacts` | Yes | SQL | SQL | Yes | Biometric | `TryOnUnitOfWork`. Erased on revoke (Rule I16) |
| **Wardrobe (Closet)** | `WardrobeRepository` | `wardrobe_items` | Yes | SQL | SQL | Yes | Account | `CommerceWardrobeUnitOfWork`. Immutable price snapshots (Rule I11) |
| **Buy Clicks (Affiliate)** | `BuyClickRepository` | `buy_clicks` | Yes | SQL | SQL | Yes | Account | Attribution tokens & merchant redirects (Rule I12) |
| **Feedback (Fit & Try-on)** | `FitFeedbackRepository`, `TryOnFeedbackRepository` | `fit_feedback`, `tryon_feedback` | Yes | SQL | SQL | Yes | Account | Sizing bias aggregate ledger & tryon ratings |
| **Analytics Events** | `AnalyticsEventRepository`, `AnalyticsMetricRepository` | `domain_events` | Yes | SQL / MEM | SQL | Yes | Anonymize | `user_id` nulled/hashed upon account deletion |
| **Platform Plumbing (Outbox & Idempotency)** | `OutboxRepository`, `IdempotencyStore` | `outbox_messages`, `idempotency_keys` | New (4B) | MEM | SQL | No | None | Must survive restarts to prevent message loss / duplicate execution |
| **Fashion Taxonomy** | `TaxonomyRepository`, `ProductFashionRepository` | `brands` | Yes | MEM | SQL | No | None | Ingest taxonomy maps to canonical brands and garments |
| **Trends (C15)** | `TrendRepository`, `TrendObservationRepository` | None | No | MEM | MEM | No | None | Background aggregations, post-MVP |
| **Frozen Domains (C05-C11)** | Cart, Checkout, Fulfillment, Inventory, Order, Payments, Pricing, Promotions, Returns | None | No | MEM (frozen) | MEM | No | None | Excluded from MVP runtime behind `FASHX_ENABLE_FROZEN` |

---

### Scope Rules & Invariants
1. **MVP Persistence Guarantee:** All user-created, feed-read, and try-on resources MUST execute against SQLAlchemy AsyncSession on PostgreSQL.
2. **Platform Reliability:** Outbox messages and Idempotency keys MUST be SQL-persisted to guarantee restart survivability and exactly-once execution semantics.
3. **Storage Hygiene (Rule I06):** Binary payloads (photos, try-on renders) are never stored in PostgreSQL. Database stores object keys; private S3/R2 stores bytes.
4. **Frozen Boundary:** C05-C11 and C15 remain strictly in-memory.
