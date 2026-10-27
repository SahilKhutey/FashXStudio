#!/usr/bin/env python3
"""Generate a signed demo JWT token for local/staging evaluator walkthroughs."""

from __future__ import annotations

import argparse
import sys

from fashx.core.settings import get_settings
from fashx.security.tokens import LocalJWTVerifier, create_demo_token


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a demo evaluator JWT token for FashXStudio."
    )
    parser.add_argument(
        "--sub",
        default="demo-tester-1",
        help="Subject / user identifier (default: demo-tester-1)",
    )
    parser.add_argument(
        "--hours",
        type=int,
        default=168,
        help="Token validity in hours (default: 168 = 7 days)",
    )
    parser.add_argument(
        "--secret",
        default=None,
        help="Signing secret (defaults to AUTH_JWT_SECRET from settings or fallback)",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Self-verify the generated token against LocalJWTVerifier before outputting",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = get_settings()

    secret = (
        args.secret
        or (settings.auth_jwt_secret.get_secret_value() if settings.auth_jwt_secret else None)
        or "test-secret-key-at-least-32-chars-long"
    )
    issuer = settings.auth_issuer or "fashx-test"
    audience = settings.auth_audience or "fashx-api"

    token = create_demo_token(
        subject=args.sub,
        secret=secret,
        issuer=issuer,
        audience=audience,
        exp_seconds=args.hours * 3600,
    )

    if args.verify:
        verifier = LocalJWTVerifier(secret=secret, issuer=issuer, audience=audience)
        claims = verifier.verify(token)
        print(f"Self-check PASS: subject='{claims.subject}', issuer='{claims.issuer}'", file=sys.stderr)

    print("\n--- FashXStudio Demo Access Token ---")
    print(f"Subject:    {args.sub}")
    print(f"Issuer:     {issuer}")
    print(f"Audience:   {audience}")
    print(f"Expires in: {args.hours} hours")
    print("\nToken:")
    print(token)
    print("\nUsage in curl:")
    print(f'curl -H "Authorization: Bearer {token}" http://localhost:8000/api/v1/me')
    print("\nUsage in mobile (.env):")
    print(f"EXPO_PUBLIC_API_TOKEN={token}\n")


if __name__ == "__main__":
    main()
