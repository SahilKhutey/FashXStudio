"""Shared secure HTTP transport for catalog source acquisition with SSRF and size safeguards."""

from __future__ import annotations

import ipaddress
import logging
import socket
from collections.abc import Sequence
from typing import Any
from urllib.parse import urlparse

import httpx

logger = logging.getLogger(__name__)


class HttpTransportError(Exception):
    """Base exception for HTTP transport failures."""


class SecurityViolationError(HttpTransportError):
    """Raised when URL or DNS fails SSRF and network security policies."""


class ResponseSizeExceededError(HttpTransportError):
    """Raised when response body exceeds the maximum permitted byte threshold."""


# Private, loopback, link-local, and reserved IP subnets prohibited for outbound requests
DISALLOWED_NETWORKS = (
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("100.64.0.0/10"),
    ipaddress.ip_network("192.0.0.0/24"),
    ipaddress.ip_network("192.0.2.0/24"),
    ipaddress.ip_network("198.51.100.0/24"),
    ipaddress.ip_network("203.0.113.0/24"),
    ipaddress.ip_network("224.0.0.0/4"),
    ipaddress.ip_network("240.0.0.0/4"),
    ipaddress.ip_network("255.255.255.255/32"),
    # IPv6
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
    ipaddress.ip_network("ff00::/8"),
)


def validate_source_url(
    url: str,
    allowed_hostnames: Sequence[str] = (),
    require_https: bool = True,
    resolve_dns: bool = True,
) -> str:
    """Validate that target URL complies with scheme, allowlist, and SSRF restrictions."""
    parsed = urlparse(url)
    scheme = parsed.scheme.lower()
    if require_https and scheme != "https":
        raise SecurityViolationError(
            f"Insecure scheme '{scheme}'. Catalog feeds strictly require HTTPS."
        )
    if not require_https and scheme not in ("http", "https"):
        raise SecurityViolationError(f"Unsupported scheme '{scheme}'. Must be HTTP or HTTPS.")

    host = parsed.hostname
    if not host:
        raise SecurityViolationError(f"Target URL '{url}' has no valid hostname.")

    # Host allowlist validation
    if allowed_hostnames:
        allowed = {h.lower() for h in allowed_hostnames}
        if host.lower() not in allowed:
            raise SecurityViolationError(
                f"Hostname '{host}' is not in the approved source host allowlist: {sorted(allowed)}"
            )

    # DNS and SSRF IP validation
    if resolve_dns:
        try:
            # Check if host is directly a literal IP
            try:
                ip = ipaddress.ip_address(host)
                resolved_ips = [ip]
            except ValueError:
                # Host is a domain name -> resolve via DNS
                addr_info = socket.getaddrinfo(host, None)
                resolved_ips = [ipaddress.ip_address(info[4][0]) for info in addr_info]

            for ip_addr in resolved_ips:
                for network in DISALLOWED_NETWORKS:
                    if ip_addr in network:
                        raise SecurityViolationError(
                            f"SSRF violation: Target hostname '{host}' resolves to prohibited IP '{ip_addr}' "
                            f"in disallowed network '{network}'."
                        )
        except socket.gaierror as exc:
            raise SecurityViolationError(
                f"DNS resolution failed for hostname '{host}': {exc}"
            ) from exc

    return url


class SourceHttpClient:
    """Secure HTTP client for external catalog feeds and partner APIs."""

    def __init__(
        self,
        timeout_seconds: float = 15.0,
        max_response_bytes: int = 10 * 1024 * 1024,  # 10 MB default limit
        allowed_hostnames: Sequence[str] = (),
        allow_redirects: bool = False,
        require_https: bool = True,
        resolve_dns: bool = True,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.timeout = httpx.Timeout(timeout_seconds)
        self.max_response_bytes = max_response_bytes
        self.allowed_hostnames = allowed_hostnames
        self.allow_redirects = allow_redirects
        self.require_https = require_https
        self.resolve_dns = resolve_dns

        self._client = httpx.AsyncClient(
            timeout=self.timeout,
            follow_redirects=False,  # Enforce manual redirect handling to validate targets
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
            headers={"User-Agent": "FashXStudio-Catalog-Sync/1.0"},
            transport=transport,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def get_response(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        etag: str | None = None,
        last_modified: str | None = None,
    ) -> httpx.Response:
        """Execute a secure GET request with SSRF validation, size bounds, and conditional headers."""
        validate_source_url(
            url,
            allowed_hostnames=self.allowed_hostnames,
            require_https=self.require_https,
            resolve_dns=self.resolve_dns,
        )

        req_headers = dict(headers or {})
        if etag:
            req_headers["If-None-Match"] = etag
        if last_modified:
            req_headers["If-Modified-Since"] = last_modified

        resp = await self._client.get(url, headers=req_headers)

        # 304 Not Modified check (evaluated before redirect check since 304 is in 3xx range)
        if resp.status_code == 304:
            return resp

        # Handle Redirects safely if explicitly enabled
        if resp.is_redirect:
            if not self.allow_redirects:
                raise SecurityViolationError(
                    f"Outbound redirect to '{resp.headers.get('location')}' blocked by security policy."
                )
            redirect_target = resp.headers.get("location")
            if not redirect_target:
                raise SecurityViolationError("Redirect response missing Location header.")

            # Validate target redirect
            validate_source_url(
                redirect_target,
                allowed_hostnames=self.allowed_hostnames,
                require_https=self.require_https,
                resolve_dns=self.resolve_dns,
            )
            resp = await self._client.get(redirect_target, headers=req_headers)

        # Validate response content size bounding
        content_length_hdr = resp.headers.get("content-length")
        if content_length_hdr and content_length_hdr.isdigit():
            if int(content_length_hdr) > self.max_response_bytes:
                raise ResponseSizeExceededError(
                    f"Declared content length {content_length_hdr} bytes exceeds limit of {self.max_response_bytes} bytes."
                )

        body = resp.content
        if len(body) > self.max_response_bytes:
            raise ResponseSizeExceededError(
                f"Response body {len(body)} bytes exceeds limit of {self.max_response_bytes} bytes."
            )

        return resp

    async def get_json(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        etag: str | None = None,
        last_modified: str | None = None,
    ) -> tuple[dict[str, Any] | None, httpx.Response]:
        """Fetch JSON data. Returns (json_dict, response). json_dict is None on 304."""
        resp = await self.get_response(url, headers=headers, etag=etag, last_modified=last_modified)
        if resp.status_code == 304:
            return None, resp

        resp.raise_for_status()
        try:
            return resp.json(), resp
        except Exception as exc:
            raise HttpTransportError(f"Failed to parse JSON response from '{url}': {exc}") from exc
