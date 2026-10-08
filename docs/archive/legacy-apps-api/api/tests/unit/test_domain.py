"""
Unit Tests: Pure Domain Rules (Rule I03)
Zero database or network dependencies.
"""

from app.domain.tryon_keys import compute_tryon_artifact_key


def test_tryon_artifact_key_determinism():
    """Identical parameters must always produce the exact same SHA-256 hash."""
    key1 = compute_tryon_artifact_key(
        user_photo_version_hash="photo_hash_abc123",
        canonical_garment_version=1,
        model_adapter_id="idm_vton_v1",
        model_weights_version="weights_2026_08",
        preprocessing_version="sam_bisenet_v2",
        render_config_hash="default_1024x768",
    )

    key2 = compute_tryon_artifact_key(
        user_photo_version_hash="photo_hash_abc123",
        canonical_garment_version=1,
        model_adapter_id="idm_vton_v1",
        model_weights_version="weights_2026_08",
        preprocessing_version="sam_bisenet_v2",
        render_config_hash="default_1024x768",
    )

    assert key1 == key2
    assert len(key1) == 64  # SHA-256 hex digest length


def test_tryon_artifact_key_invalidates_on_model_update():
    """Updating the model weights version must produce a different cache key (Rule I09)."""
    old_key = compute_tryon_artifact_key(
        user_photo_version_hash="photo_hash_abc123",
        canonical_garment_version=1,
        model_adapter_id="idm_vton_v1",
        model_weights_version="weights_2026_08",
        preprocessing_version="sam_bisenet_v2",
        render_config_hash="default_1024x768",
    )

    new_key = compute_tryon_artifact_key(
        user_photo_version_hash="photo_hash_abc123",
        canonical_garment_version=1,
        model_adapter_id="idm_vton_v1",
        model_weights_version="weights_2026_10",  # Upgraded weights
        preprocessing_version="sam_bisenet_v2",
        render_config_hash="default_1024x768",
    )

    assert old_key != new_key


def test_tryon_artifact_key_invalidates_on_garment_version_update():
    """Updating the canonical garment version must produce a different cache key."""
    key_v1 = compute_tryon_artifact_key(
        user_photo_version_hash="photo_hash_abc123",
        canonical_garment_version=1,
        model_adapter_id="idm_vton_v1",
        model_weights_version="weights_2026_08",
        preprocessing_version="sam_bisenet_v2",
        render_config_hash="default_1024x768",
    )

    key_v2 = compute_tryon_artifact_key(
        user_photo_version_hash="photo_hash_abc123",
        canonical_garment_version=2,  # New garment version
        model_adapter_id="idm_vton_v1",
        model_weights_version="weights_2026_08",
        preprocessing_version="sam_bisenet_v2",
        render_config_hash="default_1024x768",
    )

    assert key_v1 != key_v2
