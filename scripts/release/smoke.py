"""Post-deployment smoke test script.

Runs non-destructive verification against staging or production:
1. /healthz/live (or /api/v1/system/health/live)
2. /healthz/ready (or /api/v1/system/health/ready)
3. /api/v1/config
4. /api/v1/me (with synthetic test token; identifier scrubbed from output)
5. /api/v1/feed?limit=20 (verifying price freshness)

Security constraint:
- Auth tokens and user identifiers are scrubbed from console output to prevent credential leakage.
"""

import argparse
import os
import sys

import httpx


def _check_endpoint(
    client: httpx.Client,
    url: str,
    name: str,
    headers: dict[str, str] | None = None,
) -> tuple[bool, httpx.Response | None]:
    try:
        r = client.get(url, headers=headers)
        if r.status_code == 200:
            print(f"[PASS] {name} -> 200 OK")
            return True, r
        print(f"[FAIL] {name} returned HTTP {r.status_code}")
        return False, r
    except Exception as e:
        print(f"[FAIL] {name} unreachable: {type(e).__name__}")
        return False, None


def run_smoke_tests(base_url: str, token: str | None = None) -> bool:
    base = base_url.rstrip("/")
    client = httpx.Client(timeout=15.0)
    passed_count = 0
    total_count = 0

    print(f"[*] Running smoke checks against {base} (token provided: {bool(token)})...")

    # 1. Liveness check
    total_count += 1
    ok_live, _ = _check_endpoint(client, f"{base}/healthz/live", "Liveness probe (/healthz/live)")
    if not ok_live:
        # Fallback probe check
        ok_live, _ = _check_endpoint(
            client,
            f"{base}/api/v1/system/health/live",
            "Liveness fallback (/api/v1/system/health/live)",
        )
    if ok_live:
        passed_count += 1

    # 2. Readiness check
    total_count += 1
    ok_ready, _ = _check_endpoint(client, f"{base}/healthz/ready", "Readiness probe (/healthz/ready)")
    if not ok_ready:
        ok_ready, _ = _check_endpoint(
            client,
            f"{base}/api/v1/system/health/ready",
            "Readiness fallback (/api/v1/system/health/ready)",
        )
    if ok_ready:
        passed_count += 1

    # 3. Config gate
    total_count += 1
    ok_cfg, r_cfg = _check_endpoint(client, f"{base}/api/v1/config", "Client config (/api/v1/config)")
    if ok_cfg and r_cfg is not None:
        try:
            cfg = r_cfg.json()
            assert "min_app_version" in cfg, "min_app_version missing in config"
            assert "tryon_supported_categories" in cfg, "tryon_supported_categories missing"
            passed_count += 1
        except (AssertionError, ValueError) as err:
            print(f"[FAIL] Config validation failed: {err}")
    elif ok_cfg:
        passed_count += 1

    # 4. Authenticated checks (if token supplied)
    if token:
        headers = {"Authorization": f"Bearer {token}"}

        # /me check (user identifier scrubbed)
        total_count += 1
        ok_me, r_me = _check_endpoint(
            client,
            f"{base}/api/v1/me",
            "Current user identity (/api/v1/me)",
            headers=headers,
        )
        if ok_me and r_me is not None:
            try:
                me_data = r_me.json()
                assert "user_id" in me_data, "user_id missing in /me response"
                # Scrubbed log message: never print the real or synthetic user_id or token
                print("[PASS] User identity confirmed (identifier sanitized)")
                passed_count += 1
            except (AssertionError, ValueError) as err:
                print(f"[FAIL] User identity validation failed: {err}")
        elif ok_me:
            passed_count += 1

        # /feed check (pricing freshness)
        total_count += 1
        ok_feed, r_feed = _check_endpoint(
            client,
            f"{base}/api/v1/feed?limit=20",
            "Discovery feed (/api/v1/feed?limit=20)",
            headers=headers,
        )
        if ok_feed and r_feed is not None:
            try:
                feed_data = r_feed.json()
                items = feed_data.get("items", [])
                if items:
                    first_item = items[0]
                    assert "price_as_of" in first_item or "price" in first_item, "price freshness missing"
                print(f"[PASS] Feed items validated: count={len(items)}")
                passed_count += 1
            except (AssertionError, ValueError) as err:
                print(f"[FAIL] Feed validation failed: {err}")
        elif ok_feed:
            passed_count += 1

    print(f"[*] Smoke verification result: {passed_count}/{total_count} checks passed.")
    return passed_count == total_count


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FashX Deployment Smoke Test")
    parser.add_argument("--base", default=os.environ.get("API_BASE", "http://127.0.0.1:8000"), help="Base URL of deployed API")
    parser.add_argument(
        "--token",
        default=None,
        help="Synthetic test user Bearer token (preferred: set SMOKE_TEST_TOKEN environment variable)",
    )
    args = parser.parse_args()

    # Read token from environment variable or CLI argument (env var takes precedence for security)
    smoke_token = os.environ.get("SMOKE_TEST_TOKEN") or args.token

    success = run_smoke_tests(args.base, smoke_token)
    sys.exit(0 if success else 1)

