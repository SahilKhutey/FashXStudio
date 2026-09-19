from app.config.base import EnvironmentType, ModelStatus, Settings


def get_test_settings() -> Settings:
    return Settings(
        ENVIRONMENT=EnvironmentType.TEST,
        DEBUG=True,
        DATABASE_URL="sqlite+aiosqlite:///:memory:",
        DATABASE_URL_SYNC="sqlite:///:memory:",
        REDIS_URL="redis://localhost:6379/1",
        STORAGE_BACKEND="local",
        STORAGE_LOCAL_DIR="./test_storage",
        ACTIVE_TRYON_MODEL_STATUS=ModelStatus.EVALUATION,
    )
