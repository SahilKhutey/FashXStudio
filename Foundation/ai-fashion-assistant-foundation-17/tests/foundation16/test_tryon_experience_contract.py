from uuid import uuid4

from schemas.tryon.job import TryOnCreate, TryOnCreateResponse, TryOnStatusResponse
from schemas.tryon.result import TryOnResultMetadata


def test_tryon_create_contract_uses_product_id_only() -> None:
    request = TryOnCreate(product_id=uuid4())
    assert request.product_id
    assert "user_id" not in request.__class__.model_fields


def test_tryon_status_contract_supports_completed_result_delivery() -> None:
    artifact_id = uuid4()
    job_id = uuid4()
    result = TryOnResultMetadata(
        artifact_id=artifact_id,
        quality_status="accepted",
        quality_score=0.93,
        width=1024,
        height=1536,
        size_bytes=100_000,
        content_type="image/jpeg",
        content_sha256="a" * 64,
        result_url="https://signed.example/result.jpg",
    )
    response = TryOnStatusResponse(
        job_id=job_id,
        status="completed",
        result_url=result.result_url,
        model_version="v1",
        pipeline_version="v1",
        attempt_count=1,
        result=result,
    )
    assert response.status == "completed"
    assert response.result_url
    assert response.result is not None


def test_tryon_create_response_supports_cache_hit_without_gpu_work() -> None:
    response = TryOnCreateResponse(
        job_id=uuid4(),
        status="completed",
        cache_hit=True,
        result_url="https://signed.example/result.jpg",
    )
    assert response.cache_hit is True
    assert response.result_url
