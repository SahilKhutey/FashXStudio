"""Safe HTTP fetcher with SSRF prevention, rate limiting, and size boundaries."""

import ipaddress
import socket
import threading
import time
from urllib.parse import urlparse

import httpx


class Reject(Exception):
    """Exception raised when a feed URL or response violates security or operational policies."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def assert_public_https(url: str) -> None:
    """Validate that the given URL uses HTTPS and resolves exclusively to a public IP address.

    Blocks localhost, RFC 1918 private subnets, cloud link-local metadata (169.254.169.254),
    loopback, multicast, and reserved addresses.
    """
    u = urlparse(url)
    if u.scheme != "https" or not u.hostname:
        raise Reject("non_https_url")
    try:
        infos = socket.getaddrinfo(u.hostname, 443, proto=socket.IPPROTO_TCP)
    except socket.gaierror as e:
        raise Reject("dns_failure") from e

    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_multicast
        ):
            raise Reject("private_address")


class RateLimiter:
    """Thread-safe token/interval rate limiter."""

    def __init__(self, rps: float):
        self.interval = 1.0 / max(rps, 0.01)
        self._next = 0.0
        self._lock = threading.Lock()

    def wait(self) -> None:
        with self._lock:
            now = time.monotonic()
            t = max(self._next, now)
            self._next = t + self.interval
        sleep_dur = max(0.0, t - now)
        if sleep_dur > 0:
            time.sleep(sleep_dur)


def fetch_bytes(
    client: httpx.Client,
    url: str,
    *,
    limiter: RateLimiter,
    max_bytes: int,
    max_redirects: int = 3,
) -> bytes:
    """Safely stream and download bytes from a URL with redirect validation, size capping, and rate limits."""
    curr_url = url
    for _ in range(max_redirects + 1):
        assert_public_https(curr_url)
        limiter.wait()
        with client.stream("GET", curr_url, follow_redirects=False) as r:
            if r.is_redirect:
                loc = str(r.headers.get("location") or "")
                if not loc:
                    raise Reject("invalid_redirect")
                # Handle relative redirects
                if not loc.startswith("http"):
                    u = urlparse(curr_url)
                    loc = f"{u.scheme}://{u.netloc}/{loc.lstrip('/')}"
                curr_url = loc
                continue
            if r.status_code != 200:
                raise Reject(f"http_{r.status_code}")
            buf = bytearray()
            for chunk in r.iter_bytes(64 * 1024):
                buf += chunk
                if len(buf) > max_bytes:
                    raise Reject("too_large")
            return bytes(buf)
    raise Reject("too_many_redirects")
