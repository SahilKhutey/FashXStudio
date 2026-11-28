# 17 — Known Issues & Environment Gaps

1. **No Live Identity Provider Session Locally**: Registration, verification, recovery, and refresh against live Supabase/Cognito endpoints were verified with mocked provider/Supabase clients locally; live staging E2E execution remains `PENDING`.
2. **Physical Device Validation**: Android and iOS physical-device testing (`9.2.10`) remains `PENDING`.
3. **Expo Typed Routes**: `mobile/app/(auth)/sign-in.tsx` uses typed route casts for newly added `/(auth)/register` and `/(auth)/forgot-password` routes until Expo regenerates `.expo/types/router.d.ts` during dev server startup.
