from fastapi import APIRouter
from fastapi.testclient import TestClient

from api.app.main import app

router = APIRouter(prefix="/api/v1/test-errors")


@router.get("/typed")
async def typed(value: int):
    return {"value": value}


app.include_router(router)


def test_validation_errors_use_standard_envelope() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/test-errors/typed", params={"value": "bad"})
    assert response.status_code == 400
    payload = response.json()
    assert payload["error"]["code"] == "validation_error"
    assert payload["error"]["field"] == "value"
