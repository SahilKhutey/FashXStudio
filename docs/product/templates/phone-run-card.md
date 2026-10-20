---
evidence: real
collected_on: YYYY-MM-DD
collected_by: <your name>
raw_data: screen recording kept locally (no personal data in the repo)
---
# Phone run 1
**Device:** <model> · Android <version> · <RAM> GB · **Build:** Expo Go SDK 57 / preview APK <id>
**Backend:** local, AUTH_MODE=<local|jwks>, TRYON_PROVIDER=<mock|fashn_api>, embedder=<fake|marqo> · **Commit:** <git rev-parse --short HEAD>

## Checks (pass / fail / not run)
| # | Check | Result | Notes |
|---|---|---|---|
| A4 | Consent blocks until all switches on |  |  |
| A5 | Under-18 is a dead end, nothing stored |  |  |
| A6 | Hardware back button cannot skip consent |  |  |
| A7 | Profile resumes after killing the app |  |  |
| A8 | Quiz needs 3-10 picks |  |  |
| A11 | Feed respects size, budget, gender |  |  |
| A12 | Quiz picks visibly change the feed |  |  |
| A13 | Try-on works for a supported garment (mock/real: ___) |  |  |
| A14 | Unsupported garment cannot start a try-on |  |  |
| A15 | Failure messages are clear (airplane mode, wrong key) |  |  |

## Five test photos
| Photo | Gate decision | Reason code | Message shown | Correct? | Notes |
|---|---|---|---|---|---|
| good, full body |  |  |  |  |  |
| dark |  |  |  |  |  |
| blurry |  |  |  |  |  |
| cropped (head only) |  |  |  |  |  |
| two people |  |  |  |  |  |

## Performance
Feed scroll, 100+ cards: total frames ___ · janky frames ___ (___%) · 95th percentile ___ ms · memory (TOTAL PSS) ___ MB

## Bugs found
(one line each; each also filed as a GitHub issue, with its number)
