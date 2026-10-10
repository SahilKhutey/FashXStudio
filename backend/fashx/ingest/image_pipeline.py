"""Image ingestion and processing pipeline with rights-aware mirroring."""

import hashlib
import io
from dataclasses import dataclass

import httpx
from PIL import Image, ImageOps

from fashx.application.ports.storage import ObjectStorage
from fashx.catalog.deduplication.hasher import ImageHasher

from .safe_http import RateLimiter, Reject, fetch_bytes


@dataclass
class ImageRef:
    """Reference to an ingested product image."""

    url: str
    key: str | None = None
    sha256: str | None = None
    dhash: str | None = None


def process_image(
    source_slug: str,
    url: str,
    *,
    client: httpx.Client,
    limiter: RateLimiter,
    storage: ObjectStorage | None,
    policy: str,
) -> ImageRef:
    """Process an image according to the source's image policy.

    If policy is 'hotlink', returns the original URL with no mirrored storage key.
    If policy is 'mirror', safely downloads, sanitizes, converts to RGB JPEG,
    validates dimensions (minimum 400px), stores in object storage, and computes hashes.
    """
    if policy == "hotlink" or storage is None:
        return ImageRef(url=url, key=None, sha256=None, dhash=None)

    raw = fetch_bytes(client, url, limiter=limiter, max_bytes=10 * 1024 * 1024)
    try:
        with Image.open(io.BytesIO(raw)) as im:
            im.load()
            rgb = ImageOps.exif_transpose(im).convert("RGB")
    except Exception as e:
        raise Reject("image_decode_failed") from e

    if min(rgb.size) < 400:
        raise Reject("image_too_small")

    out = io.BytesIO()
    rgb.save(out, "JPEG", quality=92)
    data = out.getvalue()
    sha = hashlib.sha256(data).hexdigest()
    key = f"catalog/{source_slug}/{sha}.jpg"

    if not storage.exists(key):
        storage.put(key, data, "image/jpeg")

    dhash = ImageHasher.compute_dhash(data)
    return ImageRef(url=url, key=key, sha256=sha, dhash=dhash)
