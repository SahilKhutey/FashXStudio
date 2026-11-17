# Database Connection Pooling and Sizing Architecture

## 1. Connection Budget Calculation Model

To prevent connection exhaustion and database thread contention under traffic spikes, connection allocation is mathematically bounded across all container tasks:

$$C_{\text{max}} = N_{\text{API}} \cdot (P_{\text{API}} + O_{\text{API}}) + N_{\text{worker}} \cdot (P_{\text{worker}} + O_{\text{worker}}) + C_{\text{migration}} + C_{\text{admin}}$$

Where:
- $N$: Number of running container task instances.
- $P$: Base connection pool size per container (`pool_size`).
- $O$: Maximum burst overflow connections per container (`max_overflow`).
- $C_{\text{migration}}$: Reserved connections for active Alembic migrations ($1$).
- $C_{\text{admin}}$: Operational reserve for RDS health checks, CloudWatch, and emergency psql administration ($10$).

---

## 2. Environment Connection Budgets

| Component | Dev (Single Node) | Staging (RC) | Production Baseline | Production Peak (Auto-scale) |
| :--- | :--- | :--- | :--- | :--- |
| **API Tasks ($N_{\text{API}}$)** | 1 instance | 2 instances | 4 instances | 10 instances |
| **API Pool ($P+O$)** | $5 + 5 = 10$ | $5 + 5 = 10$ | $10 + 10 = 20$ | $10 + 10 = 20$ |
| **Total API Connections** | 10 | 20 | 80 | 200 |
| **Workers ($N_{\text{worker}}$)** | 1 instance | 2 instances | 2 instances | 6 instances |
| **Worker Pool ($P+O$)** | $3 + 2 = 5$ | $3 + 2 = 5$ | $5 + 5 = 10$ | $5 + 5 = 10$ |
| **Total Worker Connections** | 5 | 10 | 20 | 60 |
| **Migration + Admin Reserve** | 5 | 5 | 15 | 20 |
| **Calculated Peak ($C_{\text{max}}$)** | **20 connections** | **35 connections** | **115 connections** | **280 connections** |
| **Database `max_connections`** | **100** | **150** | **1,000** | **1,000** |
| **Peak Pool Utilization** | 20.0% | 23.3% | 11.5% | 28.0% |

All environments operate comfortably below the 70% threshold, ensuring database stability during sudden surges.

---

## 3. SQLAlchemy Async Engine Configuration

In [`backend/fashx/core/database.py`](file:///c:/Users/ASUS/Documents/FashXStudio/backend/fashx/core/database.py):

```python
_engine = create_async_engine(
    settings.database_url,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_timeout=settings.db_pool_timeout,
    pool_pre_ping=True,       # Validates connection health before issuing queries
    pool_recycle=1800,        # Recycles stale connections every 30 minutes
)
```

---

## 4. Operational Monitoring Queries

Run these diagnostics via psql to monitor live pool behavior:

```sql
-- 1. Active connection count by user and application
SELECT usename, application_name, state, count(*) AS connection_count
FROM pg_stat_activity
GROUP BY usename, application_name, state
ORDER BY connection_count DESC;

-- 2. Current global connection saturation
SELECT
    count(*) AS current_connections,
    current_setting('max_connections')::int AS max_connections,
    round((count(*)::numeric / current_setting('max_connections')::numeric) * 100, 2) AS utilization_pct
FROM pg_stat_activity;
```
