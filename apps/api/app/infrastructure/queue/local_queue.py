"""
Local / In-Memory Job Queue Adapter (Rule I10)
"""

import asyncio
from typing import Any, Dict
from app.application.ports.queue_port import JobQueuePort


class LocalJobQueueAdapter(JobQueuePort):
    def __init__(self):
        self.queues: Dict[str, asyncio.Queue] = {}
        self.claimed_jobs: Dict[str, str] = {}
        self.completed_jobs: Dict[str, Dict[str, Any]] = {}

    async def enqueue(self, queue_name: str, payload: Dict[str, Any], job_id: str) -> bool:
        if queue_name not in self.queues:
            self.queues[queue_name] = asyncio.Queue()
        await self.queues[queue_name].put({"job_id": job_id, "payload": payload})
        return True

    async def claim_job(self, job_id: str, worker_id: str) -> bool:
        if job_id in self.claimed_jobs:
            return False
        self.claimed_jobs[job_id] = worker_id
        return True

    async def complete_job(self, job_id: str, result: Dict[str, Any]) -> bool:
        self.completed_jobs[job_id] = result
        return True
