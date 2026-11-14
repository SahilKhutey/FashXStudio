from kombu import Exchange, Queue

EXCHANGE = Exchange("fashx", type="direct", durable=True)

TRYON_QUEUE = Queue(
    "tryon",
    exchange=EXCHANGE,
    routing_key="tryon",
    durable=True,
)

INGEST_QUEUE = Queue(
    "ingest",
    exchange=EXCHANGE,
    routing_key="ingest",
    durable=True,
)

MAINTENANCE_QUEUE = Queue(
    "maintenance",
    exchange=EXCHANGE,
    routing_key="maintenance",
    durable=True,
)

TASK_QUEUES = (
    TRYON_QUEUE,
    INGEST_QUEUE,
    MAINTENANCE_QUEUE,
)

TASK_ROUTES = {
    "fashx.workers.app.process_tryon_job": {
        "queue": "tryon",
        "routing_key": "tryon",
    },
    "fashx.workers.app.ingest_catalog_feed": {
        "queue": "ingest",
        "routing_key": "ingest",
    },
    "fashx.workers.app.enrich_garment_task": {
        "queue": "ingest",
        "routing_key": "ingest",
    },
    "fashx.workers.app.relay_outbox_events": {
        "queue": "maintenance",
        "routing_key": "maintenance",
    },
    "fashx.workers.app.sweep_storage_erasure": {
        "queue": "maintenance",
        "routing_key": "maintenance",
    },
    "fashx.workers.app.run_retention_jobs": {
        "queue": "maintenance",
        "routing_key": "maintenance",
    },
    "fashx.validation.ping_tryon": {
        "queue": "tryon",
        "routing_key": "tryon",
    },
    "fashx.validation.ping_ingest": {
        "queue": "ingest",
        "routing_key": "ingest",
    },
    "fashx.validation.ping_maintenance": {
        "queue": "maintenance",
        "routing_key": "maintenance",
    },
    "fashx.validation.retryable": {
        "queue": "maintenance",
        "routing_key": "maintenance",
    },
    "fashx.validation.fatal": {
        "queue": "maintenance",
        "routing_key": "maintenance",
    },
}
