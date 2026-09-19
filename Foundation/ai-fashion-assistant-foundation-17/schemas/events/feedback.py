from schemas.events.base import DomainEvent


class FitFeedbackSubmitted(DomainEvent):
    event_type: str = "fit_feedback_submitted"
