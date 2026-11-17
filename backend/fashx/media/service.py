from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from database.models.media import MediaUpload, UserMedia
from fashx.core.metrics import emit_metric
from fashx.core.settings import get_settings

from .errors import ImageValidationError, MediaError
from .keys import new_image_id, new_upload_id, quarantine_key, validated_image_key
from .repository import MediaRepository
from .schemas import (
    MediaAccessUrlResponse,
    MediaDeletionResponse,
    MediaMetadataResponse,
    UploadCompleteRequest,
    UploadInitiateRequest,
    UploadInitiateResponse,
    UploadStatusResponse,
)
from .validation import ALLOWED_FORMATS, MAX_FILE_BYTES, MIN_FILE_BYTES, validate_image


class MediaUploadService:
    """Service orchestrating the secure photo upload, validation, and lifecycle."""

    def __init__(
        self,
        repository: MediaRepository,
        storage: Any,
    ) -> None:
        self.repo = repository
        self.storage = storage
        self.settings = get_settings()

    async def initiate(
        self,
        user_id: UUID,
        payload: UploadInitiateRequest,
    ) -> UploadInitiateResponse:
        # 1. Rate limiting: max 5 upload intents per user per 15 minutes
        since = datetime.now(UTC) - timedelta(minutes=15)
        recent_count = await self.repo.count_recent_uploads(user_id, since)
        if recent_count >= 5:
            emit_metric("MediaUploadRateLimited", 1.0, "Count", service="media", environment=self.settings.env)
            raise MediaError(429, "upload_rate_limited", "Maximum 5 upload intents per 15 minutes exceeded.")

        # 2. Concurrency limit: max 3 concurrent pending uploads per user
        pending_count = await self.repo.count_pending_uploads(user_id)
        if pending_count >= 3:
            raise MediaError(429, "concurrent_uploads_exceeded", "Maximum 3 concurrent pending uploads exceeded.")

        # 3. Storage quota: max 100 MB of active personal media per user
        active_bytes = await self.repo.get_total_media_size(user_id)
        if active_bytes + payload.declared_size_bytes > 100 * 1024 * 1024:
            raise MediaError(413, "media_storage_quota_exceeded", "Active personal media storage quota (100 MB) exceeded.")

        # 4. Content-Type pre-check
        normalized_mime = payload.content_type.split(";")[0].strip().lower()
        if normalized_mime == "image/jpg":
            normalized_mime = "image/jpeg"
        if normalized_mime not in ALLOWED_FORMATS.values():
            raise ImageValidationError("unsupported_image_format")

        # 5. Generate secure identifiers and keys
        upload_id = new_upload_id()
        image_id = new_image_id()
        env = getattr(self.settings, "env", "dev")

        q_key = quarantine_key(env, user_id, upload_id)
        f_key = validated_image_key(user_id, image_id)

        now = datetime.now(UTC)
        expires_at = now + timedelta(minutes=15)

        # 6. Persist upload intent before issuing presigned URL
        upload = MediaUpload(
            id=upload_id,
            image_id=image_id,
            user_id=user_id,
            purpose=payload.purpose,
            status="PENDING_UPLOAD",
            quarantine_key=q_key,
            final_key=f_key,
            declared_content_type=normalized_mime,
            declared_size_bytes=payload.declared_size_bytes,
            min_size_bytes=MIN_FILE_BYTES,
            max_size_bytes=MAX_FILE_BYTES,
            created_at=now,
            expires_at=expires_at,
        )
        await self.repo.create_upload(upload)

        # 7. Generate presigned PUT URL
        ttl_s = getattr(self.settings, "signed_url_ttl_s", 300)
        upload_url = self.storage.create_upload_url(
            q_key,
            content_type=normalized_mime,
            ttl_s=ttl_s,
        )

        emit_metric("MediaUploadInitiated", 1.0, "Count", service="media", environment=self.settings.env)

        return UploadInitiateResponse(
            upload_id=upload_id,
            image_id=image_id,
            upload_url=upload_url,
            method="PUT",
            required_headers={"Content-Type": normalized_mime},
            expires_in_seconds=ttl_s,
            status="PENDING_UPLOAD",
        )

    async def get_upload_status(
        self,
        user_id: UUID,
        upload_id: UUID,
    ) -> UploadStatusResponse:
        upload = await self.repo.get_upload(upload_id, user_id)
        if upload is None:
            raise MediaError(404, "upload_not_found", "Upload intent does not exist or is not owned by user.")
        return UploadStatusResponse(
            upload_id=upload.id,
            image_id=upload.image_id,
            status=upload.status,  # type: ignore[arg-type]
            message=upload.failure_code if upload.status == "REJECTED" else None,
        )

    async def complete(
        self,
        user_id: UUID,
        upload_id: UUID,
        payload: UploadCompleteRequest | None = None,
    ) -> UploadStatusResponse:
        upload = await self.repo.get_upload(upload_id, user_id)
        if upload is None:
            raise MediaError(404, "upload_not_found", "Upload intent does not exist or is not owned by user.")

        if upload.status == "AVAILABLE":
            return UploadStatusResponse(
                upload_id=upload.id,
                image_id=upload.image_id,
                status="AVAILABLE",
                message="Upload has already been validated and is available.",
            )

        if upload.status == "VALIDATING":
            return UploadStatusResponse(
                upload_id=upload.id,
                image_id=upload.image_id,
                status="VALIDATING",
                message="Your photo is being validated.",
            )

        if upload.status != "PENDING_UPLOAD":
            raise MediaError(409, "upload_already_completed", f"Upload is already in terminal state: {upload.status}")

        now = datetime.now(UTC)
        exp = upload.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=UTC)
        if exp <= now:
            await self.repo.update_upload_status(upload.id, "EXPIRED")
            raise MediaError(410, "upload_expired", "Upload authorization has expired.")

        # Check quarantine object in storage
        if not self.storage.exists(upload.quarantine_key):
            raise MediaError(422, "upload_quarantine_missing", "Quarantine object not found in storage.")

        await self.repo.update_upload_status(upload.id, "VALIDATING")

        # Fetch and validate image bytes
        try:
            raw_bytes = self.storage.get(upload.quarantine_key)
            validated = validate_image(raw_bytes, declared_content_type=upload.declared_content_type)
            if payload and payload.client_checksum_sha256:
                if payload.client_checksum_sha256.strip().lower() != validated.original_sha256.lower():
                    raise ImageValidationError("image_validation_failed", "Client SHA-256 checksum does not match uploaded content.")
        except ImageValidationError as exc:
            await self.repo.update_upload_status(upload.id, "REJECTED", failure_code=exc.code)
            emit_metric("MediaValidationRejected", 1.0, "Count", service="media", environment=self.settings.env)
            # Try to delete invalid quarantine object
            try:
                self.storage.delete(upload.quarantine_key)
            except Exception:
                pass
            raise

        # Store validated image at final private key
        bucket_name = getattr(self.storage, "_b", getattr(self.storage, "bucket", "fashx-media"))
        self.storage.put(
            upload.final_key,
            validated.normalized_bytes,
            content_type=validated.output_content_type,
        )

        # Persist UserMedia
        user_media = UserMedia(
            id=upload.image_id,
            user_id=user_id,
            purpose=upload.purpose,
            status="AVAILABLE",
            storage_bucket=bucket_name,
            storage_key=upload.final_key,
            content_type=validated.output_content_type,
            size_bytes=validated.normalized_size_bytes,
            width=validated.width,
            height=validated.height,
            sha256_original=validated.original_sha256,
            sha256_normalized=validated.normalized_sha256,
            created_at=now,
            updated_at=now,
        )
        await self.repo.create_user_media(user_media)

        # Mark upload AVAILABLE
        await self.repo.update_upload_status(upload.id, "AVAILABLE", completed_at=now)

        # Delete quarantine object safely
        try:
            self.storage.delete(upload.quarantine_key)
        except Exception:
            pass

        emit_metric("MediaValidationSucceeded", 1.0, "Count", service="media", environment=self.settings.env)

        return UploadStatusResponse(
            upload_id=upload.id,
            image_id=upload.image_id,
            status="AVAILABLE",
            message="Your photo has been validated and is available.",
        )

    async def get_metadata(
        self,
        user_id: UUID,
        image_id: UUID,
    ) -> MediaMetadataResponse:
        media = await self.repo.get_user_media(image_id, user_id)
        if media is None or media.status == "DELETED":
            raise MediaError(404, "media_not_found", "Media not found.")

        if media.status != "AVAILABLE":
            raise MediaError(409, "image_not_available", "Image is not yet available.")

        return MediaMetadataResponse(
            id=media.id,
            user_id=media.user_id,
            purpose=media.purpose,
            status=media.status,  # type: ignore[arg-type]
            content_type=media.content_type,
            size_bytes=media.size_bytes,
            width=media.width,
            height=media.height,
            sha256_normalized=media.sha256_normalized,
            created_at=media.created_at,
        )

    async def create_access_url(
        self,
        user_id: UUID,
        image_id: UUID,
    ) -> MediaAccessUrlResponse:
        media = await self.repo.get_user_media(image_id, user_id)
        if media is None or media.status in ("DELETED", "DELETION_PENDING"):
            raise MediaError(404, "media_not_found", "Media not found or has been deleted.")

        if media.status != "AVAILABLE":
            raise MediaError(409, "image_not_available", "Media is not available.")

        url = self.storage.signed_get_url(media.storage_key, ttl_s=60)
        return MediaAccessUrlResponse(
            image_id=media.id,
            url=url,
            expires_in_seconds=60,
        )

    async def delete_media(
        self,
        user_id: UUID,
        image_id: UUID,
    ) -> MediaDeletionResponse:
        media = await self.repo.get_user_media(image_id, user_id)
        if media is None or media.status == "DELETED":
            raise MediaError(404, "media_not_found", "Media not found.")

        # Mark deletion pending first to block access
        await self.repo.mark_media_deletion_pending(image_id, user_id)

        # Delete object from storage
        try:
            self.storage.delete(media.storage_key)
            await self.repo.mark_media_deleted(image_id)
        except Exception:
            # Leave in DELETION_PENDING for background retry
            pass

        emit_metric("MediaDeletionCompleted", 1.0, "Count", service="media", environment=self.settings.env)

        return MediaDeletionResponse(
            image_id=image_id,
            status="DELETION_PENDING",
        )
