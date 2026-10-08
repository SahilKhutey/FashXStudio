from .models import PersonalizationProfile


class PersonalizationRepository:
    def __init__(self) -> None:
        self._profiles: list[PersonalizationProfile] = []

    def get(self, user_id: str) -> PersonalizationProfile | None:
        return next((p for p in self._profiles if p.user_id == user_id), None)

    def add(self, profile: PersonalizationProfile) -> None:
        self._profiles.append(profile)

    def replace(self, profile: PersonalizationProfile) -> None:
        self._profiles[
            self._profiles.index(next(p for p in self._profiles if p.user_id == profile.user_id))
        ] = profile
