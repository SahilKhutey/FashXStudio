from abc import ABC, abstractmethod
from uuid import UUID

from .entities import Price, PricingRule


class PriceRepository(ABC):
    @abstractmethod
    async def get(
        self,
        price_id: UUID,
    ) -> Price | None:
        raise NotImplementedError

    @abstractmethod
    async def save(
        self,
        price: Price,
    ) -> Price:
        raise NotImplementedError

    @abstractmethod
    async def list_for_target(
        self,
        *,
        product_id: UUID,
        variant_id: UUID | None = None,
        listing_id: UUID | None = None,
    ) -> list[Price]:
        raise NotImplementedError


class PricingRuleRepository(ABC):
    @abstractmethod
    async def get(
        self,
        rule_id: UUID,
    ) -> PricingRule | None:
        raise NotImplementedError

    @abstractmethod
    async def save(
        self,
        rule: PricingRule,
    ) -> PricingRule:
        raise NotImplementedError

    @abstractmethod
    async def list_active(
        self,
    ) -> list[PricingRule]:
        raise NotImplementedError
