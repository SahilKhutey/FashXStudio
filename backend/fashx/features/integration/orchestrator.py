from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Protocol
from uuid import uuid4

from .workflows import WORKFLOWS, WorkflowName


class FeatureAdapter(Protocol):
    def execute(self, action: str, context: Mapping[str, Any]) -> Mapping[str, Any]: ...


@dataclass(frozen=True)
class WorkflowResult:
    execution_id: str
    workflow: WorkflowName
    completed: bool
    data: Mapping[str, Any] = field(default_factory=dict)
    warnings: tuple[str, ...] = ()


class IntegrationOrchestrator:
    """F14 boundary: features communicate through adapters, never internals."""

    def __init__(self, adapters: Mapping[str, FeatureAdapter] | None = None) -> None:
        self._adapters = dict(adapters or {})
        self._idempotent: dict[str, WorkflowResult] = {}

    def register(self, feature_id: str, adapter: FeatureAdapter) -> None:
        self._adapters[feature_id] = adapter

    def execute(
        self, workflow: WorkflowName, context: Mapping[str, Any], idempotency_key: str | None = None
    ) -> WorkflowResult:
        if not context.get("user_id"):
            raise ValueError("Integration context requires user_id")
        key = f"{workflow}:{context['user_id']}:{idempotency_key}" if idempotency_key else None
        if key and key in self._idempotent:
            return self._idempotent[key]
        data: dict[str, Any] = dict(context)
        warnings: list[str] = []
        for step in WORKFLOWS[workflow]:
            adapter = self._adapters.get(step.feature_id)
            if adapter is None:
                message = f"{step.feature_id}.{step.action} is unavailable"
                if step.required:
                    return WorkflowResult(str(uuid4()), workflow, False, data, tuple((*warnings, message)))
                warnings.append(message)
                continue
            try:
                data.update(adapter.execute(step.action, data))
            except (TypeError, ValueError, KeyError) as exc:
                message = f"{step.feature_id}.{step.action} failed: {exc}"
                if step.required:
                    return WorkflowResult(str(uuid4()), workflow, False, data, tuple((*warnings, message)))
                warnings.append(message)
        result = WorkflowResult(str(uuid4()), workflow, True, data, tuple(warnings))
        if key:
            self._idempotent[key] = result
        return result
