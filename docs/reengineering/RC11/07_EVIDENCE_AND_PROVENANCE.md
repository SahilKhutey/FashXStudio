# RC11: Evidence Standards & Provenance Framework

## 1. Compliance with AGENTS.md Rules
- **Rule 1**: Only the human founder creates or modifies files in `docs/evidence/` or `docs/provenance.md`.
- **Rule 2**: No claims of pass/verification unless backed by exact command outputs pasted into replies.
- **Rule 3**: Simulated, synthetic, or test datasets must never be marked as real pilot evidence.

## 2. Evidence Card Structure (Human Founder Template)
When real participants complete cohorts, the human founder records evidence cards in `docs/evidence/RC11/`:

```markdown
---
evidence_id: EVD-RC11-YYYYMMDD-XX
metric_name: tryon_realism_mean
pilot_id: fashx-closed-beta-01
cohort: Wave1
collected_by: Human Founder Name
extraction_timestamp_utc: YYYY-MM-DDTHH:MM:SSZ
query_reference: scripts/pilot/tryon_quality.sql@commit_sha
evidence_type: real
numerator: 156
denominator: 38
sample_size: 38
exclusions: 0
raw_data: restricted://pilot/wave1/realism_export_20261120.csv
---

# Evidence Narrative
[Context, raw query outputs, confidence interval, and limitations.]
```

## 3. Data Quarantine
Non-real data (e.g. fixtures from unit tests, synthetic personas from MVP 8) are strictly flagged with `evidence_type: synthetic` or `test`. The pilot evaluator [`scripts/rc11/evaluate_pilot.py`](file:///c:/Users/ASUS/Documents/FashXStudio/scripts/rc11/evaluate_pilot.py) strictly aborts with `INCOMPLETE_EVIDENCE` if any non-real data is supplied for pilot claims.
