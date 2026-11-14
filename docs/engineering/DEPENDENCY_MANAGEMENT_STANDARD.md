# Dependency Management Standard

**Status:** Adopted
**Version:** 1.0
**Effective Date:** 2026-11-11
**Category:** Engineering Configuration

---

## 1. Purpose and Scope

FashXStudio manages dependencies across two primary package ecosystems:
- **Backend:** Python 3.12 managed via `pyproject.toml`.
- **Mobile:** Node.js 20 / TypeScript / React Native managed via `mobile/package.json` and locked with `mobile/package-lock.json`.

This standard governs the addition, pinning, upgrading, and security scanning of all direct and transitive third-party dependencies.

---

## 2. Dependency Categories

| Category | Typical Packages | Update Policy |
|---|---|---|
| **1. Backend Runtime** | `fastapi`, `sqlalchemy`, `pydantic`, `redis` | Controlled updates; requires full regression suite on PostgreSQL. |
| **2. Backend Development** | `pytest`, `ruff`, `mypy`, `bandit`, `pip-audit` | Regular updates; verify that existing lint and type checks pass. |
| **3. Mobile Runtime** | `expo`, `react-native`, `zustand`, `lucide-react-native` | High sensitivity; bound strictly by Expo SDK release compatibility. |
| **4. AI / ML & Image** | `torch`, `clip`, `pillow`, VTO SDKs | Separate evaluation; evaluate memory, CPU/GPU footprint, and license. |
| **5. Security & Crypto** | `pyjwt`, `cryptography`, `argon2-cffi` | High priority; evaluate security advisories and update promptly. |
| **6. Infrastructure & CI** | Base Docker images, GitHub Actions (`actions/checkout`) | Controlled updates; verify workflow permissions and SHA pin. |

---

## 3. Twelve Core Dependency Rules

1. **No Dependencies Without Approval:** Never introduce a new dependency without explicit review and approval from the project lead (`AGENTS.md` Rule 7).
2. **Favor Native / Existing Code:** Always evaluate standard library modules and existing utilities before introducing an external library.
3. **Minimize Transitive Footprint:** Review the dependency tree before adding packages that pull in large transitive dependency chains.
4. **Strict Pinning / Safe Ranges:** In `pyproject.toml`, specify compatible version constraints (`>=x.y, <x.y+1` or `^x.y`). Never use unbounded wildcards (`*`).
5. **Always Commit Lockfiles:** When adding or upgrading mobile dependencies, `mobile/package-lock.json` must be updated and committed in the same PR.
6. **Decoupled Ecosystem Updates:** Never combine Python dependency upgrades and Node.js mobile package updates in a single pull request.
7. **Runtime Compatibility:** Python packages must support Python 3.12+. Mobile packages must be compatible with Node.js 20 and the current Expo SDK.
8. **React Native / Expo Verification:** Mobile dependencies must not require native code compilation unless verified compatible with Expo managed workflow and EAS builds.
9. **License Review:** Only packages with permissive open-source licenses (MIT, Apache 2.0, BSD, ISC) are permitted. Copyleft licenses (GPL, AGPL) are strictly prohibited.
10. **Security Vulnerability Audits:** Zero known critical or high vulnerabilities are allowed in runtime dependencies.
11. **Document Rationale:** Every PR introducing a dependency must explain why native solutions or existing packages were insufficient.
12. **No Broad Auto-Upgrades:** Blanket upgrade commands like `npm update` or `poetry update` on the active branch are prohibited.

---

## 4. Dependency Update Workflow

```text
Identify Outdated / Vulnerable Dependency
                  │
                  ▼
Review Changelog, Breaking Changes & CVE Advisories
                  │
                  ▼
Update Isolated Package in pyproject.toml or package.json
                  │
                  ▼
Run Local Verification (Unit Tests, Postgres DB Tests, Lint, Types)
                  │
                  ▼
Run Security Scans (bandit, pip-audit, npm audit)
                  │
                  ▼
Open Dedicated PR: chore(deps): upgrade <package> to <version>
                  │
                  ▼
Green CI + Human Founder Review and Merge
```

---

## 5. Mandatory Audit and Security Commands

Engineers and CI pipelines must regularly run the following dependency verification commands:

### Backend Audit Commands

```bash
# Check Python packages for known security vulnerabilities
python -m pip_audit --desc

# Static application security testing (Bandit)
python -m bandit -r backend/fashx -ll -ii
```

### Mobile Audit Commands

```bash
cd mobile

# Clean deterministic install from lockfile
npm ci

# Scan mobile dependencies for known vulnerabilities
npm audit

# Validate Expo SDK compatibility
npx expo-doctor

# Verify TypeScript compilation with new dependency types
npx tsc --noEmit

# Run mobile test suite
npx jest --ci

cd ..
```
