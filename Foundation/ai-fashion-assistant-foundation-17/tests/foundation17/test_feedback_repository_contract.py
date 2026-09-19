import ast
from pathlib import Path


def test_feedback_repository_owns_visual_feedback_table() -> None:
    source = Path("api/app/feedback/repository.py").read_text()
    tree = ast.parse(source)
    names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
    assert "TryOnFeedback" in names


def test_tryon_feedback_table_has_unique_user_job_constraint() -> None:
    source = Path("database/models/commerce_feedback.py").read_text()
    assert 'UniqueConstraint("user_id", "tryon_job_id", name="uq_tryon_feedback_user_job")' in source
