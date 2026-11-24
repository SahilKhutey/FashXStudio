# Independent Human Review Procedure

## 1. Reviewer Allocation & Blind Evaluation

1. **Independent Panel**: Each evaluated output is reviewed by at least 3 independent reviewers who were not involved in prompt engineering or model tuning.
2. **Double-Blind**: Reviewers are presented with:
   - Reference garment image
   - Reference shopper portrait
   - Generated try-on output
   Reviewers **never see** provider brand names, model version tags, latency figures, or configuration identifiers.

---

## 2. Divergence & Consensus Adjudication

- Ratings on any single dimension that diverge by more than 1.5 points trigger `disagreement_detected = True`.
- Items with rater divergence are automatically queued for a fourth senior fashion specialist reviewer for adjudication.
- If **any** reviewer flags a `critical_issue`, the item's consensus decision is automatically marked `REJECT`.
