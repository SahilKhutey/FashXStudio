# Phase 06.2 — Execution and Developer Guide

## 1. Local Testing and Verification

To execute all unit and integration tests for Phase 06.2:

```bash
# Run enrichment unit test suite
python -m pytest tests/unit/catalog/enrichment/ -v

# Run database integration test
python -m pytest tests/integration/catalog/test_phase06_2_enrichment_database.py -v

# Run combined taxonomy and enrichment test suite
python -m pytest tests/unit/catalog/taxonomy/ tests/unit/catalog/enrichment/ tests/integration/catalog/ -v
```

## 2. Running Static Analysis

```bash
# Check formatting and lint rules
ruff check .

# Check static typing across all source files
mypy .

# Verify documentation links
python scripts/docs_lint.py
```
