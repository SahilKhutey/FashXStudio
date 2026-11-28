# 13 — Backend Authentication Contract

## Integration Boundary
- Mobile attaches `Authorization: Bearer <accessToken>` and `X-Request-ID` in `mobile/src/api/client.ts`.
- Root gate (`mobile/app/_layout.tsx`) fetches `/api/v1/me` after session restoration to resolve internal shopper identity and onboarding state.
- Backend JWT verification and staging end-to-end `/me` + profile provisioning tests run in backend CI / staging (`PENDING` live staging verification).
