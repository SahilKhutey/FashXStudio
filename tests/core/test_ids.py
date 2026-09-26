from uuid import UUID

from app.core.ids import new_id, parse_id


def test_new_id_returns_uuid():
    value = new_id()

    assert isinstance(value, UUID)


def test_parse_id_accepts_string():
    value = new_id()

    parsed = parse_id(str(value))

    assert parsed == value


def test_parse_id_accepts_uuid():
    value = new_id()

    assert parse_id(value) == value
