import hashlib

import pytest
from rest_framework import status

from apps.merchants.models import Merchant, MerchantApiKey, MerchantStatus
from apps.merchants.services import MerchantService, _hash_key
from tests.factories import MerchantApiKeyFactory, MerchantFactory, UserFactory

pytestmark = pytest.mark.django_db

VALID_CNPJ = "11222333000181"  # valid CNPJ for testing
VALID_PAYLOAD = {
    "legal_name": "Loja Teste Ltda",
    "trade_name": "Loja Teste",
    "cnpj": VALID_CNPJ,
    "email": "loja@teste.com",
    "phone": "+551133334444",
    "website": "https://lojateste.com.br",
    "pix_key": "loja@teste.com",
}


class TestMerchantCreate:
    URL = "/api/v1/merchants/"

    def test_create_merchant_success(self, merchant_user_client):
        response = merchant_user_client.post(self.URL, VALID_PAYLOAD, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()["data"]
        assert data["legal_name"] == "Loja Teste Ltda"
        assert data["status"] == MerchantStatus.PENDING

    def test_create_merchant_unauthenticated(self, api_client):
        response = api_client.post(self.URL, VALID_PAYLOAD, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_customer_cannot_create_merchant(self, customer_user_client):
        response = customer_user_client.post(self.URL, VALID_PAYLOAD, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_duplicate_profile_fails(self, merchant_user_client, merchant_user):
        MerchantFactory(user=merchant_user, cnpj=VALID_CNPJ)
        response = merchant_user_client.post(self.URL, VALID_PAYLOAD, format="json")
        assert response.status_code == status.HTTP_409_CONFLICT

    def test_duplicate_cnpj_fails(self, api_client):
        user1 = UserFactory(role="merchant_owner")
        user2 = UserFactory(role="merchant_owner")
        MerchantFactory(user=user1, cnpj=VALID_CNPJ)
        api_client.force_authenticate(user=user2)
        payload = {**VALID_PAYLOAD, "email": "outro@teste.com"}
        response = api_client.post(self.URL, payload, format="json")
        assert response.status_code == status.HTTP_409_CONFLICT

    def test_invalid_cnpj_fails(self, merchant_user_client):
        payload = {**VALID_PAYLOAD, "cnpj": "00000000000000"}
        response = merchant_user_client.post(self.URL, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestMerchantMe:
    URL = "/api/v1/merchants/me/"

    def test_get_merchant_profile(self, api_client, merchant_user):
        merchant = MerchantFactory(user=merchant_user)
        api_client.force_authenticate(user=merchant_user)
        response = api_client.get(self.URL)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["data"]["id"] == str(merchant.id)

    def test_get_profile_not_found(self, merchant_user_client):
        response = merchant_user_client.get(self.URL)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_unauthenticated(self, api_client):
        response = api_client.get(self.URL)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestApiKeyGeneration:
    URL = "/api/v1/merchants/api-keys/"

    def test_generate_key_success(self, api_client, merchant_user):
        MerchantFactory(user=merchant_user)
        api_client.force_authenticate(user=merchant_user)
        payload = {"name": "Integração WooCommerce", "environment": "production"}
        response = api_client.post(self.URL, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()["data"]
        assert data["full_key"].startswith("pk_live_")
        assert len(data["full_key"]) == len("pk_live_") + 48

    def test_full_key_not_stored(self, api_client, merchant_user):
        MerchantFactory(user=merchant_user)
        api_client.force_authenticate(user=merchant_user)
        response = api_client.post(self.URL, {"environment": "production"}, format="json")
        full_key = response.json()["data"]["full_key"]
        api_key = MerchantApiKey.objects.get(key_prefix=full_key[:16])
        assert api_key.key_hash != full_key
        assert api_key.key_hash == _hash_key(full_key)

    def test_generate_sandbox_key(self, api_client, merchant_user):
        MerchantFactory(user=merchant_user)
        api_client.force_authenticate(user=merchant_user)
        response = api_client.post(self.URL, {"environment": "sandbox"}, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["data"]["full_key"].startswith("pk_test_")

    def test_list_api_keys(self, api_client, merchant_user):
        merchant = MerchantFactory(user=merchant_user)
        MerchantApiKeyFactory(merchant=merchant)
        MerchantApiKeyFactory(merchant=merchant)
        api_client.force_authenticate(user=merchant_user)
        response = api_client.get(self.URL)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()["data"]) == 2

    def test_list_shows_no_full_key(self, api_client, merchant_user):
        merchant = MerchantFactory(user=merchant_user)
        MerchantApiKeyFactory(merchant=merchant)
        api_client.force_authenticate(user=merchant_user)
        response = api_client.get(self.URL)
        data = response.json()["data"]
        assert "full_key" not in data[0]
        assert "key_hash" not in data[0]

    def test_generate_key_without_merchant_fails(self, merchant_user_client):
        response = merchant_user_client.post(self.URL, {"environment": "production"}, format="json")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_api_key_authentication(self, api_client, merchant_user):
        merchant = MerchantFactory(user=merchant_user)
        api_client.force_authenticate(user=merchant_user)
        gen_response = api_client.post(
            "/api/v1/merchants/api-keys/", {"environment": "production"}, format="json"
        )
        full_key = gen_response.json()["data"]["full_key"]
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {full_key}")
        me_response = api_client.get("/api/v1/merchants/me/")
        assert me_response.status_code == status.HTTP_200_OK

    def test_invalid_api_key_rejected(self, api_client):
        api_client.credentials(HTTP_AUTHORIZATION="Bearer pk_live_invalidkeyhere00000000000000000000000000000000")
        response = api_client.get("/api/v1/merchants/me/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestApiKeyService:
    def test_verify_api_key_success(self, merchant_user):
        merchant = MerchantFactory(user=merchant_user)
        service = MerchantService()
        result = service.generate_api_key(user=merchant_user, name="test", environment="production")
        verified = service.verify_api_key(result.full_key)
        assert verified is not None
        assert verified.merchant_id == merchant.id

    def test_verify_tampered_key_fails(self, merchant_user):
        MerchantFactory(user=merchant_user)
        service = MerchantService()
        result = service.generate_api_key(user=merchant_user)
        tampered = result.full_key[:-4] + "xxxx"
        assert service.verify_api_key(tampered) is None

    def test_verify_unknown_key_fails(self):
        service = MerchantService()
        assert service.verify_api_key("pk_live_unknownprefix00000000000000000000000000000000") is None


class TestMerchantPortalEndpoints:
    @pytest.fixture
    def merchant_with_data(self, merchant_user):
        from apps.checkout.models import CheckoutStatus
        from apps.payments.models import Installment, InstallmentStatus
        from apps.settlements.models import Settlement
        from tests.factories import ApprovedCustomerFactory

        merchant = MerchantFactory(user=merchant_user, webhook_url="https://old.com", webhook_secret="old")
        customer = ApprovedCustomerFactory()
        session = merchant.checkout_sessions.create(
            customer=customer,
            total_amount=10000,
            mdr_amount=700,
            net_amount=9300,
            installment_count=4,
            installment_amount=2500,
            status=CheckoutStatus.APPROVED,
            merchant_order_id="order-1",
        )
        for i in range(1, 5):
            Installment.objects.create(
                checkout=session,
                customer=customer,
                number=i,
                amount=2500,
                due_date="2026-06-25",
                status=InstallmentStatus.PENDING,
            )
        Settlement.objects.create(
            merchant=merchant,
            amount=9300,
            period_start="2026-06-01",
            period_end="2026-06-30",
            status="paid",
            pix_e2e_id="E2E123",
        )
        return merchant, session

    def test_dashboard(self, api_client, merchant_user, merchant_with_data):
        api_client.force_authenticate(user=merchant_user)
        response = api_client.get("/api/v1/merchants/dashboard/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()["data"]
        assert data["gmv_today"] >= 0
        assert "approval_rate" in data

    def test_transactions_list(self, api_client, merchant_user, merchant_with_data):
        api_client.force_authenticate(user=merchant_user)
        response = api_client.get("/api/v1/merchants/transactions/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()["data"]) == 1

    def test_transaction_detail(self, api_client, merchant_user, merchant_with_data):
        _, session = merchant_with_data
        api_client.force_authenticate(user=merchant_user)
        response = api_client.get(f"/api/v1/merchants/transactions/{session.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()["data"]["installments"]) == 4

    def test_settlements_list(self, api_client, merchant_user, merchant_with_data):
        api_client.force_authenticate(user=merchant_user)
        response = api_client.get("/api/v1/merchants/settlements/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()["data"]) == 1

    def test_webhook_get_and_patch(self, api_client, merchant_user, merchant_with_data):
        api_client.force_authenticate(user=merchant_user)
        get_response = api_client.get("/api/v1/merchants/webhook/")
        assert get_response.status_code == status.HTTP_200_OK
        assert get_response.json()["data"]["webhook_url"] == "https://old.com"

        patch_response = api_client.patch(
            "/api/v1/merchants/webhook/",
            {"webhook_url": "https://new.com", "webhook_secret": "new-secret"},
            format="json",
        )
        assert patch_response.status_code == status.HTTP_200_OK
        assert patch_response.json()["data"]["webhook_url"] == "https://new.com"
        assert patch_response.json()["data"]["webhook_secret"] == "new-secret"

    def test_webhook_test_requires_url(self, api_client, merchant_user, merchant_with_data):
        api_client.force_authenticate(user=merchant_user)
        response = api_client.post("/api/v1/merchants/webhook/test/", {}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
