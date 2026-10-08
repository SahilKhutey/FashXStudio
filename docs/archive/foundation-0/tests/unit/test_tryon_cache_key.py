from uuid import uuid4

from api.app.tryon.cache_key import compute_tryon_cache_key


def test_tryon_cache_key_deterministic() -> None:
    garment_id = uuid4()
    key1 = compute_tryon_cache_key(
        user_photo_hash="photo-hash-12345",
        garment_id=garment_id,
        garment_version=1,
        model_version="vto-v1",
        pipeline_version="pipe-v1",
        render_config={"resolution": "1024x1024", "steps": 30},
    )
    key2 = compute_tryon_cache_key(
        user_photo_hash="photo-hash-12345",
        garment_id=garment_id,
        garment_version=1,
        model_version="vto-v1",
        pipeline_version="pipe-v1",
        render_config={"steps": 30, "resolution": "1024x1024"},  # Reversed order
    )

    assert key1 == key2
    assert len(key1) == 64  # Valid SHA-256 hex string


def test_tryon_cache_key_invalidates_on_garment_version_change() -> None:
    garment_id = uuid4()
    key_v1 = compute_tryon_cache_key(
        user_photo_hash="photo-hash-12345",
        garment_id=garment_id,
        garment_version=1,
        model_version="vto-v1",
        pipeline_version="pipe-v1",
    )
    key_v2 = compute_tryon_cache_key(
        user_photo_hash="photo-hash-12345",
        garment_id=garment_id,
        garment_version=2,  # Enriched or evolved
        model_version="vto-v1",
        pipeline_version="pipe-v1",
    )

    assert key_v1 != key_v2


def test_tryon_cache_key_invalidates_on_photo_or_model_change() -> None:
    garment_id = uuid4()
    key_base = compute_tryon_cache_key(
        user_photo_hash="photo-hash-A",
        garment_id=garment_id,
        garment_version=1,
        model_version="vto-v1",
        pipeline_version="pipe-v1",
    )
    key_diff_photo = compute_tryon_cache_key(
        user_photo_hash="photo-hash-B",
        garment_id=garment_id,
        garment_version=1,
        model_version="vto-v1",
        pipeline_version="pipe-v1",
    )
    key_diff_model = compute_tryon_cache_key(
        user_photo_hash="photo-hash-A",
        garment_id=garment_id,
        garment_version=1,
        model_version="vto-v2-prod",
        pipeline_version="pipe-v1",
    )

    assert key_base != key_diff_photo
    assert key_base != key_diff_model
