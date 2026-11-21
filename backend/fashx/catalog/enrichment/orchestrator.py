from __future__ import annotations

import hashlib
import json

from fashx.catalog.taxonomy.loader import get_taxonomy_registry
from fashx.catalog.taxonomy.registry import TaxonomyRegistry

from .category_mapper import map_merchant_category
from .confidence import decide_review
from .contracts import (
    AttributeResult,
    AttributeSource,
    AttributeStatus,
    EnrichmentEvidence,
    EnrichmentInput,
    EnrichmentOutput,
    EnrichmentStatus,
    ReviewFlag,
    ReviewStatus,
    ReviewSummary,
)
from .evidence import (
    image_asset_evidence,
    merchant_field_evidence,
    title_evidence,
)
from .model_gateway import ModelGateway
from .title_extractor import extract_title_attributes
from .validator import validate_enrichment_attributes

ENRICHMENT_VERSION: str = "1.0.0"


def compute_idempotency_key(
    product_id: str,
    source_revision: str | None,
    taxonomy_version: str,
    enrichment_version: str = ENRICHMENT_VERSION,
) -> str:
    """Generate SHA-256 idempotency key to prevent redundant enrichment runs (Section 10.3 / ENR-026)."""
    payload = {
        "product_id": product_id,
        "source_revision": source_revision or "",
        "taxonomy_version": taxonomy_version,
        "enrichment_version": enrichment_version,
    }
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


class EnrichmentOrchestrator:
    """End-to-end enrichment pipeline coordinating deterministic rules, AI models, and validation."""

    def __init__(
        self,
        registry: TaxonomyRegistry | None = None,
        model_gateway: ModelGateway | None = None,
    ) -> None:
        self.registry = registry or get_taxonomy_registry()
        self.model_gateway = model_gateway or ModelGateway()

    async def enrich_product(
        self,
        product: EnrichmentInput,
        existing_accepted_attributes: dict[str, AttributeResult] | None = None,
    ) -> EnrichmentOutput:
        """Execute full enrichment lifecycle on an authorized product record."""
        # 1. Permission checks (Rule 6.2.1 / ENR-023)
        if not product.text_processing_allowed:
            raise PermissionError("Text enrichment is not authorized for this source (ENR-023)")

        idempotency_key = compute_idempotency_key(
            product.product_id,
            product.source_revision,
            product.taxonomy_version,
            ENRICHMENT_VERSION,
        )

        attributes: dict[str, AttributeResult] = {}
        evidence_records: list[EnrichmentEvidence] = []
        review_reasons: list[str] = []
        review_required = False

        # 2. Category mapping (Section 6.2.4 & ENR-010)
        cat_result = map_merchant_category(
            product.content.merchant_category,
            self.registry,
        )
        category_id = cat_result.category_id
        if cat_result.quarantined or category_id is None:
            review_required = True
            review_reasons.append("UNRESOLVED_CATEGORY")

        # 3. Process structured merchant attributes (P0 source data)
        raw_attrs = product.content.attributes
        if raw_attrs:
            for k, raw_v in raw_attrs.items():
                k_lower = k.lower().strip()
                v_str = str(raw_v).strip()

                if k_lower in {"color", "colour"}:
                    ev = merchant_field_evidence(
                        product.source_product_id, product.source_revision, k, v_str
                    )
                    evidence_records.append(ev)
                    # Normalize color if known
                    norm_color = self.registry.resolve_alias("color", v_str) or v_str.lower()
                    attributes["color"] = AttributeResult(
                        value=norm_color,
                        status=AttributeStatus.KNOWN,
                        confidence=0.99,
                        source=AttributeSource.MERCHANT,
                        review_status=ReviewStatus.AUTO_ACCEPTED,
                        evidence_ids=[ev.evidence_id],
                    )
                elif k_lower in {"fit", "fit_type"}:
                    ev = merchant_field_evidence(
                        product.source_product_id, product.source_revision, k, v_str
                    )
                    evidence_records.append(ev)
                    norm_fit = self.registry.resolve_alias("silhouette", v_str) or v_str.lower()
                    attributes["fit_type"] = AttributeResult(
                        value=norm_fit,
                        status=AttributeStatus.KNOWN,
                        confidence=0.99,
                        source=AttributeSource.MERCHANT,
                        review_status=ReviewStatus.AUTO_ACCEPTED,
                        evidence_ids=[ev.evidence_id],
                    )
                elif k_lower in {"fabric", "material"}:
                    ev = merchant_field_evidence(
                        product.source_product_id, product.source_revision, k, v_str
                    )
                    evidence_records.append(ev)
                    val_lower = v_str.lower()
                    if "blend" in val_lower:
                        attributes["fabric_blend"] = AttributeResult(
                            value="cotton_blend" if "cotton" in val_lower else "blend",
                            status=AttributeStatus.KNOWN,
                            confidence=0.96,
                            source=AttributeSource.MERCHANT,
                            review_status=ReviewStatus.AUTO_ACCEPTED,
                            evidence_ids=[ev.evidence_id],
                        )
                        attributes["fabric"] = AttributeResult(
                            value=None,
                            status=AttributeStatus.UNKNOWN,
                            confidence=None,
                            source=None,
                            review_status=ReviewStatus.NOT_REQUIRED,
                            evidence_ids=[],
                        )
                    else:
                        norm_mat = self.registry.resolve_alias("fabric", val_lower) or val_lower
                        attributes["fabric"] = AttributeResult(
                            value=norm_mat,
                            status=AttributeStatus.KNOWN,
                            confidence=0.95,
                            source=AttributeSource.MERCHANT,
                            review_status=ReviewStatus.AUTO_ACCEPTED,
                            evidence_ids=[ev.evidence_id],
                        )

        # 4. Deterministic title extraction (P0 text rules)
        title_matches = extract_title_attributes(product.content.title)
        garment_type_val: str | None = None

        for match in title_matches:
            ev = title_evidence(
                product.source_product_id,
                product.source_revision,
                match.matched_text,
                match.start,
                match.end,
            )
            evidence_records.append(ev)

            if match.attribute_id == "garment_type":
                garment_type_val = match.value

            # Conflict checking between title extraction and existing merchant fields (ENR-019)
            if match.attribute_id in attributes:
                existing = attributes[match.attribute_id]
                if existing.value is not None and str(existing.value) != match.value:
                    # Conflicting evidence between merchant field and title!
                    attributes[match.attribute_id] = AttributeResult(
                        value=existing.value,
                        status=AttributeStatus.CONFLICTING,
                        confidence=0.50,
                        source=AttributeSource.FALLBACK,
                        review_status=ReviewStatus.PENDING_REVIEW,
                        evidence_ids=existing.evidence_ids + [ev.evidence_id],
                        flags=[ReviewFlag.CONFLICTING_EVIDENCE],
                    )
                    review_required = True
                    review_reasons.append(f"CONFLICTING_{match.attribute_id.upper()}")
                    continue

            # Fabric blend rule: Title containing "cotton blend" sets blend, keeps fabric unknown (ENR-013)
            if match.attribute_id == "fabric_blend":
                attributes["fabric_blend"] = AttributeResult(
                    value=match.value,
                    status=AttributeStatus.KNOWN,
                    confidence=match.confidence,
                    source=AttributeSource.RULE_BASED,
                    review_status=ReviewStatus.AUTO_ACCEPTED,
                    evidence_ids=[ev.evidence_id],
                )
                if "fabric" not in attributes:
                    attributes["fabric"] = AttributeResult(
                        value=None,
                        status=AttributeStatus.UNKNOWN,
                        confidence=None,
                        source=None,
                        review_status=ReviewStatus.NOT_REQUIRED,
                        evidence_ids=[],
                    )
                continue

            # Standard attribute result creation
            attributes[match.attribute_id] = AttributeResult(
                value=match.value,
                status=AttributeStatus.KNOWN,
                confidence=match.confidence,
                source=AttributeSource.RULE_BASED,
                review_status=ReviewStatus.AUTO_ACCEPTED,
                evidence_ids=[ev.evidence_id],
            )

        # 5. Fallback AI text extraction for unresolved attributes (e.g. occasion / style)
        if "occasion" not in attributes or attributes["occasion"].value is None:
            try:
                ai_attrs, meta = await self.model_gateway.extract_text_attributes(
                    product.content.title,
                    product.content.description,
                    product.taxonomy_version,
                )
                if "occasion" in ai_attrs and ai_attrs["occasion"]:
                    ai_occ = ai_attrs["occasion"]
                    # If AI predicted occasion, record it with AI provenance and lower confidence
                    ev_ai = title_evidence(
                        product.source_product_id,
                        product.source_revision,
                        ai_occ,
                        0,
                        len(ai_occ),
                        extraction_method=f"AI_TEXT_MODEL_{meta.model_id}",
                    )
                    evidence_records.append(ev_ai)
                    # Occasion from AI is lower confidence (0.75) -> requires review (ENR-020)
                    attributes["occasion"] = AttributeResult(
                        value=ai_occ,
                        status=AttributeStatus.KNOWN,
                        confidence=0.75,
                        source=AttributeSource.AI_TEXT,
                        review_status=ReviewStatus.PENDING_REVIEW,
                        evidence_ids=[ev_ai.evidence_id],
                        flags=[ReviewFlag.LOW_CONFIDENCE],
                    )
                    review_required = True
                    review_reasons.append("LOW_CONFIDENCE_OCCASION")
            except Exception:
                pass

        # 6. Size information policy: Never invent sizes (Section 6.2.15 / ENR-015)
        if product.content.size_information is not None:
            attributes["size"] = AttributeResult(
                value=product.content.size_information,
                status=AttributeStatus.KNOWN,
                confidence=1.0,
                source=AttributeSource.MERCHANT,
                review_status=ReviewStatus.AUTO_ACCEPTED,
                evidence_ids=[],
            )
        else:
            attributes["size"] = AttributeResult(
                value=None,
                status=AttributeStatus.NOT_PROVIDED,
                confidence=None,
                source=None,
                review_status=ReviewStatus.NOT_REQUIRED,
                evidence_ids=[],
            )

        # 7. Protect existing accepted values against uncertain overwrites (ENR-033)
        if existing_accepted_attributes:
            for k, accepted_res in existing_accepted_attributes.items():
                if accepted_res.review_status == ReviewStatus.APPROVED:
                    if k not in attributes:
                        attributes[k] = accepted_res
                    else:
                        new_res = attributes[k]
                        if new_res.confidence is None or new_res.confidence < 0.95:
                            attributes[k] = accepted_res

        # 8. Check image AI permission (ENR-024 / ENR-025)
        if product.image_ai_processing_allowed and product.images:
            # Recheck asset permission status
            for img in product.images:
                if img.has_ai_permission:
                    ev_img = image_asset_evidence(
                        product.source_product_id,
                        product.source_revision,
                        img.asset_id,
                    )
                    evidence_records.append(ev_img)
                    break

        # 9. Validate against taxonomy and policy
        validation_errors = validate_enrichment_attributes(
            attributes,
            self.registry,
            category_id,
        )
        if validation_errors:
            review_required = True
            review_reasons.extend(validation_errors)

        # 10. Evaluate review status per attribute
        for attr_id, res in attributes.items():
            if res.review_status in {ReviewStatus.APPROVED, ReviewStatus.CORRECTED}:
                continue
            if res.status == AttributeStatus.KNOWN:
                decision = decide_review(
                    attr_id,
                    res.confidence,
                    evidence_present=len(res.evidence_ids) > 0,
                    conflicting=res.status == AttributeStatus.CONFLICTING,
                )
                res.review_status = decision.review_status
                res.flags = list(set(res.flags + decision.flags))
                if decision.review_required:
                    review_required = True
                    review_reasons.extend(decision.review_reasons)

        # Determine overall status
        status: EnrichmentStatus
        if validation_errors:
            status = EnrichmentStatus.REJECTED
        elif review_required:
            status = EnrichmentStatus.REVIEW_REQUIRED
        elif any(
            v.status in {AttributeStatus.UNKNOWN, AttributeStatus.NOT_PROVIDED}
            for v in attributes.values()
        ):
            status = EnrichmentStatus.PARTIAL
        else:
            status = EnrichmentStatus.COMPLETED

        return EnrichmentOutput(
            schema_version="1.0.0",
            product_id=product.product_id,
            taxonomy_version=product.taxonomy_version,
            enrichment_version=ENRICHMENT_VERSION,
            status=status,
            category_id=category_id,
            garment_type=garment_type_val,
            attributes=attributes,
            evidence=evidence_records,
            review=ReviewSummary(
                required=review_required,
                reasons=sorted(set(review_reasons)),
            ),
            idempotency_key=idempotency_key,
        )
