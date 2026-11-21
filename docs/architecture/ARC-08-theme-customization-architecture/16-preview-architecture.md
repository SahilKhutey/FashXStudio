# ARC-08: 16 — Preview Architecture

## 1. Draft Preview Isolation
- **Authentication**: Previews require valid tenant authentication; unauthenticated or cross-tenant preview requests are rejected with 403 Forbidden.
- **Cache Header Enforcement**: Responses include `Cache-Control: no-store, no-cache, private` to prevent CDN or browser caching of draft configurations.
- **Render Parity**: Draft previews consume the exact same rendering engine (ARC-09) and token resolver as published menus.
