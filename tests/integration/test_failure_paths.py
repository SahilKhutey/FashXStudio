import json

import pytest
from starlette.requests import Request

from app.core.errors import (
    ConflictError,
    DependencyError,
    NotFoundError,
    ValidationError,
)
from app.integration.errors import core_error_handler
from fashx.security.authorization import Actor, require_role
from fashx.security.validation import SystemConfig


@pytest.mark.asyncio
async def test_core_error_handler_status_codes():
    scope = {"type": "http", "method": "GET", "path": "/test"}
    req = Request(scope)

    # Validation Error -> 422
    err_val = ValidationError("Invalid field input", details={"field": "sku"})
    res_val = await core_error_handler(req, err_val)
    assert res_val.status_code == 422
    body_val = json.loads(res_val.body)
    assert body_val["error"]["code"] == "CORE_VALIDATION_ERROR"
    assert body_val["error"]["message"] == "Invalid field input"
    assert body_val["error"]["details"] == {"field": "sku"}

    # Not Found Error -> 404
    err_nf = NotFoundError("Product missing", details={"id": "prod_1"})
    res_nf = await core_error_handler(req, err_nf)
    assert res_nf.status_code == 404
    body_nf = json.loads(res_nf.body)
    assert body_nf["error"]["code"] == "CORE_NOT_FOUND"

    # Conflict Error -> 409
    err_cf = ConflictError("State conflict", details={"state": "locked"})
    res_cf = await core_error_handler(req, err_cf)
    assert res_cf.status_code == 409
    body_cf = json.loads(res_cf.body)
    assert body_cf["error"]["code"] == "CORE_CONFLICT"

    # Dependency Error -> 503
    err_dep = DependencyError("Service unavailable", details={"service": "payment"})
    res_dep = await core_error_handler(req, err_dep)
    assert res_dep.status_code == 503
    body_dep = json.loads(res_dep.body)
    assert body_dep["error"]["code"] == "CORE_DEPENDENCY_ERROR"


def test_actor_authorization():
    admin = Actor(actor_id="admin_1", roles=frozenset(["admin", "operator"]))
    user = Actor(actor_id="user_1", roles=frozenset(["customer"]))

    # Successful authorization
    require_role(admin, "admin")
    require_role(admin, "operator")
    require_role(user, "customer")

    # Unauthorized
    with pytest.raises(ConflictError) as exc_info:
        require_role(user, "admin")
    assert "Actor is not authorized" in str(exc_info.value)


def test_system_config_validation():
    # Valid configs
    valid_cfg = SystemConfig(environment="production", debug=False, api_version="v1")
    valid_cfg.validate()

    # Invalid environment
    invalid_env_cfg = SystemConfig(environment="unknown_env", debug=False, api_version="v1")
    with pytest.raises(ValueError) as exc:
        invalid_env_cfg.validate()
    assert "Invalid environment" in str(exc.value)

    # Invalid max_request_size_mb
    invalid_size_cfg = SystemConfig(
        environment="test", debug=True, api_version="v1", max_request_size_mb=0
    )
    with pytest.raises(ValueError) as exc:
        invalid_size_cfg.validate()
    assert "Request size must be positive" in str(exc.value)
