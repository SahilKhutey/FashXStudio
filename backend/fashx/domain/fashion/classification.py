from __future__ import annotations

from uuid import UUID

from app.core.errors import ValidationError

from .entities import TaxonomyNode


def validate_parent(
    node: TaxonomyNode,
) -> None:

    if node.parent_id is not None:
        if node.parent_id == node.id:
            raise ValidationError(
                "A taxonomy node cannot be its own parent.",
                {"node_id": str(node.id)},
            )


def validate_taxonomy_path(
    node: TaxonomyNode,
    ancestors: list[TaxonomyNode],
) -> None:

    visited: set[UUID] = {node.id}

    for ancestor in ancestors:
        if ancestor.id in visited:
            raise ValidationError(
                "Taxonomy hierarchy contains a cycle."
            )

        visited.add(ancestor.id)
