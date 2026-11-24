# Phase 07.7 — Virtual Try-On (VTO) Quality Evaluation

## 1. Executive Summary & Objective

Phase 07.7 establishes a repeatable, permission-controlled, auditable evaluation framework that measures whether FashXStudio's virtual try-on renders are visually convincing, preserve garment characteristics, align correctly with the shopper's body, and avoid misleading representations.

The core engineering invariant:
**Technical job success is not visual quality, and visual quality is not physical fit accuracy.**

A generated image can return HTTP 200 and decode cleanly while still being completely unacceptable to show a real shopper because:
1. The garment's design, print, neckline, sleeves, or colour has been distorted or hallucinated.
2. The garment is unnaturally positioned or floating on the body.
3. The shopper's facial features, identity, or skin tone have been altered.
4. Unnatural body artifacts (e.g. extra fingers, blurry limbs) or background discontinuities are present.
5. The image falsely implies exact sizing, length, or fit that the model cannot guarantee.
6. The garment category (e.g. sarees, lehengas, multi-piece ethnic layers) is not reliably supported by the inference model.

---

## 2. Evaluation Architecture

```
                    +--------------------------------+
                    |  Controlled Evaluation Dataset |
                    |  (Consented & Authorized Pairs)|
                    +---------------+----------------+
                                    |
                                    v
                    +--------------------------------+
                    |   Permission & Governance Gate |
                    |   (Consent, Scope, Retention)  |
                    +---------------+----------------+
                                    |
                                    v
                    +--------------------------------+
                    | Frozen Provider Configuration  |
                    | (Model, Prompt, Preprocessing) |
                    +---------------+----------------+
                                    |
                                    v
                    +--------------------------------+
                    | Production TryOn Execution Run |
                    | (Durable Jobs, Metrics, Usage) |
                    +---------------+----------------+
                                    |
            +-----------------------+-----------------------+
            |                                               |
            v                                               v
+-------------------------+                     +-------------------------+
| Automated Image Metrics |                     | Blind Human Evaluation  |
| (SSIM, Delta-E, Masking)|                     | (3 Independent Reviewers|
+------------+------------+                     |  Across 6 Dimensions)   |
             |                                  +------------+------------+
             |                                               |
             +----------------------+------------------------+
                                    |
                                    v
                    +--------------------------------+
                    | Category Gate Acceptance Engine|
                    | (Pass / Needs Review / Block)  |
                    +---------------+----------------+
                                    |
                    +---------------+---------------+
                    |                               |
                    v                               v
       +-------------------------+     +-------------------------+
       |    APPROVED_LIMITED     |     |   BLOCKED / RESTRICTED  |
       |  (e.g. T-shirts, Tops)  |     | (e.g. Sarees, Lehengas) |
       +-------------------------+     +-------------------------+
```

---

## 3. Milestones & Work Breakdown

| Milestone | Scope | Engineering Deliverables |
|---|---|---|
| **07.7-A** | Repository Audit & Evaluation Architecture | Gap analysis, system audit, evaluation architecture spec. |
| **07.7-B** | Dataset Governance & Permissions | Consent tracking models, permission verification, retention rules. |
| **07.7-C** | Dataset Specification & Manifest | `manifest.v1.jsonl`, diversity annotations, negative cases. |
| **07.7-D** | Evaluation Pipeline & Runner | `contracts.py`, `runner.py`, configuration snapshot, metrics. |
| **07.7-E** | Quality Ratings & Scoring Engine | `ratings.py`, 6-dimension rubric, reviewer agreement stats. |
| **07.7-F** | Automated Image Metrics | `image_metrics.py`, SSIM, Delta-E CIEDE2000 color fidelity. |
| **07.7-G** | Category Gate & Policy Enforcement | `category_gate.py`, state machine (`APPROVED_LIMITED`, `BLOCKED`). |
| **07.7-H** | Database Schema & Migration 0054 | Evaluation tables, Alembic migration `0054`. |
| **07.7-I** | Verification & Comprehensive Tests | 5 test suites covering `DATA-*`, `DIV-*`, `EVAL-*`, `QUAL-*`, `GATE-*`. |
| **07.7-J** | Engineering Documentation & Sign-off | 18 technical specifications covering all evaluation protocols. |
