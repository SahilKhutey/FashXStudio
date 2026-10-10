"""Property test verifying zero hallucinated stylist explanations across 50 personas (Step 7.19)."""

import random

from eval.persona_to_context import load_personas
from fashx.discovery.pipeline import load_weights_config, rank
from tests.discovery.factories import random_persona_context


def test_zero_hallucinations_across_50_personas() -> None:
    personas = list(load_personas("eval/personas.yml"))
    # Generate up to 50 personas
    idx = 0
    while len(personas) < 50:
        personas.append(random_persona_context(random.Random(100 + idx)))
        idx += 1

    weights, _ = load_weights_config("v1")

    for p in personas:
        top_items = rank(p, page=0, limit=5, ranker="v1")
        for item in top_items:
            # Inspect item features stored during ranking to verify reason authenticity
            f = item.features
            contrib = {k: weights.get(k, 0.0) * f.get(k, 0.0) for k in f}

            for feat_key, _ in item.reasons:
                assert feat_key in f, f"Reason key {feat_key} does not exist in features"
                # Pre-registered property: feature score >= 0.6 and contribution >= 0.05
                assert f[feat_key] >= 0.599, (
                    f"Feature {feat_key} has low value {f[feat_key]} but was given as reason for {item.title}"
                )
                assert contrib[feat_key] >= 0.049, (
                    f"Feature {feat_key} contribution {contrib[feat_key]} below threshold"
                )
