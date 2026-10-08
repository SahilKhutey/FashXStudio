from datetime import UTC, datetime
from uuid import UUID, uuid4

from fashx.core.contracts import Entity


class TestEntity(Entity):
    __test__ = False

    def __init__(self):
        self.id = uuid4()
        self.created_at = datetime.now(UTC)
        self.updated_at = self.created_at

    def validate(self):
        return None


def test_entity_contract():
    entity = TestEntity()

    assert isinstance(entity.id, UUID)
    assert entity.created_at is not None
    assert entity.updated_at is not None
    assert entity.validate() is None
