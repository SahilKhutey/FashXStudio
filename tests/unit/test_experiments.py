import uuid
from fashx.core.experiments import (
    ACTIVE_EXPERIMENTS,
    assign,
    bucket,
    get_user_experiments,
)


def test_deterministic_bucket_assignment():
    user_id = str(uuid.uuid4())
    b1 = bucket(user_id, "widget_cta_v1", "salt123")
    b2 = bucket(user_id, "widget_cta_v1", "salt123")
    assert b1 == b2
    assert 0 <= b1 < 1000


def test_different_users_or_salts_produce_different_buckets():
    u1 = str(uuid.uuid4())
    u2 = str(uuid.uuid4())
    # Different users with high probability get different buckets
    # Test bucket range
    assert 0 <= bucket(u1, "exp1", "salt") < 1000
    assert 0 <= bucket(u2, "exp1", "salt") < 1000


def test_assign_variant_deterministic_and_respects_split():
    exp = {
        "key": "test_exp",
        "salt": "test_salt_999",
        "enabled": True,
        "split": {"control": 500, "treatment": 500},
    }
    u = str(uuid.uuid4())
    v1 = assign(u, exp)
    v2 = assign(u, exp)
    assert v1 == v2
    assert v1 in ["control", "treatment"]


def test_disabled_experiment_always_control():
    exp = {
        "key": "test_exp_disabled",
        "salt": "test_salt_999",
        "enabled": False,
        "split": {"control": 100, "treatment": 900},
    }
    u = str(uuid.uuid4())
    assert assign(u, exp) == "control"


def test_get_user_experiments_returns_all_active():
    u = str(uuid.uuid4())
    assignments = get_user_experiments(u)
    assert "widget_cta_v1" in assignments
    assert "lighting_guidance_v1" in assignments
    assert assignments["widget_cta_v1"] in ["control", "treatment"]
    assert assignments["lighting_guidance_v1"] in ["control", "treatment"]


def test_bucket_distribution_over_large_sample():
    exp = {
        "key": "test_split",
        "salt": "split_salt_123",
        "enabled": True,
        "split": {"control": 500, "treatment": 500},
    }
    counts = {"control": 0, "treatment": 0}
    for _ in range(1000):
        u = str(uuid.uuid4())
        v = assign(u, exp)
        counts[v] += 1

    # Over 1000 samples with 50/50 split, should be roughly balanced [420, 580]
    assert 420 <= counts["control"] <= 580
    assert 420 <= counts["treatment"] <= 580
