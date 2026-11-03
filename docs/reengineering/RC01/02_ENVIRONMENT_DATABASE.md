# RC-01 — Environment & Database Configuration

## Database Configuration

### 1. Dual-Engine Architecture
- **Development & Local Testing**: SQLite with async driver `sqlite+aiosqlite:///./fashx_local.db`.
- **Production & CI Postgres Gate**: PostgreSQL with async driver `postgresql+asyncpg://...`.
- In compliance with repository rules (`AGENTS.md` Rule 6), tests touching the database support both SQLite and PostgreSQL.

### 2. Alembic Migrations
- Migration files are located in `alembic/versions/`.
- Total migrations in tree: 32 revisions.
- Head revision: `20261028_01_privacy_audit` (chain verified complete).
- In SQLite development, database schemas can also be created via SQLAlchemy metadata reflection when testing isolated unit sessions, or migrated via standard Alembic runner.

## Catalog Hydration & Seed Verification

### 1. Source Registration & Clearance
In FashXStudio, no garment can be displayed or used in try-on unless its source is registered and cleared with valid provenance evidence:
```powershell
.venv\Scripts\python scripts/catalog/register_source.py --slug own-wardrobe --name "Own wardrobe" --kind manual --image-policy mirror
.venv\Scripts\python scripts/catalog/clear_source.py own-wardrobe --evidence-url "docs/evidence/README.md" --display --tryon
```

### 2. Seed Execution
Seeding was executed against `fashx_local.db` using `catalog_seed/catalog.csv`:
```powershell
.venv\Scripts\python scripts/catalog/seed_local.py --csv catalog_seed/catalog.csv --apply
```

### 3. Persisted Entity Counts
Verification query against `fashx_local.db`:
```python
import sqlite3
conn = sqlite3.connect("fashx_local.db")
tables = ["catalog_sources", "canonical_garments", "merchant_products", "merchant_offers", "garment_images", "garment_enrichments"]
for t in tables:
    count = conn.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
    print(f"{t}: {count}")
```

Observed counts:
| Table Name | Record Count | Status |
| :--- | :--- | :--- |
| `catalog_sources` | 1 (`own-wardrobe`) | 🟢 Verified |
| `canonical_garments` | 20 | 🟢 Verified |
| `merchant_products` | 20 | 🟢 Verified |
| `merchant_offers` | 20 | 🟢 Verified |
| `garment_images` | 20 | 🟢 Verified |
| `garment_enrichments` | 20 | 🟢 Verified |
