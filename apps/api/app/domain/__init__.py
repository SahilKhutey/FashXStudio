"""
Pure Domain Layer (Rule I03)
Zero web framework, database, or cloud infrastructure imports.
"""

from app.domain.tryon_keys import compute_tryon_artifact_key

__all__ = ["compute_tryon_artifact_key"]
