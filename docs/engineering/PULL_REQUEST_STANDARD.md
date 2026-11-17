# Pull Request Standard

**Status:** Adopted
**Version:** 1.0
**Effective Date:** 2026-11-11
**Category:** Engineering Governance

---

## 1. Purpose and Scope

This standard governs all Pull Requests (PRs) submitted to the FashXStudio repository. Every change—including application features, bug fixes, database migrations, configuration updates, and documentation—must be submitted through a Pull Request targeting `main`. Direct pushes to `main` are strictly prohibited.

---

## 2. Core Governance Rules

1. **One Open PR at a Time:** Per repository governance (`AGENTS.md` Rule 9), only one open PR may be pending at any given time. Do not create a new branch or open an additional PR while an earlier PR is unmerged, unless explicitly requested by the project lead.
2. **Push Only to Task Branch:** All commits must be pushed exclusively to the branch designated for the specific initiative.
3. **Founder Merge Authority:** Only the human founder merges PRs on GitHub, and only after CI is green and all verification evidence is verified (`AGENTS.md` Rule 12).
4. **No Weakening of Gates:** Never add `continue-on-error`, `|| true`, or ignore directives to make CI pass (`AGENTS.md` Rule 4).
5. **Verified Evidence Required:** Test tables must contain real output from executed commands or CI logs (`AGENTS.md` Rule 2).

---

## 3. Pull Request Lifecycle

```text
[Feature Branch]
       │
       ├─► 1. Local Verification (pytest, ruff, mypy, mobile tests, docs lint)
       ├─► 2. Push to Remote Branch
       ├─► 3. Open Pull Request targeting main using .github/PULL_REQUEST_TEMPLATE.md
       ├─► 4. Automated CI Execution (GitHub Actions test matrix, lint, type-check)
       ├─► 5. Peer / Founder Code Review (using CODE_REVIEW_CHECKLIST.md)
       ├─► 6. Revisions & Approvals
       │
       ▼
[Human Founder Merges to main]
```

---

## 4. Pull Request Size and Decomposition

To ensure thorough, timely code reviews and reduce integration risk:
- **Target Size:** Aim for diffs under 400 lines of functional code (excluding generated lockfiles, fixtures, and documentation).
- **Single Responsibility:** A PR should solve one problem. Split multi-stage initiatives into separate PRs (e.g., migration first, business logic second, UI integration third).
- **Code Moves First:** When refactoring or moving files across directories, perform the file relocation in an isolated commit or PR before modifying file contents.

---

## 5. Required PR Structure and Content

Every PR must be created using `.github/PULL_REQUEST_TEMPLATE.md` and must include:

### 5.1 Summary and Context
- A concise summary explaining **what** changed and **why**.
- Reference to the relevant task, issue ID, or Architectural Decision Record (ADR).

### 5.2 Scope Definition
- **Included:** Clear bullet points describing what the PR implements.
- **Explicitly Excluded:** Boundaries of what is deliberately deferred or out of scope.

### 5.3 Implementation Overview
- Highlighting impacts across Backend, Mobile, Database, API, Integrations, and Feature Flags.

### 5.4 Architecture and Compatibility
- Confirmation that existing services, repositories, and utilities are reused where possible.
- Affirmation that no frozen modules (`docs/architecture/FROZEN.md`) are modified without explicit written authorization.
- Verification that cross-subsystem direct database access is avoided.

### 5.5 Testing Evidence Table
A completed testing matrix citing exact commands or CI job runs, outcomes, and log summaries:

| Check | Command / CI Job | Result | Evidence |
|---|---|---|---|
| Unit tests | `python -m pytest tests/unit -q -m "not db and not frozen"` | Passed | e.g., 1058 passed in 14.2s |
| Integration tests (Postgres) | `python -m pytest tests -m db -q -rs` | Passed / Skip reason | PostgreSQL container run |
| Mobile tests | `cd mobile; npx jest --ci` | Passed | e.g., 22 suites, 165 passed |
| Lint | `python -m ruff check .` / `npx eslint .` | Passed | All checks passed |
| Type checking | `python -m mypy .` / `npx tsc --noEmit` | Passed | 0 issues across all source files |
| Migration upgrade/downgrade | `alembic upgrade head; downgrade -1; upgrade head` | Passed / N/A | Schema transition verified |
| Documentation lint | `python scripts/docs_lint.py` | Passed | docs lint ok |
| Security checks | `bandit` / `pip_audit` / `npm audit` | Passed | 0 vulnerabilities |

### 5.6 Security, Privacy, and Data Governance
- Strict declaration that no secrets, `.env` files, production tokens, or credentials are committed.
- Affirmation that no real user photographs, biometrics, or personal data are sent to external services without explicit user consent and founder sign-off.
- Verification of tenant isolation and resource ownership checks.
- Confirmation that logging does not expose tokens, signed URLs, or raw user images.

### 5.7 Documentation Updates
- Updating `README.md` if public setup or developer instructions change.
- Updating `docs/STATUS.md` if feature implementation status changes (using 🟢 or 🟡, never ✅).
- Documenting new API endpoints, schemas, and error responses.

### 5.8 Deployment and Rollback
- Step-by-step instructions for zero-downtime deployment.
- Explicit rollback procedures in case of operational failure.
- Feature flags or operational kill switches associated with the change.

---

## 6. Review and Approval Gates

Before any PR can be merged by the human founder:
1. **All CI Checks Green:** All GitHub Actions workflows (`ci.yml`, `rc08-staging.yml`) must pass cleanly.
2. **Review Checklist Satisfied:** The code must pass all applicable checks in `docs/engineering/CODE_REVIEW_CHECKLIST.md`.
3. **No Unresolved Discussions:** All review comments and requests for changes must be addressed and resolved.
4. **Clean Git State:** The branch must be rebased on the latest `main` with no merge conflicts.
