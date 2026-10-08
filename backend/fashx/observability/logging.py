import logging

from .correlation import get_correlation_id


class CorrelationFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        correlation_id = get_correlation_id()
        record.correlation_id = (
            str(correlation_id)
            if correlation_id
            else "-"
        )
        return True
