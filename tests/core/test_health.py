from fashx.core.health import core_health
from fashx.core.version import CORE_VERSION


def test_core_health():
    report = core_health()

    assert report.component == "fashxstudio-core"
    assert report.status == "healthy"
    assert report.version == CORE_VERSION
    assert report.details["event_bus"] == "ready"
