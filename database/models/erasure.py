from datetime import datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg
from sqlalchemy.orm import Mapped, mapped_column

from database.models.base import Base


class ErasureTombstone(Base):
    """Minimal pseudonymous tombstone of erased user IDs to prevent resurrection on backup restore."""

    __tablename__ = "erasure_tombstones"

    user_id: Mapped[UUID] = mapped_column(pg.UUID(as_uuid=True), primary_key=True)
    erased_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=False,
        server_default=sa.text("now()"),
    )
