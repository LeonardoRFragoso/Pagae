from rest_framework import status

from core import responses


class TestResponses:
    def test_success_response(self):
        response = responses.success(data={"key": "value"})
        assert response.status_code == status.HTTP_200_OK
        assert response.data["data"] == {"key": "value"}

    def test_created_response(self):
        response = responses.created(data={"id": "123"})
        assert response.status_code == status.HTTP_201_CREATED

    def test_no_content_response(self):
        response = responses.no_content()
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_error_response(self):
        response = responses.error(message="Bad request", status_code=400)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["message"] == "Bad request"
