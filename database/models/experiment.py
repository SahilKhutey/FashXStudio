from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, UUIDPrimaryKeyMixin


class ExperimentExposure(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "experiment_exposures"
    __table_args__ = (
        UniqueConstraint("user_id", "experiment", name="uq_user_experiment"),
    )

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    experiment: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    variant: Mapped[str] = mapped_column(Text, nullable=False)
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
