"""RC12 release policy, capability evaluation, and deterministic rollout engine."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import StrEnum


class ReleaseEnvironment(StrEnum):
    LOCAL = "local"
    TEST = "test"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass(frozen=True)
class Capability:
    name: str
    enabled: bool
    rollout_percent: int = 0
    allowed_environments: tuple[str, ...] = ()
    requires_real_provider: bool = False


@dataclass(frozen=True)
class ReleasePolicy:
    environment: ReleaseEnvironment
    rollout_salt: str
    capabilities: dict[str, Capability]
    real_vto_provider_verified: bool = False


@dataclass(frozen=True)
class CapabilityDecision:
    allowed: bool
    capability: str
    reason: str


def rollout_bucket(user_id: str, capability: str, salt: str = "") -> int:
    """Deterministically maps a user ID and capability to a percentage bucket (0-99)."""
    key = f"{salt}:{capability}:{user_id}".encode()
    return int(hashlib.sha256(key).hexdigest(), 16) % 100


def evaluate_capability(
    policy: ReleasePolicy,
    capability_name: str,
    user_id: str | None = None,
) -> CapabilityDecision:
    """Evaluates whether a capability is permitted for the given environment and user."""
    cap = policy.capabilities.get(capability_name)
    if cap is None:
        return CapabilityDecision(
            allowed=False,
            capability=capability_name,
            reason="unknown_capability",
        )

    if not cap.enabled:
        return CapabilityDecision(
            allowed=False,
            capability=capability_name,
            reason="disabled_by_policy",
        )

    if cap.allowed_environments and policy.environment.value not in cap.allowed_environments:
        return CapabilityDecision(
            allowed=False,
            capability=capability_name,
            reason=f"environment_not_allowed:{policy.environment.value}",
        )

    if cap.requires_real_provider and not policy.real_vto_provider_verified:
        return CapabilityDecision(
            allowed=False,
            capability=capability_name,
            reason="real_provider_not_verified",
        )

    if cap.rollout_percent <= 0:
        return CapabilityDecision(
            allowed=False,
            capability=capability_name,
            reason="rollout_percent_zero",
        )

    if cap.rollout_percent >= 100:
        return CapabilityDecision(
            allowed=True,
            capability=capability_name,
            reason="allowed_full_rollout",
        )

    if user_id is None:
        return CapabilityDecision(
            allowed=False,
            capability=capability_name,
            reason="user_id_required_for_partial_rollout",
        )

    bucket = rollout_bucket(user_id, capability_name, policy.rollout_salt)
    if bucket < cap.rollout_percent:
        return CapabilityDecision(
            allowed=True,
            capability=capability_name,
            reason="allowed_in_rollout_bucket",
        )

    return CapabilityDecision(
        allowed=False,
        capability=capability_name,
        reason="not_in_rollout_bucket",
    )
