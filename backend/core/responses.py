from typing import Any

from rest_framework import status
from rest_framework.response import Response


def success(data: Any = None, status_code: int = status.HTTP_200_OK, message: str | None = None) -> Response:
    payload: dict[str, Any] = {"data": data}
    if message:
        payload["message"] = message
    return Response(payload, status=status_code)


def created(data: Any = None, message: str | None = None) -> Response:
    return success(data=data, status_code=status.HTTP_201_CREATED, message=message)


def no_content() -> Response:
    return Response(status=status.HTTP_204_NO_CONTENT)


def error(message: str = "An error occurred.", status_code: int = status.HTTP_400_BAD_REQUEST, data: Any = None) -> Response:
    payload: dict[str, Any] = {"message": message}
    if data is not None:
        payload["data"] = data
    return Response(payload, status=status_code)
