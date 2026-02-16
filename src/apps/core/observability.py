import json
import logging
from contextvars import ContextVar
from datetime import datetime, timezone

_correlation_id_ctx: ContextVar[str] = ContextVar("correlation_id", default="-")


def get_correlation_id() -> str:
    return _correlation_id_ctx.get()


def set_correlation_id(correlation_id: str):
    return _correlation_id_ctx.set(correlation_id)


def reset_correlation_id(token):
    _correlation_id_ctx.reset(token)


class CorrelationIdFilter(logging.Filter):
    def filter(self, record):
        record.correlation_id = get_correlation_id()
        return True


class JsonFormatter(logging.Formatter):
    EXTRA_FIELDS = (
        "request_method",
        "request_path",
        "status_code",
        "duration_ms",
        "client_ip",
    )

    def format(self, record):
        level = "WARN" if record.levelname == "WARNING" else record.levelname
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": getattr(record, "correlation_id", get_correlation_id()),
        }

        for field in self.EXTRA_FIELDS:
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = value

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=True)
