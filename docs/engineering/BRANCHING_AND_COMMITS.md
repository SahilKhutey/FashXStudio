# Branching and Commit Standards

**Status:** Adopted
**Version:** 1.0
**Effective Date:** 2026-11-11
**Category:** Engineering Governance

---

## 1. Branch Naming Convention (2.6.1)

All branches in FashXStudio must use lowercase, hyphen-separated names prefixed with an approved category. Direct pushes to `main` are strictly forbidden. All code and documentation changes must be proposed through a feature branch and merged via Pull Request.

### Approved Branch Types

| Branch Type | Prefix Convention | Purpose | Example |
|---|---|---|---|
| **Feature** | `feat/<description>` | New product capabilities, user-facing or platform features | `feat/vto-result-feedback` |
| **Bug Fix** | `fix/<description>` | Bug corrections in existing functionality | `fix/profile-photo-upload` |
| **Refactor** | `refactor/<description>` | Internal code restructuring without behavioral change | `refactor/catalog-adapters` |
| **Documentation** | `docs/<description>` | Documentation additions, updates, or governance audits | `docs/engineering-standards` |
| **Tests** | `test/<description>` | Test suite additions, fixtures, or contract coverage | `test/vto-provider-contract` |
| **Maintenance** | `chore/<description>` | Housekeeping, dependency bumps, or tool configurations | `chore/update-ci-cache` |
| **Performance** | `perf/<description>` | Execution time, query, or bundle size optimizations | `perf/catalog-query-optimization` |
| **Security** | `security/<description>` | Security hardening, vulnerability fixes, access controls | `security/photo-access-authorization` |
| **Release Prep** | `release/<version>` | Release stabilization, version tagging, and release notes | `release/0.2.0` |
| **Hotfix** | `hotfix/<description>` | Critical emergency fixes branched directly from release tags | `hotfix/auth-token-validation` |
| **Recovery** | `recovery/<description>` | Special governance remediation, drift reconciliation, audit | `recovery/rc13.1-governance-correction` |

### Branch Naming Rules

1. **One Logical Scope:** Branch names must describe exactly one logical initiative or task.
2. **Character Set:** Use strictly lowercase ASCII letters, numbers, and hyphens (`[a-z0-9-]`). No underscores, spaces, or uppercase letters.
3. **No Ambiguous Names:** Names such as `my-branch`, `test`, `temp`, `final`, `patch-1`, or `work-in-progress` are prohibited.
4. **No Sensitive Information:** Never include personal names, customer identifiers, merchant IDs, credentials, or secrets in branch names.
5. **PR Target:** All branches target `main` through a Pull Request unless explicitly branched for a chained release flow authorized by the engineering lead.
6. **No Force Pushes:** Never force-push (`git push --force`) to shared branches (`main`, active PR branches) unless explicitly authorized by the human founder for emergency history repair.
7. **Branch Cleanup:** Delete remote and local branches immediately after PR merge confirmation.

### Branch Lifecycle

```text
main
  │
  ├─► feat/vto-result-feedback (branched from latest main)
  │     │
  │     ├─► implementation commits
  │     ├─► unit & contract tests
  │     ├─► local gate verification
  │     ├─► pull request opened
  │     ├─► CI passes + human code review approval
  │     │
  │     ▼
  └─◄ merged via PR (squash or rebase merge by human founder)
```

---

## 2. Commit Message Convention (2.6.2)

FashXStudio strictly enforces the Conventional Commits specification. Every commit must have a clear semantic prefix, an optional scope, and an imperative subject.

### Commit Format

```text
type(scope): short imperative description

[optional body providing technical context and justification]

[optional footer(s) such as BREAKING CHANGE or issue references]
```

### Allowed Types

| Type | Purpose | Example Scope |
|---|---|---|
| `feat` | New product capability or user-facing feature | `vto`, `catalog`, `auth`, `wardrobe` |
| `fix` | Bug correction in existing functionality | `profile`, `mobile`, `storage`, `api` |
| `refactor` | Code restructuring without behavioral change | `pipeline`, `models`, `adapters` |
| `perf` | Measurable performance optimization | `db`, `image`, `bundle`, `cache` |
| `test` | Adding or updating tests without code changes | `unit`, `e2e`, `contract`, `release` |
| `docs` | Documentation, PRDs, ADRs, or architectural guides | `standards`, `api`, `adr`, `status` |
| `chore` | Tooling, linter, formatting, repository housekeeping | `ci`, `deps`, `lint`, `scripts` |
| `build` | Changes to build systems, packaging, or lockfiles | `poetry`, `npm`, `metro`, `hermes` |
| `ci` | CI/CD pipeline, GitHub Actions, release workflows | `actions`, `docker`, `gates` |
| `security` | Security controls, authorization rules, secret redaction | `crypto`, `tokens`, `audit`, `cors` |
| `revert` | Reversion of a previously merged commit | `vto`, `db`, `auth` |

### Concrete Commit Examples

```bash
git commit -m "feat(vto): add provider result feedback"
git commit -m "fix(auth): reject expired refresh tokens"
git commit -m "test(catalog): cover duplicate product ingestion"
git commit -m "docs(engineering): define migration policy"
git commit -m "security(storage): restrict generated image access"
git commit -m "chore(ci): update python test matrix to 3.12"
```

### Breaking Changes

Any breaking contract, database, or API change must include `BREAKING CHANGE:` in the footer or an exclamation mark after the type/scope:

```text
feat(api)!: replace legacy product response

BREAKING CHANGE: product image_url is now returned as image.uri.
Mobile clients before version 1.4.0 must be upgraded.
```

### Commit Hygiene Rules

1. **Imperative Mood:** Use imperative verb forms in the summary line: `add` (not `added` or `adds`), `fix` (not `fixed`), `remove`, `refactor`, `validate`.
2. **Length Limit:** Keep the summary line under 72 characters. Do not end the subject with a period.
3. **Atomic Commits:** One logical change per commit. For large structural movements, perform the file move in one commit, followed by modifications in subsequent commits.
4. **No Combined Scope:** Do not mix unrelated refactorings, feature implementations, and formatting passes in a single commit.
5. **No Secrets or Sensitive Data:** Never commit `.env` files, production keys, raw customer photographs, biometric/body measurements, model weights, or `.zip`/binary archives.
6. **PR Context:** A commit message explains *what* changed atomically; the Pull Request description explains the overall *why*, architecture, and verification evidence.

### Recommended Commit Sequence for a Feature

When implementing a feature, structure commits into logical phases:

```bash
git commit -m "feat(vto): add garment result metadata model and schema"
git commit -m "test(vto): cover result metadata validation and boundary cases"
git commit -m "docs(vto): document result metadata contract in OpenAPI and schemas"
```

---

## 3. Acceptance and Verification

- Branch name matches approved pattern (`^[a-z0-9-]+/[a-z0-9-]+$`).
- All commits adhere to `type(scope): description`.
- No direct commits made to `main`.
- Repository working tree remains clean before opening a Pull Request.
