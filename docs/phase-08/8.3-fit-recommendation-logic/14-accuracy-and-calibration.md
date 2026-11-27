# 14 — Accuracy & Calibration Methodology (`evaluation/metrics.py`, `report.py`)

## Core Metrics Computed

- **Coverage**: `recommendations_made / total_cases`
- **Abstention rate**: `abstentions_made / total_cases`
- **Selective exact-size accuracy**: exact matches over recommendations made
- **Acceptable-size accuracy**: predictions within `{expected_size} | acceptable_sizes` over recommendations made
- **False recommendation rate**: recommendations issued when ground truth required abstention or no-match
- **No-match detection rate**
- **Per-category & per-merchant slices** with explicit `small_sample_warning` when `< 30` cases
- **Calibration bins** across intervals (`0.50-0.59` through `0.90-1.00`), gating `calibration_demonstrated`

## Target Release Gates (Pending Real Labelled Dataset)

| Gate | Target Threshold |
|---|---|
| False recommendation rate | `<= 0.05` |
| Exact-size accuracy (recommended) | `>= 0.80` |
| Acceptable-size accuracy | `>= 0.90` |
| Required-evidence violations | `0` |
| Unsupported category recommendations | `0` |
| Unauthorized chart use | `0` |
| Stale chart recommendations | `0` |
