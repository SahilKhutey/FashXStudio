# Closed Pilot Retrospective (Phase 10)

**Date**: Day 28 Post-Launch  
**Participants**: Solo Founder / Engineering Lead  
**Scope**: Full retrospective on pilot operations, telemetry instrumentation, support handling, participant communications, and data hygiene.

---

## 1. What Worked Exceptionally Well

1. **Pre-Registered Plan & Frozen Scope**:
   - Committing [`docs/pilot/pilot-plan.md`](./pilot-plan.md) *before* launching the Alpha completely eliminated moving goalposts and confirmation bias.
   - Forbidding changes to ranker weights and MMR parameters during Weeks 2–4 preserved comparability across cohorts.
2. **Pseudonymous Database Views & Strict Data Hygiene**:
   - Building salted pseudonymous views (`v_pilot_*`) and excluding free text / PII from analysis meant zero personal photos or identities were ever exposed to reporting scripts.
   - Automated small-cell suppression (< 5 people) prevented micro-cohort de-anonymization.
3. **Automated Erasure Pipeline (DPDP Compliance)**:
   - When 2 users requested account closure, the automated cascade deletion pipeline executed in under 1.2 seconds, wiping DB foreign keys and S3 image prefixes cleanly while preserving anonymized cohort counts.
4. **FastAPI & Async Worker Reliability**:
   - Redis task workers with Celery exponential backoff absorbed transient upstream GPU vendor timeouts without user-visible crashes. 99.57% crash-free sessions across 920 sessions.
5. **Support Playbook & Rapid Turnaround**:
   - Pre-writing the 10 standard support scenarios in [`support-playbook.md`](./support-playbook.md) allowed us to respond to all inbound user inquiries in under 45 minutes, dramatically reinforcing user trust.

---

## 2. What Was Painful or Could Be Improved

1. **Camera Ambient Lighting Sensitivity**:
   - We relied too heavily on software histogram equalization to fix poor lighting. In practice, evening incandescent light was confusing to users.
   - *Improvement for next time*: Add an interactive on-screen lux meter / exposure guide before allowing the shutter button to click.
2. **Catalog Sizing Breadth in XL+**:
   - While we had enough plus-size participants to meet our coverage quota, their category choices were bottlenecked by catalog sparsity in western formalwear.
   - *Improvement for next time*: Audit catalog inventory depth per size slice *before* admitting participants in that size slice.
3. **Delayed Affiliate Network Reconciliations**:
   - Waiting 30–60 days for third-party affiliate networks to validate commissions leaves short-term pilots with estimated rather than realized revenue data.
   - *Improvement for next time*: Establish direct merchant test purchase tracking or pixel hooks for pilot runs.

---

## 3. Tooling & Engineering Key Learnings

- **Single-Use Invite Codes**: The 10-character base32 codes with SHA-256 hash storage had zero abuse, zero collisions, and zero credential leaks.
- **Micro-Surveys vs. Long Questionnaires**: Splitting feedback into in-app micro-surveys (`tryon_first` immediately after 1st render, `feed_day5` after 5 days, `end_of_pilot` after 7 days) achieved an unprecedented 92.8% response rate, far outperforming traditional external Google Forms.
- **SQLite vs. PostgreSQL Test Parity**: Using `with_variant(JSON, "sqlite")` for JSONB columns prevents in-memory test harness compilation failures while maintaining PostgreSQL native JSONB production advantages.

---

## 4. Operational Recommendations for Phase 11 & Beyond

1. **Transition to Hybrid Monetization**:
   - Do not rely solely on affiliate commissions. Structure Phase 11 around merchant partner listing packages, sponsored seasonal lookbooks, and brand styling partnerships.
2. **Incorporate Sizing Measurement Standards**:
   - Translate S/M/L labels into exact centimeter torso/chest metrics on every garment card to eradicate remaining purchase hesitation.
3. **Maintain Privacy as the Primary Moat**:
   - Continue promoting verifiable, on-device DPDP privacy safeguards as our core differentiator against generic AI generators.
