import asyncio
from typing import Any, Dict
from api.app.infrastructure.queue.queue_port import QueuePort


class RedisQueueAdapter(QueuePort):
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis_url = redis_url
        self._memory_queues: Dict[str, asyncio.Queue] = {}
        self._claimed: Dict[str, str] = {}
        self._completed: Dict[str, Dict[str, Any]] = {}

    async def enqueue(self, queue_name: str, payload: Dict[str, Any], job_id: str) -> bool:
        if queue_name not in self._memory_queues:
            self._memory_queues[queue_name] = asyncio.Queue()
        await self._memory_queues[queue_name].put({"job_id": job_id, "payload": payload})
        return True

    async def claim_job(self, job_id: str, worker_id: str) -> bool:
        if job_id in self._claimed:
            return False
        self._claimed[job_id] = worker_id
        return True

    async def complete_job(self, job_id: str, result: Dict[str, Any]) -> bool:
        self._completed[job_id] = result
        return True
