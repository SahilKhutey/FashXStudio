from dataclasses import replace

from .contracts import PublishContentRequest
from .enums import ContentStatus, ContentVisibility
from .errors import ContentPublishError
from .service import ContentService


def publish_content(service: ContentService, request: PublishContentRequest):
    content = service.get(request.content_id)
    if content.author_id != request.author_id:
        raise ContentPublishError("Only the content author can publish it.")
    published = replace(
        content, status=ContentStatus.PUBLISHED, visibility=ContentVisibility.PUBLIC
    )
    service.repository.replace(published)
    return published
