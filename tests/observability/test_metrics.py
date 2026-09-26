from app.observability.metrics import Counter, MetricsRegistry


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
