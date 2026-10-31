"""Secure acquisition and normalization of authorized garment images."""

from __future__ import annotations

import hashlib
import inspect
from collections.abc import Sequence
from dataclasses import dataclass
from io import BytesIO
from typing import Any
from urllib.parse import urlparse

import httpx
from PIL import Image, ImageOps

from fashx.catalog.acquisition.image_validator import SafeImageValidator
from fashx.catalog.images.validator import validate_image_bytes

MAX_DOWNLOAD_BYTES = 8 * 1024 * 1024  # 8 MB
MAX_OUTPUT_DIMENSION = 1024


class ImagePreparationError(Exception):
    """Image could not safely be acquired or prepared."""


@dataclass(frozen=True)
class ImageRights:
    source_status: str
    source_rights_display: bool
    source_rights_tryon: bool
    source_image_policy: str
    item_image_rights: str
    item_tryon_rights: bool


@dataclass(frozen=True)
class PreparedGarmentImage:
    storage_key: str
    content_hash: str
    width: int
    height: int
    content_type: str = "image/jpeg"
    tryon_eligible: bool = True
    byte_size: int = 0


class GarmentImagePreparer:
    """Service to acquire, validate, normalize, and store authorized garment images."""

    def __init__(
        self,
        storage: Any,
        allowed_hosts: set[str] | Sequence[str] | None = None,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self.storage = storage
        self.allowed_hosts = set(allowed_hosts) if allowed_hosts else None
        self._client = http_client

    def _check_rights(
        self,
        rights: ImageRights,
        image_url: str,
    ) -> bool:
        """Validate source and item-level permissions; returns try-on eligibility."""
        result = SafeImageValidator.evaluate_permissions(
            image_url=image_url,
            source_status=rights.source_status,
            source_rights_display=rights.source_rights_display,
            source_rights_tryon=rights.source_rights_tryon,
            source_image_policy=rights.source_image_policy,
            item_image_rights=rights.item_image_rights,
            item_tryon_rights=rights.item_tryon_rights,
        )

        if not result.display_eligible:
            msg = result.error_reason or "Source or item rights do not permit display/storage"
            raise ImagePreparationError(msg)

        return result.tryon_eligible

    async def _fetch_image_bytes(self, image_url: str) -> tuple[bytes, str]:
        """Fetch image with strict HTTPS, allowlisting, SSRF guards, and redirect prohibition."""
        parsed = urlparse(image_url)
        if parsed.scheme.lower() != "https":
            raise ImagePreparationError(f"Image URL scheme must be 'https', got '{parsed.scheme}'")

        if not parsed.netloc:
            raise ImagePreparationError("Image URL missing hostname")

        host = parsed.netloc.split(":")[0].lower()
        if self.allowed_hosts is not None and host not in self.allowed_hosts:
            raise ImagePreparationError(f"Host '{host}' is not in approved image host allowlist")

        safe, ssrf_err = SafeImageValidator.is_ssrf_safe_host(host)
        if not safe:
            raise ImagePreparationError(f"SSRF check failed for host '{host}': {ssrf_err}")

        client = self._client or httpx.AsyncClient(follow_redirects=False, timeout=15.0)
        try:
            resp = await client.get(image_url)
            if 300 <= resp.status_code < 400:
                raise ImagePreparationError(f"HTTP redirects prohibited (got status {resp.status_code})")
            if resp.status_code != 200:
                raise ImagePreparationError(f"HTTP fetch failed with status {resp.status_code}")

            content_type = resp.headers.get("content-type", "").lower()
            if not content_type.startswith("image/"):
                raise ImagePreparationError(f"Unsupported content-type: '{content_type}'")

            data = resp.content
            if len(data) > MAX_DOWNLOAD_BYTES:
                raise ImagePreparationError(
                    f"Image exceeds max download limit of {MAX_DOWNLOAD_BYTES} bytes (got {len(data)})"
                )
            if not data:
                raise ImagePreparationError("Empty image received")

            return data, content_type
        except httpx.HTTPError as exc:
            raise ImagePreparationError(f"Network error while fetching image: {exc}") from exc
        finally:
            if self._client is None:
                await client.aclose()

    def _normalize_image(self, raw_bytes: bytes) -> tuple[bytes, int, int]:
        """Validate bytes and convert to standardized RGB JPEG with max dimension of 1024px."""
        try:
            validate_image_bytes(raw_bytes)
        except ValueError as exc:
            raise ImagePreparationError(f"Image byte validation failed: {exc}") from exc

        try:
            with Image.open(BytesIO(raw_bytes)) as img:
                img = ImageOps.exif_transpose(img)

                if img.mode != "RGB":
                    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
                        bg = Image.new("RGB", img.size, (255, 255, 255))
                        rgba_img = img.convert("RGBA")
                        bg.paste(rgba_img, mask=rgba_img.split()[3])
                        img = bg
                    else:
                        img = img.convert("RGB")

                orig_w, orig_h = img.size
                if max(orig_w, orig_h) > MAX_OUTPUT_DIMENSION:
                    scale = MAX_OUTPUT_DIMENSION / max(orig_w, orig_h)
                    new_w = max(1, int(orig_w * scale))
                    new_h = max(1, int(orig_h * scale))
                    img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

                final_w, final_h = img.size
                buf = BytesIO()
                img.save(buf, format="JPEG", quality=90, optimize=True)
                normalized_bytes = buf.getvalue()
                return normalized_bytes, final_w, final_h
        except Exception as exc:
            raise ImagePreparationError(f"Image normalization failed: {exc}") from exc

    async def prepare(
        self,
        source_slug: str,
        source_product_id: str,
        image_url: str,
        rights: ImageRights,
        raw_image_bytes: bytes | None = None,
    ) -> PreparedGarmentImage:
        """Acquire, validate, normalize, hash, and persist a garment image asset."""
        tryon_eligible = self._check_rights(rights, image_url)

        if raw_image_bytes is not None:
            raw_bytes = raw_image_bytes
        else:
            raw_bytes, _ = await self._fetch_image_bytes(image_url)

        jpeg_bytes, width, height = self._normalize_image(raw_bytes)
        content_hash = hashlib.sha256(jpeg_bytes).hexdigest()
        storage_key = f"garments/{source_slug}/{source_product_id}/{content_hash}.jpg"

        try:
            res = self.storage.put(storage_key, jpeg_bytes, content_type="image/jpeg")
            if inspect.isawaitable(res):
                await res
        except Exception as exc:
            raise ImagePreparationError(f"Failed to store prepared garment image: {exc}") from exc

        return PreparedGarmentImage(
            storage_key=storage_key,
            content_hash=content_hash,
            width=width,
            height=height,
            content_type="image/jpeg",
            tryon_eligible=tryon_eligible,
            byte_size=len(jpeg_bytes),
        )
