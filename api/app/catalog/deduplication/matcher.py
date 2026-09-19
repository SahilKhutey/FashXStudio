import re
from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID

from .hasher import ImageHasher


class MatchConfidence(StrEnum):
    EXACT = "exact"
    HIGH = "high"
    AMBIGUOUS = "ambiguous"
    NONE = "none"


@dataclass
class DeduplicationResult:
    matched_garment_id: UUID | None
    confidence: MatchConfidence
    score: float
    reason: str


class GarmentMatcher:
    """Evaluates multi-signal similarity to detect duplicate products across merchants."""

    @staticmethod
    def token_similarity(title1: str, title2: str) -> float:
        """Compute Jaccard similarity over word tokens."""
        tokens1 = set(re.findall(r"\w+", title1.lower()))
        tokens2 = set(re.findall(r"\w+", title2.lower()))
        if not tokens1 or not tokens2:
            return 0.0
        intersection = tokens1.intersection(tokens2)
        union = tokens1.union(tokens2)
        return len(intersection) / len(union)

    @classmethod
    def evaluate_match(
        cls,
        candidate_title: str,
        candidate_exact_hash: str | None,
        candidate_dhash: str | None,
        existing_garment_id: UUID,
        existing_title: str,
        existing_exact_hashes: list[str],
        existing_dhashes: list[str],
        same_brand: bool = True,
    ) -> DeduplicationResult:
        """Evaluate similarity between a candidate listing and an existing canonical garment."""
        # 1. Exact Image Hash Match
        if candidate_exact_hash and candidate_exact_hash in existing_exact_hashes:
            return DeduplicationResult(
                matched_garment_id=existing_garment_id,
                confidence=MatchConfidence.EXACT,
                score=1.0,
                reason="Exact image SHA-256 match",
            )

        # 2. Perceptual Image Hash Match
        if candidate_dhash and existing_dhashes:
            min_dist = min(
                ImageHasher.hamming_distance(candidate_dhash, ex_h) for ex_h in existing_dhashes
            )
            # Distance <= 4 with same brand indicates high-confidence visual match
            if min_dist <= 4 and same_brand:
                return DeduplicationResult(
                    matched_garment_id=existing_garment_id,
                    confidence=MatchConfidence.HIGH,
                    score=0.95 - (min_dist * 0.02),
                    reason=f"Perceptual image dHash match (distance={min_dist})",
                )
            if min_dist <= 8 and same_brand:
                return DeduplicationResult(
                    matched_garment_id=existing_garment_id,
                    confidence=MatchConfidence.AMBIGUOUS,
                    score=0.75 - (min_dist * 0.02),
                    reason=f"Ambiguous perceptual match (distance={min_dist})",
                )

        # 3. Lexical Token Overlap Match
        lex_sim = cls.token_similarity(candidate_title, existing_title)
        if same_brand and lex_sim >= 0.85:
            return DeduplicationResult(
                matched_garment_id=existing_garment_id,
                confidence=MatchConfidence.HIGH,
                score=lex_sim,
                reason=f"High lexical title overlap ({lex_sim:.2f})",
            )
        if same_brand and lex_sim >= 0.65:
            return DeduplicationResult(
                matched_garment_id=existing_garment_id,
                confidence=MatchConfidence.AMBIGUOUS,
                score=lex_sim,
                reason=f"Moderate lexical overlap ({lex_sim:.2f}) requiring review",
            )

        return DeduplicationResult(
            matched_garment_id=None,
            confidence=MatchConfidence.NONE,
            score=0.0,
            reason="No significant similarity detected",
        )
