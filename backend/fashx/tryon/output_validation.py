"""Provider Output Image Validation and SSRF Safeguards (Phase 07.4)."""

from __future__ import annotations

import ipaddress
from dataclasses import dataclass
from hashlib import sha256
from io import BytesIO
from urllib.parse import urlparse

from PIL import Image

MAX_OUTPUT_BYTES = 15 * 1024 * 1024  # 15 MB
MAX_OUTPUT_PIXELS = 20_000_000       # 20 MP decompression bomb limit
MAX_OUTPUT_SIDE = 4096
MIN_OUTPUT_SIDE = 256

# Configure Pillow to fail fast on decompression bombs
Image.MAX_IMAGE_PIXELS = MAX_OUTPUT_PIXELS


@dataclass(frozen=True)
class ValidatedOutput:
    data: bytes
    sha256: str
    width: int
    height: int
    content_type: str
    size_bytes: int


def validate_provider_output(raw: bytes) -> ValidatedOutput:
    """Validates raw image bytes retrieved from a provider against security and fidelity policies.

    Enforces:
    - Bounded file size (<= 15 MB)
    - Full container decode with Pillow (rejects headers-only, corrupted bytes, polyglots)
    - Supported formats: JPEG, PNG, WEBP
    - Min resolution >= 256x256; Max resolution <= 4096x4096; Max pixels <= 20 MP
    - Normalization: Strips EXIF metadata, converts to RGB mode, re-encodes to clean baseline JPEG raster
    - Computes cryptographic SHA-256
    """
    if not raw:
        raise ValueError("Provider output is empty")
    if len(raw) > MAX_OUTPUT_BYTES:
        raise ValueError(
            f"Provider output size ({len(raw)} bytes) exceeds maximum limit ({MAX_OUTPUT_BYTES} bytes)"
        )

    try:
        with Image.open(BytesIO(raw)) as img:
            fmt = img.format
            if fmt not in {"JPEG", "PNG", "WEBP"}:
                raise ValueError(f"Unsupported output format '{fmt}'; allowed: JPEG, PNG, WEBP")

            width, height = img.size
            if width < MIN_OUTPUT_SIDE or height < MIN_OUTPUT_SIDE:
                raise ValueError(
                    f"Output resolution ({width}x{height}) is below minimum allowed ({MIN_OUTPUT_SIDE}x{MIN_OUTPUT_SIDE})"
                )
            if width > MAX_OUTPUT_SIDE or height > MAX_OUTPUT_SIDE:
                raise ValueError(
                    f"Output resolution ({width}x{height}) exceeds maximum allowed ({MAX_OUTPUT_SIDE}x{MAX_OUTPUT_SIDE})"
                )
            if width * height > MAX_OUTPUT_PIXELS:
                raise ValueError(
                    f"Output pixel count ({width * height}) exceeds decompression limit ({MAX_OUTPUT_PIXELS})"
                )

            # Ensure image is readable and not truncated
            img.load()

            # Normalize to clean RGB raster
            rgb = img.convert("RGB")

            # Re-encode to clean baseline JPEG
            out_buf = BytesIO()
            rgb.save(out_buf, format="JPEG", quality=95, optimize=True)
            normalized_bytes = out_buf.getvalue()

    except Exception as exc:
        if isinstance(exc, ValueError):
            raise
        raise ValueError(f"Corrupted or invalid image data from provider: {exc}") from exc

    digest = sha256(normalized_bytes).hexdigest()
    return ValidatedOutput(
        data=normalized_bytes,
        sha256=digest,
        width=width,
        height=height,
        content_type="image/jpeg",
        size_bytes=len(normalized_bytes),
    )


def is_safe_provider_output_url(
    url: str,
    allowed_domains: tuple[str, ...] = ("api.fashn.ai", "cdn.fashn.ai", "fashn.ai", "amazonaws.com"),
) -> bool:
    """Verifies that a provider output URL is safe to retrieve (SSRF mitigation).

    Rules:
    - Must use HTTPS scheme.
    - Hostname must resolve to an allowed domain suffix.
    - Rejects localhost, loopback, private RFC-1918, link-local, and broadcast IPs.
    """
    if not url:
        return False

    try:
        parsed = urlparse(url)
        if parsed.scheme.lower() != "https":
            return False

        host = parsed.hostname
        if not host:
            return False

        host_lower = host.lower()

        # Check for IP address literals
        try:
            ip = ipaddress.ip_address(host_lower)
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_unspecified:
                return False
            # Generally disallow raw IP destinations for provider downloads
            return False
        except ValueError:
            pass  # host is a domain name

        # Disallow localhost keywords
        if host_lower in ("localhost", "ip6-localhost", "ip6-loopback"):
            return False

        # Match against allowed domain suffixes
        return any(
            host_lower == domain or host_lower.endswith(f".{domain}")
            for domain in allowed_domains
        )
    except Exception:
        return False
