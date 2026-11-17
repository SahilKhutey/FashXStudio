from __future__ import annotations

import logging
from uuid import UUID

from database.models.identity import User
from fashx.account.repository import AccountRepository
from fashx.account.schemas import AccountStatus
from fashx.profile.repositories.shopper_profile_repository import ShopperProfileRepository
from fashx.profile.schemas import (
    CategorySizeItem,
    FeatureCompletenessResponse,
    FeatureReadiness,
    ShopperProfileCreate,
    ShopperProfileResponse,
    ShopperProfileUpdate,
)
from fashx.security.errors import conflict, forbidden, not_found

logger = logging.getLogger(__name__)


class ShopperProfileService:
    """Domain service managing shopper profile creation, updates, and feature completeness."""

    def __init__(
        self, profile_repo: ShopperProfileRepository, account_repo: AccountRepository
    ) -> None:
        self._profile_repo = profile_repo
        self._account_repo = account_repo

    async def _verify_active_user(self, user_id: UUID) -> User:
        user = await self._account_repo.get_user_by_id(user_id)
        if user is None:
            raise not_found("User account not found")
        if user.status == AccountStatus.DISABLED.value:
            raise forbidden("Account is disabled")
        if user.status in (
            AccountStatus.DELETION_PENDING.value,
            AccountStatus.DELETION_IN_PROGRESS.value,
            AccountStatus.DELETED.value,
        ):
            raise forbidden("Account is scheduled for deletion")
        return user

    async def get_for_user(self, user_id: UUID) -> ShopperProfileResponse:
        await self._verify_active_user(user_id)
        profile = await self._profile_repo.get_by_user_id(user_id)
        if profile is None:
            # Auto-create empty profile for newly registered user
            profile = await self._profile_repo.create(user_id, {})

        cat_sizes = await self._profile_repo.get_category_sizes(user_id)
        return ShopperProfileResponse(
            id=str(profile.id),
            user_id=str(profile.user_id),
            height_cm=float(profile.height_cm) if profile.height_cm is not None else None,
            weight_kg=float(profile.weight_kg) if profile.weight_kg is not None else None,
            preferred_size_system=profile.preferred_size_system,
            preferred_fit=profile.preferred_fit,
            style_preferences=profile.style_preferences or [],
            preferred_colors=profile.preferred_colors or [],
            product_categories=profile.product_categories or [],
            shopping_preferences=profile.shopping_preferences or {},
            category_sizes=[
                CategorySizeItem(
                    category_code=cs.category_code,
                    size_system=cs.size_system,
                    size_label=cs.size_label,
                )
                for cs in cat_sizes
            ],
            version=profile.version,
            created_at=profile.created_at,
            updated_at=profile.updated_at,
        )

    async def create_or_replace_for_user(
        self, user_id: UUID, payload: ShopperProfileCreate
    ) -> ShopperProfileResponse:
        await self._verify_active_user(user_id)
        data = payload.model_dump(exclude={"category_sizes"}, mode="json")

        # Convert Decimals to float for JSON/Numeric storage
        if data.get("height_cm") is not None:
            data["height_cm"] = float(data["height_cm"])
        if data.get("weight_kg") is not None:
            data["weight_kg"] = float(data["weight_kg"])

        existing = await self._profile_repo.get_by_user_id(user_id)
        if existing:
            updated, conflict_detected = await self._profile_repo.update_profile(
                profile_id=existing.id,
                changes=data,
            )
            profile = updated or existing
        else:
            profile = await self._profile_repo.create(user_id, data)

        if payload.category_sizes:
            raw_sizes = [
                {
                    "category_code": item.category_code,
                    "size_system": item.size_system.value,
                    "size_label": item.size_label,
                }
                for item in payload.category_sizes
            ]
            await self._profile_repo.set_category_sizes(user_id, raw_sizes)

        cat_sizes = await self._profile_repo.get_category_sizes(user_id)
        return ShopperProfileResponse(
            id=str(profile.id),
            user_id=str(profile.user_id),
            height_cm=float(profile.height_cm) if profile.height_cm is not None else None,
            weight_kg=float(profile.weight_kg) if profile.weight_kg is not None else None,
            preferred_size_system=profile.preferred_size_system,
            preferred_fit=profile.preferred_fit,
            style_preferences=profile.style_preferences or [],
            preferred_colors=profile.preferred_colors or [],
            product_categories=profile.product_categories or [],
            shopping_preferences=profile.shopping_preferences or {},
            category_sizes=[
                CategorySizeItem(
                    category_code=cs.category_code,
                    size_system=cs.size_system,
                    size_label=cs.size_label,
                )
                for cs in cat_sizes
            ],
            version=profile.version,
            created_at=profile.created_at,
            updated_at=profile.updated_at,
        )

    async def update_for_user(
        self, user_id: UUID, payload: ShopperProfileUpdate
    ) -> ShopperProfileResponse:
        await self._verify_active_user(user_id)
        existing = await self._profile_repo.get_by_user_id(user_id)
        if existing is None:
            existing = await self._profile_repo.create(user_id, {})

        # Partial update logic: exclude unset fields to avoid overwriting omitted fields
        changes = payload.model_dump(
            exclude_unset=True,
            exclude={"category_sizes", "expected_version"},
            mode="json",
        )
        if "height_cm" in changes and changes["height_cm"] is not None:
            changes["height_cm"] = float(changes["height_cm"])
        if "weight_kg" in changes and changes["weight_kg"] is not None:
            changes["weight_kg"] = float(changes["weight_kg"])

        updated, conflict_detected = await self._profile_repo.update_profile(
            profile_id=existing.id,
            changes=changes,
            expected_version=payload.expected_version,
        )

        if conflict_detected:
            raise conflict("Profile version conflict detected. Please reload latest profile.")

        profile = updated or existing

        # Update category sizes if passed explicitly
        if payload.category_sizes is not None:
            raw_sizes = [
                {
                    "category_code": item.category_code,
                    "size_system": item.size_system.value,
                    "size_label": item.size_label,
                }
                for item in payload.category_sizes
            ]
            await self._profile_repo.set_category_sizes(user_id, raw_sizes)

        cat_sizes = await self._profile_repo.get_category_sizes(user_id)
        return ShopperProfileResponse(
            id=str(profile.id),
            user_id=str(profile.user_id),
            height_cm=float(profile.height_cm) if profile.height_cm is not None else None,
            weight_kg=float(profile.weight_kg) if profile.weight_kg is not None else None,
            preferred_size_system=profile.preferred_size_system,
            preferred_fit=profile.preferred_fit,
            style_preferences=profile.style_preferences or [],
            preferred_colors=profile.preferred_colors or [],
            product_categories=profile.product_categories or [],
            shopping_preferences=profile.shopping_preferences or {},
            category_sizes=[
                CategorySizeItem(
                    category_code=cs.category_code,
                    size_system=cs.size_system,
                    size_label=cs.size_label,
                )
                for cs in cat_sizes
            ],
            version=profile.version,
            created_at=profile.created_at,
            updated_at=profile.updated_at,
        )

    async def get_completeness_for_user(self, user_id: UUID) -> FeatureCompletenessResponse:
        await self._verify_active_user(user_id)
        profile = await self._profile_repo.get_by_user_id(user_id)
        cat_sizes = await self._profile_repo.get_category_sizes(user_id)

        features: dict[str, FeatureReadiness] = {}

        # 1. Product discovery: always ready
        features["product_discovery"] = FeatureReadiness(ready=True, missing_fields=[])

        # 2. Personalized recommendations: requires at least one style, color, or category
        has_rec = bool(
            profile
            and (
                profile.style_preferences
                or profile.preferred_colors
                or profile.product_categories
                or (
                    profile.shopping_preferences
                    and profile.shopping_preferences.get("shopping_intents")
                )
            )
        )
        missing_rec = []
        if not has_rec:
            missing_rec.append("style_preferences")
        features["personalized_recommendations"] = FeatureReadiness(
            ready=has_rec, missing_fields=missing_rec
        )

        # 3. Size guidance: requires preferred_size_system or category sizes
        has_sizing = bool((profile and profile.preferred_size_system) or len(cat_sizes) > 0)
        missing_sizing = []
        if not has_sizing:
            missing_sizing.append("preferred_size_system")
        features["size_guidance"] = FeatureReadiness(
            ready=has_sizing, missing_fields=missing_sizing
        )

        # 4. Basic fit recommendation: requires height_cm and preferred_fit
        missing_fit = []
        if not (profile and profile.height_cm):
            missing_fit.append("height_cm")
        if not (profile and profile.preferred_fit):
            missing_fit.append("preferred_fit")
        features["fit_recommendation"] = FeatureReadiness(
            ready=len(missing_fit) == 0, missing_fields=missing_fit
        )

        # 5. Advanced VTO: requires height_cm
        missing_vto = []
        if not (profile and profile.height_cm):
            missing_vto.append("height_cm")
        features["advanced_vto"] = FeatureReadiness(
            ready=len(missing_vto) == 0, missing_fields=missing_vto
        )

        # Overall calculation
        ready_count = sum(1 for f in features.values() if f.ready)
        overall_pct = int(round((ready_count / len(features)) * 100)) if features else 0
        if ready_count == len(features):
            overall = "COMPLETE"
        elif ready_count > 1:
            overall = "PARTIAL"
        else:
            overall = "EMPTY"

        return FeatureCompletenessResponse(
            overall_status=overall,
            overall_percentage=overall_pct,
            features=features,
        )

    async def update_category_sizes(
        self, user_id: UUID, sizes: list[CategorySizeItem]
    ) -> list[CategorySizeItem]:
        await self._verify_active_user(user_id)
        raw_sizes = [
            {
                "category_code": item.category_code,
                "size_system": item.size_system.value,
                "size_label": item.size_label,
            }
            for item in sizes
        ]
        results = await self._profile_repo.set_category_sizes(user_id, raw_sizes)
        return [
            CategorySizeItem(
                category_code=r.category_code,
                size_system=r.size_system,
                size_label=r.size_label,
            )
            for r in results
        ]
