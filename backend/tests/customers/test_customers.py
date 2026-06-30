import pytest
from rest_framework import status

from apps.customers.models import Customer, KYCStatus
from tests.factories import CustomerFactory, UserFactory

pytestmark = pytest.mark.django_db

VALID_CPF = "52998224725"  # valid CPF for testing
VALID_PAYLOAD = {
    "cpf": VALID_CPF,
    "full_name": "João da Silva",
    "birth_date": "1990-05-15",
    "phone": "+5511999990000",
    "email": "joao@teste.com",
    "cep": "01310-100",
    "street": "Avenida Paulista",
    "number": "1000",
    "city": "São Paulo",
    "state": "SP",
}


class TestCustomerCreate:
    URL = "/api/v1/customers/"

    def test_create_customer_success(self, customer_user_client):
        response = customer_user_client.post(self.URL, VALID_PAYLOAD, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()["data"]
        assert data["full_name"] == "João da Silva"
        assert data["kyc_status"] == KYCStatus.PENDING
        assert data["approved_limit"] == 0

    def test_create_customer_unauthenticated(self, api_client):
        response = api_client.post(self.URL, VALID_PAYLOAD, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_merchant_cannot_create_customer_profile(self, merchant_user_client):
        response = merchant_user_client.post(self.URL, VALID_PAYLOAD, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_duplicate_profile_fails(self, customer_user_client, customer_user):
        CustomerFactory(user=customer_user, cpf=VALID_CPF)
        response = customer_user_client.post(self.URL, VALID_PAYLOAD, format="json")
        assert response.status_code == status.HTTP_409_CONFLICT

    def test_duplicate_cpf_fails(self, api_client):
        user1 = UserFactory(role="customer")
        user2 = UserFactory(role="customer")
        CustomerFactory(user=user1, cpf=VALID_CPF)
        api_client.force_authenticate(user=user2)
        payload = {**VALID_PAYLOAD, "email": "outro@teste.com"}
        response = api_client.post(self.URL, payload, format="json")
        assert response.status_code == status.HTTP_409_CONFLICT

    def test_invalid_cpf_fails(self, customer_user_client):
        payload = {**VALID_PAYLOAD, "cpf": "00000000000"}
        response = customer_user_client.post(self.URL, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_underage_customer_fails(self, customer_user_client):
        payload = {**VALID_PAYLOAD, "birth_date": "2015-01-01"}
        response = customer_user_client.post(self.URL, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_missing_required_fields_fails(self, customer_user_client):
        response = customer_user_client.post(self.URL, {"cpf": VALID_CPF}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestCustomerMerchant:
    URL = "/api/v1/customers/merchant/"

    def _create_key(self, merchant_user):
        from apps.merchants.services import MerchantService
        from tests.factories import MerchantFactory

        MerchantFactory(user=merchant_user, status="active")
        service = MerchantService()
        result = service.generate_api_key(user=merchant_user)
        return result.full_key

    def _client(self, full_key: str):
        from rest_framework.test import APIClient

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {full_key}")
        return client

    def test_create_customer_via_merchant_success(self, merchant_user):
        full_key = self._create_key(merchant_user)
        payload = {
            "cpf": VALID_CPF,
            "full_name": "João da Silva",
            "email": "joao@merchant.com",
            "phone": "+5511999990000",
        }
        response = self._client(full_key).post(self.URL, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()["data"]
        assert data["cpf"] == VALID_CPF
        assert data["full_name"] == "João da Silva"
        assert data["email"] == "joao@merchant.com"
        assert data["kyc_status"] == KYCStatus.APPROVED

    def test_update_customer_via_merchant_success(self, merchant_user):
        from tests.factories import CustomerFactory

        full_key = self._create_key(merchant_user)
        CustomerFactory(cpf=VALID_CPF, full_name="Antigo Nome", email="old@merchant.com")
        payload = {
            "cpf": VALID_CPF,
            "full_name": "Novo Nome",
            "email": "new@merchant.com",
        }
        response = self._client(full_key).post(self.URL, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        customer = Customer.objects.get(cpf=VALID_CPF)
        assert customer.full_name == "Novo Nome"
        assert customer.email == "new@merchant.com"

    def test_merchant_endpoint_unauthenticated(self, api_client):
        response = api_client.post(self.URL, {"cpf": VALID_CPF}, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_merchant_endpoint_invalid_api_key(self, api_client):
        api_client.credentials(HTTP_AUTHORIZATION="Bearer pk_live_invalidkey000000000000000000000000")
        response = api_client.post(self.URL, {"cpf": VALID_CPF}, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_merchant_customer_cpf_is_normalized(self, merchant_user):
        full_key = self._create_key(merchant_user)
        payload = {"cpf": "529.982.247-25", "full_name": "João Normalizado"}
        response = self._client(full_key).post(self.URL, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["data"]["cpf"] == VALID_CPF

    def test_merchant_customer_invalid_cpf_fails(self, merchant_user):
        full_key = self._create_key(merchant_user)
        response = self._client(full_key).post(self.URL, {"cpf": "00000000000"}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_customer_user_cannot_access_merchant_endpoint(self, customer_user_client):
        response = customer_user_client.post(self.URL, {"cpf": VALID_CPF}, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestCustomerMe:
    URL = "/api/v1/customers/me/"

    def test_get_profile_success(self, api_client, customer_user):
        customer = CustomerFactory(user=customer_user)
        api_client.force_authenticate(user=customer_user)
        response = api_client.get(self.URL)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()["data"]
        assert data["id"] == str(customer.id)
        assert data["full_name"] == customer.full_name

    def test_get_profile_not_found(self, customer_user_client):
        response = customer_user_client.get(self.URL)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_profile_unauthenticated(self, api_client):
        response = api_client.get(self.URL)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_profile_success(self, api_client, customer_user):
        CustomerFactory(user=customer_user)
        api_client.force_authenticate(user=customer_user)
        payload = {"phone": "+5511888880000", "city": "Rio de Janeiro", "state": "RJ"}
        response = api_client.put(self.URL, payload, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["data"]["city"] == "Rio de Janeiro"

    def test_cannot_update_cpf(self, api_client, customer_user):
        CustomerFactory(user=customer_user, cpf=VALID_CPF)
        api_client.force_authenticate(user=customer_user)
        payload = {"cpf": "11111111111"}
        response = api_client.put(self.URL, payload, format="json")
        assert response.status_code == status.HTTP_200_OK
        customer = Customer.objects.get(user=customer_user)
        assert customer.cpf == VALID_CPF

    def test_available_limit_computed(self, api_client, customer_user):
        CustomerFactory(user=customer_user, approved_limit=50000, used_limit=20000)
        api_client.force_authenticate(user=customer_user)
        response = api_client.get(self.URL)
        assert response.json()["data"]["available_limit"] == 30000
