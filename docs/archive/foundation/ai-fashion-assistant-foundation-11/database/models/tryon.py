from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, UUIDPrimaryKeyMixin


class TryOnJob(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "tryon_jobs"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    garment_id: Mapped[UUID] = mapped_column(ForeignKey("canonical_garments.id", ondelete="CASCADE"), index=True)
    profile_photo_id: Mapped[UUID] = mapped_column(ForeignKey("user_photos.id", ondelete="RESTRICT"))
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)
    artifact_key: Mapped[str] = mapped_column(String(512), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="queued", nullable=False)
    model_version: Mapped[str] = mapped_column(String(64), nullable=False)
    pipeline_version: Mapped[str] = mapped_column(String(64), nullable=False)
    failure_reason: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        UniqueConstraint("user_id", "idempotency_key", name="uq_tryon_user_idempotency"),
        UniqueConstraint("artifact_key", name="uq_tryon_artifact_key"),
    )


class TryOnArtifact(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "tryon_artifacts"

    job_id: Mapped[UUID] = mapped_column(ForeignKey("tryon_jobs.id", ondelete="CASCADE"), unique=True)
    artifact_key: Mapped[str] = mapped_column(String(512), unique=True, nullable=False)
    result_key: Mapped[str] = mapped_column(Text, nullable=False)
    model_version: Mapped[str] = mapped_column(String(64), nullable=False)
    pipeline_version: Mapped[str] = mapped_column(String(64), nullable=False)
    photo_version: Mapped[int] = mapped_column(nullable=False)
    garment_version: Mapped[int] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
