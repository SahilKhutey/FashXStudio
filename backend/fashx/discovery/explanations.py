from __future__ import annotations

from collections.abc import Sequence

from fashx.discovery.scoring import ScoredGarmentCandidate


def build_grounded_reason_chips(
    candidate: ScoredGarmentCandidate,
    user_styles: Sequence[str] | None = None,
) -> list[str]:
    """Generate grounded, non-hallucinated reason chips strictly backed by verified attributes.

    Rule: Never make unverified fit claims (e.g. 'Fits your exact waist').
    """
    chips: list[str] = []

    # 1. High overall relevance
    if candidate.final_score >= 0.85:
        chips.append("Top Pick")

    # 2. Visual / taste alignment (only when semantic embedding match is actually measured)
    if candidate.semantic_score is not None and candidate.semantic_score >= 0.60:
        chips.append("Visual Taste Match")

    # 3. Style match
    if candidate.style_score >= 0.80:
        chips.append("Style Match")

    # 4. Color harmony
    if candidate.color_score >= 0.80 and candidate.dominant_color:
        chips.append(f"{candidate.dominant_color.capitalize()} Harmony")

    # 5. Size availability
    if candidate.size_score >= 0.99:
        chips.append("In Your Size")

    # 6. Budget
    if candidate.budget_score >= 0.90:
        chips.append("Within Budget")

    # 7. Virtual try-on support
    if candidate.tryon_supported:
        chips.append("Try-On Ready")

    # Fallback if no specific high scores triggered
    if not chips:
        if candidate.category:
            chips.append(candidate.category.capitalize())
        if candidate.dominant_color:
            chips.append(candidate.dominant_color.capitalize())
        elif candidate.silhouette:
            chips.append(f"{candidate.silhouette.replace('_', ' ').capitalize()} Cut")

    # Return up to 3 grounded chips
    return chips[:3]


def build_grounded_stylist_explanation(
    candidate: ScoredGarmentCandidate,
    user_styles: Sequence[str] | None = None,
) -> str:
    """Generate grounded natural language summary without speculative fit claims."""
    parts: list[str] = []

    if candidate.style_score >= 0.75 and user_styles:
        styles_str = ", ".join(user_styles[:2])
        parts.append(f"aligned with your preferred {styles_str} aesthetic")

    if candidate.dominant_color and candidate.color_score >= 0.70:
        parts.append(f"features flattering {candidate.dominant_color} tones")

    if candidate.silhouette and candidate.silhouette != "regular":
        clean_cut = candidate.silhouette.replace("_", " ")
        parts.append(f"offers a contemporary {clean_cut} silhouette")

    if candidate.tryon_supported:
        parts.append("supports instant AI virtual try-on")

    if not parts:
        desc = candidate.category.capitalize()
        if candidate.dominant_color:
            desc = f"{candidate.dominant_color.capitalize()} {candidate.category}"
        return f"Selected {desc} tailored for your personal discovery feed."

    joined = ", ".join(parts)
    return f"Curated garment {joined}."
