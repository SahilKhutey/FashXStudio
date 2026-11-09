# RC08 — Mobile Release & Physical Device QA

## 1. Device Test Matrix
Automated Jest tests and Expo static bundles prove JavaScript logic and layout stability, but do not replace physical hardware QA.

| Journey Step | Android Physical Device | iOS Physical Device |
|---|---|---|
| App Installation & Cold Boot | Required | Required (When iOS hardware available) |
| Supabase Auth (Sign-in / Refresh) | Required | Required |
| Onboarding & Consent Acceptance | Required | Required |
| Camera Permission Handling | Required | Required |
| High-Res Photo Capture (Camera) | Required | Required |
| Photo Upload & Background Resilience | Required | Required |
| VTO Job Submission & Polling | Required | Required |
| Result Rendering & Zoom Inspection | Required | Required |
| Wardrobe Item Persistence | Required | Required |
| Retailer Handoff (Deep Link / Browser) | Required | Required |
| Account Deletion & Local Cache Purge | Required | Required |

## 2. Network & Hardware Edge Scenarios
- **Airplane Mode / Network Drop**: Upload paused cleanly with retry prompt; no app crashes.
- **Low Light / Glare Camera Capture**: In-app photo quality validator warns user before network upload.
- **App Backgrounding During VTO**: Polling resumes cleanly when app returns to foreground.
- **Token Expiry During Active Session**: Silent refresh without kicking user back to splash screen.
