from abc import ABC, abstractmethod
from typing import Any, Dict


class QueuePort(ABC):
    @abstractmethod
    async def enqueue(self, queue_name: str, payload: Dict[str, Any], job_id: str) -> bool:
        pass

    @abstractmethod
    async def claim_job(self, job_id: str, worker_id: str) -> bool:
        pass

    @abstractmethod
    async def complete_job(self, job_id: str, result: Dict[str, Any]) -> bool:
        pass
