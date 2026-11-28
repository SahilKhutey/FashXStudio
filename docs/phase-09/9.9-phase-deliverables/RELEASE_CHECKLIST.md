# Phase 09 Release Checklist

- [x] Mobile TypeScript (`npx tsc --noEmit`) passes with 0 errors
- [x] Mobile ESLint (`npx eslint . --max-warnings 0`) passes with 0 warnings
- [x] Mobile Jest suite (`npx jest --ci`) passes (`37/37` suites, `245/245` tests)
- [x] Backend Phase 09 unit suite passes (`13/13` tests)
- [x] Sensitive data redaction verified for crash reporting (`BUG-09-00` fixed)
- [ ] Mount `catalog/detail/router.py` and `commerce_wardrobe/looks/router.py` in `backend/fashx/main.py` (`BUG-09-01`, `BUG-09-02`)
- [ ] Align `/onboarding/progress` endpoint (`BUG-09-03`)
- [ ] Run Postgres `db` integration suite & `scripts/ci/local_gate.sh` in CI/Docker
- [ ] Execute `PHYSICAL_DEVICE_TEST_PLAN.md` on physical Android and iOS devices against staging
- [ ] Verify live Supabase Auth, media storage, and VTO inference provider in staging
