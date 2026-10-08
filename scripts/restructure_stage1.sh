#!/usr/bin/env bash
# FashXStudio - Restructure Stage 1: NON-CODE moves only (docs, archives, junk).
# Safe by design: dry-run by default, never moves Python/TS source (that is Stage 2).
# Usage:  bash scripts/restructure_stage1.sh          # dry run (prints actions)
#         bash scripts/restructure_stage1.sh --apply  # performs git mv / git rm
set -euo pipefail

APPLY=0; [[ "${1:-}" == "--apply" ]] && APPLY=1
run() { if [[ $APPLY -eq 1 ]]; then echo "+ $*"; "$@"; else echo "[dry-run] $*"; fi; }

git rev-parse --is-inside-work-tree >/dev/null || { echo "Run inside the repo"; exit 1; }
if [[ $APPLY -eq 1 ]]; then
  [[ -z "$(git status --porcelain)" ]] || { echo "Working tree not clean. Commit/stash first."; exit 1; }
  git tag -f pre-restructure-2026-10-04
  git checkout -b chore/restructure-stage1
fi

mv_if_exists() {  # mv_if_exists <src> <dest>
  if [[ -e "$1" ]]; then run mkdir -p "$(dirname "$2")"; run git mv "$1" "$2"; else echo "[skip] missing: $1"; fi
}

# 1) Planning/foundation material -> docs/archive (kept, but out of the way)
mv_if_exists "Foundation"                          "docs/archive/foundation"
mv_if_exists "ai-fashion-assistant-foundation-0"   "docs/archive/foundation-0"
mv_if_exists "docs-foundation-0.md"                "docs/archive/docs-foundation-0.md"
mv_if_exists "docs-foundation-1.md"                "docs/archive/docs-foundation-1.md"

# 2) Task logs and design docs -> clear homes
shopt -s nullglob
for f in docs/task-log-*.md docs/production-validation-*.md docs/release-readiness-*.md; do
  mv_if_exists "$f" "docs/logs/$(basename "$f")"
done
for f in docs/visual-design-*.md; do
  mv_if_exists "$f" "docs/design/$(basename "$f")"
done
mv_if_exists "docs/feature-platform.md" "docs/architecture/feature-platform.md"

# 3) Committed zip bundle: remove from tree (history keeps it; use git filter-repo later if size matters)
if [[ -d "Zip File" ]]; then run git rm -r -q "Zip File"; fi

# 4) Ensure docs skeleton
run mkdir -p docs/product docs/architecture docs/adr docs/design docs/logs docs/archive

echo
echo "Done ($([[ $APPLY -eq 1 ]] && echo applied || echo dry-run))."
echo "Next: copy in README.md, docs/STATUS.md, docs/adr/0001-*.md, CI workflow, then:"
echo "  grep -rn 'docs/task-log\|docs/visual-design\|release-readiness' --include='*.md' --include='*.yml' . | head -50"
echo "  python -m pytest tests -q   # must still be green"
