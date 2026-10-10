"""Unit test verifying that all 11 scoring features return floats strictly in [0.0, 1.0] (Step 7.17)."""

import random

from eval.persona_to_context import load_personas
from fashx.discovery.catalog_data import get_catalog_items
from fashx.discovery.pipeline import compute_features
from tests.discovery.factories import random_persona_context


def test_all_11_features_bounded_in_unit_interval() -> None:
    pool = get_catalog_items()
    personas = list(load_personas("eval/personas.yml"))
    # Add random synthetic personas
    for i in range(10):
        personas.append(random_persona_context(random.Random(42 + i)))

    expected_feature_keys = {
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
        "tryon",
    }

    assert len(expected_feature_keys) == 11

    # Test across sampled catalog items and all personas
    sample_items = pool[:30]
    for p in personas:
        for it in sample_items:
            feats = compute_features(it, p)
            assert set(feats.keys()) == expected_feature_keys
            for feat_name, val in feats.items():
                assert isinstance(val, (float, int)), f"Feature {feat_name} is not numeric: {type(val)}"
                assert 0.0 <= val <= 1.0, f"Feature {feat_name} out of bounds: {val} for persona {p.id}"
