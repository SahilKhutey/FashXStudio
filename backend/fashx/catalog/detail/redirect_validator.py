from __future__ import annotations

from urllib.parse import urlparse


def validate_merchant_url(
    candidate_url: str,
    verified_hosts: set[str],
) -> str:
    """Validate that an outbound merchant URL uses HTTPS and matches a verified host."""
    if not candidate_url or not candidate_url.strip():
        raise ValueError("Merchant URL is empty")

    parsed = urlparse(candidate_url.strip())
    if parsed.scheme.lower() != "https":
        raise ValueError("Merchant URL must use HTTPS")
    if not parsed.hostname:
        raise ValueError("Merchant URL has no hostname")
    if parsed.username or parsed.password:
        raise ValueError("Credentials in merchant URL are not allowed")

    host = parsed.hostname.lower().rstrip(".")
    allowed = {item.lower().rstrip(".") for item in verified_hosts if item.strip()}
    if not allowed:
        raise ValueError("No verified merchant hosts configured")

    is_allowed = any(
        host == domain or host.endswith(f".{domain}") for domain in allowed
    )
    if not is_allowed:
        raise ValueError("Merchant domain is not authorized")

    return candidate_url.strip()
