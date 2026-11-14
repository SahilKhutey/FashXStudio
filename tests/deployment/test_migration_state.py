from alembic.config import Config
from alembic.script import ScriptDirectory

from scripts.staging.validate_migrations import validate_migrations


def test_migration_heads_single_head():
    alembic_cfg = Config("alembic.ini")
    script = ScriptDirectory.from_config(alembic_cfg)
    heads = script.get_heads()
    assert len(heads) == 1, f"Expected exactly 1 migration head, found {heads}"


def test_validate_migrations_script():
    outcome = validate_migrations()
    assert outcome["status"] in ("PASS", "WARN")
    assert "head_revision" in outcome
