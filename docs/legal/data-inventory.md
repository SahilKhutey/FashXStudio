# Personal Data Inventory (DPDP Act, 2023)

**Data Fiduciary**: FashXStudio  
**Jurisdiction**: Republic of India  
**Applicable Law**: Digital Personal Data Protection Act, 2023 & DPDP Rules 2025  
**Review Cycle**: Annual / Pre-Release Release Gate G4  

---

## 1. Inventory Matrix

| Data Item / Field | Category | Primary Purpose | DPDP Legal Basis | Storage Location | Technical Safeguards | Retention Window | Third Parties with Access |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Email Address** | Identity / Auth | Account creation, login OTP, transactional alerts, deletion confirmation | Section 6 (Consent) | Postgres (`users.email`), Supabase Auth | Encrypted at rest (`AES-256`), hashed in memory | Account lifetime + 30 days post-deletion | Supabase (Auth processor) |
| **Self-Portrait / Full-Body Photo** | Biometric / Visual Personal Data | Virtual try-on garment rendering and silhouette extraction | Section 6 (Explicit Informed Consent) | AWS S3 `ap-south-1` (`u/{user_id}/`) | S3 SSE-S3 / SSE-KMS, presigned PUT/GET (15m expiry) | Immediate deletion on consent revocation or account deletion | FASHN AI (Try-on processor via ephemeral HTTPS) |
| **Body Measurements & Silhouette** | Physical / Fit Profiling | Size recommendation and fit accuracy scoring | Section 6 (Consent) | Postgres (`body_profiles`, `user_measurements`) | Encrypted at rest, row-level authorization | Account lifetime | Internal only (never shared) |
| **Skin Tone & Color Vector** | Aesthetic Preference | Palette matching and color harmony prior | Section 6 (Consent) | Postgres (`user_style_profiles`, `skin_tone_results`) | Pseudonymous vector representation | Account lifetime | Internal only |
| **Wardrobe Items & Closet Outfits** | Commerce / User Content | Saving favorite garments and try-on output | Section 6 (User directed) | Postgres (`wardrobe_items`), S3 | Encrypted at rest | Retained until removed by user or account closure | Internal only |
| **Generated Try-On Images** | Derived Visual Personal Data | Previewing garment on user's silhouette | Section 6 (Consent) | AWS S3 `ap-south-1` (`tryon/`) | Presigned capability URLs (15m expiration) | Unsaved: 30 days. Saved: Account lifetime | FASHN AI (Transient generator), User |
| **Feed Impressions & Signals** | Behavioral / Interaction | Personalizing feed ranking and diversity | Section 6 (Consent / Legitimate Use) | Postgres (`feed_impressions`, `feed_signals`) | Anonymized session IDs | 90 days (hard purged) | Internal only |
| **Domain & Analytics Events** | Telemetry / Product Health | Reliability, error diagnosis, fraud monitoring | Legitimate Use (Section 7) / CERT-In compliance | Postgres (`domain_events`), AWS CloudWatch | Pre-redacted (no PII, no JWTs, no presigned URLs) | 365 days; user ID stripped (`NULL`) at 12 months | AWS CloudWatch (Mumbai) |
| **IP Address & User Agent** | Network Traffic | WAF abuse prevention, DDoS defense, CERT-In compliance | CERT-In Directions 2022 (Statutory Obligation) | AWS ALB access logs, CloudWatch | Scrubbed in app logs, ALB logs retained 180 days | 180 days in India | AWS (Cloud infrastructure) |
| **Erasure Tombstones** | Minimal Pseudonymous Record | Guaranteeing permanent erasure and preventing restore resurrection | Data Integrity & Statutory Compliance | Postgres (`erasure_tombstones`) | Pseudonymous (`user_id`, `erased_at`) only | Indefinite | Internal SRE only |
