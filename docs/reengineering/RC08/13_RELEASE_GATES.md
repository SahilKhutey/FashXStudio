# RC08 — Release Gates & Hard Stop Rules

## 1. Release Gates (G1–G6)
Release gates must be verified by real environment evidence before advancing to public rollout. Automated CI passes alone do not clear these gates.

| Gate | Title | Target Threshold | Required Verification Method |
|---|---|---|---|
| **G1** | Real Stack | 100% user journey passes | Physical device testing on staging environment |
| **G2** | ML Quality | VLM accuracy ≥ 90%; NDCG@10 ≥ 0.75 | Human-labeled evaluation dataset |
| **G3** | VTO Quality | Realism score ≥ 3.5/5; p95 ≤ 45s | Consented test cohort evaluation under real provider load |
| **G4** | Privacy & Recovery | Counsel sign-off; RTO ≤ 4h | Legal review documentation and live restore drill |
| **G5** | Commercial Permissions | 100% license-cleared catalog sources | Signed retailer & vendor agreements on file |
| **G6** | Closed Pilot | 20–40 participants; ≥ 75% acceptable realism | Completed closed pilot report and feedback synthesis |

## 2. Hard Stop Conditions (Immediate Pilot Halt)
Any of the following conditions triggers an immediate freeze and rollback:
1. **Cross-User Data Leakage**: Any incident where User A accesses User B's images, wardrobe, or profile.
2. **Public Image Exposure**: Any personal photo or try-on artifact accessible without a valid signed URL.
3. **Mock in Production**: Mock authentication or mock try-on active in production settings.
4. **Data Loss / Restore Failure**: Inability to restore database or verify data integrity during restore drills.
5. **Cascading Erasure Failure**: User account deleted in database while photos remain in S3.
6. **Uncontrolled Inference Costs**: Daily inference spend exceeding approved budget caps.
