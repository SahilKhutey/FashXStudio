from __future__ import annotations

import ipaddress
import socket
import time
from collections.abc import Callable
from datetime import UTC, datetime
from urllib.parse import urlparse

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.catalog import MerchantOffer
from database.models.catalog_evaluation import CatalogLinkHealthCheck
from fashx.catalog.metrics.contracts import (
    CatalogMetricResult,
    LinkCheckResult,
    LinkHealthClassification,
)
from fashx.catalog.metrics.sampling import reproducible_sample


def is_restricted_ip(ip_str: str) -> bool:
    """Checks whether an IP address belongs to private, loopback, link-local or reserved ranges."""
    try:
        ip = ipaddress.ip_address(ip_str)
        return (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
        )
    except ValueError:
        return True


def validate_url_ssrf_safety(url: str) -> tuple[bool, str | None]:
    """Validates URL scheme and resolves hostname to ensure no private/internal destinations are reached."""
    try:
        parsed = urlparse(url)
        if parsed.scheme.lower() not in ("http", "https"):
            return False, f"Disallowed URL scheme: '{parsed.scheme}'"

        hostname = parsed.hostname
        if not hostname:
            return False, "Missing hostname in URL"

        # Block localhost directly
        if hostname.lower() in ("localhost", "127.0.0.1", "::1"):
            return False, "Direct loopback address blocked"

        # Resolve IP addresses for hostname
        addr_info = socket.getaddrinfo(
            hostname, None, family=socket.AF_UNSPEC, type=socket.SOCK_STREAM
        )
        for _, _, _, _, sockaddr in addr_info:
            ip_str = sockaddr[0]
            if is_restricted_ip(ip_str):
                return False, f"Destination resolved to restricted IP: {ip_str}"

        return True, None
    except Exception as e:
        return False, f"DNS resolution or SSRF safety check failed: {e}"


async def safe_check_product_link(
    url: str,
    client: httpx.AsyncClient | None = None,
    timeout: float = 5.0,
    max_retries: int = 1,
) -> LinkCheckResult:
    """Safely checks a merchant product destination link with SSRF protection, timeout, and classification."""
    start_time = time.perf_counter()

    # 1. SSRF Safety Check
    is_safe, ssrf_err = validate_url_ssrf_safety(url)
    if not is_safe:
        elapsed_ms = int((time.perf_counter() - start_time) * 1000)
        return LinkCheckResult(
            url=url,
            status=LinkHealthClassification.INVALID_REDIRECT,
            response_time_ms=elapsed_ms,
            error_message=ssrf_err or "SSRF check failed",
        )

    # 2. HTTP Request with bounded retries
    headers = {"User-Agent": "FashXStudio-LinkVerifier/1.0 (+https://fashx.com/bot-info)"}
    should_close_client = False
    if client is None:
        client = httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=False,
            verify=True,
        )
        should_close_client = True

    try:
        attempt = 0
        last_exception = None
        while attempt <= max_retries:
            attempt += 1
            try:
                # Try HEAD first
                resp = await client.head(url, headers=headers)
                # If 405 Method Not Allowed, fallback to GET with stream
                if resp.status_code == 405:
                    resp = await client.get(url, headers=headers)

                elapsed_ms = int((time.perf_counter() - start_time) * 1000)
                status_code = resp.status_code

                # Check redirect safety if 3xx
                if 300 <= status_code < 400 and "location" in resp.headers:
                    redirect_target = resp.headers["location"]
                    r_safe, r_err = validate_url_ssrf_safety(redirect_target)
                    if not r_safe:
                        return LinkCheckResult(
                            url=url,
                            status=LinkHealthClassification.INVALID_REDIRECT,
                            http_status=status_code,
                            response_time_ms=elapsed_ms,
                            error_message=f"Redirect blocked: {r_err}",
                            redirect_url=redirect_target,
                        )

                # Classify based on status code
                if 200 <= status_code < 400:
                    classification = LinkHealthClassification.VALID
                elif status_code == 404:
                    classification = LinkHealthClassification.BROKEN
                elif status_code == 410:
                    classification = LinkHealthClassification.BROKEN_OR_REMOVED
                elif status_code in (401, 403):
                    classification = LinkHealthClassification.UNAVAILABLE
                elif status_code in (429, 500, 502, 503, 504):
                    classification = LinkHealthClassification.TEMPORARY_FAILURE
                else:
                    classification = LinkHealthClassification.UNVERIFIED

                return LinkCheckResult(
                    url=url,
                    status=classification,
                    http_status=status_code,
                    response_time_ms=elapsed_ms,
                    redirect_url=resp.headers.get("location"),
                )

            except (httpx.TimeoutException, httpx.NetworkError) as net_err:
                last_exception = net_err
                if attempt > max_retries:
                    break

        elapsed_ms = int((time.perf_counter() - start_time) * 1000)
        return LinkCheckResult(
            url=url,
            status=LinkHealthClassification.TEMPORARY_FAILURE,
            response_time_ms=elapsed_ms,
            error_message=str(last_exception) if last_exception else "Transient network failure",
        )

    finally:
        if should_close_client:
            await client.aclose()


async def evaluate_link_health(
    session: AsyncSession,
    sample_size: int | None = None,
    random_seed: int = 42,
    maximum_broken_percentage: float = 1.0,
    check_fn: Callable[[str], LinkCheckResult] | None = None,
) -> tuple[CatalogMetricResult, dict]:
    """Evaluates CAT-TGT-05: Broken product destination links strictly below 1.0%."""
    now = datetime.now(UTC)

    # 1. Fetch eligible active offers with non-empty URLs
    query = select(MerchantOffer).where(
        MerchantOffer.status == "ACTIVE",
        MerchantOffer.in_stock == True,  # noqa: E712
    )
    result = await session.execute(query)
    offers = list(result.scalars().all())

    if not offers:
        empty_res = CatalogMetricResult(
            metric_id="CAT-TGT-05",
            target_value=maximum_broken_percentage,
            actual_value=0.0,
            unit="percent",
            passed=True,
            measured_at=now,
            numerator=0,
            denominator=0,
            sample_size=0,
            evidence_reference="product_link_health_audit",
            notes=["No active offers with destination URLs found in catalog."],
        )
        return empty_res, {"valid": 0, "broken": 0, "broken_rate": 0.0}

    # 2. Sample offers deterministically
    sampled_offers = (
        reproducible_sample(offers, sample_size, random_seed=random_seed)
        if sample_size and sample_size < len(offers)
        else offers
    )

    counts_by_status: dict[str, int] = {c.value: 0 for c in LinkHealthClassification}
    broken_offer_ids: list[str] = []

    for offer in sampled_offers:
        if check_fn:
            check_res = check_fn(offer.url)
        else:
            check_res = await safe_check_product_link(offer.url)

        counts_by_status[check_res.status.value] += 1

        if check_res.status in (
            LinkHealthClassification.BROKEN,
            LinkHealthClassification.BROKEN_OR_REMOVED,
        ):
            broken_offer_ids.append(str(offer.id))

        # Record link check observation
        obs = CatalogLinkHealthCheck(
            offer_id=offer.id,
            url=offer.url,
            status=check_res.status.value,
            http_status=check_res.http_status,
            checked_at=now,
            error_message=check_res.error_message,
            response_time_ms=check_res.response_time_ms,
            redirect_url=check_res.redirect_url,
        )
        session.add(obs)

    await session.flush()

    total_sampled = len(sampled_offers)
    confirmed_broken = (
        counts_by_status[LinkHealthClassification.BROKEN.value]
        + counts_by_status[LinkHealthClassification.BROKEN_OR_REMOVED.value]
    )

    broken_rate = round((confirmed_broken / total_sampled) * 100.0, 2) if total_sampled > 0 else 0.0
    passed = broken_rate < maximum_broken_percentage

    metric_result = CatalogMetricResult(
        metric_id="CAT-TGT-05",
        target_value=maximum_broken_percentage,
        actual_value=broken_rate,
        unit="percent",
        passed=passed,
        measured_at=now,
        numerator=confirmed_broken,
        denominator=total_sampled,
        sample_size=total_sampled,
        evidence_reference="product_link_health_audit",
        notes=[
            f"Broken link rate: {broken_rate}% (threshold: <{maximum_broken_percentage}%).",
            f"Classifications: {counts_by_status}.",
            "Temporary failures and bot challenges reported separately, not classified as broken.",
        ],
    )

    details = {
        "total_eligible_offers": len(offers),
        "total_sampled": total_sampled,
        "confirmed_broken_count": confirmed_broken,
        "broken_rate_percentage": broken_rate,
        "counts_by_classification": counts_by_status,
        "broken_offer_ids": broken_offer_ids[:50],
    }

    return metric_result, details
