"""Canonical product representation matching Google Merchant feed schema."""

import re
from decimal import Decimal, InvalidOperation
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl, field_validator


class CanonicalProduct(BaseModel):
    source_product_id: str
    item_group_id: str | None = None
    title: str = Field(min_length=2, max_length=300)
    description: str = Field(default="", max_length=5000)
    brand: str | None = None
    link: HttpUrl
    image_url: HttpUrl
    extra_image_urls: list[HttpUrl] = Field(default_factory=list)
    price: Decimal
    sale_price: Decimal | None = None
    currency: str = "INR"
    in_stock: bool = True
    gender: Literal["female", "male", "unisex"] | None = None
    age_group: str | None = None
    color: str | None = None
    size: str | None = None
    material: str | None = None
    pattern: str | None = None
    gtin: str | None = None
    source_category: str | None = None

    @field_validator("price", "sale_price")
    @classmethod
    def positive(cls, v: Decimal | None) -> Decimal | None:
        if v is not None and v <= 0:
            raise ValueError("price must be positive")
        return v

    @field_validator("currency")
    @classmethod
    def validate_inr(cls, v: str) -> str:
        if v != "INR":
            raise ValueError("unsupported_currency")
        return v


def parse_price(raw: str) -> tuple[Decimal, str]:
    """Parse price string into a Decimal amount and currency code.

    Examples:
    '1499 INR' -> (Decimal('1499'), 'INR')
    '1,499.50' -> (Decimal('1499.50'), 'INR')
    '₹2499'    -> (Decimal('2499'), 'INR')
    '99.00 USD' -> (Decimal('99.00'), 'USD')
    """
    cleaned = (raw or "").strip().replace("₹", "").replace("Rs.", "").replace("Rs", "").strip()
    m = re.match(r"^([\d,]+(?:\.\d+)?)\s*([A-Za-z]{3})?$", cleaned)
    if not m:
        raise ValueError(f"unparseable price: {raw!r}")
    try:
        val = Decimal(m.group(1).replace(",", ""))
        curr = (m.group(2) or "INR").upper()
        return val, curr
    except InvalidOperation as e:
        raise ValueError(f"unparseable price: {raw!r}") from e
