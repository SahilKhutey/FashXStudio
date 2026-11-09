from fashx.core.rc10_timing import measure_call


def test_measure_call_returns_value():
    value, timing = measure_call(lambda: 42)
    assert value == 42
    assert timing.value == 42
    assert timing.duration_ms >= 0.0


def test_measure_call_preserves_exception():
    def fail():
        raise ValueError("expected")

    try:
        measure_call(fail)
    except ValueError as exc:
        assert str(exc) == "expected"
    else:
        raise AssertionError("Expected ValueError")
