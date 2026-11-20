from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Any, Protocol

from .policy import validate_model_attributes


class ModelProviderError(Exception):
    """Raised when an external AI model provider call fails."""

    def __init__(self, message: str, is_retryable: bool = True) -> None:
        super().__init__(message)
        self.is_retryable = is_retryable


@dataclass(frozen=True)
class ModelRunMetadata:
    provider: str
    model_id: str
    model_version: str
    latency_ms: int
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    cost_usd: float | None = None


class TextEnrichmentProvider(Protocol):
    """Protocol for text-based AI attribute extraction models."""

    async def extract(
        self,
        title: str,
        description: str | None,
        taxonomy_version: str,
    ) -> tuple[dict[str, Any], ModelRunMetadata]:
        ...


class MockTextEnrichmentProvider:
    """Deterministic, high-accuracy mock AI provider for testing and validation."""

    def __init__(
        self,
        canned_attributes: dict[str, Any] | None = None,
        latency_ms: int = 15,
        fail_with_retryable: bool = False,
    ) -> None:
        self.canned_attributes = canned_attributes
        self.latency_ms = latency_ms
        self.fail_with_retryable = fail_with_retryable
        self.call_count = 0

    async def extract(
        self,
        title: str,
        description: str | None,
        taxonomy_version: str,
    ) -> tuple[dict[str, Any], ModelRunMetadata]:
        self.call_count += 1
        if self.fail_with_retryable:
            raise ModelProviderError("Mock provider transient network timeout", is_retryable=True)

        if self.canned_attributes is not None:
            attrs = dict(self.canned_attributes)
        else:
            # Deterministic text heuristic simulation
            text = f"{title} {description or ''}".lower()
            attrs = {}
            if "casual" in text:
                attrs["occasion"] = "casual"
            elif "formal" in text:
                attrs["occasion"] = "formal"
            elif "festive" in text:
                attrs["occasion"] = "festive"

            if "minimal" in text:
                attrs["style_descriptors"] = ["minimal"]

        meta = ModelRunMetadata(
            provider="mock-ai",
            model_id="mock-fashion-llm",
            model_version="1.0.0",
            latency_ms=self.latency_ms,
            prompt_tokens=len(title.split()),
            completion_tokens=len(attrs),
            cost_usd=0.0,
        )
        return attrs, meta


class ModelGateway:
    """Provider-agnostic model gateway with timeout, bounded retries, and strict validation."""

    def __init__(
        self,
        text_provider: TextEnrichmentProvider | None = None,
        max_retries: int = 2,
        timeout_seconds: float = 5.0,
    ) -> None:
        self.text_provider = text_provider or MockTextEnrichmentProvider()
        self.max_retries = max_retries
        self.timeout_seconds = timeout_seconds

    async def extract_text_attributes(
        self,
        title: str,
        description: str | None,
        taxonomy_version: str,
    ) -> tuple[dict[str, Any], ModelRunMetadata]:
        """Call text AI model with bounded retry and strict policy enforcement."""
        last_error: Exception | None = None
        start_time = time.perf_counter()

        for attempt in range(self.max_retries + 1):
            try:
                attrs, meta = await asyncio.wait_for(
                    self.text_provider.extract(title, description, taxonomy_version),
                    timeout=self.timeout_seconds,
                )

                # Gate: Immediately validate that model output does NOT contain forbidden source-only fields
                validate_model_attributes(attrs)

                return attrs, meta
            except (TimeoutError, ModelProviderError) as e:
                last_error = e
                is_retryable = getattr(e, "is_retryable", True)
                if not is_retryable or attempt >= self.max_retries:
                    break
                await asyncio.sleep(0.05 * (2**attempt))
            except Exception as e:
                # Policy or non-retryable errors break immediately
                raise e

        elapsed_ms = int((time.perf_counter() - start_time) * 1000)
        raise ModelProviderError(
            f"AI model extraction failed after {self.max_retries + 1} attempts ({elapsed_ms}ms): {last_error}",
            is_retryable=False,
        )
