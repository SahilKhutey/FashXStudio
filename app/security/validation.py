from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SystemConfig:
    environment: str
    debug: bool
    api_version: str
    max_request_size_mb: int = 10

    def validate(self) -> None:
        if self.environment not in {
            "development",
            "test",
            "staging",
            "production",
        }:
            raise ValueError("Invalid environment.")

        if self.max_request_size_mb <= 0:
            raise ValueError("Request size must be positive.")
