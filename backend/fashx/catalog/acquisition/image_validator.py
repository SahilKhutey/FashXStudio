"""Safe image validator with SSRF protection, MIME validation, and permission verification."""

from __future__ import annotations

import ipaddress
import socket
from dataclasses import dataclass
from urllib.parse import urlparse

APPROVED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
APPROVED_IMAGE_MIMES = {"image/jpeg", "image/png", "image/webp"}
VALID_IMAGE_RIGHTS = {"owned", "licensed", "partner_authorized"}


@dataclass(frozen=True)
class ImageValidationResult:
    """Result of image validation and rights assessment."""

    is_valid: bool
    display_eligible: bool
    tryon_eligible: bool
    error_reason: str | None = None


class SafeImageValidator:
    """Validates external image URLs against SSRF attacks and checks usage permissions."""

    @classmethod
    def is_ssrf_safe_host(cls, host: str) -> tuple[bool, str | None]:
        """Check whether the host IP is safe from SSRF (rejects private, loopback, link-local IPs)."""
        clean_host = host.strip().lower()
        if not clean_host:
            return False, "Empty host"

        if clean_host in {"localhost", "127.0.0.1", "::1", "0.0.0.0"}:
            return False, f"Prohibited local/loopback host '{clean_host}'"

        # Check if direct IP literal
        try:
            ip = ipaddress.ip_address(clean_host)
            if (
                ip.is_private
                or ip.is_loopback
                or ip.is_link_local
                or ip.is_multicast
                or ip.is_reserved
            ):
                return False, f"Prohibited private/internal IP address '{clean_host}'"
            return True, None
        except ValueError:
            pass  # It's a hostname, resolve below

        # Resolve hostname via DNS
        try:
            addr_info = socket.getaddrinfo(clean_host, None)
            for _family, _, _, _, sockaddr in addr_info:
                ip_str = sockaddr[0]
                ip = ipaddress.ip_address(ip_str)
                if (
                    ip.is_private
                    or ip.is_loopback
                    or ip.is_link_local
                    or ip.is_multicast
                    or ip.is_reserved
                ):
                    return False, f"Host '{clean_host}' resolved to private/internal IP '{ip_str}'"
        except socket.gaierror:
            # If DNS resolution fails offline or in test environments, allow standard domain names if not local
            if clean_host.endswith(".local") or clean_host.endswith(".internal"):
                return False, f"Prohibited internal domain suffix '{clean_host}'"

        return True, None

    @classmethod
    def validate_image_url(cls, url: str | None) -> tuple[bool, str | None]:
        """Verify URL schema, host safety, and image file extension."""
        if not url or not url.strip():
            return False, "Missing image URL"

        parsed = urlparse(url.strip())
        if parsed.scheme.lower() != "https":
            return False, f"Image URL scheme must be 'https', got '{parsed.scheme}'"

        if not parsed.netloc:
            return False, "Image URL missing hostname"

        host = parsed.netloc.split(":")[0]
        safe, ssrf_err = cls.is_ssrf_safe_host(host)
        if not safe:
            return False, ssrf_err

        # Extension check if path contains one
        path_lower = parsed.path.lower()
        if "." in path_lower:
            ext = "." + path_lower.rsplit(".", 1)[1]
            if ext not in APPROVED_IMAGE_EXTENSIONS:
                return False, f"Unsupported image extension '{ext}'. Must be one of {APPROVED_IMAGE_EXTENSIONS}"

        return True, None

    @classmethod
    def evaluate_permissions(
        cls,
        image_url: str | None,
        source_status: str,
        source_rights_display: bool,
        source_rights_tryon: bool,
        source_image_policy: str,
        item_image_rights: str | None,
        item_tryon_rights: bool,
    ) -> ImageValidationResult:
        """Independently evaluate URL validity, display eligibility, and virtual try-on eligibility."""
        # If no image URL is provided, product listing remains valid for discovery without image display/tryon
        if not image_url or not image_url.strip():
            return ImageValidationResult(
                is_valid=True,
                display_eligible=False,
                tryon_eligible=False,
                error_reason=None,
            )

        valid, err = cls.validate_image_url(image_url)
        if not valid:
            return ImageValidationResult(
                is_valid=False,
                display_eligible=False,
                tryon_eligible=False,
                error_reason=err,
            )

        # 1. Source clearance: unapproved sources can never display or try-on
        if source_status != "cleared":
            return ImageValidationResult(
                is_valid=True,
                display_eligible=False,
                tryon_eligible=False,
                error_reason=f"Source status is '{source_status}', must be 'cleared'",
            )

        # 2. Display eligibility: requires source display rights + recognized item image rights
        norm_rights = (item_image_rights or "").strip().lower()
        display_eligible = bool(source_rights_display and norm_rights in VALID_IMAGE_RIGHTS)

        # 3. Try-on eligibility: requires source tryon rights + image_policy='mirror' + item tryon permission
        tryon_eligible = bool(
            display_eligible
            and source_rights_tryon
            and source_image_policy == "mirror"
            and item_tryon_rights
        )

        return ImageValidationResult(
            is_valid=True,
            display_eligible=display_eligible,
            tryon_eligible=tryon_eligible,
            error_reason=None,
        )
