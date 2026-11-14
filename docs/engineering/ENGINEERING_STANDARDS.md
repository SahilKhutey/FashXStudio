# FashXStudio Engineering Standards

**Status:** Adopted
**Version:** 1.0
**Effective date:** 2026-11-11
**Owner:** Product / Engineering Lead

---

## Purpose

Establish consistent engineering, quality, security, testing, deployment, and documentation practices across the FashXStudio platform.

---

## Scope

Applies to:
- Backend and API
- Mobile application
- Database and migrations
- AI/ML and virtual try-on
- Catalog and merchant integrations
- Infrastructure and CI/CD
- Documentation and release governance

---

## Mandatory Standards

1. **Branches follow the approved naming convention:** Lowercase, hyphen-separated with an approved prefix (`feat/`, `fix/`, `chore/`, etc.).
2. **Commits follow the approved message convention:** Conventional Commits (`type(scope): summary`).
3. **Every code change is submitted through a pull request:** No direct pushes to `main`.
4. **Every PR includes test evidence and a security/privacy review:** Backed by real execution commands or CI output.
5. **Database changes require Alembic migrations:** Tested with upgrade and downgrade cycles.
6. **Database integration tests use PostgreSQL:** Tests that touch the database run on PostgreSQL with `pgvector`.
7. **Public application APIs follow `/api/v1`:** Predictable URI major versioning and synchronized OpenAPI contracts.
8. **Secrets and personal data must never be committed or exposed in logs:** Zero-PII logging and `SecretStr` environment configuration.
9. **Dependencies require approval before addition:** No unvetted third-party libraries; pinned and scanned for vulnerabilities.
10. **Feature flags must have documented owners and safe defaults:** Security and external-spend flags default to disabled.
11. **No release gate may be weakened to make CI pass:** No `continue-on-error`, `|| true`, or unjustified ignores.
12. **Only the human founder merges changes into main:** Strictly on GitHub after all CI gates pass green.

---

## Detailed Standards

The following documents define the comprehensive requirements for each domain:

- **Branching and Commits:** [BRANCHING_AND_COMMITS.md](BRANCHING_AND_COMMITS.md)
- **Pull Requests:** [PULL_REQUEST_STANDARD.md](PULL_REQUEST_STANDARD.md)
- **Code Reviews:** [CODE_REVIEW_CHECKLIST.md](CODE_REVIEW_CHECKLIST.md)
- **Testing:** [TESTING_STANDARD.md](TESTING_STANDARD.md)
- **API Versioning:** [API_VERSIONING_STANDARD.md](API_VERSIONING_STANDARD.md)
- **Database Migrations:** [DATABASE_MIGRATION_STANDARD.md](DATABASE_MIGRATION_STANDARD.md)
- **Logging:** [LOGGING_STANDARD.md](LOGGING_STANDARD.md)
- **Error Handling:** [ERROR_HANDLING_STANDARD.md](ERROR_HANDLING_STANDARD.md)
- **Environment Configuration:** [ENVIRONMENT_CONFIGURATION_STANDARD.md](ENVIRONMENT_CONFIGURATION_STANDARD.md)
- **Dependency Management:** [DEPENDENCY_MANAGEMENT_STANDARD.md](DEPENDENCY_MANAGEMENT_STANDARD.md)
- **Feature Flags:** [FEATURE_FLAG_STANDARD.md](FEATURE_FLAG_STANDARD.md)

---

## Enforcement

Engineering standards are strictly enforced through:
- Automated CI workflows (`.github/workflows/ci.yml`)
- PostgreSQL database integration test execution
- Static typing (`mypy`) and linting (`ruff`, `eslint`)
- Dependency vulnerability scans (`pip-audit`, `bandit`, `npm audit`)
- Structured code reviews using the [Code Review Checklist](CODE_REVIEW_CHECKLIST.md)
- Release gate evaluation scripts (`scripts/rc13/evaluate_release_gates.py`)

---

## Exceptions

Any exception to these standards requires:
- A documented business and technical reason
- Comprehensive risk assessment
- Explicit scope boundary and time duration
- Written approval from the human founder
- A defined follow-up remediation task or removal condition

> **Notice:** Under no circumstances may an exception bypass legal compliance, biometric user consent, security authorization, or release gate integrity.

---

## Change Management

These engineering standards are version-controlled in the repository. Any modification, addition, or retirement of a standard must be proposed through a Pull Request, reviewed against platform governance, and approved by the engineering lead and human founder.
