import os
import sys

import pytest

# Ensure packages and backend are in sys.path
sys.path.insert(0, os.path.abspath("packages"))
sys.path.insert(0, os.path.abspath("backend"))


@pytest.fixture(autouse=True)
def setup_test_identity_override():
    """Override root conftest autouse fixture to avoid aiosqlite event loop deadlocks."""
    yield
