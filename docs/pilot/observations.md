# Pilot Behavioral Observations Log (Days 1–28)

**Scope**: Empirical observation log recorded daily during closed pilot operations across Wave 1, Wave 2, and Wave 3.  
**Rule**: Record observed user behavior (actions taken, abandonment points, repeat loops), not self-reported intentions or compliments.

---

## Week 1: Wave 1 Rollout (14 Invites Sent, 12 Activated)

### Day 1
- **Observation**: 8 of 12 Wave 1 participants completed onboarding within 90 minutes of receiving their invitation code. All 8 took their calibration photo using the rear camera with mirror reflection or self-timer rather than front selfie camera.
- **Behavioral Signal**: Users immediately navigated to ethnic wear and oversized tops rather than curated generic casuals. First try-on was triggered within 6.2 minutes of onboarding completion.
- **Queue/Infra**: Mean try-on generation latency 7.8s; Redis queue depth never exceeded 2 concurrent jobs. Zero crash groups detected in Sentry/Bugsnag.

### Day 2
- **Observation**: 3 users experienced try-on failure with error `ERR_GARMENT_OCCLUSION` when trying a multi-layer lehenga/dupatta set. 2 of the 3 immediately retried with a simpler cotton kurta, which succeeded.
- **Behavioral Signal**: Users do not read multi-paragraph error alerts; they immediately hit "Retry" or pick a simpler item from the feed. Shortened error copy to 1 sentence with an action button.
- **Feedback Inbox**: 1 support query regarding whether photos are stored publicly. User was directed to the 1-pager and in-app privacy card; user continued testing.

### Day 3
- **Observation**: Participants actively used the "Filter by Size" pill before scrolling the feed. 4 participants set filter to "M" and scrolled through 35+ items without hiding any card.
- **Behavioral Signal**: Users spend an average of 42 seconds on the garment detail sheet inspecting fabric composition and size charts before clicking "Try On". Virtual try-on is used as an evaluation gate before deciding to save.

### Day 4
- **Observation**: First repeat sessions observed without prompts or push notifications. 5 participants opened the app during lunch hour (12:30–14:00 IST) and browsed the "New In" tab.
- **Behavioral Signal**: 3 participants saved 4 items to their Closet. 1 participant triggered 7 try-on jobs in a single 15-minute session across western blazers and formal trousers.

### Day 5
- **Observation**: Automated in-app micro-survey `feed_day5` triggered for eligible Wave 1 users. 9 of 10 completed it within 2 hours of app launch.
- **Behavioral Signal**: 78% rated feed recommendations 4/5 or 5/5. Negative signal rate on feed cards remained low (6.8% "not interested" or hide).
- **Issue Discovered**: iOS users on low-power mode noted a brief stutter during image crossfade animation on the Try-On result sheet.

### Day 6
- **Observation**: Saturday shopping spike: highest try-on generation volume (34 jobs processed in 24 hours). 2 users clicked "Buy on Store" external affiliate handoff links to Myntra.
- **Behavioral Signal**: Users who share try-on results with friends via WhatsApp screenshot return to the app within 20 minutes to try an alternative colorway.

### Day 7 (Wave 1 Mini-Review)
- **Weekly Rollup**: 12 active users, 71 try-on jobs completed (mean 5.9 try-ons/user). Zero crashes (100% crash-free sessions across 142 sessions). 0 stop rules tripped.
- **Top 3 Issues Identified**:
  1. Low-power mode stutter on iOS image reveal animation.
  2. Ethnic dupatta layering artifacts on complex draped garments.
  3. "Saved to Closet" button lacked instant tactile haptic feedback.
- **Action**: Deployed OTA Patch v0.10.1 addressing haptics and image crossfade rendering. Prepared Wave 2 rollout.

---

## Week 2: Wave 2 Rollout & Broadening Mix (19 Invites Sent, 16 Activated)

### Day 8
- **Observation**: Wave 2 invited (19 invitations, targeting XL+ sizing, non-metro tier-2 locations, and 100% strangers/weak ties). 11 users onboarded by 21:00 IST.
- **Behavioral Signal**: Strangers spent 25% longer reviewing the DPDP privacy and consent screen before ticking the biometric/photo consent checkbox, but 100% ultimately accepted. Zero consent abandonments.

### Day 9
- **Observation**: 2 participants in the XL+ size group encountered `no_items_in_size` on narrow category filters (formal dresses). The relaxation ladder triggered automatically, surfacing matching plus-size kurtas and oversized shirts.
- **Behavioral Signal**: Rather than dropping out, both users browsed the relaxed recommendations and initiated 3 try-ons each.

### Day 10
- **Observation**: Android low-end device (Redmi Note 10) tested in Tier-2 city (Jaipur) on 4G cellular data. Try-on generation completed in 8.4s end-to-end, image render took 1.2s over cellular.
- **Behavioral Signal**: Fast latency builds user confidence. User immediately conducted 4 successive try-on sessions.

### Day 11
- **Observation**: Second wave of external "Buy on Store" affiliate clicks: 6 users clicked external merchant deep links (Ajio and Myntra).
- **Behavioral Signal**: Users click "Buy on Store" specifically when the virtual try-on confirms that garment length aligns with their height/torso proportions.

### Day 12
- **Observation**: First voluntary erasure request received from a Wave 1 participant who completed testing. Triggered automated erasure pipeline: participant record purged in 1.2s, S3 photo prefix purged, tombstone logged with zero PII retention.
- **Behavioral Signal**: User expressed appreciation in support chat for prompt, verifiable deletion confirmation.

### Day 13
- **Observation**: Week-2 retention tracking for Wave 1 cohort: 8 of 12 Wave 1 users (66.7%) actively returned and logged at least one session between Days 7 and 13.
- **Behavioral Signal**: Organic repeat visits occur even without re-engagement push notifications.

### Day 14 (Mid-Pilot Checkpoint 1)
- **Checkpoint Review**: Evaluated M1–M5 and S1–S4 progress in [`checkpoint-1.md`](./checkpoint-1.md).
- **Findings**: Activation (87.5%), Realism (mean 4.14/5), Reliability (99.6% crash-free), and Privacy (0 breaches) are strongly on track. Sizing diversity in XL+ showed slight catalog sparsity in formal wear.
- **Decision**: Trigger Wave 3 (12 targeted invites) specifically focused on plus-size and ethnic wear discovery.

---

## Week 3: Wave 3 Targeted Expansion & In-Depth Interviews (12 Invites Sent, 10 Activated)

### Day 15
- **Observation**: Wave 3 invites delivered. 8 users onboarded on Day 15. All 8 added their sizes (including 4 in XL/XXL).
- **Behavioral Signal**: Users immediately test the fit on garments they previously hesitated to purchase online due to uncertain draping.

### Day 16
- **Observation**: Scheduled Qualitative Interview #1 (Wave 1 user) and #2 (Wave 2 stranger). Both confirmed they felt comfortable uploading body photos because of the explicit on-device calibration and zero public sharing guarantees.
- **Behavioral Signal**: Participants specifically praised the realistic depiction of sleeve length and waist taper.

### Day 17
- **Observation**: Interview #3 conducted with a participant who dropped off after Day 3 without trying on garments.
- **Root Cause**: User felt their bedroom lighting was too yellow and doubted the app would produce accurate colors; did not know retaking photo with natural light was easy.
- **Insight**: Add explicit ambient lighting guidance on the photo preview screen.

### Day 18
- **Observation**: Peak catalog engagement across all active cohorts (38 total active users). 61 try-on requests handled seamlessly. Vendor API circuit breaker remained fully closed (healthy).
- **Behavioral Signal**: Users save outfits to custom tags ("Work", "Wedding Guest", "Weekend").

### Day 19
- **Observation**: Conducted Interview #4 and #5 (including tier-2 participant and iOS user). 2 users reported making an actual purchase on Ajio using the link-out from FashXStudio.
- **Behavioral Signal**: High correlation between saving an item to Closet and subsequent external merchant click within 48 hours.

### Day 20
- **Observation**: Conducted Interview #6, #7, and #8. Users emphasized that try-on feels substantially more realistic than generic 2D sticker overlays seen on legacy fashion apps.
- **Behavioral Signal**: Defect flagging rate dropped to 7.6% as users followed guided pose guidelines.

### Day 21
- **Observation**: Feature flag `end_survey_open` enabled for all participants who have been active for ≥ 7 days.
- **Behavioral Signal**: Within 24 hours, 28 of 38 eligible users completed the System Usability Scale (SUS) and PMF survey.

---

## Week 4: End-of-Pilot Data Collection & Study Wrap-up

### Day 22
- **Observation**: Additional 9 survey submissions received (37 total survey responses logged). Median completion time: 3.4 minutes.
- **Behavioral Signal**: SUS responses show exceptional ease of navigation and high trust in photo handling.

### Day 23
- **Observation**: Conducted final qualitative interviews #9 and #10 (including second drop-off user).
- **Insight**: Drop-off user wanted instant size recommendations across multiple brands rather than just visual try-on. Identified as a high-value roadmap feature for Phase 11.

### Day 24
- **Observation**: Total cumulative try-on jobs reached 215. Mean generation latency held steady at 8.2s (P95 at 14.1s, far below the 45s threshold).
- **Behavioral Signal**: Repeat usage concentrated in users who discovered at least 2 distinct brands they had not previously shopped.

### Day 25
- **Observation**: Third verified purchase reported by a Wave 2 participant (cotton Anarkali kurta ordered on Myntra after try-on verification).
- **Behavioral Signal**: Validates commercial hypothesis H4 (virtual try-on provides sufficient purchase confidence to drive real conversion).

### Day 26
- **Observation**: Participant support volume declined to zero inbound bugs. System operating at steady state with zero crashes over preceding 10 days.

### Day 27
- **Observation**: Final reminder sent for end-of-pilot survey. Total completed survey count reached 39.

### Day 28 (Freeze Day)
- **Observation**: Closed pilot data collection officially frozen at 23:59 IST. Commenced automated data extraction via pseudonymous views (`v_pilot_*`).
- **Summary**: 45 invitations across 3 waves produced 42 logins, 38 activated participants, 215 try-ons, 39 survey completions, and 0 security or privacy incidents.
