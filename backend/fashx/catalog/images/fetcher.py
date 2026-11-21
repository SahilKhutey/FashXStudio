"""Secure streaming image fetcher with SSRF defense, DNS rebinding guards, and byte limits."""

from __future__ import annotations

import ipaddress
import socket
from collections.abc import Sequence
from urllib.parse import urlparse

import httpx

from fashx.catalog.acquisition.image_validator import SafeImageValidator
from fashx.catalog.images.validator import ValidatedImage, validate_image_bytes

DEFAULT_MAX_DOWNLOAD_BYTES = 10 * 1024 * 1024  # 10 MB
DEFAULT_CONNECT_TIMEOUT = 5.0
DEFAULT_READ_TIMEOUT = 15.0
DEFAULT_TOTAL_TIMEOUT = 30.0

PROHIBITED_CONTENT_TYPES = {
    "text/html",
    "text/plain",
    "application/xml",
    "text/xml",
    "image/svg+xml",
    "application/pdf",
    "application/x-msdownload",
    "application/zip",
}


class ImageFetchError(Exception):
    """Base exception for image retrieval failures."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int | None = None,
        retry_after: int | None = None,
    ) -> None:
        super().__init__(f"[{code}] {message}")
        self.code = code
        self.message = message
        self.status_code = status_code
        self.retry_after = retry_after


class SafeImageFetcher:
    """Safely retrieves images over HTTPS preventing SSRF, DNS rebinding, and resource exhaustion."""

    def __init__(
        self,
        allowed_hosts: set[str] | Sequence[str] | None = None,
        max_bytes: int = DEFAULT_MAX_DOWNLOAD_BYTES,
        connect_timeout: float = DEFAULT_CONNECT_TIMEOUT,
        read_timeout: float = DEFAULT_READ_TIMEOUT,
        total_timeout: float = DEFAULT_TOTAL_TIMEOUT,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.allowed_hosts = {h.lower() for h in allowed_hosts} if allowed_hosts else None
        self.max_bytes = max_bytes
        self.timeout = httpx.Timeout(
            timeout=total_timeout,
            connect=connect_timeout,
            read=read_timeout,
        )
        self._client = client

    def _sanitize_url_for_error(self, url: str) -> str:
        """Strip sensitive query parameters and tokens from error reporting."""
        try:
            parsed = urlparse(url)
            return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        except Exception:
            return "redacted-url"

    def validate_url(self, url: str) -> str:
        """Enforce HTTPS, valid hostname, SSRF defense, and host allowlist."""
        if not url or not url.strip():
            raise ImageFetchError("missing_url", "Image URL is required")

        parsed = urlparse(url.strip())
        scheme = parsed.scheme.lower()
        if scheme != "https":
            raise ImageFetchError(
                "insecure_scheme", f"Image scheme must be 'https', got '{scheme}'"
            )

        if not parsed.netloc:
            raise ImageFetchError("missing_hostname", "Image URL missing hostname")

        host = parsed.netloc.split(":")[0].lower()

        # Host allowlist check
        if self.allowed_hosts is not None and host not in self.allowed_hosts:
            raise ImageFetchError(
                "disallowed_host",
                f"Host '{host}' is not in the approved image host allowlist",
            )

        # Pre-resolve and SSRF check
        safe, ssrf_err = SafeImageValidator.is_ssrf_safe_host(host)
        if not safe:
            raise ImageFetchError("ssrf_violation", f"SSRF violation: {ssrf_err}")

        return host

    def _check_ip_address(self, host: str) -> None:
        """DNS resolution & rebinding guard: ensures resolved IPs are strictly public."""
        try:
            addr_info = socket.getaddrinfo(host, None)
            for _family, _, _, _, sockaddr in addr_info:
                ip_str = sockaddr[0]
                ip = ipaddress.ip_address(ip_str)
                if ip.is_unspecified:
                    continue
                if (
                    ip.is_private
                    or ip.is_loopback
                    or ip.is_link_local
                    or ip.is_multicast
                    or ip.is_reserved
                ):
                    raise ImageFetchError(
                        "ssrf_private_ip",
                        f"Host resolved to prohibited private or loopback IP '{ip_str}'",
                    )
        except socket.gaierror as exc:
            if host.endswith(".local") or host.endswith(".internal"):
                raise ImageFetchError("dns_failed", f"Prohibited internal domain: {exc}") from exc

    async def fetch_bytes(self, url: str) -> tuple[bytes, str]:
        """Fetch raw bytes with streaming length check, timeout, and redirect protection."""
        host = self.validate_url(url)
        self._check_ip_address(host)

        sanitized_url = self._sanitize_url_for_error(url)
        client = self._client or httpx.AsyncClient(timeout=self.timeout, follow_redirects=False)

        try:
            async with client.stream("GET", url) as response:
                status = response.status_code

                # Redirect handling
                if 300 <= status < 400:
                    location = response.headers.get("location")
                    if location:
                        try:
                            loc_parsed = urlparse(location)
                            loc_host = (loc_parsed.netloc or "").split(":")[0].lower()
                            if loc_host:
                                if (
                                    self.allowed_hosts is not None
                                    and loc_host not in self.allowed_hosts
                                ):
                                    raise ImageFetchError(
                                        "unapproved_redirect_domain",
                                        f"Redirect target host '{loc_host}' is not permitted",
                                        status_code=status,
                                    )
                                safe, ssrf_err = SafeImageValidator.is_ssrf_safe_host(loc_host)
                                if not safe:
                                    raise ImageFetchError(
                                        "redirect_to_private_ip",
                                        f"Redirect target SSRF violation: {ssrf_err}",
                                        status_code=status,
                                    )
                        except ImageFetchError:
                            raise
                        except Exception:
                            pass
                    raise ImageFetchError(
                        "redirect_prohibited",
                        f"HTTP redirect (status {status}) prohibited by policy",
                        status_code=status,
                    )

                if status == 404 or status == 410:
                    raise ImageFetchError(
                        "not_found", f"Image not found at {sanitized_url}", status_code=status
                    )

                if status == 429:
                    retry_after_hdr = response.headers.get("retry-after")
                    retry_after = (
                        int(retry_after_hdr)
                        if retry_after_hdr and retry_after_hdr.isdigit()
                        else 30
                    )
                    raise ImageFetchError(
                        "rate_limited",
                        f"Image source rate limited with Retry-After: {retry_after}s",
                        status_code=status,
                        retry_after=retry_after,
                    )

                if 500 <= status < 600:
                    raise ImageFetchError(
                        "server_error",
                        f"Image host returned server error status {status}",
                        status_code=status,
                    )

                if status != 200:
                    raise ImageFetchError(
                        "http_error",
                        f"Image fetch returned status {status}",
                        status_code=status,
                    )

                # Content-Type pre-validation
                content_type = (
                    (response.headers.get("content-type") or "").lower().split(";")[0].strip()
                )
                if (
                    content_type in PROHIBITED_CONTENT_TYPES
                    or "html" in content_type
                    or "text" in content_type
                ):
                    raise ImageFetchError(
                        "prohibited_content_type",
                        f"Prohibited Content-Type: '{content_type}'",
                        status_code=status,
                    )

                chunks: list[bytes] = []
                total_bytes = 0

                async for chunk in response.aiter_bytes():
                    total_bytes += len(chunk)
                    if total_bytes > self.max_bytes:
                        raise ImageFetchError(
                            "oversized_image",
                            f"Image exceeded maximum size limit of {self.max_bytes} bytes",
                        )
                    chunks.append(chunk)

                if not chunks:
                    raise ImageFetchError("empty_image", "Received empty response body")

                raw_bytes = b"".join(chunks)
                return raw_bytes, content_type or "image/jpeg"

        except httpx.TimeoutException as exc:
            raise ImageFetchError("timeout", f"Image fetch timed out: {exc}") from exc
        except httpx.NetworkError as exc:
            raise ImageFetchError(
                "network_error", f"Network error during image fetch: {exc}"
            ) from exc
        finally:
            if self._client is None:
                await client.aclose()

    async def fetch_and_validate(self, url: str) -> ValidatedImage:
        """Fetch image bytes and validate with Pillow (backwards compatibility)."""
        raw_bytes, _ = await self.fetch_bytes(url)
        return validate_image_bytes(raw_bytes)
