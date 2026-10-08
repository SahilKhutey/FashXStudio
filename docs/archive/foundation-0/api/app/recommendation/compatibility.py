from dataclasses import dataclass

WARM_PALETTE = {"olive", "navy", "beige", "brown", "burgundy", "green", "red", "gold"}
COOL_PALETTE = {"white", "black", "blue", "charcoal", "grey", "pink", "navy", "silver"}

BUILD_CUT_MATRIX: dict[str, dict[str, float]] = {
    "slim": {"slim": 1.0, "regular": 0.85, "relaxed": 0.75, "oversized": 0.65},
    "athletic": {"slim": 0.95, "regular": 1.0, "relaxed": 0.85, "oversized": 0.75},
    "regular": {"regular": 1.0, "slim": 0.85, "relaxed": 0.85, "oversized": 0.75},
    "broad": {"relaxed": 1.0, "regular": 0.95, "oversized": 0.80, "slim": 0.60},
}


@dataclass
class CompatibilityScore:
    total_score: float
    color_score: float
    silhouette_score: float
    color_reason: str
    silhouette_reason: str


class CompatibilityMatrix:
    """Stage 2: Evaluates color harmony and physical body-cut compatibility."""

    @classmethod
    def evaluate(
        cls,
        user_undertone: str | None,
        user_build: str | None,
        garment_color: str | None,
        garment_cut: str | None,
        favored_colors: list[str] | None = None,
        favored_categories: list[str] | None = None,
        category: str | None = None,
    ) -> CompatibilityScore:
        undertone = (user_undertone or "neutral").lower()
        build = (user_build or "regular").lower()
        color = (garment_color or "navy").lower()
        cut = (garment_cut or "regular").lower()

        # 1. Color Harmony
        color_score = 0.80
        color_reason = f"{color.title()} is a versatile staple."

        if undertone == "warm":
            if color in WARM_PALETTE:
                color_score = 1.0
                color_reason = f"The {color} hue harmonizes naturally with your warm undertone."
            else:
                color_score = 0.80
                color_reason = (
                    f"A classic {color} providing balanced contrast with your warm undertone."
                )
        elif undertone == "cool":
            if color in COOL_PALETTE:
                color_score = 1.0
                color_reason = f"The crisp {color} palette complements your cool undertone."
            else:
                color_score = 0.75
                color_reason = f"An earthy {color} tone providing distinctive warmth."
        else:
            color_score = 0.90
            color_reason = f"The {color} hue is universally flattering with your neutral undertone."

        # Bonus if color is explicitly in user's favored colors
        if favored_colors and color in {c.lower() for c in favored_colors}:
            color_score = min(1.0, color_score + 0.15)
            color_reason += f" Matches your preferred color ({color})."

        # 2. Silhouette & Cut Compatibility
        cut_table = BUILD_CUT_MATRIX.get(build, BUILD_CUT_MATRIX["regular"])
        sil_score = cut_table.get(cut, 0.80)

        if sil_score >= 0.95:
            sil_reason = f"The {cut} cut aligns cleanly with your {build} build."
        else:
            sil_reason = f"The {cut} profile provides an easy, comfortable silhouette for your {build} frame."

        # Category affinity boost
        category_boost = 0.0
        if favored_categories and category and category in favored_categories:
            category_boost = 0.05

        total = round((0.55 * sil_score + 0.45 * color_score) + category_boost, 3)

        return CompatibilityScore(
            total_score=total,
            color_score=round(color_score, 3),
            silhouette_score=round(sil_score, 3),
            color_reason=color_reason,
            silhouette_reason=sil_reason,
        )
