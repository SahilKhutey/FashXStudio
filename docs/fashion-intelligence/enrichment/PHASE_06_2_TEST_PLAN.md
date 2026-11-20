# Phase 06.2 — Acceptance Test Plan

## 1. Test Matrix Mapping

| Test ID | Test Description | Target Module |
|---|---|---|
| **ENR-001** | Valid enrichment input accepted | `test_contracts.py` |
| **ENR-002** | Missing product ID rejected | `test_contracts.py` |
| **ENR-003** | Missing taxonomy version rejected | `test_contracts.py` |
| **ENR-004** | Empty product title rejected | `test_contracts.py` |
| **ENR-005** | Extract garment type from title | `test_title_extractor.py` |
| **ENR-006** | Extract fit from title | `test_title_extractor.py` |
| **ENR-007** | Extract color from title | `test_title_extractor.py` |
| **ENR-008** | Extract pattern from title | `test_title_extractor.py` |
| **ENR-009** | Extract occasion from title | `test_title_extractor.py` |
| **ENR-010** | Unknown category quarantined | `test_category_mapper.py` |
| **ENR-011** | Unsupported taxonomy value rejected | `test_orchestrator.py` |
| **ENR-012** | Unknown material remains unknown | `test_orchestrator.py` |
| **ENR-013** | Fabric blend without percentages | `test_orchestrator.py` |
| **ENR-014** | Image-only fabric inference rejected | `test_policy.py` |
| **ENR-015** | Missing size information remains not provided | `test_orchestrator.py` |
| **ENR-016** | AI attempts to invent sizes blocked | `test_policy.py` |
| **ENR-017** | AI attempts to invent fabric percentages blocked | `test_policy.py` |
| **ENR-018** | Invalid evidence reference rejected | `test_evidence.py` |
| **ENR-019** | Conflicting color evidence triggers review | `test_orchestrator.py` |
| **ENR-020** | Low-confidence occasion triggers review | `test_confidence.py` |
| **ENR-021** | High-confidence supported attribute auto-accepted | `test_confidence.py` |
| **ENR-022** | AI output containing unknown field rejected | `test_contracts.py` |
| **ENR-023** | Text processing permission absent blocks run | `test_orchestrator.py` |
| **ENR-024** | Image AI permission absent blocks visual analysis | `test_orchestrator.py` |
| **ENR-026** | Duplicate enrichment job has identical idempotency key | `test_orchestrator.py` |
| **ENR-027** | Failed model provider request exhausts bounded retry | `test_orchestrator.py` |
| **ENR-028** | Reviewer approves attribute with audit event | `test_review_service.py` |
| **ENR-029** | Reviewer corrects attribute with history retained | `test_review_service.py` |
| **ENR-030** | Reviewer rejects attribute preventing publishing | `test_review_service.py` |
| **ENR-031** | Cross-merchant review access denied | `test_review_service.py` |
| **ENR-033** | Existing accepted value preserved against uncertain prediction | `test_orchestrator.py` |
| **ENR-035** | Model output with prompt injection treated as data | `test_orchestrator.py` |
| **DB-ENR** | Database persistence, cascades, and relationships | `test_phase06_2_enrichment_database.py` |
