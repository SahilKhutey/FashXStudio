from dataclasses import dataclass

from .enums import SignalType


@dataclass(frozen=True)
class RecordSignalRequest:
    user_id: str
    signal_type: SignalType
    target_id: str
    attributes: dict[str, str]


@dataclass(frozen=True)
class PersonalizationRequest:
    user_id: str
    candidate_ids: tuple[str, ...]
    limit: int = 10
