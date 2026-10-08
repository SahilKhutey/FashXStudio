#!/usr/bin/env bash
# Requires GitHub CLI (gh auth login). Run from repo root. Creates labels, milestones, issues.
set -euo pipefail
for l in "scope:mvp:0E8A16" "scope:frozen:BFD4F2" "blocker:D93F0B" "legal:5319E7" "security:B60205" "ml:1D76DB" "mobile:FBCA04" "infra:C5DEF5" "docs:0075CA"; do
  name="${l%:*}"; col="${l##*:}"
  gh label create "$name" --color "$col" --force
done
for m in "M0 Cleanup" "M1 Real spine" "M2 Real try-on" "M3 Real catalog" "M4 Mobile pilot"; do
  gh api repos/:owner/:repo/milestones -f title="$m" >/dev/null 2>&1 || true
done
mk() { gh issue create --title "$1" --label "$2" --milestone "$3" --body "$4"; }

mk "Restructure Stage 1: move docs/archives, drop Zip File"               "docs,scope:mvp"      "M0 Cleanup" "Run scripts/restructure_stage1.sh --apply. Fix doc links. Tests stay green."
mk "Restructure Stage 2: merge api/ + app/ into backend/fashx"             "infra,scope:mvp"     "M0 Cleanup" "Check root app/ vs api/app/ package collision first. One move per commit."
mk "Merge apps/mobile and mobile/ into a single Expo app"                  "mobile,scope:mvp"    "M0 Cleanup" "Pick canonical dir, port missing screens/state, delete the other."
mk "Freeze C05-C11 and F11-F13; unmount from production router"            "scope:frozen"        "M0 Cleanup" "Move to domain/frozen or flag-gate. Exclude from gates. Add FROZEN.md."
mk "Make repo private; decide license/positioning"                         "legal"               "M0 Cleanup" "Proprietary license on a public repo is contradictory."
mk "Replace README badges with CI-generated ones; publish docs/STATUS.md"  "docs"                "M0 Cleanup" "No hand-written test counts or gate claims."
mk "CI: lint + mypy + pytest on Postgres/pgvector + migrations"            "infra,blocker"       "M0 Cleanup" "Use .github/workflows/ci.yml as base."
mk "Auth: JWT/session + ownership checks on every {user_id} route"         "security,blocker"    "M1 Real spine" "Biometric endpoints must reject cross-user access. Add negative tests."
mk "Persist all MVP domains in PostgreSQL (remove in-memory from runtime)" "scope:mvp,blocker"   "M1 Real spine" "Profile, catalog, tryon jobs, closet, feedback, analytics. Test on real Postgres."
mk "Photo storage on R2/S3 with signed URLs and erasure test"              "security"            "M1 Real spine" "Verify cascading hard delete on consent revoke end to end."
mk "Select license-cleared try-on path (commercial API or licensed model)" "legal,ml,blocker"    "M2 Real try-on" "Gate G5. Keep license evidence in docs/architecture."
mk "Implement CommercialApiAdapter + one live GPU/API worker"              "ml"                  "M2 Real try-on" "Replace MockAdapter in staging."
mk "Build try-on eval set (50-100 pairs) + realism/latency scorecard"      "ml"                  "M2 Real try-on" "Honest G2/G3 numbers."
mk "Choose legitimate catalog source (affiliate feed / Shopify brands)"    "legal,scope:mvp"     "M3 Real catalog" "Avoid ToS-violating scraping. Ingest 5-10k products."
mk "Hand-validate VLM enrichment accuracy on 200 products"                 "ml"                  "M3 Real catalog" "Report per-attribute accuracy."
mk "Mobile: onboarding+capture, feed, try-on result, closet+buy screens"   "mobile"              "M4 Mobile pilot" "Bind to real API. E2E on a device."
mk "DPDP privacy review + retention/breach policy before real photos"      "legal,security"      "M4 Mobile pilot" "Required before pilot."
mk "Pilot: 20-50 users; track completion/save/buy-click/realism"           "scope:mvp"           "M4 Mobile pilot" "Feeds G6."
