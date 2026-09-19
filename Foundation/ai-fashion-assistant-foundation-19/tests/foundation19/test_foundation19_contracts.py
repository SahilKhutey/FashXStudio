from pathlib import Path

from api.app.main import create_app
from schemas.journey.mvp import MvpJourneyGate, MvpJourneyState


ROOT = Path(__file__).resolve().parents[2]


def test_required_mvp_modules_exist():
    required = [
        ROOT / "mobile",
        ROOT / "api",
        ROOT / "schemas",
        ROOT / "workers",
        ROOT / "ml",
        ROOT / "database",
        ROOT / "tests",
        ROOT / "docs-foundation-18.md",
    ]
    assert all(path.exists() for path in required)


def test_application_has_core_public_routes():
    app = create_app()
    paths = {route.path for route in app.routes}
    expected = {
        "/api/v1/profile",
        "/api/v1/profile/me",
        "/api/v1/catalog/search",
        "/api/v1/feed/me",
        "/api/v1/tryon",
        "/api/v1/commerce/buy-click",
        "/api/v1/tryon/{job_id}/feedback",
        "/api/v1/analytics/session-events",
    }
    assert expected.issubset(paths)


def test_journey_contracts_reject_extra_fields():
    state = MvpJourneyState.model_validate(
        {
            "user_id": "00000000-0000-0000-0000-000000000001",
            "stage": "profile_ready",
        }
    )
    assert state.profile_ready is False

    try:
        MvpJourneyGate.model_validate({"allowed": True, "stage": "profile_ready", "extra": 1})
    except Exception:
        pass
    else:
        raise AssertionError("MvpJourneyGate must reject unknown fields")
