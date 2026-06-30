import pytest
from rest_framework import status

from tests.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestRegister:
    URL = "/api/v1/auth/register/"

    def test_register_customer_success(self, api_client):
        payload = {"email": "novo@teste.com", "password": "Senha@12345", "phone": "+5511999990000", "role": "customer"}
        response = api_client.post(self.URL, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()["data"]
        assert data["user"]["email"] == "novo@teste.com"
        assert data["user"]["role"] == "customer"
        assert "tokens" in data
        assert "access" in data["tokens"]
        assert "refresh" in data["tokens"]

    def test_register_merchant_owner_success(self, api_client):
        payload = {"email": "loja@teste.com", "password": "Senha@12345", "role": "merchant_owner"}
        response = api_client.post(self.URL, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["data"]["user"]["role"] == "merchant_owner"

    def test_register_duplicate_email_fails(self, api_client):
        UserFactory(email="exists@teste.com")
        payload = {"email": "exists@teste.com", "password": "Senha@12345"}
        response = api_client.post(self.URL, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_weak_password_fails(self, api_client):
        payload = {"email": "fraco@teste.com", "password": "123"}
        response = api_client.post(self.URL, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_missing_email_fails(self, api_client):
        payload = {"password": "Senha@12345"}
        response = api_client.post(self.URL, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_invalid_role_fails(self, api_client):
        payload = {"email": "hacker@teste.com", "password": "Senha@12345", "role": "admin"}
        response = api_client.post(self.URL, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestLogin:
    URL = "/api/v1/auth/login/"

    def test_login_success(self, api_client):
        UserFactory(email="login@teste.com", password="correct_pass")
        payload = {"email": "login@teste.com", "password": "correct_pass"}
        response = api_client.post(self.URL, payload, format="json")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access" in data
        assert "refresh" in data

    def test_login_wrong_password(self, api_client):
        UserFactory(email="lock@teste.com", password="correct_pass")
        payload = {"email": "lock@teste.com", "password": "wrong_pass"}
        response = api_client.post(self.URL, payload, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_nonexistent_user(self, api_client):
        payload = {"email": "ghost@teste.com", "password": "any_pass"}
        response = api_client.post(self.URL, payload, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_inactive_user(self, api_client):
        UserFactory(email="inactive@teste.com", password="pass123456", is_active=False)
        payload = {"email": "inactive@teste.com", "password": "pass123456"}
        response = api_client.post(self.URL, payload, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestLogout:
    LOGIN_URL = "/api/v1/auth/login/"
    LOGOUT_URL = "/api/v1/auth/logout/"

    def _get_tokens(self, api_client):
        UserFactory(email="logout_user@teste.com", password="pass123456")
        response = api_client.post(
            self.LOGIN_URL,
            {"email": "logout_user@teste.com", "password": "pass123456"},
            format="json",
        )
        return response.json()

    def test_logout_success(self, api_client):
        tokens = self._get_tokens(api_client)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
        response = api_client.post(self.LOGOUT_URL, {"refresh": tokens["refresh"]}, format="json")
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_logout_without_refresh_token(self, api_client, customer_user_client):
        response = customer_user_client.post(self.LOGOUT_URL, {}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_logout_unauthenticated(self, api_client):
        response = api_client.post(self.LOGOUT_URL, {"refresh": "some_token"}, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestTokenRefresh:
    LOGIN_URL = "/api/v1/auth/login/"
    REFRESH_URL = "/api/v1/auth/refresh/"

    def test_refresh_success(self, api_client):
        UserFactory(email="refresh@teste.com", password="pass123456")
        login_resp = api_client.post(
            self.LOGIN_URL,
            {"email": "refresh@teste.com", "password": "pass123456"},
            format="json",
        )
        refresh_token = login_resp.json()["refresh"]
        response = api_client.post(self.REFRESH_URL, {"refresh": refresh_token}, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.json()

    def test_refresh_invalid_token(self, api_client):
        response = api_client.post(self.REFRESH_URL, {"refresh": "invalid.token.here"}, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestMeEndpoint:
    URL = "/api/v1/auth/me/"

    def test_me_authenticated(self, customer_user_client, customer_user):
        response = customer_user_client.get(self.URL)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["data"]["email"] == customer_user.email

    def test_me_unauthenticated(self, api_client):
        response = api_client.get(self.URL)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
