from fashx.core.release_policy import (
    Capability,
    ReleaseEnvironment,
    ReleasePolicy,
    evaluate_capability,
    rollout_bucket,
)


def make_policy(
    *,
    enabled: bool = True,
    rollout: int = 100,
    real_provider: bool = False,
    environment: ReleaseEnvironment = ReleaseEnvironment.STAGING,
) -> ReleasePolicy:
    return ReleasePolicy(
        environment=environment,
        rollout_salt="test-salt",
        real_vto_provider_verified=real_provider,
        capabilities={
            "vto_real": Capability(
                name="vto_real",
                enabled=enabled,
                rollout_percent=rollout,
                allowed_environments=("staging", "production"),
                requires_real_provider=True,
            ),
            "feed_discovery": Capability(
                name="feed_discovery",
                enabled=enabled,
                rollout_percent=rollout,
                allowed_environments=("local", "test", "staging", "production"),
                requires_real_provider=False,
            ),
        },
    )


def test_rollout_bucket_is_deterministic():
    b1 = rollout_bucket(user_id="user-1", capability="feed_discovery", salt="salt-a")
    b2 = rollout_bucket(user_id="user-1", capability="feed_discovery", salt="salt-a")
    assert b1 == b2
    assert 0 <= b1 < 100

    b3 = rollout_bucket(user_id="user-2", capability="feed_discovery", salt="salt-a")
    # Different users can fall into different buckets
    assert isinstance(b3, int)


def test_unknown_capability_is_denied():
    policy = make_policy()
    decision = evaluate_capability(policy, "unknown_feature")
    assert not decision.allowed
    assert decision.reason == "unknown_capability"


def test_disabled_capability_is_denied():
    policy = make_policy(enabled=False)
    decision = evaluate_capability(policy, "feed_discovery")
    assert not decision.allowed
    assert decision.reason == "disabled_by_policy"


def test_environment_restriction_denies():
    policy = make_policy(environment=ReleaseEnvironment.LOCAL)
    # vto_real is only allowed in staging and production
    decision = evaluate_capability(policy, "vto_real")
    assert not decision.allowed
    assert "environment_not_allowed" in decision.reason


def test_real_provider_required_denies_when_unverified():
    policy = make_policy(real_provider=False)
    decision = evaluate_capability(policy, "vto_real")
    assert not decision.allowed
    assert decision.reason == "real_provider_not_verified"


def test_real_provider_allowed_when_verified():
    policy = make_policy(real_provider=True, rollout=100)
    decision = evaluate_capability(policy, "vto_real")
    assert decision.allowed
    assert decision.reason == "allowed_full_rollout"


def test_zero_rollout_denies():
    policy = make_policy(rollout=0)
    decision = evaluate_capability(policy, "feed_discovery", user_id="user-1")
    assert not decision.allowed
    assert decision.reason == "rollout_percent_zero"


def test_partial_rollout_requires_user_id():
    policy = make_policy(rollout=50)
    decision = evaluate_capability(policy, "feed_discovery", user_id=None)
    assert not decision.allowed
    assert decision.reason == "user_id_required_for_partial_rollout"


def test_partial_rollout_cohort_stability():
    policy = make_policy(rollout=50)
    d1 = evaluate_capability(policy, "feed_discovery", user_id="user-cohort-a")
    d2 = evaluate_capability(policy, "feed_discovery", user_id="user-cohort-a")
    assert d1.allowed == d2.allowed
    assert d1.reason == d2.reason
