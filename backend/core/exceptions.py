import logging
from typing import Any

from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from rest_framework import exceptions, status
from rest_framework.response import Response

logger = logging.getLogger(__name__)


class PagaeException(Exception):
    """Base exception for all Pagaê domain errors."""

    default_message = "An unexpected error occurred."
    default_code = "error"
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    def __init__(self, message: str | None = None, code: str | None = None) -> None:
        self.message = message or self.default_message
        self.code = code or self.default_code
        super().__init__(self.message)


class ValidationError(PagaeException):
    default_message = "Validation failed."
    default_code = "validation_error"
    status_code = status.HTTP_400_BAD_REQUEST


class NotFoundError(PagaeException):
    default_message = "Resource not found."
    default_code = "not_found"
    status_code = status.HTTP_404_NOT_FOUND


class ConflictError(PagaeException):
    default_message = "Resource already exists."
    default_code = "conflict"
    status_code = status.HTTP_409_CONFLICT


class ForbiddenError(PagaeException):
    default_message = "You do not have permission to perform this action."
    default_code = "forbidden"
    status_code = status.HTTP_403_FORBIDDEN


class ServiceUnavailableError(PagaeException):
    default_message = "An external service is temporarily unavailable."
    default_code = "service_unavailable"
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE


def custom_exception_handler(exc: Any, context: Any) -> Response | None:
    if isinstance(exc, DjangoValidationError):
        exc = exceptions.ValidationError(detail=exc.message_dict if hasattr(exc, "message_dict") else exc.messages)

    if isinstance(exc, Http404):
        exc = exceptions.NotFound()

    if isinstance(exc, PagaeException):
        return Response(
            data={"error": {"code": exc.code, "message": exc.message}},
            status=exc.status_code,
        )

    from rest_framework.views import exception_handler as drf_exception_handler

    response = drf_exception_handler(exc, context)

    if response is not None:
        error_data: dict[str, Any] = {}

        if isinstance(response.data, dict):
            error_data = response.data
        elif isinstance(response.data, list):
            error_data = {"detail": response.data}
        else:
            error_data = {"detail": str(response.data)}

        response.data = {"error": error_data}

    if response is None:
        logger.exception("Unhandled exception", exc_info=exc)
        return Response(
            data={"error": {"code": "internal_error", "message": "An internal error occurred."}},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return response
