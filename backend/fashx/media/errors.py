from __future__ import annotations

from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse


class MediaError(Exception):
    """Base exception for media upload and storage domain."""

    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: Any = None,
    ) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details
        super().__init__(message)


class ImageValidationError(MediaError):
    """Validation exception for image format, size, dimensions, or corruption."""

    DEFAULT_MESSAGES = {
        "unsupported_image_format": "This image format is not supported. Allowed formats: JPEG, PNG, WebP.",
        "image_size_exceeded": "The uploaded file exceeds the 10 MB maximum size limit.",
        "image_size_below_minimum": "The uploaded file is below the 10 KB minimum size limit.",
        "image_dimensions_exceeded": "This image exceeds the maximum supported dimensions (4096x4096px or 20MP).",
        "image_decode_failed": "The image file is corrupted or could not be decoded.",
        "image_content_type_mismatch": "The declared content type does not match the actual image format.",
        "animated_image_unsupported": "Multi-frame or animated images are not supported.",
        "image_validation_failed": "Content failed security and validation checks.",
    }

    STATUS_CODES = {
        "unsupported_image_format": 415,
        "image_size_exceeded": 413,
        "image_size_below_minimum": 422,
        "image_dimensions_exceeded": 422,
        "image_decode_failed": 422,
        "image_content_type_mismatch": 422,
        "animated_image_unsupported": 422,
        "image_validation_failed": 422,
    }

    def __init__(self, code: str, message: str | None = None) -> None:
        status_code = self.STATUS_CODES.get(code, 422)
        msg = message or self.DEFAULT_MESSAGES.get(code, code)
        super().__init__(status_code=status_code, code=code, message=msg)


async def media_error_handler(request: Request, exc: MediaError) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "") or request.headers.get("x-request-id", "")
    content = {
        "error": {
            "code": exc.code,
            "message": exc.message,
            "details": exc.details,
            "field_errors": [],
        },
        "request_id": request_id,
        "title": exc.code,
        "status": exc.status_code,
        "detail": exc.message,
    }
    return JSONResponse(status_code=exc.status_code, content=content)
