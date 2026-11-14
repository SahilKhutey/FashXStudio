import pytest

from fashx.infrastructure.storage.s3 import S3Storage


def test_s3_storage_metrics_on_put_and_delete(monkeypatch):
    emitted = []

    def mock_emit_metric(name, value, unit, **kwargs):
        emitted.append((name, value, unit, kwargs))
        return {}

    monkeypatch.setattr("fashx.infrastructure.storage.s3.emit_metric", mock_emit_metric)

    storage = S3Storage(
        bucket="test-bucket",
        endpoint_url="http://localhost:9000",
        environment="test",
    )

    class MockClient:
        def put_object(self, **kwargs):
            return {}

        def get_object(self, **kwargs):
            from io import BytesIO
            return {"Body": BytesIO(b"test-bytes-content")}

        def delete_object(self, **kwargs):
            return {}

    storage._c = MockClient()

    # 1. Put object
    storage.put("products/p1/img.webp", b"1234567890", content_type="image/webp")
    assert any(m[0] == "StorageUploadCount" for m in emitted)
    assert any(m[0] == "StorageBytesUploaded" and m[1] == 10.0 for m in emitted)
    assert any(m[0] == "StorageOperationLatency" for m in emitted)

    # Verify no raw key or user ID in dimensions
    for item in emitted:
        dims = item[3].get("dimensions", {})
        assert "products/p1/img.webp" not in str(dims)
        assert "key" not in dims

    # 2. Get object
    emitted.clear()
    data = storage.get("products/p1/img.webp")
    assert data == b"test-bytes-content"
    assert any(m[0] == "StorageDownloadCount" for m in emitted)
    assert any(m[0] == "StorageBytesDownloaded" for m in emitted)

    # 3. Delete object
    emitted.clear()
    storage.delete("products/p1/img.webp")
    assert any(m[0] == "StorageDeleteCount" for m in emitted)
    assert any(m[0] == "StorageOperationLatency" for m in emitted)


def test_s3_storage_metrics_on_failure(monkeypatch):
    emitted = []

    def mock_emit_metric(name, value, unit, **kwargs):
        emitted.append((name, value, unit, kwargs))
        return {}

    monkeypatch.setattr("fashx.infrastructure.storage.s3.emit_metric", mock_emit_metric)

    storage = S3Storage(
        bucket="test-bucket",
        endpoint_url="http://localhost:9000",
        environment="staging",
    )

    class FailingClient:
        def put_object(self, **kwargs):
            raise RuntimeError("S3 Put Failed")

        def delete_object(self, **kwargs):
            raise RuntimeError("S3 Delete Failed")

    storage._c = FailingClient()

    # Put failure
    with pytest.raises(RuntimeError, match="S3 Put Failed"):
        storage.put("tryon/t1/out.webp", b"123")
    assert any(m[0] == "StorageUploadErrors" for m in emitted)

    # Delete failure
    emitted.clear()
    with pytest.raises(RuntimeError, match="S3 Delete Failed"):
        storage.delete("tryon/t1/out.webp")
    assert any(m[0] == "StorageDeleteErrors" for m in emitted)
