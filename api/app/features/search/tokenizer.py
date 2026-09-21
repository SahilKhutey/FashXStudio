import re

STOP_WORDS = frozenset({"a", "an", "the", "for", "and", "or", "with"})


def tokenize(query: str) -> tuple[str, ...]:
    return tuple(
        token for token in re.findall(r"[a-z0-9]+", query.lower()) if token not in STOP_WORDS
    )
