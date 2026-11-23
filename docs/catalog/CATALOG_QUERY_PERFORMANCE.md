# Catalog Query Performance Report

## 1. Benchmark Harness and Workload
Benchmarks were run against seeded datasets measuring P50 and P95 latency distributions across critical catalog queries.

## 2. Benchmark Results
| Workload | P50 (ms) | P95 (ms) | P95 Target (ms) | Status |
|---|---|---|---|---|
| Source Product Identity Lookup | 1.48 | 7.65 | < 50 | Within Target |
| Product Detail Retrieval | 2.77 | 7.50 | < 100 | Within Target |
| Category / Brand Filter | 1.41 | 3.18 | < 150 | Within Target |
| Combined Multi-factor Filter | 1.22 | 2.68 | < 200 | Within Target |
| Merchant Active Offers Listing | 1.78 | 2.91 | < 150 | Within Target |
| Stale Offer Query | 1.00 | 2.97 | < 250 | Within Target |
| Price History Lookup | 0.58 | 1.49 | < 100 | Within Target |

*Note per AGENTS.md Rule 14: Benchmark latencies measured locally using SQLite / AsyncEngine in automated test runner; live PostgreSQL execution under production concurrency will be verified on staging CI.*
