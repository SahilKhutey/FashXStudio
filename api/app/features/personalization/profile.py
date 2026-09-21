from dataclasses import replace

from .enums import PreferenceDomain
from .models import PersonalizationProfile, PreferenceWeight


class PreferenceProfileEngine:
    def update(
        self, profile: PersonalizationProfile, *, domain: PreferenceDomain, key: str, delta: float
    ) -> PersonalizationProfile:
        weights = list(profile.weights)
        for index, weight in enumerate(weights):
            if weight.domain == domain and weight.key == key:
                weights[index] = replace(
                    weight,
                    weight=max(-1.0, min(1.0, weight.weight + delta)),
                    interaction_count=weight.interaction_count + 1,
                )
                return replace(profile, weights=tuple(weights), version=profile.version + 1)
        weights.append(PreferenceWeight(domain, key, max(-1.0, min(1.0, delta)), 1))
        return replace(profile, weights=tuple(weights), version=profile.version + 1)
