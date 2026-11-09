# RC12: Public Beta Release Gates (G1–G6)

## 1. Release Gate Criteria & Status
Evaluated via [`scripts/rc12/beta_gates.py`](file:///c:/Users/ASUS/Documents/FashXStudio/scripts/rc12/beta_gates.py):

| Gate | Description | Criteria | Status | Evidence Reference |
| :--- | :--- | :--- | :--- | :--- |
| **G1** | Real-Stack User Journey | Profile, feed, VTO, closet, redirect on PostgreSQL | 🟡 UNVERIFIED | Pending live cloud staging run |
| **G2** | Production Hardening | Zero migrations pending, CI green, health checks | 🟢 VERIFIED | CI workflows green, alembic check |
| **G3** | VTO Quality & SLA | Real provider verified, P95 $\le 45\text{s}$, quality score | 🟡 UNVERIFIED | Pending live vendor API run |
| **G4** | Privacy, Legal & Erasure | Signed S3 URLs, GDPR/DPDP erasure, ownership | 🟢 VERIFIED | Security test suites pass |
| **G5** | Catalog & Merchant Rights | 100% verified commercial feed agreements | 🟡 UNVERIFIED | Commercial partner agreement pending |
| **G6** | Real-User Pilot Validation | Frozen pilot Must-Haves (M1–M5) verified | 🟡 UNVERIFIED | RC11 pilot cohort run pending |

**Public Beta Decision**: **`HOLD`**  
*Public beta authorization requires all six gates (G1–G6) to evaluate to `PASS` with authentic human evidence cards.*
