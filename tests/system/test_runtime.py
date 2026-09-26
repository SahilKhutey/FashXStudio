import pytest

from app.core.bootstrap import (
    REQUIRED_COMPONENTS,
    register_core_services,
    validate_required_services,
    validate_runtime,
)
from app.core.runtime import CoreRuntime
from app.core.version import (
    BUILD_INFO,
    CORE_API_VERSION,
    CORE_VERSION,
    PRODUCT_NAME,
    RELEASE_STATUS,
    SYSTEM_STAGE,
)


def test_core_version_lock():
    assert CORE_VERSION == "1.0.0"
    assert CORE_API_VERSION == "v1"
    assert PRODUCT_NAME == "FashXStudio"
    assert SYSTEM_STAGE == "core"
    assert RELEASE_STATUS == "production-ready"

    assert BUILD_INFO.product == PRODUCT_NAME
    assert BUILD_INFO.core_version == "1.0.0"
    assert BUILD_INFO.api_version == "v1"
    assert BUILD_INFO.stage == "core"
    assert BUILD_INFO.release_status == "production-ready"


def test_validate_runtime_with_bootstrapped_services():
    runtime = CoreRuntime()
    register_core_services(runtime)

    # All required components should be present
    assert validate_runtime(runtime) is True
    assert validate_required_services(runtime) is True

    for comp in REQUIRED_COMPONENTS:
        assert runtime.registry.contains(comp)


def test_validate_runtime_missing_component():
    runtime = CoreRuntime()
    with pytest.raises(RuntimeError) as exc_info:
        validate_runtime(runtime, required_components=["nonexistent_service"])
    assert "Missing components" in str(exc_info.value)
