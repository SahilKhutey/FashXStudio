"""Seed synthetic test users and mint tokens for staging testing and load tests."""

import json
import os
import sys
import time
from uuid import uuid4

import jwt

NUM_USERS = 10
STAGING_ISSUER = os.getenv("AUTH_ISSUER", "https://staging-ref.supabase.co/auth/v1")
STAGING_AUDIENCE = os.getenv("AUTH_AUDIENCE", "authenticated")


def seed_synthetic_staging_users(output_path: str = "tokens.json") -> list[dict]:
    users = []
    tokens = []

    now = int(time.time())

    for i in range(1, NUM_USERS + 1):
        user_sub = str(uuid4())
        email = f"staging-tester-{i:02d}@fashx-test.internal"

        # Generate test payload
        payload = {
            "sub": user_sub,
            "email": email,
            "iss": STAGING_ISSUER,
            "aud": STAGING_AUDIENCE,
            "exp": now + 86400,
            "iat": now,
        }

        secret = os.getenv("AUTH_JWT_SECRET", "test-secret-key-at-least-32-chars-long")
        token = jwt.encode(payload, secret, algorithm="HS256")

        users.append({"user_id": user_sub, "email": email, "token": token})
        tokens.append(token)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(tokens, f, indent=2)

    print(f"[*] Seeded {NUM_USERS} synthetic staging users; tokens written to {output_path}")
    return users


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "tokens.json"
    seed_synthetic_staging_users(out)
