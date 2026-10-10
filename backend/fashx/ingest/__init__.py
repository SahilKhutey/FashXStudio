"""Ingest domain models and feed ingestion pipeline."""

from .model import CanonicalProduct, parse_price

__all__ = ["CanonicalProduct", "parse_price"]
