from typing import Annotated
from uuid import UUID

from fastapi import Header, HTTPException, status

DEFAULT_ORG_ID = UUID("00000000-0000-0000-0000-000000000001")


def get_current_organization_id(
    x_organization_id: Annotated[str | None, Header()] = None,
) -> UUID:
    if not x_organization_id:
        return DEFAULT_ORG_ID
    try:
        return UUID(x_organization_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid X-Organization-Id UUID: '{x_organization_id}'",
        )


def get_expected_revision(
    if_match: Annotated[str | None, Header()] = None,
) -> int | None:
    if not if_match:
        return None
    cleaned = if_match.strip('"').strip("'")
    if cleaned.startswith("revision-"):
        cleaned = cleaned[len("revision-") :]
    try:
        return int(cleaned)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid If-Match revision header: '{if_match}'",
        )
