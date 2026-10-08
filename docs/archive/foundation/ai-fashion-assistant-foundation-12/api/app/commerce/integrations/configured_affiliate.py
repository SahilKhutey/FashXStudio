from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from uuid import UUID

from api.app.core.settings import Settings
from api.app.commerce.ports.affiliate import AffiliateRedirect


class ConfiguredAffiliateProvider:
    """Small MVP affiliate adapter.

    It appends a configured tracking parameter to a trusted merchant URL. Real
    networks should be implemented as separate adapters once their exact
    redirect contract is known.
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def build_redirect(
        self,
        *,
        merchant_url: str,
        merchant_id: UUID,
        offer_id: UUID,
        tracking_id: str,
    ) -> AffiliateRedirect:
        parts = urlsplit(merchant_url)
        if parts.scheme not in {"https", "http"} or not parts.netloc:
            raise ValueError("Merchant URL is invalid")

        query = dict(parse_qsl(parts.query, keep_blank_values=True))
        query[self.settings.affiliate_tracking_param] = tracking_id
        if self.settings.affiliate_source_param:
            query[self.settings.affiliate_source_param] = self.settings.affiliate_network

        redirect_url = urlunsplit(
            (parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment)
        )
        return AffiliateRedirect(
            redirect_url=redirect_url,
            affiliate_network=self.settings.affiliate_network,
            tracking_id=tracking_id,
        )
