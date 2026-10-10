"""Canonical two-phase TryOn adapter port and domain request/output contracts."""

from dataclasses import dataclass
from typing import Literal, Protocol


@dataclass(frozen=True)
class TryOnRequest:
    person_jpeg: bytes
    garment_jpeg: bytes
    category: Literal["auto", "tops", "bottoms", "one-pieces"] = "auto"


@dataclass(frozen=True)
class TryOnOutput:
    image_bytes: bytes
    provider: str
    model: str
    provider_job_id: str
    latency_ms: int
    cost_usd_est: float | None = None


class TryOnError(Exception):
    """Domain exception representing recoverable or permanent try-on failures."""

    def __init__(
        self,
        code: str,
        user_message: str,
        *,
        retryable: bool,
        detail: str = "",
    ) -> None:
        super().__init__(f"{code}: {detail or user_message}")
        self.code = code
        self.user_message = user_message
        self.retryable = retryable
        self.detail = detail


class TryOnAdapter(Protocol):
    """Pluggable adapter protocol supporting asynchronous two-phase submit & collect."""

    provider: str
    license_id: str

    def submit(self, req: TryOnRequest) -> str:
        """Submit job to provider, returning vendor's provider_job_id immediately."""
        ...

    def collect(self, provider_job_id: str, *, deadline_s: float) -> TryOnOutput:
        """Poll or wait for provider completion until deadline_s expires."""
        ...

    def run(self, req: TryOnRequest) -> TryOnOutput:
        """Single-shot submit and collect convenience method."""
        ...
