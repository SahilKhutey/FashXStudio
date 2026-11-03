#!/usr/bin/env python3
"""RC-03 End-to-End System Integration Smoke Verification Script.

Verifies end-to-end integration across:
- Liveness & Readiness probes (/healthz/live, /healthz/ready)
- Authenticated identity (/api/v1/me)
- Fashion catalog discovery feed (/api/v1/feed)
- Commerce outbound affiliate click tracking (/api/v1/commerce/buy-clicks)
- Wardrobe persistence lifecycle (/api/v1/wardrobe/items: save, list, remove)
- Virtual try-on jobs query (/api/v1/tryon/jobs)
"""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from typing import Any

from fashx.core.settings import get_settings
from fashx.security.tokens import create_demo_token


class SmokeVerificationFailure(Exception):
    pass


def request_json(
    url: str,
    method: str = "GET",
    body: dict[str, Any] | None = None,
    token: str | None = None,
) -> tuple[int, Any]:
    headers = {"Accept": "application/json"}
    data = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode("utf-8")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            content = resp.read()
            if not content:
                return resp.status, None
            return resp.status, json.loads(content.decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        try:
            parsed = json.loads(err_body)
        except Exception:
            parsed = err_body
        return e.code, parsed


def run_smoke_verification(base_url: str = "http://localhost:8000") -> None:
    print(f"=== FashXStudio RC-03 Smoke Verification against {base_url} ===\n")
    settings = get_settings()

    # Step 1: Health Probes
    print("[1/6] Verifying Health & Readiness probes...")
    status, live_res = request_json(f"{base_url}/healthz/live")
    if status != 200 or live_res.get("status") != "ok":
        raise SmokeVerificationFailure(f"Liveness check failed: HTTP {status} -> {live_res}")
    print(f"  + /healthz/live: OK (status={live_res.get('status')})")

    status, ready_res = request_json(f"{base_url}/healthz/ready")
    if status != 200 or ready_res.get("database") != "ok":
        raise SmokeVerificationFailure(f"Readiness check failed: HTTP {status} -> {ready_res}")
    print(f"  + /healthz/ready: OK (status={ready_res.get('status')}, db={ready_res.get('database')})")

    # Step 2: Auth & Identity
    print("\n[2/6] Generating Demo JWT & Verifying User Identity...")
    test_subject = "11111111-1111-1111-1111-111111111111"
    secret = (
        settings.auth_jwt_secret.get_secret_value()
        if settings.auth_jwt_secret
        else "test-secret-key-at-least-32-chars-long"
    )
    token = create_demo_token(
        subject=test_subject,
        secret=secret,
        issuer=settings.auth_issuer or "fashx-local",
        audience=settings.auth_audience or "fashx-api",
        exp_seconds=3600,
    )

    status, me_res = request_json(f"{base_url}/api/v1/me", token=token)
    if status != 200 or not me_res.get("user_id"):
        raise SmokeVerificationFailure(f"/api/v1/me check failed: HTTP {status} -> {me_res}")
    user_id = me_res["user_id"]
    print(f"  + /api/v1/me: Authenticated as user_id={user_id} (roles={me_res.get('roles')})")

    # Step 3: Discovery & Feed
    print("\n[3/6] Verifying Discovery Feed...")
    status, feed_res = request_json(f"{base_url}/api/v1/feed", token=token)
    if status != 200 or not feed_res.get("items"):
        raise SmokeVerificationFailure(f"/api/v1/feed check failed: HTTP {status} -> {feed_res}")
    feed_items = feed_res["items"]
    sample_item = feed_items[0]
    garment_id = sample_item["garment_id"]
    print(
        f"  + /api/v1/feed: Loaded {len(feed_items)} garments. First: '{sample_item.get('title')}' (id={garment_id})"
    )

    # Step 4: Outbound Commerce Tracking
    print("\n[4/6] Verifying Outbound Commerce Affiliate Redirect...")
    buy_payload = {"garment_id": garment_id}
    status, buy_res = request_json(
        f"{base_url}/api/v1/commerce/buy-clicks",
        method="POST",
        body=buy_payload,
        token=token,
    )
    if status != 201 or not buy_res.get("redirect_url"):
        raise SmokeVerificationFailure(
            f"/api/v1/commerce/buy-clicks failed: HTTP {status} -> {buy_res}"
        )
    redirect_url = buy_res["redirect_url"]
    if not redirect_url.startswith("https://"):
        raise SmokeVerificationFailure(f"Insecure redirect URL returned: {redirect_url}")
    print(
        f"  + /api/v1/commerce/buy-clicks: Success (tracking_id={buy_res.get('tracking_id')}, redirect={redirect_url[:60]}...)"
    )

    # Step 5: Wardrobe Persistence Lifecycle
    print("\n[5/6] Verifying Wardrobe Persistence (Save, List, Remove)...")
    save_payload = {"garment_id": garment_id}
    status, save_res = request_json(
        f"{base_url}/api/v1/wardrobe/items",
        method="POST",
        body=save_payload,
        token=token,
    )
    if status != 201 or not save_res.get("item_id"):
        raise SmokeVerificationFailure(f"Wardrobe save failed: HTTP {status} -> {save_res}")
    item_id = save_res["item_id"]
    print(f"  + Saved garment to closet: item_id={item_id}")

    status, list_res = request_json(f"{base_url}/api/v1/wardrobe/items", token=token)
    if status != 200 or not any(it.get("item_id") == item_id for it in list_res):
        raise SmokeVerificationFailure(f"Wardrobe list did not contain item_id {item_id}: {list_res}")
    print(f"  + Wardrobe query verified: item exists in user wardrobe")

    status, _ = request_json(
        f"{base_url}/api/v1/wardrobe/items/{item_id}",
        method="DELETE",
        token=token,
    )
    if status != 204:
        raise SmokeVerificationFailure(f"Wardrobe remove failed: HTTP {status}")
    print(f"  + Wardrobe item removed cleanly (HTTP 204)")

    # Step 6: Virtual Try-On Jobs
    print("\n[6/6] Verifying Virtual Try-On Jobs query...")
    status, jobs_res = request_json(f"{base_url}/api/v1/tryon/jobs", token=token)
    if status != 200 or not isinstance(jobs_res, list):
        raise SmokeVerificationFailure(f"TryOn jobs query failed: HTTP {status} -> {jobs_res}")
    print(f"  + /api/v1/tryon/jobs: Query successful (total existing jobs={len(jobs_res)})")

    print("\n=======================================================")
    print("SUCCESS: ALL RC-03 SYSTEM INTEGRATION WORKFLOWS VERIFIED")
    print("=======================================================")


if __name__ == "__main__":
    try:
        run_smoke_verification()
    except SmokeVerificationFailure as e:
        print(f"\nSMOKE VERIFICATION FAILED: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\nUNEXPECTED FAILURE: {e}", file=sys.stderr)
        sys.exit(2)
