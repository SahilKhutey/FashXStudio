"""Rule I08: Commercial license verification for ML models and try-on adapters."""

ALLOWED_LICENSE_IDS = {"commercial-api", "apache-2.0", "mit"}
REJECTED_LICENSE_IDS = {"cc-by-nc", "cc-by-nc-sa", "research-only", "unknown", "mock"}


def assert_production_license(adapter: object) -> None:
    """Ensure adapter declares a verified commercial license before running in production."""
    lic = getattr(adapter, "license_id", "unknown")
    if lic not in ALLOWED_LICENSE_IDS:
        raise RuntimeError(
            f"adapter {adapter.__class__.__name__} has license '{lic}' not allowed in production (rule I08)"
        )
