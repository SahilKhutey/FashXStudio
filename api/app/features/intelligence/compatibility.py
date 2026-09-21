from dataclasses import dataclass


@dataclass(frozen=True)
class CompatibilityResult:
    compatible: bool
    score: float
    reasons: tuple[str, ...]


class CompatibilityEngine:
    def evaluate(
        self,
        *,
        styles_a: tuple[str, ...],
        styles_b: tuple[str, ...],
        colors_a: tuple[str, ...] = (),
        colors_b: tuple[str, ...] = (),
    ) -> CompatibilityResult:
        style = bool(set(styles_a) & set(styles_b))
        color = bool(set(colors_a) & set(colors_b))
        score = 0.6 * style + 0.4 * color
        return CompatibilityResult(
            score >= 0.5,
            score,
            (
                "Shared style" if style else "No shared style",
                "Shared color" if color else "No shared color",
            ),
        )
