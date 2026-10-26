from datetime import date, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from database.models.catalog import (
    CanonicalGarment,
    CatalogSource,
    Merchant,
    MerchantOffer,
    MerchantProduct,
)
from database.models.identity import ConsentRecord, User, UserPhoto
from database.models.tryon import TryOnJob
from fashx.catalog.application import (
    ApproveCatalogSourceCommand,
    IngestMerchantProductUseCase,
    IngestProductCommand,
    ManageCatalogSourceUseCase,
)
from fashx.catalog.repositories.catalog_repository import CatalogUnitOfWork
from fashx.core.errors import EntityNotFoundError, ValidationError
from fashx.profile.repositories.profile_repository import ProfileUnitOfWork
from fashx.tryon.application.process_job import ProcessTryOnJobUseCase
from fashx.tryon.repositories.tryon_repository import TryOnUnitOfWork


class FakeUnitOfWork:
    def __init__(self, source: object | None = None) -> None:
        self.sources = SimpleNamespace(
            get_by_id=AsyncMock(return_value=source),
            get_by_slug=AsyncMock(return_value=source),
        )
        self.commit = AsyncMock()

    async def __aenter__(self) -> "FakeUnitOfWork":
        return self

    async def __aexit__(self, exc_type: object, exc: object, tb: object) -> bool:
        return False


def make_source(
    status: str = "pending",
    rights_display: bool = False,
    rights_tryon: bool = False,
    image_policy: str = "hotlink",
) -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid4(),
        slug="test-source",
        name="Test Source",
        kind="manual",
        status=status,
        rights_display=rights_display,
        rights_tryon=rights_tryon,
        image_policy=image_policy,
        terms_url=None,
        terms_checked_on=None,
        notes=None,
    )


# ---------------------------------------------------------------------------
# Unit Tests (Fast, In-Memory via FakeUnitOfWork)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_approve_source_success() -> None:
    source = make_source()
    uow = FakeUnitOfWork(source)
    use_case = ManageCatalogSourceUseCase(uow)  # type: ignore[arg-type]

    cmd = ApproveCatalogSourceCommand(
        source_id=source.id,
        rights_display=True,
        rights_tryon=True,
        image_policy="mirror",
        terms_url="https://source.example.com/legal/terms",
        terms_checked_on=date.today(),
    )

    decision = await use_case.approve_source(cmd)
    assert decision.status == "cleared"
    assert decision.rights_display is True
    assert decision.rights_tryon is True
    assert decision.image_policy == "mirror"
    assert source.status == "cleared"
    assert source.terms_url == "https://source.example.com/legal/terms"
    uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_approve_source_not_found_raises_entity_not_found() -> None:
    uow = FakeUnitOfWork(source=None)
    use_case = ManageCatalogSourceUseCase(uow)  # type: ignore[arg-type]

    cmd = ApproveCatalogSourceCommand(
        source_id=uuid4(),
        rights_display=True,
        rights_tryon=False,
        image_policy="hotlink",
        terms_url="https://source.example.com/terms",
        terms_checked_on=date.today(),
    )

    with pytest.raises(EntityNotFoundError) as exc_info:
        await use_case.approve_source(cmd)
    assert "CatalogSource" in str(exc_info.value)


@pytest.mark.asyncio
async def test_approve_source_rejects_unsupported_image_policy() -> None:
    source = make_source()
    uow = FakeUnitOfWork(source)
    use_case = ManageCatalogSourceUseCase(uow)  # type: ignore[arg-type]

    cmd = ApproveCatalogSourceCommand(
        source_id=source.id,
        rights_display=True,
        rights_tryon=False,
        image_policy="s3_scrape",  # Unsupported policy
        terms_url="https://source.example.com/terms",
        terms_checked_on=date.today(),
    )

    with pytest.raises(ValidationError) as exc_info:
        await use_case.approve_source(cmd)
    assert exc_info.value.field == "image_policy"


@pytest.mark.asyncio
async def test_approve_source_rejects_future_terms_checked_date() -> None:
    source = make_source()
    uow = FakeUnitOfWork(source)
    use_case = ManageCatalogSourceUseCase(uow)  # type: ignore[arg-type]

    cmd = ApproveCatalogSourceCommand(
        source_id=source.id,
        rights_display=True,
        rights_tryon=False,
        image_policy="mirror",
        terms_url="https://source.example.com/terms",
        terms_checked_on=date.today() + timedelta(days=2),
    )

    with pytest.raises(ValidationError) as exc_info:
        await use_case.approve_source(cmd)
    assert exc_info.value.field == "terms_checked_on"


@pytest.mark.asyncio
async def test_approve_source_rejects_tryon_without_display_rights() -> None:
    source = make_source()
    uow = FakeUnitOfWork(source)
    use_case = ManageCatalogSourceUseCase(uow)  # type: ignore[arg-type]

    cmd = ApproveCatalogSourceCommand(
        source_id=source.id,
        rights_display=False,
        rights_tryon=True,  # Tryon cannot be granted without display
        image_policy="mirror",
        terms_url="https://source.example.com/terms",
        terms_checked_on=date.today(),
    )

    with pytest.raises(ValidationError) as exc_info:
        await use_case.approve_source(cmd)
    assert exc_info.value.field == "rights_tryon"


@pytest.mark.asyncio
async def test_suspend_source_revokes_rights_and_records_reason() -> None:
    source = make_source(status="cleared", rights_display=True, rights_tryon=True)
    uow = FakeUnitOfWork(source)
    use_case = ManageCatalogSourceUseCase(uow)  # type: ignore[arg-type]

    decision = await use_case.suspend_source(source.id, reason="DMCA Notice received")
    assert decision.status == "suspended"
    assert decision.rights_display is False
    assert decision.rights_tryon is False
    assert source.status == "suspended"
    assert source.rights_display is False
    assert source.rights_tryon is False
    assert "DMCA Notice received" in (source.notes or "")
    uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_revoke_tryon_rights_preserves_display() -> None:
    source = make_source(status="cleared", rights_display=True, rights_tryon=True)
    uow = FakeUnitOfWork(source)
    use_case = ManageCatalogSourceUseCase(uow)  # type: ignore[arg-type]

    decision = await use_case.revoke_tryon_rights(source.id)
    assert decision.rights_tryon is False
    assert decision.rights_display is True
    assert source.rights_tryon is False
    assert source.rights_display is True
    uow.commit.assert_awaited_once()


# ---------------------------------------------------------------------------
# Integration Tests (SQLite in-memory session factory)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_ingest_fails_for_unregistered_unknown_source(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Ingestion must NEVER create or clear a source implicitly; missing source raises EntityNotFoundError."""
    uow = CatalogUnitOfWork(session_factory)
    async with uow:
        merchant = Merchant(name="Brand Unknown", merchant_type="brand")
        uow.merchants.add(merchant)
        await uow.commit()
        merchant_id = merchant.id

    use_case = IngestMerchantProductUseCase(uow)
    cmd = IngestProductCommand(
        merchant_id=merchant_id,
        source_product_id="SKU-UNREG-01",
        title="Unregistered Shirt",
        source_url="https://merchant.example.com/items/01",
        category="tops",
        price_minor=199900,
    )

    with pytest.raises(EntityNotFoundError) as exc_info:
        await use_case.execute(cmd)
    assert "CatalogSource" in str(exc_info.value)


@pytest.mark.asyncio
async def test_feed_excludes_pending_suspended_and_display_denied_sources(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """CanonicalGarmentRepository.list_feed_candidates must enforce status == 'cleared' and rights_display == True."""
    uow = CatalogUnitOfWork(session_factory)

    async with uow:
        merchant = Merchant(name="MultiSource Retailer", merchant_type="retailer")
        uow.merchants.add(merchant)
        await uow.flush()
        merchant_id = merchant.id

        # 1. Cleared Source with display rights (Eligible)
        src_cleared = CatalogSource(
            slug=f"merchant-{merchant_id}-cleared",
            name="Cleared Source",
            kind="manual",
            status="cleared",
            rights_display=True,
            rights_tryon=True,
            image_policy="mirror",
        )
        # 2. Pending Source (Ineligible)
        src_pending = CatalogSource(
            slug=f"merchant-{merchant_id}-pending",
            name="Pending Source",
            kind="manual",
            status="pending",
            rights_display=False,
            rights_tryon=False,
            image_policy="hotlink",
        )
        # 3. Suspended Source (Ineligible)
        src_suspended = CatalogSource(
            slug=f"merchant-{merchant_id}-suspended",
            name="Suspended Source",
            kind="manual",
            status="suspended",
            rights_display=False,
            rights_tryon=False,
            image_policy="mirror",
        )
        # 4. Cleared but rights_display = False (Ineligible)
        src_nodisplay = CatalogSource(
            slug=f"merchant-{merchant_id}-nodisplay",
            name="NoDisplay Source",
            kind="manual",
            status="cleared",
            rights_display=False,
            rights_tryon=False,
            image_policy="mirror",
        )

        uow.sources.add(src_cleared)
        uow.sources.add(src_pending)
        uow.sources.add(src_suspended)
        uow.sources.add(src_nodisplay)
        await uow.flush()

        async def _create_garment(source_id: UUID, sku: str, title: str) -> CanonicalGarment:
            g = CanonicalGarment(
                category="tops",
                display_name=title,
                price_minor=100000,
                version=1,
                in_stock=True,
                tryon_supported=True,
            )
            uow.canonical_garments.add(g)
            await uow.canonical_garments.flush()

            prod = MerchantProduct(
                merchant_id=merchant_id,
                source_id=source_id,
                source_product_id=sku,
                status="active",
                title=title,
                source_url=f"https://example.com/{sku}",
                canonical_garment_id=g.id,
            )
            uow.merchant_products.add(prod)
            await uow.merchant_products.flush()

            offer = MerchantOffer(
                garment_id=g.id,
                merchant_id=merchant_id,
                source_product_id=sku,
                url=f"https://example.com/{sku}",
                price_minor=100000,
                currency="INR",
                in_stock=True,
            )
            uow.offers.add(offer)
            await uow.offers.flush()
            return g

        g_cleared = await _create_garment(src_cleared.id, "SKU-CLEARED", "Cleared Shirt")
        g_pending = await _create_garment(src_pending.id, "SKU-PENDING", "Pending Shirt")
        g_suspended = await _create_garment(src_suspended.id, "SKU-SUSPENDED", "Suspended Shirt")
        g_nodisplay = await _create_garment(src_nodisplay.id, "SKU-NODISPLAY", "NoDisplay Shirt")
        await uow.commit()

    # Query feed candidates
    candidates = await uow.canonical_garments.list_feed_candidates(limit=50)
    candidate_ids = {c.id for c in candidates}

    assert g_cleared.id in candidate_ids, "Cleared source with display rights MUST be in feed"
    assert g_pending.id not in candidate_ids, "Pending source MUST be excluded from feed"
    assert g_suspended.id not in candidate_ids, "Suspended source MUST be excluded from feed"
    assert g_nodisplay.id not in candidate_ids, "Source with rights_display=False MUST be excluded"


@pytest.mark.asyncio
async def test_tryon_worker_fails_if_source_rights_revoked_at_job_execution(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """When a job is queued for an eligible product but source try-on rights are subsequently revoked,

    the try-on worker rechecks rights and fails authorization before inference.
    """
    catalog_uow = CatalogUnitOfWork(session_factory)
    profile_uow = ProfileUnitOfWork(session_factory)
    tryon_uow = TryOnUnitOfWork(session_factory)

    user_id = uuid4()
    # 1. Setup user with body_photo consent and photo
    async with profile_uow:
        user = User(id=user_id)
        profile_uow.users.add(user)
        consent = ConsentRecord(
            user_id=user_id, data_type="body_photo", granted=True, is_18_or_older=True
        )
        profile_uow.consents.add(consent)
        photo = UserPhoto(
            user_id=user_id,
            storage_key="photos/ref.jpg",
            photo_type="tryon_reference",
            status="accepted",
        )
        profile_uow.photos.add(photo)
        await profile_uow.commit()

    # 2. Setup merchant and source with try-on rights originally
    async with catalog_uow:
        merchant = Merchant(name="Revokeable Store", merchant_type="brand")
        catalog_uow.merchants.add(merchant)
        await catalog_uow.flush()

        source = CatalogSource(
            slug=f"merchant-{merchant.id}",
            name=merchant.name,
            kind="manual",
            status="cleared",
            rights_display=True,
            rights_tryon=True,
            image_policy="mirror",
        )
        catalog_uow.sources.add(source)
        await catalog_uow.flush()

        garment = CanonicalGarment(
            category="tops",
            display_name="Tuxedo Shirt",
            price_minor=300000,
            version=1,
            in_stock=True,
            tryon_supported=True,
        )
        catalog_uow.canonical_garments.add(garment)
        await catalog_uow.flush()

        product = MerchantProduct(
            merchant_id=merchant.id,
            source_id=source.id,
            source_product_id="SKU-TUX",
            status="active",
            title="Tuxedo Shirt",
            source_url="https://store.example.com/tux",
            canonical_garment_id=garment.id,
        )
        catalog_uow.merchant_products.add(product)
        await catalog_uow.commit()
        garment_id = garment.id
        source_id = source.id

    # 3. Create a pending try-on job
    job_id = uuid4()
    async with tryon_uow:
        job = TryOnJob(
            id=job_id,
            user_id=user_id,
            profile_photo_id=photo.id,
            garment_id=garment_id,
            status="queued",
            artifact_key=f"artifact-{job_id}",
            idempotency_key=f"idem-{job_id}",
            model_version="tryon-v1.6",
            pipeline_version="pilot-pipe-v1",
        )
        tryon_uow.jobs.add(job)
        await tryon_uow.commit()

    # 4. Now simulate source rights revocation (e.g. rights_tryon set to False)
    async with catalog_uow:
        src = await catalog_uow.sources.get_by_id(source_id)
        assert src is not None
        src.rights_tryon = False
        await catalog_uow.commit()

    # 5. Execute try-on job via ProcessTryOnJobUseCase
    worker = ProcessTryOnJobUseCase(
        tryon_uow=tryon_uow,
        profile_uow=profile_uow,
        catalog_uow=catalog_uow,
    )
    res = await worker.execute(job_id)

    # Job must fail authorization because source try-on rights were revoked
    assert res.status == "failed"
    assert res.failure_reason == "tryon_rights_revoked"

    async with tryon_uow:
        updated_job = await tryon_uow.jobs.get_by_id(job_id)
        assert updated_job is not None
        assert updated_job.status == "failed"
        assert updated_job.failure_reason == "tryon_rights_revoked"
