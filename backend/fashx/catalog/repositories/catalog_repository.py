from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from database.models.catalog import (
    CanonicalGarment,
    CatalogSource,
    CategoryMap,
    GarmentEnrichment,
    GarmentImage,
    IngestRun,
    Merchant,
    MerchantOffer,
    MerchantProduct,
    SizeChart,
    SizeMeasurement,
)
from fashx.core.repository import BaseRepository
from fashx.core.unit_of_work import SqlAlchemyUnitOfWork


class MerchantRepository(BaseRepository[Merchant]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Merchant)

    async def get_by_name(self, name: str) -> Merchant | None:
        stmt = select(Merchant).where(Merchant.name == name)
        result = await self.session.scalars(stmt)
        return result.first()


class MerchantProductRepository(BaseRepository[MerchantProduct]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, MerchantProduct)

    async def get_by_source_id(
        self, merchant_id: UUID, source_product_id: str
    ) -> MerchantProduct | None:
        stmt = select(MerchantProduct).where(
            MerchantProduct.merchant_id == merchant_id,
            MerchantProduct.source_product_id == source_product_id,
        )
        result = await self.session.scalars(stmt)
        return result.first()


class CanonicalGarmentRepository(BaseRepository[CanonicalGarment]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, CanonicalGarment)

    async def list_feed_candidates(self, limit: int = 200) -> Sequence[CanonicalGarment]:
        """Fetch canonical garments that have active offers from cleared sources."""
        stmt = (
            select(CanonicalGarment)
            .join(MerchantOffer, MerchantOffer.garment_id == CanonicalGarment.id)
            .join(
                MerchantProduct,
                (MerchantProduct.merchant_id == MerchantOffer.merchant_id)
                & (MerchantProduct.source_product_id == MerchantOffer.source_product_id),
            )
            .join(CatalogSource, CatalogSource.id == MerchantProduct.source_id)
            .where(
                CatalogSource.status == "cleared",
                MerchantProduct.status == "active",
            )
            .distinct()
            .limit(limit)
        )
        result = await self.session.scalars(stmt)
        return result.all()


class CatalogSourceRepository(BaseRepository[CatalogSource]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, CatalogSource)

    async def get_by_slug(self, slug: str) -> CatalogSource | None:
        stmt = select(CatalogSource).where(CatalogSource.slug == slug)
        result = await self.session.scalars(stmt)
        return result.first()


class CategoryMapRepository(BaseRepository[CategoryMap]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, CategoryMap)

    async def get_mapping(self, source_id: UUID, source_category: str) -> CategoryMap | None:
        stmt = select(CategoryMap).where(
            CategoryMap.source_id == source_id,
            CategoryMap.source_category == source_category,
        )
        result = await self.session.scalars(stmt)
        return result.first()

    async def list_for_source(self, source_id: UUID) -> Sequence[CategoryMap]:
        stmt = select(CategoryMap).where(CategoryMap.source_id == source_id)
        result = await self.session.scalars(stmt)
        return result.all()


class IngestRunRepository(BaseRepository[IngestRun]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, IngestRun)

    async def get_latest_run(self, source_id: UUID) -> IngestRun | None:
        stmt = (
            select(IngestRun)
            .where(IngestRun.source_id == source_id)
            .order_by(IngestRun.started_at.desc())
            .limit(1)
        )
        result = await self.session.scalars(stmt)
        return result.first()


class MerchantOfferRepository(BaseRepository[MerchantOffer]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, MerchantOffer)

    async def get_by_merchant_and_product(
        self, merchant_id: UUID, source_product_id: str
    ) -> MerchantOffer | None:
        stmt = select(MerchantOffer).where(
            MerchantOffer.merchant_id == merchant_id,
            MerchantOffer.source_product_id == source_product_id,
        )
        result = await self.session.scalars(stmt)
        return result.first()

    async def list_for_garment(self, garment_id: UUID) -> Sequence[MerchantOffer]:
        stmt = select(MerchantOffer).where(MerchantOffer.garment_id == garment_id)
        result = await self.session.scalars(stmt)
        return result.all()

    async def upsert_offer(
        self,
        garment_id: UUID,
        merchant_id: UUID,
        source_product_id: str,
        url: str,
        price_minor: int,
        currency: str = "INR",
        in_stock: bool = True,
    ) -> MerchantOffer:
        offer = await self.get_by_merchant_and_product(merchant_id, source_product_id)
        if offer is not None:
            offer.garment_id = garment_id
            offer.url = url
            offer.price_minor = price_minor
            offer.currency = currency
            offer.in_stock = in_stock
            offer.last_synced_at = datetime.now(UTC)
            return offer

        offer = MerchantOffer(
            garment_id=garment_id,
            merchant_id=merchant_id,
            source_product_id=source_product_id,
            url=url,
            price_minor=price_minor,
            currency=currency,
            in_stock=in_stock,
        )
        self.add(offer)
        return offer


class GarmentImageRepository(BaseRepository[GarmentImage]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, GarmentImage)

    async def get_by_hash(self, content_hash: str) -> GarmentImage | None:
        stmt = select(GarmentImage).where(GarmentImage.content_hash == content_hash)
        result = await self.session.scalars(stmt)
        return result.first()

    async def list_for_garment(self, garment_id: UUID) -> Sequence[GarmentImage]:
        stmt = select(GarmentImage).where(GarmentImage.garment_id == garment_id)
        result = await self.session.scalars(stmt)
        return result.all()


class GarmentEnrichmentRepository(BaseRepository[GarmentEnrichment]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, GarmentEnrichment)

    async def get_by_garment_id(self, garment_id: UUID) -> GarmentEnrichment | None:
        stmt = (
            select(GarmentEnrichment)
            .where(GarmentEnrichment.garment_id == garment_id)
            .order_by(GarmentEnrichment.created_at.desc())
        )
        result = await self.session.scalars(stmt)
        return result.first()


class SizeChartRepository(BaseRepository[SizeChart]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, SizeChart)

    async def get_by_garment_id(self, garment_id: UUID) -> SizeChart | None:
        stmt = (
            select(SizeChart)
            .where(SizeChart.garment_id == garment_id)
            .order_by(SizeChart.created_at.desc())
        )
        result = await self.session.scalars(stmt)
        return result.first()


class SizeMeasurementRepository(BaseRepository[SizeMeasurement]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, SizeMeasurement)

    async def list_for_garment(self, garment_id: UUID) -> Sequence[SizeMeasurement]:
        stmt = select(SizeMeasurement).where(SizeMeasurement.garment_id == garment_id)
        result = await self.session.scalars(stmt)
        return result.all()

    async def list_for_chart(self, size_chart_id: UUID) -> Sequence[SizeMeasurement]:
        stmt = select(SizeMeasurement).where(SizeMeasurement.size_chart_id == size_chart_id)
        result = await self.session.scalars(stmt)
        return result.all()


class CatalogUnitOfWork(SqlAlchemyUnitOfWork):
    """Unit of Work bundling Catalog aggregate repositories."""

    def __init__(
        self,
        session_factory: (
            Callable[[], AsyncSession] | async_sessionmaker[AsyncSession] | None
        ) = None,
    ) -> None:
        super().__init__(session_factory)
        self._merchants: MerchantRepository | None = None
        self._merchant_products: MerchantProductRepository | None = None
        self._canonical_garments: CanonicalGarmentRepository | None = None
        self._offers: MerchantOfferRepository | None = None
        self._images: GarmentImageRepository | None = None
        self._enrichments: GarmentEnrichmentRepository | None = None
        self._size_charts: SizeChartRepository | None = None
        self._size_measurements: SizeMeasurementRepository | None = None
        self._sources: CatalogSourceRepository | None = None
        self._category_maps: CategoryMapRepository | None = None
        self._ingest_runs: IngestRunRepository | None = None

    async def __aenter__(self) -> "CatalogUnitOfWork":
        await super().__aenter__()
        self._merchants = None
        self._merchant_products = None
        self._canonical_garments = None
        self._offers = None
        self._images = None
        self._enrichments = None
        self._size_charts = None
        self._size_measurements = None
        self._sources = None
        self._category_maps = None
        self._ingest_runs = None
        return self

    @property
    def merchants(self) -> MerchantRepository:
        if self._merchants is None:
            self._merchants = MerchantRepository(self.session)
        return self._merchants

    @property
    def merchant_products(self) -> MerchantProductRepository:
        if self._merchant_products is None:
            self._merchant_products = MerchantProductRepository(self.session)
        return self._merchant_products

    @property
    def products(self) -> MerchantProductRepository:
        return self.merchant_products

    @property
    def canonical_garments(self) -> CanonicalGarmentRepository:
        if self._canonical_garments is None:
            self._canonical_garments = CanonicalGarmentRepository(self.session)
        return self._canonical_garments

    @property
    def offers(self) -> MerchantOfferRepository:
        if self._offers is None:
            self._offers = MerchantOfferRepository(self.session)
        return self._offers

    @property
    def images(self) -> GarmentImageRepository:
        if self._images is None:
            self._images = GarmentImageRepository(self.session)
        return self._images

    @property
    def enrichments(self) -> GarmentEnrichmentRepository:
        if self._enrichments is None:
            self._enrichments = GarmentEnrichmentRepository(self.session)
        return self._enrichments

    @property
    def size_charts(self) -> SizeChartRepository:
        if self._size_charts is None:
            self._size_charts = SizeChartRepository(self.session)
        return self._size_charts

    @property
    def size_measurements(self) -> SizeMeasurementRepository:
        if self._size_measurements is None:
            self._size_measurements = SizeMeasurementRepository(self.session)
        return self._size_measurements

    @property
    def sources(self) -> CatalogSourceRepository:
        if self._sources is None:
            self._sources = CatalogSourceRepository(self.session)
        return self._sources

    @property
    def category_maps(self) -> CategoryMapRepository:
        if self._category_maps is None:
            self._category_maps = CategoryMapRepository(self.session)
        return self._category_maps

    @property
    def ingest_runs(self) -> IngestRunRepository:
        if self._ingest_runs is None:
            self._ingest_runs = IngestRunRepository(self.session)
        return self._ingest_runs
