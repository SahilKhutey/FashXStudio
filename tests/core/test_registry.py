import pytest

from app.core.registry import CoreRegistry


def test_registry_register_and_get():
    registry = CoreRegistry()
    service = object()

    registry.register("product_service", service)

    assert registry.get("product_service") is service
    assert registry.contains("product_service")


def test_registry_rejects_duplicate():
    registry = CoreRegistry()

    registry.register("service", object())

    with pytest.raises(ValueError):
        registry.register("service", object())


def test_registry_missing_component():
    registry = CoreRegistry()

    with pytest.raises(KeyError):
        registry.get("missing")
