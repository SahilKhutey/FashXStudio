"""Script to generate single-use invite codes for closed pilot cohorts.

Stores only sha256(code) in the database and outputs plaintext codes once.
"""

import argparse
import hashlib
import secrets
import sys
from datetime import UTC, datetime

from sqlalchemy import create_engine, text

from fashx.core.settings import get_settings

# Crockford-like Base32 alphabet omitting easily confused chars (I, L, O, 0, 1)
ALPHABET = "23456789ABCDEFGHJKMNPQRSTUVWXYZ"


def generate_code(length: int = 10) -> str:
    """Generate cryptographically secure random base32 code (50 bits of entropy)."""
    return "".join(secrets.choice(ALPHABET) for _ in range(length))


def hash_code(code: str) -> str:
    """Compute normalized SHA-256 hash of invite code."""
    normalized = code.strip().upper()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def make_invites(cohort: str, channel: str, n: int, db_url: str | None = None) -> list[str]:
    settings = get_settings()
    url = db_url or settings.database_url
    # Convert asyncpg url to psycopg2/sync for CLI script if necessary
    sync_url = url.replace("+asyncpg", "")

    engine = create_engine(sync_url)
    codes: list[str] = []

    with engine.begin() as conn:
        for _ in range(n):
            code = generate_code(10)
            code_h = hash_code(code)
            conn.execute(
                text(
                    """
                    INSERT INTO pilot_invites (code_hash, cohort, channel, created_at)
                    VALUES (:code_hash, :cohort, :channel, :created_at)
                    ON CONFLICT (code_hash) DO NOTHING
                    """
                ),
                {
                    "code_hash": code_h,
                    "cohort": cohort,
                    "channel": channel,
                    "created_at": datetime.now(UTC),
                },
            )
            codes.append(code)

    return codes


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate single-use pilot invite codes")
    parser.add_argument("--cohort", required=True, help="Pilot cohort tag (e.g. alpha, w1, w2, w3)")
    parser.add_argument(
        "--channel",
        required=True,
        choices=["campus", "community", "referral", "other"],
        help="Recruitment channel",
    )
    parser.add_argument("--n", type=int, default=15, help="Number of invite codes to generate")
    parser.add_argument("--db-url", default=None, help="Database URL override")

    args = parser.parse_args()

    try:
        codes = make_invites(args.cohort, args.channel, args.n, args.db_url)
        print(f"\n[+] Generated {len(codes)} single-use invite codes for cohort='{args.cohort}', channel='{args.channel}':")
        print("-" * 50)
        for i, code in enumerate(codes, 1):
            print(f"{i:2d}. {code}")
        print("-" * 50)
        print("[!] NOTICE: Plaintext codes are displayed only once and cannot be recovered from the database.")
    except Exception as e:
        print(f"[-] Failed to generate invite codes: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
