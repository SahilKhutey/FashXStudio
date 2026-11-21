# ARC-08: 21 — Performance and Reliability

## 1. Performance Targets
- **Theme Resolver Latency**: < 5 ms for 95th percentile.
- **Draft Save API Latency**: < 50 ms for 95th percentile.
- **Configuration Size Limit**: 512 KB maximum.
- **Component Limit**: 100 components per menu.

## 2. Reliability & Cache Outages
Resolver output is deterministically computable in-process. In the event of a cache outage, menus can be resolved directly from the PostgreSQL JSONB draft without service degradation.
