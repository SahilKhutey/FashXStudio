from datetime import datetime
from uuid import UUID

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, UUIDPrimaryKeyMixin


class User(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "users"

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    photos: Mapped[list["UserPhoto"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    consents: Mapped[list["ConsentRecord"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class ConsentRecord(Base):
    __tablename__ = "consent_records"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    data_type: Mapped[str] = mapped_column(String(64), primary_key=True)
    granted: Mapped[bool] = mapped_column(Boolean, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    policy_version: Mapped[str] = mapped_column(String(16), default="2026.1", nullable=False)
    is_18_or_older: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    consented_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[User] = relationship(back_populates="consents")


class UserPhoto(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "user_photos"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    photo_type: Mapped[str] = mapped_column(String(32), nullable=False)
    storage_key: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    reject_reason: Mapped[str | None] = mapped_column(Text)
    version: Mapped[int] = mapped_column(default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    content_sha256: Mapped[str | None] = mapped_column(String(64), index=True)
    width: Mapped[int | None] = mapped_column(Integer)
    height: Mapped[int | None] = mapped_column(Integer)
    image_format: Mapped[str | None] = mapped_column(String(16))
    file_size_bytes: Mapped[int | None] = mapped_column(Integer)
    has_person: Mapped[bool | None] = mapped_column(Boolean)
    has_face: Mapped[bool | None] = mapped_column(Boolean)
    quality_score: Mapped[float | None] = mapped_column(Float)
    pose_score: Mapped[float | None] = mapped_column(Float)
    framing_score: Mapped[float | None] = mapped_column(Float)
    landmark_confidence: Mapped[float | None] = mapped_column(Float)
    ready_for_tryon: Mapped[bool | None] = mapped_column(Boolean)
    quality_reasons: Mapped[list[str]] = mapped_column(JSON, default=list)
    pose_provider: Mapped[str | None] = mapped_column(String(64))
    pose_provider_version: Mapped[str | None] = mapped_column(String(64))

    user: Mapped[User] = relationship(back_populates="photos")
