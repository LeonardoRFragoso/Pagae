import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.checkout.credit import BureauResult, CreditEngine
from apps.checkout.models import CheckoutStatus
from apps.merchants.services import MerchantService
from tests.factories import ApprovedCustomerFactory, MerchantFactory

pytestmark = pytest.mark.django_db

URL = "/api/v1/checkout/"


class TestCheckoutCreate:
    def _create_key(self, merchant_user):
        MerchantFactory(user=merchant_user, status="active")
        service = MerchantService()
        result = service.generate_api_key(user=merchant_user)
        return result.full_key

    def _client(self, full_key: str) -> APIClient:
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {full_key}")
        return client

    def test_create_checkout_success(self, merchant_user):
        full_key = self._create_key(merchant_user)
        customer = ApprovedCustomerFactory()
        payload = {
            "merchant_order_id": "ORDER-123",
            "customer": {"cpf": customer.cpf},
            "total_amount": 10000,  # R$100
            "installment_count": 4,
        }
        response = self._client(full_key).post(URL, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()["data"]
        assert data["status"] == CheckoutStatus.APPROVED
        assert data["decision"] == "approve"
        assert data["total_amount"] == 10000
        assert data["installment_count"] == 4
        assert data["qr_code"]
        assert len(data["schedule"]) == 4

    def test_create_checkout_denied_kyc_not_approved(self, merchant_user):
        full_key = self._create_key(merchant_user)
        customer = ApprovedCustomerFactory(kyc_status="pending")
        payload = {
            "customer": {"cpf": customer.cpf},
            "total_amount": 10000,
            "installment_count": 4,
        }
        response = self._client(full_key).post(URL, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()["data"]
        assert data["status"] == CheckoutStatus.DENIED
        assert data["denial_reason"] == "kyc_not_approved"
        assert data["qr_code"] == ""

    def test_create_checkout_denied_insufficient_limit(self, merchant_user):
        full_key = self._create_key(merchant_user)
        customer = ApprovedCustomerFactory(approved_limit=5000, used_limit=0)
        payload = {
            "customer": {"cpf": customer.cpf},
            "total_amount": 10000,
            "installment_count": 4,
        }
        response = self._client(full_key).post(URL, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()["data"]
        assert data["status"] == CheckoutStatus.DENIED
        assert data["denial_reason"] == "insufficient_limit"

    def test_create_checkout_with_server_to_server_customer(self, merchant_user):
        full_key = self._create_key(merchant_user)
        payload = {
            "merchant_order_id": "ORDER-S2S-001",
            "customer": {
                "cpf": "52998224725",
                "full_name": "Maria Server",
                "email": "maria@server.com",
                "phone": "+5511999991111",
            },
            "total_amount": 20000,
            "installment_count": 3,
        }
        response = self._client(full_key).post(URL, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()["data"]
        assert data["status"] == CheckoutStatus.APPROVED
        assert data["total_amount"] == 20000
        assert data["installment_count"] == 3
        assert data["qr_code"]
        assert len(data["schedule"]) == 3
        from apps.customers.models import Customer

        assert Customer.objects.filter(cpf="52998224725").exists()

    def test_create_checkout_invalid_api_key(self, api_client):
        api_client.credentials(HTTP_AUTHORIZATION="Bearer pk_live_invalidkeyhere00000000000000000000000000000000")
        response = api_client.post(
            URL,
            {
                "customer": {"cpf": "00000000000"},
                "total_amount": 10000,
                "installment_count": 4,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_checkout_merchant_not_active(self, merchant_user):
        MerchantFactory(user=merchant_user, status="pending")
        service = MerchantService()
        result = service.generate_api_key(user=merchant_user)
        full_key = result.full_key

        customer = ApprovedCustomerFactory()
        response = self._client(full_key).post(
            URL,
            {
                "customer": {"cpf": customer.cpf},
                "total_amount": 10000,
                "installment_count": 4,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestCreditEngine:
    def test_approve_customer_with_good_score(self):
        customer = ApprovedCustomerFactory(approved_limit=50000, used_limit=0)
        engine = CreditEngine()
        decision = engine.decide(customer, 10000)
        assert decision.result == "approve"
        assert decision.approved_amount == 10000

    def test_deny_kyc_not_approved(self):
        customer = ApprovedCustomerFactory(kyc_status="pending")
        engine = CreditEngine()
        decision = engine.decide(customer, 10000)
        assert decision.result == "deny"
        assert decision.reason == "kyc_not_approved"

    def test_deny_blocked_customer(self):
        customer = ApprovedCustomerFactory(is_blocked=True)
        engine = CreditEngine()
        decision = engine.decide(customer, 10000)
        assert decision.result == "deny"
        assert decision.reason == "customer_blocked"

    def test_deny_velocity_exceeded(self):
        customer = ApprovedCustomerFactory()
        engine = CreditEngine()
        for _ in range(2):
            assert engine.decide(customer, 1000).result == "approve"
        decision = engine.decide(customer, 1000)
        assert decision.result == "deny"
        assert decision.reason == "velocity_exceeded"

    def test_deny_exceeds_limit(self):
        customer = ApprovedCustomerFactory(approved_limit=500_00)
        engine = CreditEngine()
        decision = engine.decide(customer, 1000_00)  # exceeds the score-based limit (150_00)
        assert decision.result == "deny"
        assert decision.reason == "amount_exceeds_limit"

    def test_stub_bureau_client(self):
        client = CreditEngine().bureau_client
        result = client.check("12345678909")
        assert isinstance(result, BureauResult)
        assert 500 <= result.score <= 800
