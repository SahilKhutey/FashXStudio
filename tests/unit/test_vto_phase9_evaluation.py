import pytest

from fashx.tryon.evaluation import (
    HumanVisualRating,
    VisualEvaluationSummary,
    summarize_visual_ratings,
)


def test_human_visual_rating_validation() -> None:
    # Valid creation
    rating = HumanVisualRating(
        sample_id="sample-001",
        visual_accuracy="accurate",
        issue_tags=["unnatural_fit", "unnatural_fit", "blurry_artifacts"],
        purchase_confidence=4,
        rater_id="evaluator-1",
    )
    assert rating.visual_accuracy == "accurate"
    assert rating.issue_tags == ["blurry_artifacts", "unnatural_fit"]
    assert rating.purchase_confidence == 4

    # Invalid visual accuracy
    with pytest.raises(ValueError, match="Invalid visual_accuracy"):
        HumanVisualRating(
            sample_id="sample-002",
            visual_accuracy="invalid_level",
        )

    # Invalid purchase confidence (< 1 or > 5)
    with pytest.raises(ValueError, match="Purchase confidence must be between 1 and 5"):
        HumanVisualRating(
            sample_id="sample-003",
            visual_accuracy="neutral",
            purchase_confidence=0,
        )

    with pytest.raises(ValueError, match="Purchase confidence must be between 1 and 5"):
        HumanVisualRating(
            sample_id="sample-004",
            visual_accuracy="neutral",
            purchase_confidence=6,
        )


def test_summarize_empty_ratings() -> None:
    summary = summarize_visual_ratings([])
    assert isinstance(summary, VisualEvaluationSummary)
    assert summary.total_samples == 0
    assert summary.acceptable_count == 0
    assert summary.acceptable_rate == 0.0
    assert summary.mean_accuracy_score is None
    assert summary.mean_purchase_confidence is None
    assert summary.accuracy_counts["accurate"] == 0
    assert summary.issue_tag_counts["unnatural_fit"] == 0


def test_summarize_mixed_ratings() -> None:
    ratings = [
        HumanVisualRating(
            sample_id="s1",
            visual_accuracy="very_accurate",  # 5
            issue_tags=[],
            purchase_confidence=5,
        ),
        HumanVisualRating(
            sample_id="s2",
            visual_accuracy="accurate",  # 4
            issue_tags=["color_inaccurate"],
            purchase_confidence=4,
        ),
        HumanVisualRating(
            sample_id="s3",
            visual_accuracy="neutral",  # 3
            issue_tags=["unnatural_fit", "blurry_artifacts"],
            purchase_confidence=3,
        ),
        HumanVisualRating(
            sample_id="s4",
            visual_accuracy="inaccurate",  # 2
            issue_tags=["garment_distorted", "unnatural_fit"],
            purchase_confidence=1,
        ),
        HumanVisualRating(
            sample_id="s5",
            visual_accuracy="very_inaccurate",  # 1
            issue_tags=["wrong_garment"],
            purchase_confidence=None,
        ),
    ]

    summary = summarize_visual_ratings(ratings, acceptable_threshold="accurate")

    assert summary.total_samples == 5
    # acceptable = very_accurate (5) and accurate (4) -> 2 out of 5
    assert summary.acceptable_count == 2
    assert summary.acceptable_rate == 0.4
    assert summary.accuracy_counts["very_accurate"] == 1
    assert summary.accuracy_counts["accurate"] == 1
    assert summary.accuracy_counts["neutral"] == 1
    assert summary.accuracy_counts["inaccurate"] == 1
    assert summary.accuracy_counts["very_inaccurate"] == 1

    # Issue tag aggregation
    assert summary.issue_tag_counts["unnatural_fit"] == 2
    assert summary.issue_tag_counts["garment_distorted"] == 1
    assert summary.issue_tag_counts["color_inaccurate"] == 1
    assert summary.issue_tag_counts["blurry_artifacts"] == 1
    assert summary.issue_tag_counts["wrong_garment"] == 1
    assert summary.issue_tag_counts["occlusion_error"] == 0

    # Scores: (5 + 4 + 3 + 2 + 1) / 5 = 3.0
    assert summary.mean_accuracy_score == 3.0

    # Purchase confidences: (5 + 4 + 3 + 1) / 4 = 3.25
    assert summary.mean_purchase_confidence == 3.25


def test_custom_acceptable_threshold() -> None:
    ratings = [
        HumanVisualRating(sample_id="s1", visual_accuracy="neutral"),
        HumanVisualRating(sample_id="s2", visual_accuracy="accurate"),
        HumanVisualRating(sample_id="s3", visual_accuracy="inaccurate"),
    ]
    summary = summarize_visual_ratings(ratings, acceptable_threshold="neutral")
    # neutral (3) and accurate (4) >= neutral (3) -> 2 out of 3
    assert summary.acceptable_count == 2
    assert summary.acceptable_rate == 0.6667
