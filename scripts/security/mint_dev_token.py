#!/usr/bin/env python3
"""Mint a developer JWT for local testing.

Usage:
    python scripts/security/mint_dev_token.py [--sub SUB] [--exp-hours HOURS]
"""

import argparse
import sys
import time

import jwt

from fashx.core.settings import get_settings


def mint_token(
    sub: str,
    exp_hours: int = 24,
    issuer: str | None = None,
    audience: str | None = None,
) -> str:
    settings = get_settings()

    if settings.is_production or settings.env == "prod":
        sys.stderr.write("ERROR: mint_dev_token cannot be run in production environment.\n")
        sys.exit(1)

    if settings.auth_mode != "local":
        sys.stderr.write("ERROR: mint_dev_token requires AUTH_MODE=local.\n")
        sys.exit(1)

    if not settings.auth_jwt_secret:
        sys.stderr.write("ERROR: AUTH_JWT_SECRET is not configured.\n")
        sys.exit(1)

    now = int(time.time())
    payload = {
        "sub": sub,
        "iss": issuer or settings.auth_issuer,
        "aud": audience or settings.auth_audience,
        "iat": now,
        "nbf": now,
        "exp": now + (exp_hours * 3600),
    }

    token = jwt.encode(
        payload,
        settings.auth_jwt_secret.get_secret_value(),
        algorithm="HS256",
    )
    return token


def main() -> None:
    parser = argparse.ArgumentParser(description="Mint a local dev JWT token")
    parser.add_argument("--sub", default="dev-user-001", help="Subject identifier (e.g. user id)")
    parser.add_argument("--exp-hours", type=int, default=24, help="Token expiration in hours")
    parser.add_argument("--iss", default=None, help="Issuer override")
    parser.add_argument("--aud", default=None, help="Audience override")
    args = parser.parse_args()

    token = mint_token(
        sub=args.sub,
        exp_hours=args.exp_hours,
        issuer=args.iss,
        audience=args.aud,
    )

    print(f"Token: {token}\n")
    print(f"Header: Authorization: Bearer {token}")
    print("\nTest with curl:")
    print(f"curl -H 'Authorization: Bearer {token}' http://localhost:8000/api/v1/me")


if __name__ == "__main__":
    main()
