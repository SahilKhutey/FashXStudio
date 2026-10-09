import base64
import io
from uuid import UUID

from PIL import Image

from fashx.infrastructure.storage.local import LocalStorage


def create_jpeg_bytes() -> bytes:
    img = Image.new("RGB", (600, 800), (140, 120, 105))
    for x in range(300):
        for y in range(800):
            img.putpixel((x, y), (100, 80, 65))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def test_photo_upload_and_signed_url_flow(client_a, tmp_path):
    storage = LocalStorage(tmp_path)
    from fashx.core.dependencies import get_storage
    from fashx.profile.router import get_profile_uow

    photo_bytes = create_jpeg_bytes()
    photo_b64 = base64.b64encode(photo_bytes).decode("ascii")

    # Mock in-memory uow to test API flow without external db
    class MockPhoto:
        def __init__(self, id, user_id, storage_key):
            self.id = id
            self.user_id = user_id
            self.storage_key = storage_key
            self.photo_type = "tryon_reference"
            self.status = "accepted"
            self.reject_reason = None

    class MockUser:
        def __init__(self, id):
            self.id = id

    class MockConsent:
        granted = True

    class MockUoW:
        def __init__(self):
            self.photos_store = {}
            self.media_store = {}

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def commit(self):
            pass

        async def flush(self):
            pass

        class MockUserRepo:
            async def get_by_id(self, uid):
                return MockUser(uid)

        class MockConsentRepo:
            async def get_by_user_and_type(self, uid, dtype):
                return MockConsent()

        class MockPhotoRepo:
            def __init__(self, parent):
                self.parent = parent

            def add(self, p):
                self.parent.photos_store[p.id] = p

            async def get_by_id(self, pid):
                return self.parent.photos_store.get(pid)

        class MockMediaRepo:
            def __init__(self, parent):
                self.parent = parent

            def add(self, m):
                self.parent.media_store[m.id] = m

            async def get_by_id_and_user(self, mid, uid):
                return self.parent.media_store.get(mid)

        @property
        def users(self):
            return self.MockUserRepo()

        @property
        def consents(self):
            return self.MockConsentRepo()

        @property
        def photos(self):
            return self.MockPhotoRepo(self)

        @property
        def media(self):
            return self.MockMediaRepo(self)

    uow = MockUoW()
    client_a.app.dependency_overrides[get_storage] = lambda: storage
    client_a.app.dependency_overrides[get_profile_uow] = lambda: uow

    try:
        me_res = client_a.get("/api/v1/me")
        user_id = UUID(me_res.json()["user_id"])

        # 1. Upload photo
        upload_res = client_a.post(
            f"/api/v1/profile/{user_id}/photos",
            json={"photo_type": "tryon_reference", "photo_b64": photo_b64},
        )
        assert upload_res.status_code == 201
        upload_data = upload_res.json()
        photo_id = upload_data["photo_id"]
        storage_key = upload_data["storage_key"]
        assert storage_key.startswith(f"u/{user_id}/photos/")
        assert storage.exists(storage_key)

        # 2. Get signed URL
        url_res = client_a.get(
            f"/api/v1/profile/{user_id}/photos/{photo_id}/url",
        )
        assert url_res.status_code == 200
        signed_url = url_res.json()["url"]
        assert storage_key in signed_url

        # 3. Retrieve file via dev-files route
        # Strip host prefix
        dev_path = signed_url.split("127.0.0.1:8000")[-1]
        fetch_res = client_a.get(dev_path)
        assert fetch_res.status_code == 200
        assert fetch_res.content == storage.get(storage_key)

        # 4. Bad signature returns 403
        bad_sig_path = dev_path.replace("sig=", "sig=invalid")
        bad_res = client_a.get(bad_sig_path)
        assert bad_res.status_code == 403

        # 5. Expired URL returns 403
        expired_url = storage.signed_get_url(storage_key, ttl_s=-10)
        exp_path = expired_url.split("127.0.0.1:8000")[-1]
        exp_res = client_a.get(exp_path)
        assert exp_res.status_code == 403

    finally:
        client_a.app.dependency_overrides.pop(get_storage, None)
        client_a.app.dependency_overrides.pop(get_profile_uow, None)
