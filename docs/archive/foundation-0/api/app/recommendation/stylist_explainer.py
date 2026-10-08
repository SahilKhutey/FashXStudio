from .compatibility import CompatibilityScore
from .filters import CandidateItem


class StylistExplainer:
    """Generates natural language styling justifications explaining why an item was recommended (Roadmap 3.2)."""

    @classmethod
    def generate_explanation(
        cls,
        item: CandidateItem,
        compatibility: CompatibilityScore,
        user_build: str | None,
        user_undertone: str | None,
    ) -> str:
        color_part = compatibility.color_reason
        sil_part = compatibility.silhouette_reason

        # Combine reasoning smoothly into a personalized stylist sentence
        build_str = (user_build or "balanced").lower()
        undertone_str = (user_undertone or "neutral").lower()

        cut = item.silhouette or "classic"
        color = item.dominant_color or "staple"

        if compatibility.total_score >= 0.90:
            return (
                f"Top Stylist Pick: The {cut} cut harmonizes with your {build_str} build, "
                f"while the {color} palette complements your {undertone_str} undertone."
            )
        elif compatibility.silhouette_score >= 0.90:
            return (
                f"Silhouette Match: {sil_part} It works as an everyday {item.category} essential."
            )
        elif compatibility.color_score >= 0.90:
            return f"Color Harmony: {color_part} Perfect for your current seasonal rotation."

        return f"A versatile {cut} {item.category} option tailored to your profile preferences."
