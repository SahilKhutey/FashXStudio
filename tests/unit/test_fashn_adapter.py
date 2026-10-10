import io

import httpx
import pytest
from PIL import Image

from fashx.application.ports.tryon import TryOnError, TryOnRequest
from fashx.infrastructure.tryon.fashn_api import FashnApiAdapter


def create_tiny_png() -> bytes:
    img = Image.new("RGB", (32, 32), (200, 100, 50))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


TINY_PNG = create_tiny_png()


def make_adapter(handler, download_handler=None, **kwargs):
    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport, base_url="https://api.fashn.ai/v1")

    dl_handler = download_handler or (lambda req: httpx.Response(200, content=TINY_PNG))
    dl_transport = httpx.MockTransport(dl_handler)
    dl_client = httpx.Client(transport=dl_transport)

    return FashnApiAdapter(
        api_key="test-key-123",
        base_url="https://api.fashn.ai/v1",
        model="tryon-v1.6",
        mode=None,
        client=client,
        download_client=dl_client,
        sleep=lambda s: None,
        **kwargs,
    )


def test_fashn_adapter_happy_path():
    polls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal polls
        if request.url.path == "/v1/run":
            return httpx.Response(200, json={"id": "job-abc-456"})
        if request.url.path == "/v1/status/job-abc-456":
            polls += 1
            if polls == 1:
                return httpx.Response(200, json={"status": "in_queue"})
            if polls == 2:
                return httpx.Response(200, json={"status": "processing"})
            return httpx.Response(
                200, json={"status": "completed", "output": ["https://cdn.fashn.ai/results/out.png"]}
            )
        return httpx.Response(404)

    adapter = make_adapter(handler)
    req = TryOnRequest(person_jpeg=TINY_PNG, garment_jpeg=TINY_PNG, category="tops")
    out = adapter.run(req, deadline_s=10.0)

    assert out.provider == "fashn_api"
    assert out.provider_job_id == "job-abc-456"
    assert out.image_bytes == TINY_PNG
    assert polls == 3


@pytest.mark.parametrize("status_code", [429, 500, 502, 503, 504])
def test_fashn_adapter_retryable_errors(status_code):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code, text="Service busy")

    adapter = make_adapter(handler)
    req = TryOnRequest(person_jpeg=TINY_PNG, garment_jpeg=TINY_PNG)
    with pytest.raises(TryOnError) as exc:
        adapter.submit(req)
    assert exc.value.code == "provider_unavailable"
    assert exc.value.retryable is True


def test_fashn_adapter_auth_error_is_non_retryable():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, text="Unauthorized key")

    adapter = make_adapter(handler)
    req = TryOnRequest(person_jpeg=TINY_PNG, garment_jpeg=TINY_PNG)
    with pytest.raises(TryOnError) as exc:
        adapter.submit(req)
    assert exc.value.code == "provider_auth"
    assert exc.value.retryable is False


def test_fashn_adapter_credits_error_is_non_retryable():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(402, text="Credits exhausted")

    adapter = make_adapter(handler)
    req = TryOnRequest(person_jpeg=TINY_PNG, garment_jpeg=TINY_PNG)
    with pytest.raises(TryOnError) as exc:
        adapter.submit(req)
    assert exc.value.code == "provider_credits"
    assert exc.value.retryable is False


def test_fashn_adapter_status_timeout_is_retryable():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"status": "time_out"})

    adapter = make_adapter(handler)
    with pytest.raises(TryOnError) as exc:
        adapter.collect("job-timeout", deadline_s=10.0)
    assert exc.value.code == "provider_timeout"
    assert exc.value.retryable is True


def test_fashn_adapter_status_failed_is_non_retryable():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"status": "failed", "error": {"name": "NoPersonFound"}})

    adapter = make_adapter(handler)
    with pytest.raises(TryOnError) as exc:
        adapter.collect("job-failed", deadline_s=10.0)
    assert "nopersonfound" in exc.value.code
    assert exc.value.retryable is False


def test_fashn_adapter_ssrf_guard():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, json={"status": "completed", "output": ["https://malicious-host.com/out.png"]}
        )

    adapter = make_adapter(handler)
    with pytest.raises(TryOnError) as exc:
        adapter.collect("job-ssrf", deadline_s=10.0)
    assert exc.value.code == "provider_bad_url"


def test_fashn_adapter_rejects_undecodable_image():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, json={"status": "completed", "output": ["https://cdn.fashn.ai/out.png"]}
        )

    def download_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b"corrupted-not-an-image-payload")

    adapter = make_adapter(handler, download_handler=download_handler)
    with pytest.raises(TryOnError) as exc:
        adapter.collect("job-corrupt", deadline_s=10.0)
    assert exc.value.code == "provider_bad_image"


def test_fashn_adapter_no_auth_header_to_download_client():
    captured_headers = {}

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, json={"status": "completed", "output": ["https://cdn.fashn.ai/out.png"]}
        )

    def download_handler(request: httpx.Request) -> httpx.Response:
        captured_headers.update(request.headers)
        return httpx.Response(200, content=TINY_PNG)

    adapter = make_adapter(handler, download_handler=download_handler)
    adapter.collect("job-headers", deadline_s=10.0)
    assert "authorization" not in captured_headers
