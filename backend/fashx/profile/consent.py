"""Purpose-specific consent & ownership enforcement for Shopper Fit Profile (Phase 08.2 - Task 8.2 privacy)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from fashx.core.errors import ConsentRequiredError
from fashx.profile.fit_schemas import ConsentPurpose
from fashx.profile.repositories.profile_repository import UserConsentRepository


class FitConsentService:
    """Manages purpose-specific consent verification and withdrawal for fit profile operations."""

    def __init__(self, session: Any = None) -> None:
        self._session = session
        self._consent_repo = UserConsentRepository(session) if session is not None else None
        # In-memory fallback for unit tests running without a live DB session
        self._mem_consents: dict[tuple[UUID, str], bool] = {}

    async def has_consent(self, user_id: UUID, purpose: ConsentPurpose | str) -> bool:
        purpose_str = purpose.value if isinstance(purpose, ConsentPurpose) else str(purpose)
        if self._consent_repo is not None:
            return await self._consent_repo.has_valid_consent(
                user_id=user_id,
                data_type=purpose_str,
                require_adult=True,
            )
        return bool(self._mem_consents.get((user_id, purpose_str), False))

    async def get_all_consents(self, user_id: UUID) -> dict[str, bool]:
        """Return explicit purpose-specific consent map for a shopper."""
        return {
            purpose.value: await self.has_consent(user_id, purpose)
            for purpose in ConsentPurpose
        }

    async def require_storage_consent(self, user_id: UUID) -> None:
        """Require explicit FIT_PROFILE_STORAGE consent before saving or processing body measurements."""
        if not await self.has_consent(user_id, ConsentPurpose.FIT_PROFILE_STORAGE):
            raise ConsentRequiredError(
                data_type=ConsentPurpose.FIT_PROFILE_STORAGE.value,
                message=(
                    "Explicit consent for fit_profile_storage is required before storing body measurements."
                ),
            )

    async def require_recommendation_consent(self, user_id: UUID) -> None:
        """Require explicit FIT_RECOMMENDATION_PROCESSING consent before computing fit guidance."""
        if not await self.has_consent(user_id, ConsentPurpose.FIT_RECOMMENDATION_PROCESSING):
            raise ConsentRequiredError(
                data_type=ConsentPurpose.FIT_RECOMMENDATION_PROCESSING.value,
                message=(
                    "Explicit consent for fit_recommendation_processing is required before calculating fit guidance."
                ),
            )

    async def set_consent(
        self,
        *,
        user_id: UUID,
        purpose: ConsentPurpose | str,
        granted: bool,
        is_18_or_older: bool | None = None,
        consent_version: str = "2026.1",
        decision_source: str = "fit_profile_api",
    ) -> dict[str, Any]:
        """Grant or withdraw consent for a single isolated fit profile purpose."""
        purpose_str = purpose.value if isinstance(purpose, ConsentPurpose) else str(purpose)
        if granted and is_18_or_older is False:
            raise ConsentRequiredError(
                data_type=purpose_str,
                message="You must be 18 or older to grant fit profile measurement consent.",
            )

        if self._consent_repo is not None:
            record = await self._consent_repo.upsert(
                user_id=user_id,
                data_type=purpose_str,
                granted=granted,
                is_18_or_older=is_18_or_older,
                consent_version=consent_version,
                decision_source=decision_source,
            )
            return {
                "user_id": record.user_id,
                "purpose": purpose_str,
                "granted": record.granted,
                "updated_at": record.updated_at or datetime.now(UTC),
            }

        self._mem_consents[(user_id, purpose_str)] = granted
        return {
            "user_id": user_id,
            "purpose": purpose_str,
            "granted": granted,
            "updated_at": datetime.now(UTC),
        }
