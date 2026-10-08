from fashx.features.personalization.contracts import PersonalizationRequest, RecordSignalRequest
from fashx.features.personalization.enums import SignalType
from fashx.features.personalization.profile import PreferenceProfileEngine
from fashx.features.personalization.repository import PersonalizationRepository
from fashx.features.personalization.service import PersonalizationService


def test_signals_are_clamped_and_drive_explainable_ranking() -> None:
    service = PersonalizationService(PersonalizationRepository(), PreferenceProfileEngine())
    profile = service.record_signal(
        RecordSignalRequest("u", SignalType.SAVE, "p1", {"style": "casual"})
    )
    result = service.personalize(
        PersonalizationRequest("u", ("p1", "p2")),
        {"p1": {"style": "casual"}, "p2": {"style": "formal"}},
    )
    assert (
        profile.weights[0].weight > 0.5
        and result.candidates[0].candidate_id == "p1"
        and "style" in result.candidates[0].explanation
    )
