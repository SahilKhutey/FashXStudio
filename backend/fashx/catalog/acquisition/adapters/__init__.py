"""Store-specific catalog acquisition adapters."""

from fashx.catalog.acquisition.adapters.amazon import AmazonAdapter
from fashx.catalog.acquisition.adapters.base import (
    BaseSourceAdapter,
    CircuitBreakerOpenError,
)
from fashx.catalog.acquisition.adapters.flipkart import FlipkartAdapter
from fashx.catalog.acquisition.adapters.myntra import MyntraAdapter
from fashx.catalog.acquisition.adapters.partner_feed import PartnerFeedAdapter

__all__ = [
    "AmazonAdapter",
    "BaseSourceAdapter",
    "CircuitBreakerOpenError",
    "FlipkartAdapter",
    "MyntraAdapter",
    "PartnerFeedAdapter",
]
