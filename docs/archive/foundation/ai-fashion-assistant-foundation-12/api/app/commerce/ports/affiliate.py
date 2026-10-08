from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID


@dataclass(frozen=True, slots=True)
class AffiliateRedirect:
    redirect_url: str
    affiliate_network: str
    tracking_id: str


class AffiliateProvider(Protocol):
    def build_redirect(
        self,
        *,
        merchant_url: str,
        merchant_id: UUID,
        offer_id: UUID,
        tracking_id: str,
    ) -> AffiliateRedirect: ...
