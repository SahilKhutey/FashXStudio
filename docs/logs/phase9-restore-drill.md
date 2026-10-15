# Disaster Recovery & Restore Drill Procedure (Phase 9)

**Status**: NOT YET PERFORMED (Staging environment not yet provisioned)  
**Target SLAs**: RPO ≤ 24 Hours, RTO ≤ 4 Hours  
**Invariant to Test**: Rule 9.8 Erasure Replay Invariant (Zero user resurrects)  

> [!WARNING]
> This drill has **not yet been executed** against live AWS infrastructure. The timeline below represents the operational procedure and acceptance criteria to be followed during the live staging restore drill in Step E.

---

## 1. Planned Drill Execution Procedure

| Step | Action / State | Verification Criteria |
| :--- | :--- | :--- |
| **0** | Trigger daily RDS automated snapshot in staging. | Snapshot state `available`. |
| **1** | Synthetic user deletion: submit erasure request for test user. | Tombstone recorded in `erasure_tombstones`. |
| **2** | Simulate catastrophic failure: terminate primary staging database. | Health check `/healthz/ready` reports database down. |
| **3** | Initiate recovery via AWS CLI/console from snapshot. | Provisioning begins within 5 minutes. |
| **4** | Restored instance storage attached and state transitioned to `available`. | Target: < 1 hour. |
| **5** | Update application database URL to point to restored instance. | Connection pool initialized. |
| **6** | Execute tombstone replay: `python scripts/maintenance/replay_erasure.py`. | Erased user records re-purged from restored DB. |
| **7** | Execute automated smoke test suite: `python scripts/release/smoke.py`. | All endpoints return 200 OK. |

---

## 2. Acceptance Criteria

- **Achieved Recovery Time (RTO)**: Target **≤ 4 Hours**.
- **Achieved Recovery Point (RPO)**: Target **≤ 24 Hours**.
- **Rule 9.8 Tombstone Invariant**: Zero resurrection of deleted users.
