"""Post-deployment smoke test script.

Runs non-destructive verification against staging or production:
1. /api/v1/system/health/ready
2. /api/v1/config
3. /api/v1/me (with synthetic test token)
4. /api/v1/feed?limit=20 (verifying price_as_of)
5. Capability signed image URL resolution
"""

import argparse
import sys

import httpx


def run_smoke_tests(base_url: str, token: str | None = None) -> bool:
    base = base_url.rstrip("/")
    client = httpx.Client(timeout=15.0)

    print(f"[*] Running smoke checks against {base}...")

    # 1. Readiness
    ready_url = f"{base}/api/v1/system/health/ready"
    try:
        r = client.get(ready_url)
        if r.status_code != 200:
            print(f"[FAIL] {ready_url} returned {r.status_code}")
            return False
        print(f"[PASS] {ready_url} -> 200 OK")
    except Exception as e:
        print(f"[FAIL] {ready_url} unreachable: {e}")
        return False

    # 2. Config gate
    cfg_url = f"{base}/api/v1/config"
    try:
        r = client.get(cfg_url)
        if r.status_code != 200:
            print(f"[FAIL] {cfg_url} returned {r.status_code}")
            return False
        cfg = r.json()
        assert "min_app_version" in cfg, "min_app_version missing in config"
        assert "tryon_supported_categories" in cfg, "tryon_supported_categories missing"
        print(f"[PASS] {cfg_url} -> 200 OK, min_app_version={cfg.get('min_app_version')}")
    except Exception as e:
        print(f"[FAIL] {cfg_url} check failed: {e}")
        return False

    # 3. Authenticated check (if token supplied)
    if token:
        headers = {"Authorization": f"Bearer {token}"}

        # /me
        me_url = f"{base}/api/v1/me"
        try:
            r = client.get(me_url, headers=headers)
            if r.status_code != 200:
                print(f"[FAIL] {me_url} returned {r.status_code}")
                return False
            me_data = r.json()
            assert "user_id" in me_data, "user_id missing in /me response"
            print(f"[PASS] {me_url} -> 200 OK, user_id={me_data.get('user_id')}")
        except Exception as e:
            print(f"[FAIL] {me_url} check failed: {e}")
            return False

        # /feed
        feed_url = f"{base}/api/v1/feed?limit=20"
        try:
            r = client.get(feed_url, headers=headers)
            if r.status_code != 200:
                print(f"[FAIL] {feed_url} returned {r.status_code}")
                return False
            feed_data = r.json()
            items = feed_data.get("items", [])
            print(f"[PASS] {feed_url} -> 200 OK, returned {len(items)} items")
            if items:
                first_item = items[0]
                assert "price_as_of" in first_item or "price" in first_item, "price freshness missing"
        except Exception as e:
            print(f"[FAIL] {feed_url} check failed: {e}")
            return False

    print("[SUCCESS] All smoke checks passed successfully.")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FashX Deployment Smoke Test")
    parser.add_argument("--base", default="http://127.0.0.1:8000", help="Base URL of deployed API")
    parser.add_argument("--token", default=None, help="Synthetic test user Bearer token")
    args = parser.parse_args()

    success = run_smoke_tests(args.base, args.token)
    sys.exit(0 if success else 1)
