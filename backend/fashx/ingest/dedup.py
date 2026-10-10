"""Catalog deduplication and grouping logic based on exact hash, perceptual dHash, and variants."""

from dataclasses import dataclass

from fashx.catalog.deduplication.hasher import ImageHasher


@dataclass
class DedupDecision:
    """Represents a deduplication / grouping resolution."""

    action: str  # "exact_match" | "variant_group" | "perceptual_match" | "unique"
    canonical_id: str | None = None
    reason: str = ""
    hamming_distance: int = 64


def evaluate_dedup(
    *,
    source_product_id: str,
    item_group_id: str | None,
    image_sha256: str | None,
    image_dhash: str | None,
    brand: str | None,
    category: str | None,
    existing_records: list[dict],
    max_dhash_distance: int = 4,
) -> DedupDecision:
    """Evaluate whether an incoming item matches existing items or forms a new variant/product.

    Rules:
    1. Variant grouping: Same item_group_id groups variants together without overwriting.
    2. Exact match: Matching image SHA-256 within the same brand.
    3. Perceptual match: dHash distance <= max_dhash_distance within same (brand, category).
    4. Otherwise, marked as unique.
    """
    # 1. Variant grouping via item_group_id
    if item_group_id:
        for rec in existing_records:
            if rec.get("item_group_id") == item_group_id:
                return DedupDecision(
                    action="variant_group",
                    canonical_id=rec.get("canonical_garment_id"),
                    reason=f"Shares item_group_id '{item_group_id}' with {rec.get('source_product_id')}",
                )

    # 2. Exact match on SHA-256
    if image_sha256:
        for rec in existing_records:
            if rec.get("image_sha256") == image_sha256:
                return DedupDecision(
                    action="exact_match",
                    canonical_id=rec.get("canonical_garment_id"),
                    reason=f"Exact image SHA-256 match with {rec.get('source_product_id')}",
                    hamming_distance=0,
                )

    # 3. Perceptual hash comparison within same (brand, category)
    if image_dhash and brand and category:
        for rec in existing_records:
            if rec.get("brand") == brand and rec.get("category") == category:
                rec_dhash = rec.get("image_dhash")
                if rec_dhash:
                    dist = ImageHasher.hamming_distance(image_dhash, rec_dhash)
                    if dist <= max_dhash_distance:
                        return DedupDecision(
                            action="perceptual_match",
                            canonical_id=rec.get("canonical_garment_id"),
                            reason=f"Perceptual dHash distance {dist} <= {max_dhash_distance} with {rec.get('source_product_id')}",
                            hamming_distance=dist,
                        )

    return DedupDecision(action="unique", reason="No duplicate match found")
