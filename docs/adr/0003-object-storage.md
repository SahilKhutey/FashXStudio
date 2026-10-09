# ADR-0003: Object Storage and Capabilities

## Status
Accepted

## Context
FashX Studio handles sensitive visual and biometric assets, including raw user portrait photos, body landmarks, and rendered virtual try-on images.
Under Rule I06 and privacy requirements (GDPR, India DPDP Act), storing binary assets directly in the primary PostgreSQL database is prohibited to prevent bloat, maintain query performance, and ensure strict separation of concerns.

Additionally, raw cloud storage URLs (e.g., public AWS S3 or Cloudflare R2 bucket URLs) must never be stored in the database or exposed directly to public clients or third-party web crawlers.

## Decision
1. **Target Object Storage Providers:**
   - **Cloudflare R2** (Primary cloud target): Zero-egress fee architecture natively aligned with high-frequency image streaming for AI virtual try-on workflows.
   - **AWS S3** (`ap-south-1` Mumbai): Low-latency Indian data residency alternative.
   - Both backends are S3 API-compatible (Signature Version 4), allowing seamless portability via the canonical `ObjectStorage` port.

2. **Private Bucket Security Posture:**
   - All environment buckets (`fashx-media-dev`, `fashx-media-prod`) are strictly private.
   - Public access is permanently disabled; no public DNS or custom domains are bound directly to the storage bucket.
   - All client access to media assets is mediated exclusively via expiring presigned capability URLs with short TTL (default: 300 seconds / 5 minutes) generated on demand.

3. **Key Layout & Namespacing:**
   - User assets are strictly isolated under user prefixes:
     - Reference user photos: `u/<user_id>/photos/<media_id>.jpg`
     - Try-on output renders: `u/<user_id>/tryon/<job_id>.jpg`
     - Temporary scratch data: `tmp/<random>.bin` (governed by 24h lifecycle expiry)
   - Catalog and merchant garment assets are decoupled from user namespaces:
     - Garment product renders: `catalog/<catalog_id>/garments/<garment_id>.jpg`

4. **Persistence Invariant (Rule I06):**
   - The PostgreSQL database (`media_objects` table) stores metadata only: `id`, `user_id`, `kind`, `object_key`, `sha256`, `size_bytes`, `content_type`, `created_at`.
   - The database NEVER stores image byte blobs or full URLs.
   - Read endpoints dynamically construct presigned capability URLs via the storage adapter per request.

5. **Storage Ports & Development Adapters:**
   - The application layer exposes `ObjectStorage` protocol defining `put`, `get`, `delete`, `delete_prefix`, `exists`, `list_prefix`, and `signed_get_url`.
   - `S3Storage` adapter interfaces with AWS S3 / Cloudflare R2.
   - `LocalStorage` adapter provides a local filesystem implementation (`./.local_storage/`) for local development, offline workflows, and unit testing, refusing execution when `ENV=prod`.

6. **Cascading Erasure Integration (Rules I16 & Gate G4):**
   - The `u/<user_id>/` key hierarchy guarantees that upon consent revocation (`erase_biometrics`) or full account erasure (`erase_account`), all user-associated assets can be reliably discovered and wiped.
   - Erasure operations are orchestrated via the transactional Outbox (`storage.delete_prefix` event) ensuring zero biometric residue without blocking client request latency.

## Consequences
- Zero egress overhead when running on Cloudflare R2.
- Robust prevention of direct file leakage or unauthorized scraping.
- Provable, auditable data erasure adhering to Gate G4 and DPDP/GDPR regulations.
- Complete parity between local offline developer workflow and production cloud infrastructure.
