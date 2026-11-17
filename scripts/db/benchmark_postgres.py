"""FashXStudio: PostgreSQL Connection & Query Latency Benchmark Tool."""

from __future__ import annotations

import asyncio
import os
import statistics
import time

import asyncpg


def normalize_dsn(url: str) -> str:
    """Normalize SQLAlchemy asyncpg connection URL to standard PostgreSQL DSN."""
    if url.startswith("postgresql+asyncpg://"):
        return "postgresql://" + url[len("postgresql+asyncpg://") :]
    if url.startswith("postgres://"):
        return "postgresql://" + url[len("postgres://") :]
    return url


async def measure_worker(pool: asyncpg.Pool, iterations: int) -> list[float]:
    latencies: list[float] = []
    async with pool.acquire() as conn:
        for _ in range(iterations):
            t0 = time.perf_counter()
            await conn.fetchval("SELECT 1")
            latencies.append((time.perf_counter() - t0) * 1000.0)
    return latencies


async def main() -> None:
    raw_url = os.environ.get("DATABASE_URL")
    if not raw_url:
        print("ERROR: DATABASE_URL environment variable must be set")
        return

    dsn = normalize_dsn(raw_url)
    concurrency = int(os.environ.get("DB_BENCH_CONCURRENCY", "5"))
    iterations = int(os.environ.get("DB_BENCH_ITERATIONS", "50"))

    print("==================================================================")
    print("FASHXSTUDIO DATABASE BENCHMARK")
    print(f"Concurrency : {concurrency} workers")
    print(f"Iterations  : {iterations} queries / worker (Total: {concurrency * iterations})")
    print("==================================================================")

    # 1. Connection Establishment Latency
    conn_t0 = time.perf_counter()
    pool = await asyncpg.create_pool(
        dsn=dsn,
        min_size=concurrency,
        max_size=concurrency + 5,
        command_timeout=10,
    )
    conn_time_ms = (time.perf_counter() - conn_t0) * 1000.0
    print(f"Pool initialization ({concurrency} connections): {conn_time_ms:.2f} ms")

    try:
        # 2. Concurrent Query Latency
        bench_t0 = time.perf_counter()
        tasks = [asyncio.create_task(measure_worker(pool, iterations)) for _ in range(concurrency)]
        results = await asyncio.gather(*tasks)
        total_time_s = time.perf_counter() - bench_t0

        all_latencies: list[float] = [lat for worker_res in results for lat in worker_res]
        all_latencies.sort()

        p50 = statistics.median(all_latencies)
        p95 = all_latencies[int(len(all_latencies) * 0.95)]
        p99 = all_latencies[int(len(all_latencies) * 0.99)]
        mean = statistics.mean(all_latencies)
        qps = len(all_latencies) / total_time_s

        print("------------------------------------------------------------------")
        print(f"Total Queries  : {len(all_latencies)}")
        print(f"Total Duration : {total_time_s:.2f} s")
        print(f"Throughput     : {qps:.1f} QPS")
        print(f"Mean Latency   : {mean:.2f} ms")
        print(f"P50 Latency    : {p50:.2f} ms")
        print(f"P95 Latency    : {p95:.2f} ms")
        print(f"P99 Latency    : {p99:.2f} ms")
        print("==================================================================")
    finally:
        await pool.close()


if __name__ == "__main__":
    asyncio.run(main())
