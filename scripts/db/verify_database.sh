#!/usr/bin/env bash
set -Eeuo pipefail

# ==============================================================================
# FashXStudio: PostgreSQL Database Preflight & Health Verification
# ==============================================================================

: "${DATABASE_URL:?DATABASE_URL must be set via environment or secret manager}"

echo "=================================================================="
echo "FASHXSTUDIO DATABASE PREFLIGHT VERIFICATION"
echo "=================================================================="

# Check database connectivity, identity, and extension status
python -c "
import asyncio
import os
import sys
from urllib.parse import urlparse
import asyncpg

raw_url = os.environ['DATABASE_URL']
if raw_url.startswith('postgresql+asyncpg://'):
    dsn = 'postgresql://' + raw_url[len('postgresql+asyncpg://'):]
elif raw_url.startswith('postgres://'):
    dsn = 'postgresql://' + raw_url[len('postgres://'):]
else:
    dsn = raw_url

async def verify():
    try:
        conn = await asyncpg.connect(dsn=dsn, timeout=10)
    except Exception as e:
        print(f'ERROR: Connection failed: {e}')
        sys.exit(1)

    try:
        db = await conn.fetchval('SELECT current_database()')
        user = await conn.fetchval('SELECT current_user')
        ver = await conn.fetchval('SELECT version()')
        ssl = await conn.fetchval('SELECT ssl_is_used()') if conn.get_server_version().major >= 12 else 'unknown'
        vec = await conn.fetchval(\"\"\"
            SELECT extversion FROM pg_extension WHERE extname = 'vector'
        \"\"\")

        print(f'Database Name       : {db}')
        print(f'Connected User      : {user}')
        print(f'PostgreSQL Version  : {ver.split()[0]} {ver.split()[1]}')
        print(f'SSL / TLS Active    : {ssl}')
        print(f'pgvector Installed  : {vec if vec else \"NOT INSTALLED\"}')

        tables = await conn.fetchval(\"\"\"
            SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'
        \"\"\")
        print(f'Public Tables Count : {tables}')

        try:
            rev = await conn.fetchval('SELECT version_num FROM alembic_version')
            print(f'Alembic Revision    : {rev}')
        except Exception:
            print('Alembic Revision    : (No alembic_version table found)')

        print('Preflight Verification: SUCCESS')
    finally:
        await conn.close()

asyncio.run(verify())
"
