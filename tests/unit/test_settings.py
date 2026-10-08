from fashx.core.settings import Settings


def test_production_settings_flag() -> None:
    settings = Settings(APP_ENV="production")
    assert settings.is_production is True


def test_development_defaults() -> None:
    settings = Settings(APP_ENV="development")
    assert settings.readiness_requires_database is False
