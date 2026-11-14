#!/usr/bin/env python3
"""FashXStudio — Async Redis Throughput and Latency Benchmark Utility.

Measures connection latency, read/write throughput, and tail percentiles
against AWS ElastiCache for Redis or local Redis instances.

Usage:
    python scripts/redis/benchmark_redis.py --url redis://localhost:6379/0 --concurrency 20 --requests 1000
"""

from __future__ import annotations

import argparse
import asyncio
import statistics
import sys
import time
from typing import Any


def calculate_percentiles(latencies: list[float]) -> dict[str, float]:
    if not latencies:
        return {"min": 0.0, "max": 0.0, "mean": 0.0, "p50": 0.0, "p95": 0.0, "p99": 0.0}
    sorted_lat = sorted(latencies)
    n = len(sorted_lat)
    return {
        "min": sorted_lat[0] * 1000.0,
        "max": sorted_lat[-1] * 1000.0,
        "mean": statistics.mean(sorted_lat) * 1000.0,
        "p50": statistics.median(sorted_lat) * 1000.0,
        "p95": sorted_lat[min(int(n * 0.95), n - 1)] * 1000.0,
        "p99": sorted_lat[min(int(n * 0.99), n - 1)] * 1000.0,
    }


async def worker_task(
    queue: asyncio.Queue[int],
    client: Any,
    op: str,
    latencies: list[float],
) -> None:
    while not queue.empty():
        try:
            item_id = await queue.get()
        except asyncio.QueueEmpty:
            break

        start = time.perf_counter()
        try:
            key = f"benchmark:key:{item_id}"
            if op == "ping":
                await client.ping()
            elif op == "set":
                await client.set(key, f"val_{item_id}", ex=60)
            elif op == "get":
                await client.get(key)
            elapsed = time.perf_counter() - start
            latencies.append(elapsed)
        except Exception as exc:
            print(f"Operation {op} failed for item {item_id}: {exc}", file=sys.stderr)
        finally:
            queue.task_done()


async def run_benchmark(
    url: str,
    concurrency: int,
    total_requests: int,
    operation: str,
) -> tuple[float, dict[str, float]]:
    import redis.asyncio as aioredis

    client = aioredis.from_url(
        url,
        max_connections=concurrency * 2,
        socket_timeout=5.0,
        socket_connect_timeout=5.0,
    )

    queue: asyncio.Queue[int] = asyncio.Queue()
    for i in range(total_requests):
        await queue.put(i)

    latencies: list[float] = []
    start_total = time.perf_counter()

    workers = [
        asyncio.create_task(worker_task(queue, client, operation, latencies))
        for _ in range(concurrency)
    ]
    await asyncio.gather(*workers)
    total_duration = time.perf_counter() - start_total

    # Cleanup benchmark keys if set
    if operation == "set":
        keys_to_clean = [f"benchmark:key:{i}" for i in range(min(total_requests, 500))]
        if keys_to_clean:
            try:
                await client.delete(*keys_to_clean)
            except Exception:
                pass

    await client.aclose()
    stats = calculate_percentiles(latencies)
    return total_duration, stats


def print_results(
    op: str, total_duration: float, total_requests: int, stats: dict[str, float]
) -> None:
    rps = total_requests / total_duration if total_duration > 0 else 0.0
    print(f"\n--- Operation: {op.upper()} ---")
    print(f"Total Completed:  {total_requests} operations in {total_duration:.3f}s")
    print(f"Throughput:       {rps:.1f} ops/sec")
    print(f"Min Latency:      {stats['min']:.2f} ms")
    print(f"Mean Latency:     {stats['mean']:.2f} ms")
    print(f"Median (p50):     {stats['p50']:.2f} ms")
    print(f"p95 Latency:      {stats['p95']:.2f} ms")
    print(f"p99 Latency:      {stats['p99']:.2f} ms")
    print(f"Max Latency:      {stats['max']:.2f} ms")


async def main() -> None:
    parser = argparse.ArgumentParser(description="FashXStudio Redis Benchmark")
    parser.add_argument(
        "--url", default="redis://localhost:6379/0", help="Redis connection URL"
    )
    parser.add_argument(
        "--concurrency", type=int, default=20, help="Concurrent async worker count"
    )
    parser.add_argument(
        "--requests", type=int, default=500, help="Total requests per operation phase"
    )
    args = parser.parse_args()

    print("==================================================================")
    print("FASHXSTUDIO REDIS PERFORMANCE BENCHMARK")
    print(f"Target URL:    {args.url}")
    print(f"Concurrency:   {args.concurrency}")
    print(f"Reqs / Phase:  {args.requests}")
    print("==================================================================")

    for op in ["ping", "set", "get"]:
        try:
            duration, stats = await run_benchmark(
                args.url, args.concurrency, args.requests, op
            )
            print_results(op, duration, args.requests, stats)
        except Exception as exc:
            print(f"Benchmark error during {op}: {exc}")


if __name__ == "__main__":
    asyncio.run(main())
