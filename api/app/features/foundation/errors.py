"""Structured failures for the feature layer; Core error handling remains unchanged."""


class FeatureError(Exception):
    """Base feature-layer exception."""


class FeatureAlreadyRegisteredError(FeatureError):
    """Raised when a feature ID already exists."""


class FeatureNotFoundError(FeatureError):
    """Raised when a requested feature does not exist."""


class FeatureDependencyError(FeatureError):
    """Raised when feature dependencies cannot be satisfied."""


class FeatureCircularDependencyError(FeatureDependencyError):
    """Raised when a circular dependency is detected."""


class FeatureConfigurationError(FeatureError):
    """Raised for invalid feature configuration."""


class FeatureDisabledError(FeatureError):
    """Raised when attempting to execute a disabled feature."""


class FeatureLifecycleError(FeatureError):
    """Raised when an invalid lifecycle transition is requested."""
