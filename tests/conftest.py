import os
import pathlib
import sys
import pytest

FROZEN_DIRS = {
    "inventory",
    "promotions",
    "cart",
    "checkout",
    "orders",
    "payments",
    "fulfillment",
    "returns",
}
FROZEN_FILES = {"test_cross_core.py"}

# Enable frozen routers if running all tests or specifically running frozen tests,
# unless "not frozen" is specified in the pytest marker argument.
if "not frozen" not in " ".join(sys.argv) and os.getenv("FASHX_ENABLE_FROZEN") is None:
    os.environ["FASHX_ENABLE_FROZEN"] = "1"


def pytest_collection_modifyitems(items):
    for item in items:
        p = pathlib.Path(str(item.fspath))
        if FROZEN_DIRS & set(p.parts) or p.name in FROZEN_FILES:
            item.add_marker(pytest.mark.frozen)
