"""Experiment framework for deterministic bucket assignment (Rule 12.4)."""

import hashlib
from typing import Any

# Registry of active experiments (versioned definitions)
ACTIVE_EXPERIMENTS: dict[str, dict[str, Any]] = {
    "widget_cta_v1": {
        "key": "widget_cta_v1",
        "salt": "fashx_exp_salt_cta_2026",
        "enabled": True,
        "split": {"control": 500, "treatment": 500},
    },
    "lighting_guidance_v1": {
        "key": "lighting_guidance_v1",
        "salt": "fashx_exp_salt_lighting_2026",
        "enabled": True,
        "split": {"control": 500, "treatment": 500},
    },
}


def bucket(user_id: str, experiment: str, salt: str, buckets: int = 1000) -> int:
    """Deterministically assign user to integer bucket [0, buckets)."""
    h = hashlib.sha256(f"{salt}:{experiment}:{user_id}".encode()).digest()
    return int.from_bytes(h[:4], "big") % buckets


def assign(user_id: str, exp: dict[str, Any]) -> str:
    """Deterministically assign user to a variant arm according to bucket split."""
    if not exp.get("enabled", False):
        return "control"
    b = bucket(user_id, exp["key"], exp.get("salt", "default_salt"))
    acc = 0
    for name, size in exp.get("split", {}).items():
        acc += size
        if b < acc:
            return name
    return "control"


def get_user_experiments(user_id: str) -> dict[str, str]:
    """Return dictionary of {experiment_key: assigned_variant} for user."""
    return {
        key: assign(user_id, cfg)
        for key, cfg in ACTIVE_EXPERIMENTS.items()
    }
