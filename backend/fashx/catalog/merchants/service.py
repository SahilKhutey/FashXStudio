from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.catalog import CatalogSource, Merchant
from database.models.catalog_auth import CatalogSourceStatus, MerchantVerificationStatus
from fashx.catalog.errors import MerchantNotFoundError, MerchantVerificationError
from fashx.catalog.merchants.repository import MerchantRepository
from fashx.catalog.merchants.schemas import (
    MerchantCreate,
    MerchantUpdate,
    MerchantVerificationRequest,
)


class MerchantService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = MerchantRepository(session)

    async def register_merchant(self, payload: MerchantCreate) -> Merchant:
        # Check duplicate legal name if provided
        if payload.legal_name:
            existing = await self.repo.get_by_legal_name(payload.legal_name)
            if existing:
                raise MerchantVerificationError(
                    f"Merchant with legal name '{payload.legal_name}' already exists.",
                    code="merchant_legal_name_conflict",
                )

        if payload.registration_reference:
            existing_reg = await self.repo.get_by_registration_reference(
                payload.registration_reference
            )
            if existing_reg:
                raise MerchantVerificationError(
                    f"Merchant with registration reference '{payload.registration_reference}' already exists.",
                    code="merchant_registration_conflict",
                )

        merchant = Merchant(
            name=payload.name,
            merchant_type=payload.merchant_type,
            legal_name=payload.legal_name,
            display_name=payload.display_name or payload.name,
            website=payload.website,
            country_code=payload.country_code.upper(),
            registration_reference=payload.registration_reference,
            verification_status=MerchantVerificationStatus.UNVERIFIED.value,
            primary_contact_id=payload.primary_contact_id,
            technical_contact_id=payload.technical_contact_id,
            takedown_contact_id=payload.takedown_contact_id,
        )
        return await self.repo.create(merchant)

    async def get_merchant(self, merchant_id: UUID) -> Merchant:
        merchant = await self.repo.get_by_id(merchant_id)
        if not merchant:
            raise MerchantNotFoundError(merchant_id)
        return merchant

    async def update_merchant(self, merchant_id: UUID, payload: MerchantUpdate) -> Merchant:
        merchant = await self.get_merchant(merchant_id)
        update_data = payload.model_dump(exclude_unset=True)

        if "legal_name" in update_data and update_data["legal_name"] != merchant.legal_name:
            existing = await self.repo.get_by_legal_name(update_data["legal_name"])
            if existing and existing.id != merchant.id:
                raise MerchantVerificationError(
                    f"Merchant with legal name '{update_data['legal_name']}' already exists.",
                    code="merchant_legal_name_conflict",
                )

        if (
            "registration_reference" in update_data
            and update_data["registration_reference"] != merchant.registration_reference
        ):
            existing_reg = await self.repo.get_by_registration_reference(
                update_data["registration_reference"]
            )
            if existing_reg and existing_reg.id != merchant.id:
                raise MerchantVerificationError(
                    f"Merchant with registration reference '{update_data['registration_reference']}' already exists.",
                    code="merchant_registration_conflict",
                )

        for field, value in update_data.items():
            setattr(merchant, field, value)

        return await self.repo.update(merchant)

    async def verify_merchant(
        self, merchant_id: UUID, req: MerchantVerificationRequest
    ) -> Merchant:
        merchant = await self.get_merchant(merchant_id)
        target_status = req.verification_status.value
        current_status = merchant.verification_status

        # Transition validation
        valid_transitions = {
            MerchantVerificationStatus.UNVERIFIED.value: [
                MerchantVerificationStatus.UNDER_REVIEW.value,
                MerchantVerificationStatus.VERIFIED.value,
                MerchantVerificationStatus.REJECTED.value,
            ],
            MerchantVerificationStatus.UNDER_REVIEW.value: [
                MerchantVerificationStatus.VERIFIED.value,
                MerchantVerificationStatus.REJECTED.value,
                MerchantVerificationStatus.SUSPENDED.value,
            ],
            MerchantVerificationStatus.VERIFIED.value: [
                MerchantVerificationStatus.SUSPENDED.value,
                MerchantVerificationStatus.UNDER_REVIEW.value,
            ],
            MerchantVerificationStatus.SUSPENDED.value: [
                MerchantVerificationStatus.UNDER_REVIEW.value,
                MerchantVerificationStatus.VERIFIED.value,
            ],
            MerchantVerificationStatus.REJECTED.value: [
                MerchantVerificationStatus.UNDER_REVIEW.value,
            ],
        }

        if target_status not in valid_transitions.get(current_status, []):
            raise MerchantVerificationError(
                f"Invalid verification status transition from {current_status} to {target_status}.",
                code="invalid_merchant_transition",
            )

        merchant.verification_status = target_status
        await self.repo.update(merchant)

        # Cascade suspension to sources if merchant is SUSPENDED
        if target_status == MerchantVerificationStatus.SUSPENDED.value:
            stmt = (
                update(CatalogSource)
                .where(
                    CatalogSource.merchant_id == merchant.id,
                    CatalogSource.source_status == CatalogSourceStatus.ACTIVE.value,
                )
                .values(source_status=CatalogSourceStatus.SUSPENDED.value)
            )
            await self.session.execute(stmt)

        return merchant

    async def list_merchants(
        self,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Sequence[Merchant]:
        return await self.repo.list_merchants(status=status, limit=limit, offset=offset)
