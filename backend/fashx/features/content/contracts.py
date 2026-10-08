from dataclasses import dataclass


@dataclass(frozen=True)
class CreateContentRequest:
    author_id: str
    title: str
    content_type: str
    template_id: str


@dataclass(frozen=True)
class UpdateContentRequest:
    content_id: str
    title: str | None = None
    description: str | None = None


@dataclass(frozen=True)
class PublishContentRequest:
    content_id: str
    author_id: str
