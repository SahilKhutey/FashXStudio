"""
Abstract Job Queue Port (Rule I07 & I10)
Supports atomic task enqueueing, claiming, and completion.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class JobQueuePort(ABC):
    @abstractmethod
    async def enqueue(self, queue_name: str, payload: Dict[str, Any], job_id: str) -> bool:
        """Enqueues a background job payload with explicit job_id."""
        pass

    @abstractmethod
    async def claim_job(self, job_id: str, worker_id: str) -> bool:
        """
        Atomically claims a job for execution.
        Returns True if the claim was successful, False if already claimed.
        """
        pass

    @abstractmethod
    async def complete_job(self, job_id: str, result: Dict[str, Any]) -> bool:
        """Marks the job as completed with output payload."""
        pass
