from .enums import IntelligenceState


class IntelligenceExperienceState:
    def __init__(self) -> None:
        self.state, self.error = IntelligenceState.IDLE, None

    def analyzing(self) -> None:
        self.state, self.error = IntelligenceState.ANALYZING, None

    def ready(self) -> None:
        self.state, self.error = IntelligenceState.READY, None

    def failure(self, message: str) -> None:
        self.state, self.error = IntelligenceState.ERROR, message
