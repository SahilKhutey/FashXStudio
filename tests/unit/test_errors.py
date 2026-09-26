from fastapi import APIRouter
from fastapi.testclient import TestClient

from api.app.core.errors import (
    ConsentRequiredError,
    DuplicateEntityError,
    EntityNotFoundError,
    IdempotencyConflictError,
    ValidationError,
)
from api.app.main import app

router = APIRouter(prefix="/api/v1/test-errors")


@router.get("/typed")
async def typed(value: int):
    return {"value": value}


@router.get("/not-found")
async def trigger_not_found():
    raise EntityNotFoundError("User", "12345")


@router.get("/consent")
async def trigger_consent():
    raise ConsentRequiredError("measurements")


@router.get("/duplicate")
async def trigger_duplicate():
    raise DuplicateEntityError("Brand", "name", "Zara")


@router.get("/conflict")
async def trigger_conflict():
    raise IdempotencyConflictError("Request in flight")


@router.get("/domain-val")
async def trigger_domain_val():
    raise ValidationError("Invalid height measurement", field="height_cm")


app.include_router(router)


def test_validation_errors_use_standard_envelope() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/test-errors/typed", params={"value": "bad"})
    assert response.status_code == 400
    payload = response.json()
    assert payload["error"]["code"] == "validation_error"
    assert payload["error"]["field"] == "value"


def test_entity_not_found_returns_404() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/test-errors/not-found")
    assert response.status_code == 404
    payload = response.json()
    assert payload["error"]["code"] == "entity_not_found"
    assert "User with identifier '12345' was not found" in payload["error"]["message"]


def test_consent_required_returns_403() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/test-errors/consent")
    assert response.status_code == 403
    payload = response.json()
    assert payload["error"]["code"] == "consent_required"


def test_duplicate_entity_returns_409() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/test-errors/duplicate")
    assert response.status_code == 409
    payload = response.json()
    assert payload["error"]["code"] == "duplicate_entity"
    assert payload["error"]["field"] == "name"


def test_idempotency_conflict_returns_409() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/test-errors/conflict")
    assert response.status_code == 409
    payload = response.json()
    assert payload["error"]["code"] == "idempotency_conflict"


def test_domain_validation_returns_422() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/test-errors/domain-val")
    assert response.status_code == 422
    payload = response.json()
    assert payload["error"]["code"] == "validation_error"
    assert payload["error"]["field"] == "height_cm"
