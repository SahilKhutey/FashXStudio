from dataclasses import replace
from uuid import uuid4

from .contracts import CreateContentRequest, UpdateContentRequest
from .enums import ContentType
from .errors import ContentNotFoundError, ContentTemplateError
from .models import Content
from .repository import ContentRepository
from .templates import get_template


class ContentService:
    def __init__(self, repository: ContentRepository) -> None:
        self.repository = repository

    def create(self, request: CreateContentRequest) -> Content:
        if not request.author_id.strip() or not request.title.strip() or len(request.title) > 200:
            raise ValueError("A valid author and title of up to 200 characters are required.")
        template = get_template(request.template_id)
        if template is None or template.content_type != request.content_type:
            raise ContentTemplateError(request.template_id)
        content = Content(
            str(uuid4()),
            request.author_id,
            request.title,
            content_type=ContentType(request.content_type),
        )
        self.repository.add(content)
        return content

    def get(self, content_id: str) -> Content:
        content = self.repository.get(content_id)
        if content is None:
            raise ContentNotFoundError(content_id)
        return content

    def update(self, request: UpdateContentRequest) -> Content:
        content = self.get(request.content_id)
        updated = replace(
            content,
            title=request.title if request.title is not None else content.title,
            description=request.description
            if request.description is not None
            else content.description,
        )
        self.repository.replace(updated)
        return updated
