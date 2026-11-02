# VTO Phase 9 Quality Evaluation Scorecard Template

> **Notice:** Specification and evaluation protocol document. In accordance with repository rules, no simulated measurements, fake human ratings, or synthetic partner scores are claimed here. Live evaluation metrics are computed exclusively from verified test runs or authenticated founder evaluations.

## 1. Evaluation Protocol

The quality scorecard summarizes perceived visual realism, artifact defect rates, and user purchase confidence for candidate AI inference models and adapters.

### Release Gate Thresholds
- **Minimum Acceptable Realism Rate**: $\ge 80\%$ of evaluated samples rated `accurate` (score 4) or `very_accurate` (score 5).
- **Maximum Critical Defect Rate**: $< 5\%$ of samples tagged with `wrong_garment` or severe `person_appearance_changed`.
- **Minimum Mean Purchase Confidence**: $\ge 3.5$ on a 1–5 scale.

## 2. Metrics Definition & Calculation

Computed via `fashx.tryon.evaluation.summarize_visual_ratings`:

| Metric | Formula | Description |
|---|---|---|
| **Total Samples** | $N$ | Number of evaluated generations |
| **Acceptable Count** | $\sum [s_i \ge \text{threshold}]$ | Count of samples rated `accurate` or `very_accurate` |
| **Acceptable Rate** | $\frac{\text{Acceptable Count}}{N}$ | Percentage of acceptable generations |
| **Mean Realism Score** | $\frac{1}{N} \sum_{i=1}^N \text{Score}(r_i)$ | Mean accuracy score (1 to 5) |
| **Mean Purchase Confidence** | $\frac{1}{M} \sum_{i=1}^M \text{Conf}_i$ | Mean purchase confidence (1 to 5) across samples reporting confidence |

## 3. Defect Taxonomy

Defects are tracked across 7 standardized issue tags:
- `unnatural_fit`: Fabric drape or sizing looks disproportionate to body frame.
- `garment_distorted`: Garment shape, sleeves, or seams are unnaturally warped.
- `color_inaccurate`: Garment color significantly departs from catalog asset.
- `blurry_artifacts`: Edge blurring, smudging, or pixelation along boundaries.
- `person_appearance_changed`: Unintended modifications to face, hair, or skin tone.
- `wrong_garment`: Garment substituted or blended with background clothes.
- `occlusion_error`: Failure to properly render hands, arms, hair, or accessories over garment.

## 4. Scorecard Recording Format

```markdown
### Evaluation Run: [Candidate Model / Version]
- Evaluator(s): [Founder / Team]
- Dataset: `docs/evaluation/vto-benchmark-manifest.md`
- Total Evaluated: [N]
- Acceptable Rate: [Pct]%
- Mean Realism Score: [Score] / 5.0
- Top Observed Issues:
  1. [Tag 1] ([Count])
  2. [Tag 2] ([Count])
- Verdict: [🟢 Approved for Release / 🟡 Needs Tuning]
```
