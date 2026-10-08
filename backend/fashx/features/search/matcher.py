from .models import SearchDocument
from .tokenizer import tokenize


def match_score(query: str, document: SearchDocument) -> float:
    query_tokens = set(tokenize(query))
    if not query_tokens:
        return 0.0
    fields = (
        document.title,
        document.description,
        document.category or "",
        document.subcategory or "",
        document.brand or "",
        *document.tags,
        *document.styles,
        *document.colors,
    )
    document_tokens = {token for value in fields for token in tokenize(value)}
    return len(query_tokens & document_tokens) / len(query_tokens)
