from .contracts import PersonalizationRequest, RecordSignalRequest
from .enums import PersonalizationStatus, PreferenceDomain
from .models import PersonalizationProfile, PersonalizationResult, PersonalizedCandidate
from .profile import PreferenceProfileEngine
from .repository import PersonalizationRepository
from .signals import signal_strength


class PersonalizationService:
    def __init__(
        self, repository: PersonalizationRepository, profile_engine: PreferenceProfileEngine
    ) -> None:
        self.repository, self.profile_engine = repository, profile_engine

    def get_profile(self, user_id: str) -> PersonalizationProfile:
        profile = self.repository.get(user_id)
        if profile is None:
            profile = PersonalizationProfile(user_id)
            self.repository.add(profile)
        return profile

    def record_signal(self, request: RecordSignalRequest) -> PersonalizationProfile:
        if not request.user_id.strip() or not request.target_id.strip():
            raise ValueError("User and target IDs are required.")
        profile = self.get_profile(request.user_id)
        if profile.status == PersonalizationStatus.DISABLED:
            raise ValueError("Personalization is disabled.")
        for domain, key in request.attributes.items():
            profile = self.profile_engine.update(
                profile,
                domain=PreferenceDomain(domain),
                key=key,
                delta=signal_strength(request.signal_type),
            )
        self.repository.replace(profile)
        return profile

    def personalize(
        self, request: PersonalizationRequest, candidate_attributes: dict[str, dict[str, str]]
    ) -> PersonalizationResult:
        profile = self.get_profile(request.user_id)
        candidates = []
        for candidate_id in request.candidate_ids:
            matched = tuple(
                weight.domain
                for weight in profile.weights
                if candidate_attributes.get(candidate_id, {}).get(weight.domain.value) == weight.key
            )
            score = sum(weight.weight for weight in profile.weights if weight.domain in matched)
            candidates.append(
                PersonalizedCandidate(
                    candidate_id,
                    score,
                    matched,
                    f"Matches your preferences in: {', '.join(d.value for d in matched)}."
                    if matched
                    else "",
                )
            )
        return PersonalizationResult(
            request.user_id,
            tuple(sorted(candidates, key=lambda c: c.score, reverse=True)[: request.limit]),
            profile.version,
        )
