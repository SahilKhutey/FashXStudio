from app.core.errors import ValidationError
from app.core.result import Failure, Success


def test_success_result():
    res = Success(value="styled_outfit")
    assert res.value == "styled_outfit"


def test_failure_result():
    err = ValidationError("invalid attribute")
    res = Failure(error=err)
    assert res.error is err
    assert res.error.code == "CORE_VALIDATION_ERROR"
