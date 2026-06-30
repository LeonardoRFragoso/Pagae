import json
import logging
import traceback
from datetime import UTC, datetime
from typing import Any


class JsonFormatter(logging.Formatter):
    """Emit structured JSON log records for centralized log aggregation."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: dict[str, Any] = {
            "timestamp": datetime.now(tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if record.exc_info:
            log_data["exception"] = traceback.format_exception(*record.exc_info)

        extra_keys = {
            "method", "path", "status_code", "duration_ms",
            "user_id", "correlation_id", "customer_id", "merchant_id",
        }
        for key in extra_keys:
            if hasattr(record, key):
                log_data[key] = getattr(record, key)

        return json.dumps(log_data, ensure_ascii=False, default=str)
