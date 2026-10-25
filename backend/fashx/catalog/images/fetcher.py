"""Secure streaming image fetcher with SSRF defense and byte size limits."""

from __future__ import annotations

from urllib.parse import urlparse

import httpx

from fashx.catalog.acquisition.image_validator import SafeImageValidator
from fashx.catalog.images.validator import MAX_IMAGE_BYTES, ValidatedImage, validate_image_bytes


class SafeImageFetcher:
    """Safely retrieves and validates images over HTTPS preventing SSRF and resource exhaustion."""

    def __init__(self, timeout_seconds: float = 10.0) -> None:
        self.timeout_seconds = timeout_seconds

    async def fetch_and_validate(self, url: str) -> ValidatedImage:
        if not url or not url.strip():
            raise ValueError("Image URL is required")

        parsed = urlparse(url.strip())
        if parsed.scheme.lower() != "https":
            raise ValueError(f"Image scheme must be 'https', got '{parsed.scheme}'")

        if not parsed.netloc:
            raise ValueError("Image URL missing hostname")

        host = parsed.netloc.split(":")[0]
        safe, ssrf_err = SafeImageValidator.is_ssrf_safe_host(host)
        if not safe:
            raise ValueError(f"SSRF violation: {ssrf_err}")

        # Stream response to strictly enforce byte limit
        chunks: list[bytes] = []
        total_bytes = 0

        async with httpx.AsyncClient(
            timeout=self.timeout_seconds,
            follow_redirects=False,  # strict redirect policy to prevent open-redirect SSRF
        ) as client:
            async with client.stream("GET", url) as response:
                if response.status_code != 200:
                    raise ValueError(f"Image download failed with HTTP status {response.status_code}")

                content_type = (response.headers.get("content-type") or "").lower()
                if "html" in content_type or "text" in content_type:
                    raise ValueError(f"Prohibited non-image Content-Type: '{content_type}'")

                async for chunk in response.aiter_bytes():
                    total_bytes += len(chunk)
                    if total_bytes > MAX_IMAGE_BYTES:
                        raise ValueError(f"Image exceeded maximum size limit of {MAX_IMAGE_BYTES} bytes")
                    chunks.append(chunk)

        raw_bytes = b"".join(chunks)
        return validate_image_bytes(raw_bytes)
