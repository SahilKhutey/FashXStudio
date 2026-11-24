# Release Approval Protocol & Category Decisions

## 1. Approval Authority & Workflow

Category release decisions follow a formal sign-off hierarchy:

```
[ Automated Quality Gate (evaluate_category) ]
                     |
                     v
[ Independent Reviewer Consensus (Ratings >= 3.8, Crit = 0) ]
                     |
                     v
[ Engineering Lead Audit (Traceable Git & Model Versions) ]
                     |
                     v
[ Human Founder Sign-Off (Recorded in tryon_evaluation_category_gates) ]
```

---

## 2. Release Eligibility Checklist

Before marking any category `APPROVED_LIMITED` in production:
- [ ] At least 30 diverse, consented image pairs evaluated.
- [ ] Job success rate $\ge 90\%$.
- [ ] Garment preservation $\ge 3.8/5.0$.
- [ ] Body alignment $\ge 3.8/5.0$.
- [ ] Identity preservation $\ge 4.0/5.0$.
- [ ] Critical misleading outputs = 0.
- [ ] Signed off by authorized human founder.
- [ ] Exact model, configuration, and prompt versions locked in database record.
