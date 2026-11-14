from fashx.core.metrics import PROHIBITED_DIMENSION_KEYS, emit_metric
from fashx.observability.metrics import Counter, MetricsRegistry


def test_counter_increment():
    c = Counter(name="orders_processed")
    assert c.name == "orders_processed"
    assert c.value == 0

    c.increment()
    assert c.value == 1

    c.increment(5)
    assert c.value == 6


def test_metrics_registry():
    registry = MetricsRegistry()
    assert len(registry.counters) == 0

    counter1 = registry.counter("http_requests")
    assert counter1.value == 0
    counter1.increment(2)

    # Retrieval gets the same instance
    counter2 = registry.counter("http_requests")
    assert counter2 is counter1
    assert counter2.value == 2

    # Different counter
    other_counter = registry.counter("db_queries")
    assert other_counter.value == 0
    assert other_counter is not counter1


def test_emit_metric_emf_specification():
    event = emit_metric(
        name="RequestLatency",
        value=124.5,
        unit="Milliseconds",
        service="api",
        environment="staging",
        dimensions={"Route": "/api/v1/feed", "Method": "GET", "StatusClass": "2xx"},
        namespace="FashX/API",
    )

    assert "_aws" in event
    aws_meta = event["_aws"]
    assert "Timestamp" in aws_meta
    assert len(aws_meta["CloudWatchMetrics"]) == 1

    cw_metric = aws_meta["CloudWatchMetrics"][0]
    assert cw_metric["Namespace"] == "FashX/API"
    assert len(cw_metric["Dimensions"]) == 1
    assert set(cw_metric["Dimensions"][0]) == {"Service", "Environment", "Route", "Method", "StatusClass"}
    assert cw_metric["Metrics"][0] == {"Name": "RequestLatency", "Unit": "Milliseconds"}

    # Top-level properties
    assert event["Service"] == "api"
    assert event["Environment"] == "staging"
    assert event["Route"] == "/api/v1/feed"
    assert event["Method"] == "GET"
    assert event["StatusClass"] == "2xx"
    assert event["RequestLatency"] == 124.5


def test_emit_metric_strips_high_cardinality_dimensions():
    event = emit_metric(
        name="RequestCount",
        value=1.0,
        unit="Count",
        service="api",
        environment="prod",
        dimensions={
            "Route": "/api/v1/feed",
            "request_id": "req-12345",
            "user_id": "usr-secret-999",
            "job_id": "job-888",
            "url": "https://api.fashx.com/api/v1/feed?query=shirt",
        },
    )

    dimensions_in_event = event["_aws"]["CloudWatchMetrics"][0]["Dimensions"][0]
    for prohibited in PROHIBITED_DIMENSION_KEYS:
        assert prohibited not in dimensions_in_event
        assert prohibited not in event
    assert "Route" in dimensions_in_event
