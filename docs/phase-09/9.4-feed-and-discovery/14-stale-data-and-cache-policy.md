# 14 — Stale Data and Cache Policy

- Feed results: `staleTime: 60_000`.
- Search results: `staleTime: 30_000`, `gcTime: 5 * 60_000`.
- Facets: `staleTime: 5 * 60_000`.
- Cached results remain displayed during background refresh (`isError && items.length === 0` guards full-screen error).
