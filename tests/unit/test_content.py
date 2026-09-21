import pytest

from api.app.features.content.contracts import CreateContentRequest, PublishContentRequest
from api.app.features.content.enums import ContentStatus, ContentVisibility
from api.app.features.content.errors import ContentPublishError, ContentTemplateError
from api.app.features.content.linking import link_outfit, link_product
from api.app.features.content.repository import ContentRepository
from api.app.features.content.service import ContentService


def test_create_link_and_publish_content() -> None:
    service = ContentService(ContentRepository())
    content = service.create(
        CreateContentRequest("author", "Summer Minimal", "post", "fashion_post")
    )
    linked = link_outfit(link_product(content, "p1"), "o1")
    service.repository.replace(linked)
    published = __import__(
        "api.app.features.content.publishing", fromlist=["publish_content"]
    ).publish_content(service, PublishContentRequest(linked.content_id, "author"))
    assert (
        published.status == ContentStatus.PUBLISHED
        and published.visibility == ContentVisibility.PUBLIC
        and published.product_ids == ("p1",)
    )


def test_content_rejects_bad_template_and_unauthorized_publish() -> None:
    service = ContentService(ContentRepository())
    with pytest.raises(ContentTemplateError):
        service.create(CreateContentRequest("a", "x", "post", "lookbook"))
    content = service.create(CreateContentRequest("a", "x", "post", "fashion_post"))
    with pytest.raises(ContentPublishError):
        __import__(
            "api.app.features.content.publishing", fromlist=["publish_content"]
        ).publish_content(service, PublishContentRequest(content.content_id, "other"))
