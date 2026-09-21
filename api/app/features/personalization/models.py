from dataclasses import dataclass

from .enums import PersonalizationStatus, PreferenceDomain


@dataclass(frozen=True)
class PreferenceWeight:
    domain: PreferenceDomain
    key: str
    weight: float = 0.0
    interaction_count: int = 0


@dataclass(frozen=True)
class PersonalizationProfile:
    user_id: str
    weights: tuple[PreferenceWeight, ...] = ()
    status: PersonalizationStatus = PersonalizationStatus.ACTIVE
    version: int = 1


@dataclass(frozen=True)
class PersonalizedCandidate:
    candidate_id: str
    score: float
    matched_domains: tuple[PreferenceDomain, ...] = ()
    explanation: str = ""


@dataclass(frozen=True)
class PersonalizationResult:
    user_id: str
    candidates: tuple[PersonalizedCandidate, ...] = ()
    profile_version: int = 1
