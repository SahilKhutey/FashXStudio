import io

import httpx
import pytest
from PIL import Image

from fashx.application.ports.tryon import TryOnAdapter, TryOnOutput, TryOnRequest
from fashx.infrastructure.tryon.fashn_api import FashnApiAdapter
from fashx.tryon.adapters.mock_adapter import MockAdapter


def create_valid_jpeg() -> bytes:
    img = Image.new("RGB", (64, 64), (120, 150, 180))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


VALID_JPEG = create_valid_jpeg()


@pytest.fixture(params=["mock", "fashn_api"])
def tryon_adapter(request) -> TryOnAdapter:
    if request.param == "mock":
        return MockAdapter()

    def handler(req: httpx.Request) -> httpx.Response:
        if req.url.path == "/v1/run":
            return httpx.Response(200, json={"id": "job-contract-123"})
        if req.url.path == "/v1/status/job-contract-123":
            return httpx.Response(
                200, json={"status": "completed", "output": ["https://cdn.fashn.ai/out.png"]}
            )
        return httpx.Response(404)

    dl_transport = httpx.MockTransport(lambda req: httpx.Response(200, content=VALID_JPEG))
    transport = httpx.MockTransport(handler)

    return FashnApiAdapter(
        api_key="contract-key",
        base_url="https://api.fashn.ai/v1",
        model="tryon-v1.6",
        client=httpx.Client(transport=transport, base_url="https://api.fashn.ai/v1"),
        download_client=httpx.Client(transport=dl_transport),
        sleep=lambda s: None,
    )


def test_tryon_adapter_contract_run_returns_decodable_image(tryon_adapter):
    req = TryOnRequest(person_jpeg=VALID_JPEG, garment_jpeg=VALID_JPEG, category="tops")
    out = tryon_adapter.run(req)

    assert isinstance(out, TryOnOutput)
    assert out.provider in ("mock", "fashn_api")
    assert len(out.image_bytes) > 0

    # Image must be decodable
    img = Image.open(io.BytesIO(out.image_bytes))
    assert img.size[0] > 0 and img.size[1] > 0


def test_tryon_adapter_contract_submit_and_collect_parity(tryon_adapter):
    req = TryOnRequest(person_jpeg=VALID_JPEG, garment_jpeg=VALID_JPEG, category="tops")
    job_id = tryon_adapter.submit(req)
    assert isinstance(job_id, str)
    assert len(job_id) > 0

    out = tryon_adapter.collect(job_id, deadline_s=10.0)
    assert isinstance(out, TryOnOutput)
    assert out.provider_job_id == job_id
    assert len(out.image_bytes) > 0
