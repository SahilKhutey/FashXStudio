from unittest.mock import MagicMock

import httpx
import pytest

from fashx.application.ports.tryon import TryOnError, TryOnRequest
from fashx.infrastructure.tryon.fashn_api import FashnApiAdapter


def _valid_image_bytes():
    from io import BytesIO

    from PIL import Image

    img = Image.new("RGB", (300, 400), color="blue")
    buf = BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def test_fashn_api_metrics_submit_and_succeed(monkeypatch):
    emitted = []

    def mock_emit_metric(name, value, unit, **kwargs):
        emitted.append((name, value, unit, kwargs))
        return {}

    monkeypatch.setattr("fashx.infrastructure.tryon.fashn_api.emit_metric", mock_emit_metric)

    mock_http = MagicMock()
    mock_http.post.return_value = httpx.Response(200, json={"id": "fashn-job-123"})
    mock_http.get.return_value = httpx.Response(
        200, json={"status": "completed", "output": ["https://cdn.fashn.ai/result.jpg"]}
    )

    mock_dl = MagicMock()
    mock_dl.get.return_value = httpx.Response(200, content=_valid_image_bytes())

    adapter = FashnApiAdapter(
        api_key="fa_test_key",
        client=mock_http,
        download_client=mock_dl,
        environment="staging",
    )

    req = TryOnRequest(
        person_jpeg=_valid_image_bytes(),
        garment_jpeg=_valid_image_bytes(),
        category="tops",
    )

    # 1. Submit
    job_id = adapter.submit(req)
    assert job_id == "fashn-job-123"
    assert any(m[0] == "VTOJobSubmitted" for m in emitted)

    # 2. Collect
    emitted.clear()
    out = adapter.collect(job_id, deadline_s=5.0)
    assert out is not None
    assert any(m[0] == "VTOJobSucceeded" for m in emitted)
    assert any(m[0] == "VTOProviderLatency" for m in emitted)
    assert any(m[0] == "VTOProviderCostEstimate" for m in emitted)


def test_fashn_api_metrics_timeout(monkeypatch):
    emitted = []

    def mock_emit_metric(name, value, unit, **kwargs):
        emitted.append((name, value, unit, kwargs))
        return {}

    monkeypatch.setattr("fashx.infrastructure.tryon.fashn_api.emit_metric", mock_emit_metric)

    mock_http = MagicMock()
    mock_http.get.return_value = httpx.Response(200, json={"status": "in_queue"})

    adapter = FashnApiAdapter(
        api_key="fa_test_key",
        client=mock_http,
        environment="staging",
    )

    with pytest.raises(TryOnError, match="provider_timeout"):
        adapter.collect("fashn-job-timeout", deadline_s=-1.0)

    assert any(m[0] == "VTOProviderTimeout" for m in emitted)
    assert any(m[0] == "VTOJobFailed" for m in emitted)


def test_fashn_api_metrics_rate_limit_and_auth_failure(monkeypatch):
    emitted = []

    def mock_emit_metric(name, value, unit, **kwargs):
        emitted.append((name, value, unit, kwargs))
        return {}

    monkeypatch.setattr("fashx.infrastructure.tryon.fashn_api.emit_metric", mock_emit_metric)

    adapter = FashnApiAdapter(
        api_key="fa_test_key",
        environment="staging",
    )

    # 1. Rate limit (429)
    with pytest.raises(TryOnError):
        raise adapter._from_http(429, "Too Many Requests")
    assert any(m[0] == "VTOProviderRateLimit" for m in emitted)
    assert any(m[0] == "VTOJobFailed" for m in emitted)

    # 2. Auth failure (401)
    emitted.clear()
    with pytest.raises(TryOnError):
        raise adapter._from_http(401, "Unauthorized")
    assert any(m[0] == "VTOProviderAuthFailure" for m in emitted)
    assert any(m[0] == "VTOJobFailed" for m in emitted)
