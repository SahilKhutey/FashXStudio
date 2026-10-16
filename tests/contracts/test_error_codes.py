"""Contract test verifying backend ErrorCode enum matches mobile/src/api/error-codes.json."""

import json
from pathlib import Path

from fashx.core.errors import ErrorCode


def test_error_codes_json_matches_backend_enum() -> None:
    path = Path("mobile/src/api/error-codes.json")
    assert path.is_file(), "mobile/src/api/error-codes.json must exist"

    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)

    expected = {e.name: e.value for e in ErrorCode}
    assert data == expected, "mobile/src/api/error-codes.json has drifted from ErrorCode enum"
