class ContentError(Exception):
    pass


class ContentNotFoundError(ContentError):
    pass


class ContentTemplateError(ContentError):
    pass


class ContentPublishError(ContentError):
    pass


class ContentLinkError(ContentError):
    pass
