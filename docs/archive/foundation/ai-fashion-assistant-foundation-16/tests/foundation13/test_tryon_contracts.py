from uuid import uuid4

import pytest
from pydantic import ValidationError

from schemas.tryon.job import TryOnCreate, TryOnCreateResponse


def test_tryon_create_contract() -> None:
    product_id = uuid4()
    payload = TryOnCreate(product_id=product_id)
    assert payload.product_id == product_id


def test_tryon_response_requires_job_id() -> None:
    with pytest.raises(ValidationError):
        TryOnCreateResponse(status="queued", cache_hit=False)
