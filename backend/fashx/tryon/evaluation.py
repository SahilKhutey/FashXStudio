import statistics
from collections.abc import Sequence
from dataclasses import dataclass, field

VALID_VISUAL_ACCURACIES: tuple[str, ...] = (
    "very_inaccurate",
    "inaccurate",
    "neutral",
    "accurate",
    "very_accurate",
)

ACCURACY_SCORES: dict[str, int] = {
    "very_inaccurate": 1,
    "inaccurate": 2,
    "neutral": 3,
    "accurate": 4,
    "very_accurate": 5,
}

VALID_ISSUE_TAGS: frozenset[str] = frozenset(
    {
        "unnatural_fit",
        "garment_distorted",
        "color_inaccurate",
        "blurry_artifacts",
        "person_appearance_changed",
        "wrong_garment",
        "occlusion_error",
    }
)


@dataclass
class HumanVisualRating:
    sample_id: str
    visual_accuracy: str
    issue_tags: list[str] = field(default_factory=list)
    purchase_confidence: int | None = None
    rater_id: str | None = None

    def __post_init__(self) -> None:
        if self.visual_accuracy not in ACCURACY_SCORES:
            raise ValueError(
                f"Invalid visual_accuracy '{self.visual_accuracy}'; must be one of {VALID_VISUAL_ACCURACIES}"
            )
        if self.purchase_confidence is not None and not (1 <= self.purchase_confidence <= 5):
            raise ValueError(
                f"Purchase confidence must be between 1 and 5; got {self.purchase_confidence}"
            )
        # Deduplicate and sort tags
        self.issue_tags = sorted(set(self.issue_tags))


@dataclass(frozen=True)
class VisualEvaluationSummary:
    total_samples: int
    acceptable_count: int
    acceptable_rate: float
    accuracy_counts: dict[str, int]
    issue_tag_counts: dict[str, int]
    mean_accuracy_score: float | None
    mean_purchase_confidence: float | None


def summarize_visual_ratings(
    ratings: Sequence[HumanVisualRating],
    acceptable_threshold: str = "accurate",
) -> VisualEvaluationSummary:
    """Summarizes human visual realism evaluations into release gate metrics.

    Note: This measures visual fidelity and user-perceived realism of the VTO output.
    It does NOT measure or claim objective physical fit or sizing correctness.
    """
    threshold_score = ACCURACY_SCORES.get(acceptable_threshold, 4)
    total = len(ratings)

    accuracy_counts = dict.fromkeys(VALID_VISUAL_ACCURACIES, 0)
    issue_tag_counts = dict.fromkeys(sorted(VALID_ISSUE_TAGS), 0)

    if total == 0:
        return VisualEvaluationSummary(
            total_samples=0,
            acceptable_count=0,
            acceptable_rate=0.0,
            accuracy_counts=accuracy_counts,
            issue_tag_counts=issue_tag_counts,
            mean_accuracy_score=None,
            mean_purchase_confidence=None,
        )

    acceptable_count = 0
    accuracy_scores_list: list[int] = []
    purchase_confidences_list: list[int] = []

    for r in ratings:
        accuracy_counts[r.visual_accuracy] = accuracy_counts.get(r.visual_accuracy, 0) + 1
        score = ACCURACY_SCORES[r.visual_accuracy]
        accuracy_scores_list.append(score)
        if score >= threshold_score:
            acceptable_count += 1

        for tag in r.issue_tags:
            issue_tag_counts[tag] = issue_tag_counts.get(tag, 0) + 1

        if r.purchase_confidence is not None:
            purchase_confidences_list.append(r.purchase_confidence)

    acceptable_rate = round(acceptable_count / total, 4)
    mean_accuracy_score = (
        round(statistics.mean(accuracy_scores_list), 2) if accuracy_scores_list else None
    )
    mean_purchase_conf = (
        round(statistics.mean(purchase_confidences_list), 2)
        if purchase_confidences_list
        else None
    )

    return VisualEvaluationSummary(
        total_samples=total,
        acceptable_count=acceptable_count,
        acceptable_rate=acceptable_rate,
        accuracy_counts=accuracy_counts,
        issue_tag_counts=issue_tag_counts,
        mean_accuracy_score=mean_accuracy_score,
        mean_purchase_confidence=mean_purchase_conf,
    )
