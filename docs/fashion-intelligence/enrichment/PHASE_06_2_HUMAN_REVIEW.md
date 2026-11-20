# Phase 06.2 — Human Review Workflow Specification

## 1. Review Workflow

```mermaid
sequenceDiagram
    participant O as Enrichment Orchestrator
    participant R as Review Service
    participant H as Authorized Reviewer
    participant DB as Audit Log DB

    O->>R: create_review_task(flags, proposed_val, evidence)
    H->>R: list_pending_reviews(merchant_id)
    H->>R: inspect_evidence()
    H->>R: submit_decision(APPROVE | CORRECT | REJECT)
    R->>DB: record_audit_event(actor_id, action, previous_val, new_val)
    R-->>O: update_attribute_status()
```

## 2. Reviewer Capabilities

1. **Approve**: Confirms proposed attribute value with recorded audit reason.
2. **Correct**: Updates attribute value to a valid Phase 06.1 taxonomy term. Preserves previous value in audit history.
3. **Reject**: Discards proposed value, preventing it from publishing to search indexing.
4. **Mark Unknown**: Marks attribute as `UNKNOWN` when source evidence is genuinely absent.

## 3. Tenant Isolation and Role Security

- `PLATFORM_ADMIN` & `PLATFORM_REVIEWER`: Can inspect and decide reviews across all merchants.
- `MERCHANT_REVIEWER`: Strictly restricted to reviewing products belonging to their authenticated `merchant_id`. Cross-merchant review attempts raise `ReviewPermissionError` (403 Forbidden).
