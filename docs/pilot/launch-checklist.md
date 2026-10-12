# Pilot Launch Readiness Checklist (PR 10A)

**Target Milestone**: Launch of Pilot Wave 1 (Closed Beta)  
**Release Version**: `v0.9-pilot-ready` / `v0.9.1-pilot`  
**Date**: October 2026  
**Status**: **ALL ITEMS CHECKED & VERIFIED (READY TO INVITE)**  

---

## 1. Readiness Verifications

- [x] **Phase 9 Go/No-Go Signed**: Release tag `v0.9-pilot-ready` exists on `main`; all release gates G1, G3, G4, G5 formally cleared with evidence in `docs/release/gates.md`.
- [x] **Pre-Registered Pilot Plan Frozen**: `docs/pilot/pilot-plan.md` committed with unchangeable M1–M5 and S1–S4 thresholds, coverage quotas, and stop rules.
- [x] **Alerting & Spend Safeguards Active**: Paging alerts (`APIHigh5xxRate`, `TryOnFailureRateHigh`) active in CloudWatch; dynamic kill switches (`tryon_enabled`, `maintenance_mode`) tested; daily vendor spend cap ($50/day alarm) armed.
- [x] **Mobile Builds Distributed & Verified**: Android Google Play Internal Testing and iOS TestFlight builds installed and tested; Supabase email OTP configured.
- [x] **Legal & Privacy Policies Live**: Privacy Policy, Terms of Use, Pilot Participant Terms, and English+Hindi consent screens live and identical between app and web endpoints.
- [x] **Single-Use Invite Codes Generated**: Invite generation script (`scripts/pilot/make_invites.py`) verified; initial batches generated for Wave 1 and Wave 2 with SHA-256 hashes stored in database.
- [x] **Support Kit Ready**: Dedicated support inbox (`pilot-support@fashx.studio`), participant one-pager (`docs/pilot/participant-one-pager.md`), known issues tracker (`docs/pilot/known-issues.md`), and top-10 support playbook (`docs/pilot/support-playbook.md`) operational.
- [x] **Telemetry & Reporting Views Verified**: Salted pseudonymous views (`v_pilot_events`, `v_pilot_tryon_jobs`) and reporting scripts (`funnel.sql`, `retention.sql`, `pilot_report.py`) tested with Wilson 95% intervals and `<5` cell suppression.
- [x] **Production Erasure Rehearsed**: 1-click account deletion and S3 prefix purge rehearsed on production during Alpha; zero posthumous data revival confirmed.
- [x] **Alpha Exit Completed**: 5 alpha testers completed 3-day dry run with zero open severity-1/2 defects.

---

## 2. Sign-Off Authorization

- **Technical Lead / Founder**: *Verified & Signed (2026-10-12)*
- **Security & Privacy Lead**: *Verified & Signed (2026-10-12)*
- **Pilot Operations Lead**: *Verified & Signed (2026-10-12)*

**Verdict**: All systems operational. Authorizing distribution of Wave 1 invitations.
