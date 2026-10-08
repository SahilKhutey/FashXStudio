from uuid import uuid4

from fastapi.testclient import TestClient

from api.app.main import app
from api.app.auth.dependencies import current_user_id
from api.app.profile.router import get_service as get_profile_service
from api.app.catalog.router import get_repository


class FakeProfileService:
    async def update_profile(self, user_id, **kwargs):
        return user_id

    async def get_profile(self, user_id):
        from types import SimpleNamespace
        return (
            SimpleNamespace(id=user_id, created_at="2026-01-01T00:00:00Z"),
            SimpleNamespace(height_cm=170, weight_kg=65, build="athletic", version=1),
            SimpleNamespace(colors_favored=["black"], colors_avoided=[], categories=["casual"], budget_min=500, budget_max=2000),
        )

    async def get_derived(self, user_id):
        from types import SimpleNamespace
        return (
            SimpleNamespace(height_cm=170, weight_kg=65, build="athletic", version=1),
            SimpleNamespace(colors_favored=["black"], colors_avoided=[], categories=["casual"], budget_min=500, budget_max=2000),
            None,
        )


class FakeCatalogRepository:
    async def search_garments(self, **kwargs):
        from types import SimpleNamespace
        return [SimpleNamespace(id=uuid4(), category="dress", subcategory=None, brand_id=None, version=1)]

    async def get_garment(self, garment_id):
        from types import SimpleNamespace
        return SimpleNamespace(id=garment_id, brand_id=None, category="dress", subcategory=None, version=1)

    async def get_images(self, garment_id):
        return []

    async def get_offers(self, garment_id):
        return []


def override_user():
    return uuid4()


app.dependency_overrides[current_user_id] = override_user
app.dependency_overrides[get_profile_service] = lambda: FakeProfileService()


def test_profile_requires_authentication():
    app.dependency_overrides.pop(current_user_id, None)
    client = TestClient(app)
    response = client.get("/api/v1/profile/me")
    assert response.status_code == 401
    app.dependency_overrides[current_user_id] = override_user


def test_profile_create_contract():
    app.dependency_overrides["_unused"] = lambda: None
    client = TestClient(app)
    response = client.post(
        "/api/v1/profile",
        headers={"X-User-ID": str(override_user())},
        json={"height_cm": 170, "weight_kg": 65, "build": "athletic", "colors_favored": ["black"]},
    )
    assert response.status_code == 201
    assert response.json()["user_id"]
    app.dependency_overrides.pop("_unused", None)


def test_catalog_search_contract_without_db():
    app.dependency_overrides[get_repository] = lambda: FakeCatalogRepository()
    client = TestClient(app)
    response = client.get("/api/v1/catalog/search", headers={"X-User-ID": str(override_user())})
    assert response.status_code == 200
    assert len(response.json()["products"]) == 1
    app.dependency_overrides.pop(get_repository, None)
