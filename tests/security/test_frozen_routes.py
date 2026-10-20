from __future__ import annotations

import os

from fashx.core.settings import Settings
from fashx.main import create_app

FROZEN_DOMAINS = [
    "cart",
    "checkout",
    "payment",
    "order",
    "inventory",
    "promotion",
    "fulfil",
    "return",
]


def test_frozen_routes_absent_in_default_mvp() -> None:
    orig_frozen = os.environ.pop("FASHX_ENABLE_FROZEN", None)
    try:
        settings = Settings(enable_frozen=False, enable_b2b=False)
        app = create_app(settings)
        paths = app.openapi()["paths"]

        matched = [
            path
            for path in paths
            if any(term in path.lower() for term in FROZEN_DOMAINS)
        ]
        assert (
            matched == []
        ), f"Expected zero frozen domain paths in default MVP, but found: {matched}"
    finally:
        if orig_frozen is not None:
            os.environ["FASHX_ENABLE_FROZEN"] = orig_frozen


def test_frozen_routes_mounted_when_flag_enabled() -> None:
    orig_frozen = os.environ.pop("FASHX_ENABLE_FROZEN", None)
    try:
        settings = Settings(enable_frozen=True, enable_b2b=False)
        app = create_app(settings)
        paths = app.openapi()["paths"]

        matched = [
            path
            for path in paths
            if any(term in path.lower() for term in FROZEN_DOMAINS)
        ]
        assert len(matched) > 0, "Expected frozen routes to mount when enable_frozen=True"
        assert "/api/v1/cart" in paths
        assert "/api/v1/checkout" in paths
        assert "/api/v1/inventory/items" in paths
    finally:
        if orig_frozen is not None:
            os.environ["FASHX_ENABLE_FROZEN"] = orig_frozen
