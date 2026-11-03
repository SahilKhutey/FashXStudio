# RC-00 Test Plan

## 1. Test Levels
- **Level 1 — Static Analysis**: Audit inventory, route extraction, migration syntax.
- **Level 2 — Unit Testing**: Pytest test suite (`tests/unit/`) and Jest mobile suite (`mobile/__tests__/`).
- **Level 3 — Integration Testing**: API contracts, local storage signatures, database repos.
- **Level 4 — System Testing**: Full core loop (Discovery → Detail → Try-On → Save → Closet → Merchant handoff).
- **Level 5 — Physical-Device Testing**: Expo on physical Android device over LAN.

## 2. Core User Journeys
1. Auth / Token Login → Me / Profile check
2. Profile Onboarding → Reference portrait capture & quality gate
3. Feed Discovery → Catalog garment inspection
4. Garment Detail → Virtual try-on job submission
5. Try-On Job Execution → Render result viewer & feedback
6. Garment / Look → Save to Wardrobe
7. Wardrobe → List items & Delete item
8. Garment Detail → Affiliate buy-click tracked redirect
9. DPDP Consent Management → Revoke consent & purge photos
10. Account Erasure → Queue deletion & verify tombstone
