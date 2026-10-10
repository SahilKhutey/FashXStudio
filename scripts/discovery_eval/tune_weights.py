"""Weight tuning via coordinate ascent with train/holdout split (Step 7.20).

Hold out: p04, p08, p12.
Train: p01, p02, p03, p05, p06, p07, p09, p10, p11.
Decision rule: write v2.yml ONLY if holdout nDCG@10 improves by >= 0.02 over v1.
"""

import argparse
import copy
import pathlib
import sys

import numpy as np
import yaml

from eval.persona_to_context import load_personas
from fashx.discovery.catalog_data import get_catalog_items
from fashx.discovery.pipeline import DEFAULT_WEIGHTS, compute_features, mmr_select
from scripts.discovery_eval.metrics import ndcg_at_k
from scripts.discovery_eval.score import load_judgments

HOLDOUT_IDS = {"p04", "p08", "p12"}


def rank_with_custom_weights(
    ctx,
    weights: dict[str, float],
    pool,
    limit: int = 20,
    lam: float = 0.7,
) -> list[str]:
    """Fast candidate ranking with custom weight dictionary."""
    hard_candidates = []
    for it in pool:
        if it.source_status != "cleared":
            continue
        if not (it.status == "active" and it.in_stock):
            continue
        if it.price_age_hours > 72.0:
            continue
        if it.age_group == "kids":
            continue
        if it.gender not in ctx.genders:
            continue
        if it.id in ctx.hidden_ids or it.id in ctx.saved_ids:
            continue
        if not (set(it.sizes_in_stock) & set(ctx.sizes)):
            continue
        hard_candidates.append(it)

    if not hard_candidates:
        return []

    # Filter by budget
    surviving = [it for it in hard_candidates if ctx.budget_min <= it.price <= ctx.budget_max * 1.5]
    if not surviving:
        surviving = hard_candidates

    emb_matrix = np.array([it.embedding for it in surviving])
    rel_scores = []

    for it in surviving:
        f = compute_features(it, ctx)
        contrib = sum(weights.get(k, 0.0) * f.get(k, 0.0) for k in f)
        rel_scores.append(contrib)

    rel_arr = np.array(rel_scores, dtype=np.float32)
    brands = [it.brand for it in surviving]
    sources = [str(it.source_id) for it in surviving]
    sub_cats = [it.sub_category for it in surviving]

    selected_idx = mmr_select(
        emb=emb_matrix,
        rel=rel_arr,
        brand=brands,
        source=sources,
        sub_categories=sub_cats,
        k=min(len(surviving), limit),
        lam=0.5 if ctx.cold_start else lam,
        max_per_brand=3,
        max_source_share=0.6,
        max_per_subcat=3,
    )

    return [str(surviving[idx].id) for idx in selected_idx]


def evaluate_set_ndcg(
    personas_subset,
    weights: dict[str, float],
    judgments: dict[str, dict[str, int]],
    pool,
    k: int = 10,
) -> float:
    scores = []
    for p in personas_subset:
        ranked_ids = rank_with_custom_weights(p, weights, pool, limit=k)
        p_judgments = judgments.get(p.id, {})
        val = ndcg_at_k(ranked_ids, p_judgments, k=k)
        scores.append(val)
    return float(np.mean(scores)) if scores else 0.0


def tune_weights(
    personas_path: str = "eval/personas.yml",
    judgments_path: str = "eval/judgments.csv",
    max_iters: int = 10,
    step: float = 0.05,
    min_improvement: float = 0.005,
) -> dict:
    all_personas = load_personas(personas_path)
    train_personas = [p for p in all_personas if p.id not in HOLDOUT_IDS]
    holdout_personas = [p for p in all_personas if p.id in HOLDOUT_IDS]
    judgments = load_judgments(judgments_path)
    pool = get_catalog_items()

    # Load baseline v1 weights
    v1_weights = DEFAULT_WEIGHTS.copy()
    current_weights = copy.deepcopy(v1_weights)

    initial_train_ndcg = evaluate_set_ndcg(train_personas, current_weights, judgments, pool)
    initial_holdout_ndcg = evaluate_set_ndcg(holdout_personas, current_weights, judgments, pool)

    best_train_ndcg = initial_train_ndcg
    iteration_log = []

    tunable_keys = [
        "taste",
        "style",
        "occasion",
        "formality",
        "color",
        "skin_harmony",
        "size_fit",
        "price",
        "freshness",
        "popularity",
    ]

    for it in range(max_iters):
        improved = False
        for key in tunable_keys:
            orig_val = current_weights[key]
            best_val = orig_val
            best_step_ndcg = best_train_ndcg

            # Try +step and -step
            for delta in [step, -step]:
                cand_val = round(max(0.0, min(1.5, orig_val + delta)), 3)
                if cand_val == orig_val:
                    continue
                current_weights[key] = cand_val
                cand_ndcg = evaluate_set_ndcg(train_personas, current_weights, judgments, pool)

                if cand_ndcg > best_step_ndcg + min_improvement:
                    best_step_ndcg = cand_ndcg
                    best_val = cand_val
                    improved = True

            current_weights[key] = best_val
            best_train_ndcg = best_step_ndcg

        iteration_log.append({
            "iter": it + 1,
            "train_ndcg": best_train_ndcg,
            "weights": copy.deepcopy(current_weights),
        })

        if not improved:
            break

    final_holdout_ndcg = evaluate_set_ndcg(holdout_personas, current_weights, judgments, pool)
    holdout_delta = final_holdout_ndcg - initial_holdout_ndcg
    cleared_threshold = holdout_delta >= 0.02

    return {
        "initial_train_ndcg": initial_train_ndcg,
        "final_train_ndcg": best_train_ndcg,
        "initial_holdout_ndcg": initial_holdout_ndcg,
        "final_holdout_ndcg": final_holdout_ndcg,
        "holdout_delta": holdout_delta,
        "cleared_threshold": cleared_threshold,
        "v1_weights": v1_weights,
        "tuned_weights": current_weights,
        "iterations": len(iteration_log),
        "history": iteration_log,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="docs/logs/phase7-tuning.md")
    args = parser.parse_args()

    results = tune_weights()

    lines = []
    lines.append("# Phase 7: Ranker Weight Tuning & Coordinate Ascent")
    lines.append("")
    lines.append("**Date**: 2026-10-10  ")
    lines.append("**Train Personas (9)**: p01, p02, p03, p05, p06, p07, p09, p10, p11  ")
    lines.append("**Holdout Personas (3)**: p04 (Professional), p08 (Wedding/Royal), p12 (Relaxed Fit)  ")
    lines.append("**ADR-0006 Promotion Threshold**: Holdout nDCG@10 >= +0.020  ")
    lines.append("")
    lines.append("## Optimization Scorecard")
    lines.append("")
    lines.append("| Metric | Baseline (v1) | Tuned Candidate | Delta | Promotion Status |")
    lines.append("|---|---|---|---|---|")
    lines.append(f"| **Train nDCG@10 (9 Personas)** | {results['initial_train_ndcg']:.4f} | {results['final_train_ndcg']:.4f} | +{results['final_train_ndcg'] - results['initial_train_ndcg']:.4f} | - |")
    lines.append(f"| **Holdout nDCG@10 (3 Personas)** | {results['initial_holdout_ndcg']:.4f} | {results['final_holdout_ndcg']:.4f} | **{'+' if results['holdout_delta'] >= 0 else ''}{results['holdout_delta']:.4f}** | **{'PROMOTE TO V2' if results['cleared_threshold'] else 'REJECT V2 (KEEP V1)'}** |")
    lines.append("")
    lines.append("## Tuned Weights Comparison")
    lines.append("")
    lines.append("| Feature | v1 Baseline Weight | Tuned Weight | Rationale |")
    lines.append("|---|---|---|---|")
    for k, v1_w in results["v1_weights"].items():
        tun_w = results["tuned_weights"].get(k, v1_w)
        lines.append(f"| `{k}` | {v1_w:.2f} | {tun_w:.2f} | Coordinate ascent delta: {tun_w - v1_w:+.2f} |")

    lines.append("")
    lines.append("## Decision & Gate Action")
    lines.append("")
    if results["cleared_threshold"]:
        lines.append(f"- **Decision**: Holdout nDCG@10 improved by **+{results['holdout_delta']:.4f}** (>= +0.020 threshold). Candidate approved for promotion.")
        lines.append("- Writing `backend/fashx/discovery/weights/v2.yml`.")

        v2_data = {
            "version": "v2",
            "weights": {k: float(v) for k, v in results["tuned_weights"].items()},
            "mmr": {"lambda": 0.7, "max_per_brand": 3, "max_source_share": 0.6},
        }
        v2_path = pathlib.Path("backend/fashx/discovery/weights/v2.yml")
        v2_path.parent.mkdir(parents=True, exist_ok=True)
        with open(v2_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(v2_data, f, sort_keys=False)
    else:
        lines.append(f"- **Decision**: Holdout nDCG@10 delta was **{results['holdout_delta']:+.4f}** (< +0.020 required by ADR-0006).")
        lines.append("- In accordance with ADR-0006 non-negotiable decision rule: **v1 remains the active ranker**.")
        lines.append("- Candidate v2 was rejected to prevent overfitting to training judgments.")

    report = "\n".join(lines) + "\n"
    pathlib.Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(report)

    sys.stdout.buffer.write(
        f"Weight Tuning Complete: Train nDCG={results['final_train_ndcg']:.4f}, Holdout nDCG={results['final_holdout_ndcg']:.4f} (Delta={results['holdout_delta']:+.4f}, {'PROMOTED' if results['cleared_threshold'] else 'KEPT V1'}). Output written to {args.out}\n".encode()
    )


if __name__ == "__main__":
    main()
