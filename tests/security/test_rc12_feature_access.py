"""RC12 feature capability access and security tests."""
from __future__ import annotations

from fashx.core.release_policy import (
    Capability,
    ReleaseEnvironment,
    ReleasePolicy,
    evaluate_capability,
)


def test_client_cannot_enable_server_capability():
    policy = ReleasePolicy(
        environment=ReleaseEnvironment.PRODUCTION,
        rollout_salt="prod-salt-123",
        real_vto_provider_verified=False,
        capabilities={
            "admin_debug": Capability(
                name="admin_debug",
                enabled=False,
                rollout_percent=0,
                allowed_environments=("local", "test"),
            ),
            "vto_real": Capability(
                name="vto_real",
                enabled=True,
                rollout_percent=100,
                allowed_environments=("production",),
                requires_real_provider=True,
            ),
        },
    )

    # Disabled capability is strictly blocked
    decision = evaluate_capability(policy, "admin_debug", user_id="attacker-user")
    assert not decision.allowed
    assert decision.reason == "disabled_by_policy"

    # Capability requiring real provider is blocked if provider unverified
    decision_vto = evaluate_capability(policy, "vto_real", user_id="attacker-user")
    assert not decision_vto.allowed
    assert decision_vto.reason == "real_provider_not_verified"


def test_tampered_capability_name_fails_closed():
    policy = ReleasePolicy(
        environment=ReleaseEnvironment.PRODUCTION,
        rollout_salt="prod-salt-123",
        capabilities={},
    )
    decision = evaluate_capability(policy, "unregistered_injection_attempt")
    assert not decision.allowed
    assert decision.reason == "unknown_capability"
