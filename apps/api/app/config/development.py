from app.config.base import EnvironmentType, Settings


def get_development_settings() -> Settings:
    return Settings(
        ENVIRONMENT=EnvironmentType.DEVELOPMENT,
        DEBUG=True,
    )
