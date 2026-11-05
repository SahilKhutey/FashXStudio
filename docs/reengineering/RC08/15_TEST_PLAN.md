# RC08 — Test Plan

## 1. Test Architecture Matrix

| Level | Path | Scope |
|---|---|---|
| **Unit** | `tests/unit/test_rc08_*.py` | Release config validation, security headers, rate limits, storage policies |
| **Integration** | `tests/integration/test_rc08_*.py` | Staging auth verification, database migrations, signed URL expiry, cascading object erasure |
| **Security** | `tests/security/test_rc08_*.py` | IDOR isolation, malicious upload sniffing, open redirect prevention |
| **Mobile** | `mobile/__tests__/rc08_*.test.ts` | Upload retry, offline handling, token expiration recovery, privacy deletion |
| **Release Contract**| `tests/release/test_rc08_*.py` | Staging smoke contract, readiness probe validation, release gate verification |

## 2. Test Execution Commands
```bash
# Code Quality & Documentation
python scripts/docs_lint.py
ruff check .
mypy .

# Unit & Security Tests
python -m pytest tests/unit -q
python -m pytest tests/security -q

# Database Tests (against PostgreSQL)
python -m pytest tests -m db -q -rs

# Full Regression
python -m pytest tests -q -p no:cacheprovider -m "not frozen"

# Mobile Tests & Static Export
cd mobile
npm ci
npx tsc --noEmit
npx eslint . --max-warnings 0
npx jest --ci
```
