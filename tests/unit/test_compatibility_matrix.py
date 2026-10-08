from fashx.recommendation.compatibility import CompatibilityMatrix


def test_color_harmony_warm_undertone() -> None:
    # Olive on warm undertone should score 1.0
    res_warm_olive = CompatibilityMatrix.evaluate(
        user_undertone="warm",
        user_build="regular",
        garment_color="olive",
        garment_cut="regular",
    )
    assert res_warm_olive.color_score == 1.0
    assert "harmonizes" in res_warm_olive.color_reason.lower()


def test_color_harmony_cool_undertone() -> None:
    # White on cool undertone should score 1.0
    res_cool_white = CompatibilityMatrix.evaluate(
        user_undertone="cool",
        user_build="regular",
        garment_color="white",
        garment_cut="regular",
    )
    assert res_cool_white.color_score == 1.0
    assert "complements" in res_cool_white.color_reason.lower()


def test_silhouette_compatibility_athletic_build() -> None:
    # Slim cut on athletic build should score high
    res = CompatibilityMatrix.evaluate(
        user_undertone="neutral",
        user_build="athletic",
        garment_color="navy",
        garment_cut="slim",
    )
    assert res.silhouette_score >= 0.95
    assert "athletic" in res.silhouette_reason.lower()


def test_silhouette_compatibility_broad_build_penalizes_skinny() -> None:
    # Slim/skinny cut on broad build scores lower
    res = CompatibilityMatrix.evaluate(
        user_undertone="neutral",
        user_build="broad",
        garment_color="navy",
        garment_cut="slim",
    )
    assert res.silhouette_score <= 0.70
