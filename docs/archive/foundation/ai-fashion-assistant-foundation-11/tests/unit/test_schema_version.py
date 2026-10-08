from schemas import SCHEMA_VERSION
from schemas.common.version import API_CONTRACT_VERSION


def test_contract_versions_are_explicit() -> None:
    assert SCHEMA_VERSION == 1
    assert API_CONTRACT_VERSION == "v1"
