#!/usr/bin/env python3
"""Mobile LAN API Configuration Utility (FX-005 / RC-04).

Detects local network IPv4 address, checks backend connectivity on port 8000,
and configures mobile/.env for physical device testing via Expo Go QR code.
"""

from __future__ import annotations

import argparse
import socket
import urllib.error
import urllib.request
from pathlib import Path


def get_lan_ip() -> str:
    """Resolve active outbound LAN IPv4 address."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Does not actually transmit packets, just routes to determine outbound interface
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = socket.gethostbyname(socket.gethostname())
    finally:
        s.close()
    return ip


def check_api_reachability(ip: str, port: int = 8000) -> bool:
    """Verify backend responsiveness on LAN interface."""
    url = f"http://{ip}:{port}/healthz/live"
    try:
        with urllib.request.urlopen(url, timeout=3) as resp:
            return resp.status == 200
    except Exception:
        return False


def update_env_file(env_path: Path, new_url: str) -> None:
    """Update EXPO_PUBLIC_API_URL in .env preserving all other environment variables."""
    lines: list[str] = []
    found = False

    if env_path.exists():
        content = env_path.read_text(encoding="utf-8")
        for line in content.splitlines():
            if line.startswith("EXPO_PUBLIC_API_URL="):
                lines.append(f"EXPO_PUBLIC_API_URL={new_url}")
                found = True
            else:
                lines.append(line)

    if not found:
        lines.append(f"EXPO_PUBLIC_API_URL={new_url}")

    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Configure mobile/.env for physical device testing on local Wi-Fi."
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="FastAPI backend port (default: 8000)",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write updated EXPO_PUBLIC_API_URL to mobile/.env",
    )
    args = parser.parse_args()

    lan_ip = get_lan_ip()
    api_url = f"http://{lan_ip}:{args.port}"
    env_file = Path("mobile/.env")

    print("=== FashXStudio Mobile LAN Configuration Utility ===")
    print(f"Detected LAN IPv4: {lan_ip}")
    print(f"Target Mobile API: {api_url}")

    reachable = check_api_reachability(lan_ip, args.port)
    if reachable:
        print(f"Backend Status:   ONLINE & REACHABLE at {api_url}/healthz/live")
    else:
        print(f"Backend Status:   UNREACHABLE on {lan_ip}:{args.port}")
        print("  Hint: Ensure FastAPI is running with: uvicorn fashx.main:app --host 0.0.0.0 --port 8000")

    if args.apply:
        update_env_file(env_file, api_url)
        print(f"\n[APPLIED] Successfully updated '{env_file}' -> EXPO_PUBLIC_API_URL={api_url}")
    else:
        print(f"\n[DRY RUN] Run with --apply to write to '{env_file}'")

    print("\nPhysical Device Testing Instructions:")
    print("  1. Connect your smartphone to the SAME Wi-Fi network.")
    print("  2. In your terminal: cd mobile && npx expo start --lan")
    print("  3. Scan the terminal QR code using Expo Go (Android) or Camera app (iOS).")


if __name__ == "__main__":
    main()
