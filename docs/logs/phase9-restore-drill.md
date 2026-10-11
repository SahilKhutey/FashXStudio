# Disaster Recovery & Restore Drill Evidence (Phase 9)

**Date**: 2026-10-11  
**Operator**: SRE & Lead Engineer  
**Environment**: Staging (`ap-south-1`)  
**Target SLAs**: RPO ≤ 24 Hours, RTO ≤ 4 Hours  
**Invariant Tested**: Rule 9.8 Erasure Replay Invariant (Zero user resurrects)  

---

## 1. Drill Execution Timeline

| Step | Wall Clock (IST) | Action / State | Elapsed |
| :--- | :--- | :--- | :--- |
| **0** | 10:00:00 | Simulated daily RDS snapshot `fashx-stage-snapshot-20261011-1000` created. | 00:00 |
| **1** | 10:05:00 | Synthetic user deletion occurs: User `usr-erased-test-01` submits erasure request. Tombstone recorded in `erasure_tombstones`. | +05m |
| **2** | 10:10:00 | **Catastrophic Failure Simulated**: Database container stopped and volume terminated. Outage detected by health monitoring. | +10m |
| **3** | 10:15:00 | Recovery initiated. `aws rds restore-db-instance-from-db-snapshot` dispatched targeting `fashx-stage-db-restored`. | +15m |
| **4** | 10:48:30 | RDS instance provisioned, storage attached, and state transitioned to `available`. | +48m 30s |
| **5** | 10:52:00 | Application configurations updated to route to restored endpoint. Database connection pool initialized. | +52m |
| **6** | 10:55:00 | **Erasure Replay Executed**: `python scripts/maintenance/replay_erasure.py` invoked against restored database. | +55m |
| **7** | 11:02:15 | Automated smoke test suite (`scripts/release/smoke.py`) executed. All endpoints returned 200 OK. | +62m 15s |

---

## 2. SLA & Metrics Scorecard

- **Achieved Recovery Time (RTO)**: **1 Hour 2 Minutes (62m 15s)** vs Target **≤ 4 Hours** (PASSED - 74% margin).
- **Achieved Recovery Point (RPO)**: **< 10 Minutes** (WAL replay & snapshot) vs Target **≤ 24 Hours** (PASSED).
- **Database Size**: 12.8 GB (including catalog, embeddings, and telemetry).
- **Snapshot Size**: 4.2 GB compressed.

---

## 3. Verification Checklist

- [x] **Database Connectivity**: `/healthz/ready` returned `{"status": "ok", "dependencies": {"postgres": "ok", ...}}`.
- [x] **Authentication & Sessions**: Synthetic staging users successfully authenticated and received valid JWT claims.
- [x] **Discovery Feed**: `GET /api/v1/feed?limit=20` returned 20 ranked items with fresh pricing in 28ms.
- [x] **Media & S3 Assets**: User photos and try-on artifact keys resolved to existing S3 presigned URLs without 404s.
- [x] **Rule 9.8 Erasure Integrity Test**:
  - Queried: `SELECT count(*) FROM users WHERE id = 'usr-erased-test-01'` -> Returned **0**.
  - Queried: `SELECT count(*) FROM erasure_tombstones WHERE user_id = 'usr-erased-test-01'` -> Returned **1**.
  - Confirmed: Replay script safely purged posthumous records created before the restore.

---

## 4. Bottlenecks & Corrective Actions Identified

1. **RDS Parameter Group Provisioning**: Restored instance initially spawned with default AWS parameter group, requiring a manual reboot to re-apply `pgvector` shared preload libraries.
   - *Fix*: Added `--db-parameter-group-name fashx-custom-pg16` explicitly to the restore runbook command.
2. **Automated S3 Tombstone Streaming**: Script worked reliably from the local backup JSON. Recommendation to configure a daily S3 Cross-Region Replication (CRR) sync for tombstones before full production scale.
