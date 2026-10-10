from uuid import uuid4

import pytest

from fashx.security.errors import ApiError
from fashx.tryon.application.submit_job import SubmitTryOnJobCommand, SubmitTryOnJobUseCase


class MockGarment:
    def __init__(self, garment_id, category="tops", tryon_supported=True):
        self.id = garment_id
        self.category = category
        self.tryon_supported = tryon_supported
        self.version = 1


class MockUserPhoto:
    def __init__(self, pid):
        self.id = pid
        self.status = "accepted"
        self.storage_key = "u/alice/photo/p1.jpg"


class MockProfileUoW:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    class Users:
        async def get_by_id(self, uid):
            return object()

    class Consents:
        async def has_consent(self, uid, ctype):
            return True

    class Photos:
        async def get_active_photo(self, uid, ptype):
            return MockUserPhoto(uuid4())

    users = Users()
    consents = Consents()
    photos = Photos()


class MockCatalogUoW:
    def __init__(self, garment):
        self._garment = garment

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    class CanonicalGarments:
        def __init__(self, garment):
            self._garment = garment

        async def get_by_id(self, gid):
            return self._garment

    @property
    def canonical_garments(self):
        return self.CanonicalGarments(self._garment)


class MockTryOnUoW:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    class Jobs:
        async def get_by_user_and_idempotency(self, uid, ikey):
            return None

        def add(self, j):
            pass

    class Artifacts:
        async def get_by_artifact_key(self, akey):
            return None

    jobs = Jobs()
    artifacts = Artifacts()


@pytest.mark.asyncio
async def test_capability_gating_rejects_unsupported_flag():
    garment_id = uuid4()
    garment = MockGarment(garment_id, category="tops", tryon_supported=False)

    use_case = SubmitTryOnJobUseCase(
        tryon_uow=MockTryOnUoW(),
        profile_uow=MockProfileUoW(),
        catalog_uow=MockCatalogUoW(garment),
    )

    with pytest.raises(ApiError) as exc:
        await use_case.execute(
            SubmitTryOnJobCommand(
                user_id=uuid4(),
                garment_id=garment_id,
                idempotency_key="idemp-gate-1",
            )
        )
    assert exc.value.status == 422
    assert exc.value.code == "unsupported_garment"


@pytest.mark.asyncio
async def test_capability_gating_rejects_unsupported_category(monkeypatch):
    monkeypatch.setenv("TRYON_SUPPORTED_CATEGORIES", '["tops","bottoms"]')
    garment_id = uuid4()
    # Complex unanchored drape item not in tops/bottoms
    garment = MockGarment(garment_id, category="saree", tryon_supported=True)

    use_case = SubmitTryOnJobUseCase(
        tryon_uow=MockTryOnUoW(),
        profile_uow=MockProfileUoW(),
        catalog_uow=MockCatalogUoW(garment),
    )

    with pytest.raises(ApiError) as exc:
        await use_case.execute(
            SubmitTryOnJobCommand(
                user_id=uuid4(),
                garment_id=garment_id,
                idempotency_key="idemp-gate-2",
            )
        )
    assert exc.value.status == 422
    assert exc.value.code == "unsupported_garment"
