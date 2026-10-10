# Phase 7: Discovery Feed Latency & Load Benchmark

**Date**: 2026-10-10  
**Concurrency**: 50 virtual users  
**Total Requests**: 200 (Page 1 & Page 2 mix)  
**Throughput**: 177.6 QPS  
**Pre-registered Target**: p95 <= 300 ms  

## Latency Distribution

| Percentile | Latency (ms) | Target | Result |
|---|---|---|---|
| **p50** | **1.6 ms** | <= 100 ms | **PASS** |
| **p90** | **48.4 ms** | <= 200 ms | **PASS** |
| **p95** | **60.1 ms** | <= 300 ms | **PASS** |
| **p99** | **88.6 ms** | <= 450 ms | **PASS** |
| **Max** | **121.3 ms** | <= 600 ms | **PASS** |
| **Mean** | **17.0 ms** | - | - |

## Breakdown by Pipeline Stage

| Stage | Typical Duration | Server-Timing Key |
|---|---|---|
| Hard Invariant Filtering & Relaxation Ladder | ~4-7 ms | `retrieval` |
| 11-Feature Weighted Scoring | ~8-14 ms | `scoring` |
| Constrained MMR Diversification | ~4-8 ms | `mmr` |
| Truthful Stylist Explanations | ~1-2 ms | `explanation` |

## Observations & Decision

- Under concurrent load of 50 virtual users across multiple feed pages, p95 latency is **60.1 ms**, well under the 300 ms threshold.
- Exact in-memory numpy scoring and constrained MMR execute reliably without database contention.
- Cache invalidation upon positive signal keeps session state fresh without incurring repeat computation during rapid pagination.
