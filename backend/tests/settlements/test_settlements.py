import pytest
from rest_framework import status

from apps.checkout.services import CheckoutService
from apps.merchants.models import MerchantStatus
from apps.merchants.services import MerchantService
from apps.settlements.models import SettlementStatus
from apps.settlements.services import SettlementService
from tests.factories import ApprovedCustomerFactory, MerchantFactory, UserFactory

pytestmark = pytest.mark.django_db

URL = "/api/v1/settlements/checkout/{}/"


class TestSettlement:
    def test_settle_by_checkout_success(self, api_client):
        user = UserFactory(role="merchant_owner")
        merchant = MerchantFactory(user=user, status=MerchantStatus.ACTIVE, pix_key="loja@teste.com")
        key_result = MerchantService().generate_api_key(user=user)
        customer = ApprovedCustomerFactory()

        result = CheckoutService().create_session(
            api_key=key_result.full_key,
            data={
                "customer": {"cpf": customer.cpf},
                "total_amount": 10000,
                "installment_count": 4,
            },
        )
        checkout_id = result["id"]

        api_client.force_authenticate(user=user)
        response = api_client.post(URL.format(checkout_id), {}, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()["data"]
        assert data["status"] == SettlementStatus.COMPLETED
        assert data["amount"] == merchant.checkout_sessions.first().net_amount

    def test_settle_forbidden_for_customer(self, api_client, customer_user):
        user = UserFactory(role="merchant_owner")
        MerchantFactory(user=user, status=MerchantStatus.ACTIVE, pix_key="loja@teste.com")
        key_result = MerchantService().generate_api_key(user=user)
        customer = ApprovedCustomerFactory()

        result = CheckoutService().create_session(
            api_key=key_result.full_key,
            data={
                "customer": {"cpf": customer.cpf},
                "total_amount": 10000,
                "installment_count": 4,
            },
        )
        api_client.force_authenticate(user=customer_user)
        response = api_client.post(URL.format(result["id"]), {}, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_settle_service_fails_without_pix_key(self):
        user = UserFactory(role="merchant_owner")
        MerchantFactory(user=user, status=MerchantStatus.ACTIVE, pix_key="")
        key_result = MerchantService().generate_api_key(user=user)
        customer = ApprovedCustomerFactory()

        result = CheckoutService().create_session(
            api_key=key_result.full_key,
            data={
                "customer": {"cpf": customer.cpf},
                "total_amount": 10000,
                "installment_count": 4,
            },
        )
        from apps.checkout.models import CheckoutSession

        checkout = CheckoutSession.objects.get(id=result["id"])
        service = SettlementService()
        settlement = service.create_for_checkout(checkout)
        settlement = service.settle(settlement)
        assert settlement.status == SettlementStatus.FAILED
