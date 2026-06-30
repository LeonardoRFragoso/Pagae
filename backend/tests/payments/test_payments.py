import pytest
from rest_framework import status

from apps.checkout.services import CheckoutService
from apps.merchants.models import MerchantStatus
from apps.merchants.services import MerchantService
from apps.payments.services import PaymentService
from tests.factories import ApprovedCustomerFactory, MerchantFactory, UserFactory

pytestmark = pytest.mark.django_db

WEBHOOK_URL = "/api/v1/webhooks/celcoin/pix/"


class TestCelcoinWebhook:
    def test_webhook_marks_installment_paid(self, api_client):
        user = UserFactory(role="merchant_owner")
        MerchantFactory(user=user, status=MerchantStatus.ACTIVE)
        service = MerchantService()
        key_result = service.generate_api_key(user=user)

        customer = ApprovedCustomerFactory()
        checkout_service = CheckoutService()
        result = checkout_service.create_session(
            api_key=key_result.full_key,
            data={
                "customer": {"cpf": customer.cpf},
                "total_amount": 10000,
                "installment_count": 4,
            },
        )
        txid = result["txid"]

        response = api_client.post(
            WEBHOOK_URL,
            {"txid": txid, "amount": 25.0, "paidAt": "2026-06-22T12:00:00Z", "payer": {"name": "João", "cpf": "12345678909"}},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()["data"]
        assert data["status"] == "paid"

    def test_webhook_unknown_txid_is_ignored(self, api_client):
        response = api_client.post(
            WEBHOOK_URL,
            {"txid": "unknown-txid-000000000000000000000000000000", "amount": 10.0},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["data"]["status"] == "not_found"

    def test_webhook_invalid_payload_ignored(self, api_client):
        response = api_client.post(WEBHOOK_URL, {"amount": 10.0}, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["data"]["status"] == "ignored"


class TestPaymentService:
    def test_process_payment_already_paid(self):
        user = UserFactory(role="merchant_owner")
        MerchantFactory(user=user, status=MerchantStatus.ACTIVE)
        service = MerchantService()
        key_result = service.generate_api_key(user=user)

        customer = ApprovedCustomerFactory()
        checkout_service = CheckoutService()
        result = checkout_service.create_session(
            api_key=key_result.full_key,
            data={
                "customer": {"cpf": customer.cpf},
                "total_amount": 10000,
                "installment_count": 4,
            },
        )
        txid = result["txid"]
        payment_service = PaymentService()
        payment_service.process_payment(txid)
        second = payment_service.process_payment(txid)
        assert second["status"] == "already_paid"
