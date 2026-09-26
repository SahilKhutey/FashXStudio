from app.core.runtime import get_core_runtime, reset_core_runtime


def test_core_runtime_singleton():
    reset_core_runtime()
    rt1 = get_core_runtime()
    rt2 = get_core_runtime()

    assert rt1 is rt2
    assert rt1.registry is not None
    assert rt1.event_bus is not None

    reset_core_runtime()
    rt3 = get_core_runtime()
    assert rt3 is not rt1
    reset_core_runtime()
