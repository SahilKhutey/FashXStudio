import pathlib
import re
import subprocess
from sqlalchemy import create_engine, inspect

from database.models import Base
from fashx.core.settings import get_settings

src = subprocess.run(
    ["git", "ls-files", "backend"], capture_output=True, text=True, check=True
).stdout.split()

ports: dict[str, list[str]] = {}
for f in src:
    if f.endswith(".py"):
        p = pathlib.Path(f)
        if p.exists():
            content = p.read_text(encoding="utf-8")
            for m in re.finditer(r"class (\w+Repository)\b", content):
                ports.setdefault(m.group(1), []).append(f)

print("REPOSITORY CLASSES")
for name, files in sorted(ports.items()):
    kind = (
        "memory"
        if any("memory" in f.lower() for f in files)
        else ("sql" if any(re.search(r"sql|orm|pg", f.lower()) for f in files) else "port/other")
    )
    print(f"  {name:45} {kind:10} {files[0]}")

print("\nORM TABLES (Base.metadata)")
for t_name, table in sorted(Base.metadata.tables.items()):
    cols = {c.name for c in table.columns}
    flags = ("user_id " if "user_id" in cols else "") + (
        "vector " if any("embedding" in c or "vector" in c for c in cols) else ""
    )
    print(f"  {t_name:40} {flags}")

settings = get_settings()
db_url = settings.database_url
# Convert asyncpg to sync psycopg or psycopg2 if testing live db
sync_url = db_url.replace("+asyncpg", "").replace("+aiosqlite", "")

try:
    engine = create_engine(sync_url)
    insp = inspect(engine)
    print(f"\nLIVE DB TABLES ({sync_url})")
    tables = insp.get_table_names()
    if not tables:
        print("  (Connected, but no tables found. Run alembic upgrade head)")
    for t in sorted(tables):
        cols = {c["name"] for c in insp.get_columns(t)}
        flags = ("user_id " if "user_id" in cols else "") + (
            "vector " if any("embedding" in c for c in cols) else ""
        )
        print(f"  {t:40} {flags}")
except Exception as e:
    print(f"\nLIVE DB CONNECTION NOTICE: {e}")
    print("  Using ORM table metadata as source of truth for offline audit.")
