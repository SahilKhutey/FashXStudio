class OnboardingError(Exception):
    """Base onboarding exception."""


class ProfileValidationError(OnboardingError):
    """Invalid profile information."""


class OnboardingStepError(OnboardingError):
    """Invalid onboarding step transition."""
