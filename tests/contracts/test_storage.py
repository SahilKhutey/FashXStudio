import pytest
from moto import mock_aws

from fashx.infrastructure.storage.local import LocalStorage
from fashx.infrastructure.storage.s3 import S3Storage


@pytest.fixture(params=["local", "s3"])
def storage(request, tmp_path):
    if request.param == "local":
        yield LocalStorage(tmp_path)
    else:
        with mock_aws():
            import boto3

            boto3.client("s3", region_name="us-east-1").create_bucket(Bucket="test-bucket")
            yield S3Storage("test-bucket", None, "us-east-1", "x", "x")


def test_put_get_exists_delete(storage):
    key = "u/user-1/photos/p1.jpg"
    data = b"\xff\xd8\xff\xe0testjpeg"

    assert not storage.exists(key)
    storage.put(key, data, "image/jpeg")
    assert storage.exists(key)
    assert storage.get(key) == data

    storage.delete(key)
    assert not storage.exists(key)


def test_delete_prefix_removes_all_and_only_prefix(storage):
    storage.put("u/user-1/photos/p1.jpg", b"photo1", "image/jpeg")
    storage.put("u/user-1/tryon/t1.jpg", b"tryon1", "image/jpeg")
    storage.put("u/user-2/photos/p2.jpg", b"photo2", "image/jpeg")
    storage.put("catalog/garments/g1.jpg", b"garment1", "image/jpeg")

    deleted = storage.delete_prefix("u/user-1/")
    assert deleted == 2
    assert not storage.exists("u/user-1/photos/p1.jpg")
    assert not storage.exists("u/user-1/tryon/t1.jpg")
    assert storage.exists("u/user-2/photos/p2.jpg")
    assert storage.exists("catalog/garments/g1.jpg")


def test_list_prefix_paginates_over_1000(storage):
    # Insert 1005 keys to trigger S3 ContinuationToken pagination
    for i in range(1005):
        storage.put(f"bulk/item-{i:04d}.bin", b"x", "application/octet-stream")

    keys = storage.list_prefix("bulk/")
    assert len(keys) == 1005
    assert "bulk/item-0000.bin" in keys
    assert "bulk/item-1004.bin" in keys

    deleted = storage.delete_prefix("bulk/")
    assert deleted == 1005
    assert len(storage.list_prefix("bulk/")) == 0


def test_signed_url_is_generated_and_not_stored(storage):
    key = "u/user-1/photos/photo.jpg"
    storage.put(key, b"data", "image/jpeg")

    url = storage.signed_get_url(key, ttl_s=300)
    assert key in url
    assert ("sig=" in url or "X-Amz-Signature=" in url or "AWSAccessKeyId=" in url)
