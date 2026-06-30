import logging
import time
import uuid
from collections.abc import Callable

from django.http import HttpRequest, HttpResponse

logger = logging.getLogger(__name__)

CORRELATION_ID_HEADER = "X-Correlation-ID"
REQUEST_ID_HEADER = "X-Request-ID"


class CorrelationIdMiddleware:
    """Attach a correlation ID to every request for distributed tracing."""

    def __init__(self, get_response: Callable) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        correlation_id = request.headers.get(CORRELATION_ID_HEADER) or str(uuid.uuid4())
        request.correlation_id = correlation_id  # type: ignore[attr-defined]
        response = self.get_response(request)
        response[CORRELATION_ID_HEADER] = correlation_id
        return response


class RequestLoggingMiddleware:
    """Structured log every inbound HTTP request and its outcome."""

    def __init__(self, get_response: Callable) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        start = time.monotonic()
        response = self.get_response(request)
        duration_ms = round((time.monotonic() - start) * 1000, 2)

        correlation_id = getattr(request, "correlation_id", "-")
        user_id = str(request.user.pk) if request.user.is_authenticated else "anonymous"

        logger.info(
            "http_request",
            extra={
                "method": request.method,
                "path": request.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
                "user_id": user_id,
                "correlation_id": correlation_id,
            },
        )
        return response
