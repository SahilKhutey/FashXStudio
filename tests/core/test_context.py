from app.core.context import CoreContext


def test_context_creation():
    context = CoreContext.create()

    assert context.request_id is not None
    assert context.correlation_id is not None
    assert context.actor_id is None


def test_context_preserves_actor():
    actor = CoreContext.create().request_id

    context = CoreContext.create(actor_id=actor)

    assert context.actor_id == actor
