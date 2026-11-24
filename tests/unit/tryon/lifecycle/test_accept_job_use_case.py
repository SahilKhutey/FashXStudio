"""Unit tests for AcceptTryOnJobUseCase (Phase 07.4)."""

from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest

from fashx.security.errors import ApiError
from fashx.tryon.application.accept_job import (
    AcceptTryOnCommand,
    AcceptTryOnJobUseCase,
)


class FakeUserRepo:
    def __init__(self, user: object | None = None) -> None:
        self.user = user or SimpleNamespace(id=uuid4(), email="user@example.com")

    async def get_by_id(self, uid: object) -> object | None:
        return self.user


class FakeConsentRepo:
    def __init__(self, has_consent: bool = True) -> None:
        self._has_consent = has_consent

    async def has_consent(self, uid: object, purpose: str) -> bool:
        return self._has_consent


class FakePhotoRepo:
    def __init__(self, photo: object | None = None) -> None:
        self.photo = photo

    async def get_owned(self, photo_id: object, user_id: object) -> object | None:
        if self.photo and self.photo.id == photo_id and self.photo.user_id == user_id:
            return self.photo
        return None


class FakeGarmentRepo:
    def __init__(self, garment: object | None = None) -> None:
        self.garment = garment or SimpleNamespace(
            id=uuid4(),
            category="tops",
            version=1,
            tryon_supported=True,
        )

    async def get_by_id(self, gid: object) -> object | None:
        return self.garment


class FakeProfileUoW:
    def __init__(self, user_id: object, photo_id: object, has_consent: bool = True) -> None:
        self.users = FakeUserRepo(SimpleNamespace(id=user_id))
        self.consents = FakeConsentRepo(has_consent=has_consent)
        self.photos = FakePhotoRepo(
            SimpleNamespace(
                id=photo_id,
                user_id=user_id,
                status="accepted",
                version=1,
                storage_key="u/photo.jpg",
                content_sha256="aabbccddeeff00112233445566778899aabbccddeeff00112233445566778899",
            )
        )

    async def __aenter__(self) -> FakeProfileUoW:
        return self

    async def __aexit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        pass


class FakeCatalogUoW:
    def __init__(self, garment_id: object, category: str = "tops") -> None:
        self.canonical_garments = FakeGarmentRepo(
            SimpleNamespace(
                id=garment_id,
                category=category,
                version=1,
                tryon_supported=True,
            )
        )

    async def __aenter__(self) -> FakeCatalogUoW:
        return self

    async def __aexit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        pass


class FakeJobRepo:
    def __init__(self) -> None:
        self.jobs: dict[tuple[object, str], object] = {}
        self.created_jobs: list[object] = []

    async def get_by_user_and_idempotency(self, user_id: object, key: str) -> object | None:
        return self.jobs.get((user_id, key))

    async def get_by_id(self, jid: object) -> object | None:
        for j in self.jobs.values():
            if j.id == jid:
                return j
        return None

    async def create(self, **kwargs: object) -> object:
        job = SimpleNamespace(
            id=uuid4(),
            status="queued",
            progress_stage="waiting_for_worker",
            artifact_key=kwargs.get("artifact_key"),
            request_hash=kwargs.get("request_hash"),
            user_id=kwargs.get("user_id"),
        )
        self.jobs[(kwargs["user_id"], kwargs["idempotency_key"])] = job
        self.created_jobs.append(job)
        return job


class FakeArtifactRepo:
    def __init__(self) -> None:
        self.artifacts: dict[str, object] = {}

    async def get_by_artifact_key(self, key: str) -> object | None:
        return self.artifacts.get(key)


class FakeSession:
    async def scalar(self, stmt: object) -> object:
        return 0.0

    def add(self, obj: object) -> None:
        pass

    async def flush(self) -> None:
        pass


class FakeTryOnUoW:
    def __init__(self) -> None:
        self.jobs = FakeJobRepo()
        self.artifacts = FakeArtifactRepo()
        self.session = FakeSession()
        self.outbox_messages: list[dict] = []

    async def __aenter__(self) -> FakeTryOnUoW:
        return self

    async def __aexit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        pass

    async def commit(self) -> None:
        pass

    async def rollback(self) -> None:
        pass


async def test_accept_job_happy_path() -> None:
    user_id = uuid4()
    photo_id = uuid4()
    garment_id = uuid4()

    profile_uow = FakeProfileUoW(user_id, photo_id, has_consent=True)
    catalog_uow = FakeCatalogUoW(garment_id, category="tops")
    tryon_uow = FakeTryOnUoW()

    use_case = AcceptTryOnJobUseCase(
        tryon_uow=tryon_uow,
        profile_uow=profile_uow,
        catalog_uow=catalog_uow,
        adapter=SimpleNamespace(provider="mock", model_version="v1", pipeline_version="v1"),
    )
    cmd = AcceptTryOnCommand(
        user_id=user_id,
        product_id=garment_id,
        offer_id=None,
        shopper_asset_id=photo_id,
        garment_asset_id=None,
        idempotency_key="key-001",
    )
    res = await use_case.execute(cmd)

    assert res.status == "queued"
    assert res.progress_stage == "waiting_for_worker"
    assert not res.reused
    assert not res.is_cached
    assert str(res.job_id) in res.status_url


async def test_accept_job_missing_consent_raises_403() -> None:
    user_id = uuid4()
    photo_id = uuid4()
    garment_id = uuid4()

    profile_uow = FakeProfileUoW(user_id, photo_id, has_consent=False)
    catalog_uow = FakeCatalogUoW(garment_id, category="tops")
    tryon_uow = FakeTryOnUoW()

    use_case = AcceptTryOnJobUseCase(
        tryon_uow=tryon_uow,
        profile_uow=profile_uow,
        catalog_uow=catalog_uow,
    )
    cmd = AcceptTryOnCommand(
        user_id=user_id,
        product_id=garment_id,
        offer_id=None,
        shopper_asset_id=photo_id,
        garment_asset_id=None,
        idempotency_key="key-002",
    )
    with pytest.raises(ApiError) as exc:
        await use_case.execute(cmd)
    assert exc.value.status == 403
    assert exc.value.code == "VTO_CONSENT_REQUIRED"


async def test_accept_job_unowned_photo_raises_404() -> None:
    user_id = uuid4()
    photo_id = uuid4()
    garment_id = uuid4()

    profile_uow = FakeProfileUoW(user_id, photo_id, has_consent=True)
    catalog_uow = FakeCatalogUoW(garment_id, category="tops")
    tryon_uow = FakeTryOnUoW()

    use_case = AcceptTryOnJobUseCase(
        tryon_uow=tryon_uow,
        profile_uow=profile_uow,
        catalog_uow=catalog_uow,
    )
    # Different unowned photo ID
    cmd = AcceptTryOnCommand(
        user_id=user_id,
        product_id=garment_id,
        offer_id=None,
        shopper_asset_id=uuid4(),
        garment_asset_id=None,
        idempotency_key="key-003",
    )
    with pytest.raises(ApiError) as exc:
        await use_case.execute(cmd)
    assert exc.value.status == 404
    assert exc.value.code == "IMAGE_NOT_OWNED_OR_NOT_FOUND"


async def test_accept_job_unsupported_category_raises_422() -> None:
    user_id = uuid4()
    photo_id = uuid4()
    garment_id = uuid4()

    profile_uow = FakeProfileUoW(user_id, photo_id, has_consent=True)
    catalog_uow = FakeCatalogUoW(garment_id, category="footwear")
    tryon_uow = FakeTryOnUoW()

    use_case = AcceptTryOnJobUseCase(
        tryon_uow=tryon_uow,
        profile_uow=profile_uow,
        catalog_uow=catalog_uow,
    )
    cmd = AcceptTryOnCommand(
        user_id=user_id,
        product_id=garment_id,
        offer_id=None,
        shopper_asset_id=photo_id,
        garment_asset_id=None,
        idempotency_key="key-004",
    )
    with pytest.raises(ApiError) as exc:
        await use_case.execute(cmd)
    assert exc.value.status == 422
    assert exc.value.code == "UNSUPPORTED_GARMENT_CATEGORY"


async def test_accept_job_idempotency_conflict_raises_409() -> None:
    user_id = uuid4()
    photo_id = uuid4()
    garment_id = uuid4()

    profile_uow = FakeProfileUoW(user_id, photo_id, has_consent=True)
    catalog_uow = FakeCatalogUoW(garment_id, category="tops")
    tryon_uow = FakeTryOnUoW()

    use_case = AcceptTryOnJobUseCase(
        tryon_uow=tryon_uow,
        profile_uow=profile_uow,
        catalog_uow=catalog_uow,
        adapter=SimpleNamespace(provider="mock", model_version="v1", pipeline_version="v1"),
    )
    cmd1 = AcceptTryOnCommand(
        user_id=user_id,
        product_id=garment_id,
        offer_id=None,
        shopper_asset_id=photo_id,
        garment_asset_id=None,
        idempotency_key="reused-key",
    )
    res1 = await use_case.execute(cmd1)
    assert res1.status == "queued"

    # Re-submit with SAME idempotency key but DIFFERENT offer_id -> changes request hash!
    cmd2 = AcceptTryOnCommand(
        user_id=user_id,
        product_id=garment_id,
        offer_id=uuid4(),  # Different!
        shopper_asset_id=photo_id,
        garment_asset_id=None,
        idempotency_key="reused-key",
    )
    with pytest.raises(ApiError) as exc:
        await use_case.execute(cmd2)
    assert exc.value.status == 409
    assert exc.value.code == "IDEMPOTENCY_CONFLICT"
