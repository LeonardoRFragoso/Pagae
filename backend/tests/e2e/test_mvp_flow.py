import random
import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User, UserRole
from apps.checkout.models import OrderStatus
from apps.customers.models import Customer, KYCStatus
from apps.merchants.models import Merchant, MerchantApiKey, MerchantStatus
from apps.payments.models import InstallmentStatus, PixChargeStatus


def _calc_digit(cpf_or_cnpj: list[int], weights: list[int]) -> int:
    total = sum(d * w for d, w in zip(cpf_or_cnpj, weights, strict=False))
    digit = (total * 10 % 11) % 10
    return digit


def generate_valid_cpf() -> str:
    digits = [random.randint(0, 9) for _ in range(9)]
    digits.append(_calc_digit(digits, [10, 9, 8, 7, 6, 5, 4, 3, 2]))
    digits.append(_calc_digit(digits, [11, 10, 9, 8, 7, 6, 5, 4, 3, 2]))
    return "".join(str(d) for d in digits)


def generate_valid_cnpj() -> str:
    digits = [random.randint(0, 9) for _ in range(12)]
    weights1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    weights2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]

    def calc_digit(digits_: list[int], weights: list[int]) -> int:
        total = sum(d * w for d, w in zip(digits_, weights, strict=False))
        remainder = total % 11
        return 0 if remainder < 2 else 11 - remainder

    digits.append(calc_digit(digits, weights1))
    digits.append(calc_digit(digits, weights2))
    return "".join(str(d) for d in digits)


pytestmark = pytest.mark.django_db


class TestMVPFlow:
    def test_full_merchant_checkout_and_payment_flow(self, mocker):
        # Mock external webhook delivery so it doesn't try HTTP in tests.
        mocker.patch("apps.webhooks.tasks.deliver_webhook.delay")

        merchant_client = APIClient()
        customer_client = APIClient()

        merchant_cnpj = generate_valid_cnpj()
        customer_cpf = generate_valid_cpf()

        # 1. Register merchant owner
        merchant_user_payload = {
            "email": "lojista@pagae.local",
            "password": "SenhaSegura123",
            "phone": "+5511988888888",
            "role": "merchant_owner",
        }
        response = merchant_client.post("/api/v1/auth/register/", merchant_user_payload, format="json")
        assert response.status_code == 201, response.data
        merchant_user = User.objects.get(email=merchant_user_payload["email"])

        # 2. Login
        login_response = merchant_client.post(
            "/api/v1/auth/login/",
            {"email": merchant_user_payload["email"], "password": merchant_user_payload["password"]},
            format="json",
        )
        assert login_response.status_code == 200, login_response.data
        merchant_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login_response.data['access']}")

        # 3. Create merchant profile
        merchant_response = merchant_client.post(
            "/api/v1/merchants/",
            {
                "legal_name": "Loja Demo Pagaê Ltda",
                "trade_name": "Loja Demo Pagaê",
                "cnpj": merchant_cnpj,
                "email": "lojista@pagae.local",
                "phone": "+5511988888888",
                "website": "https://lojademo.pagae.local",
                "pix_key": "lojista@pagae.local",
            },
            format="json",
        )
        assert merchant_response.status_code == 201, merchant_response.data
        merchant = Merchant.objects.get(user=merchant_user)
        merchant.status = MerchantStatus.ACTIVE
        merchant.save()
        assert merchant.trade_name == "Loja Demo Pagaê"

        # 4. Create API key
        api_key_response = merchant_client.post(
            "/api/v1/merchants/api-keys/",
            {"name": "Sandbox Key", "environment": "sandbox"},
            format="json",
        )
        assert api_key_response.status_code == 201, api_key_response.data
        full_key = api_key_response.data["data"]["full_key"]
        assert MerchantApiKey.objects.filter(merchant=merchant).exists()

        api_key_client = APIClient()
        api_key_client.credentials(HTTP_AUTHORIZATION=f"Bearer {full_key}")

        # 5. Register customer user
        customer_user_payload = {
            "email": "cliente@pagae.local",
            "password": "SenhaSegura123",
            "phone": "+5511999999999",
            "role": "customer",
        }
        customer_response = customer_client.post("/api/v1/auth/register/", customer_user_payload, format="json")
        assert customer_response.status_code == 201, customer_response.data
        customer_user = User.objects.get(email=customer_user_payload["email"])

        customer_login = customer_client.post(
            "/api/v1/auth/login/",
            {"email": customer_user_payload["email"], "password": customer_user_payload["password"]},
            format="json",
        )
        assert customer_login.status_code == 200, customer_login.data
        customer_client.credentials(HTTP_AUTHORIZATION=f"Bearer {customer_login.data['access']}")

        # 6. Create customer profile
        customer_profile_response = customer_client.post(
            "/api/v1/customers/",
            {
                "cpf": customer_cpf,
                "full_name": "Cliente Teste",
                "birth_date": "1990-05-15",
                "phone": "+5511999999999",
                "email": "cliente@pagae.local",
                "cep": "01001000",
                "street": "Rua Augusta",
                "number": "100",
                "complement": "Apto 42",
                "neighborhood": "Consolação",
                "city": "São Paulo",
                "state": "SP",
            },
            format="json",
        )
        assert customer_profile_response.status_code == 201, customer_profile_response.data
        customer = Customer.objects.get(user=customer_user)
        assert customer.cpf == customer_cpf

        # 7. Sandbox KYC approval and credit limit
        customer.kyc_status = KYCStatus.APPROVED
        customer.approved_limit = 50_000  # R$ 500,00
        customer.serasa_score = 750
        customer.save()

        # 8. Create order via API key
        order_response = api_key_client.post(
            "/api/v1/orders/",
            {
                "merchant_order_id": "ORDER-001",
                "customer": {"cpf": customer_cpf},
                "total_amount": 30_000,  # R$ 300,00
                "installment_count": 3,
                "description": "Pedido sandbox Pagaê",
            },
            format="json",
        )
        assert order_response.status_code == 201, order_response.data
        order_id = order_response.data["data"]["id"]
        assert order_response.data["data"]["total_amount"] == 30_000
        assert order_response.data["data"]["installment_count"] == 3

        # 9. Create checkout session via API key
        checkout_response = api_key_client.post(
            "/api/v1/checkout/",
            {
                "order_id": order_id,
                "customer": {"cpf": customer_cpf},
                "total_amount": 30_000,
                "installment_count": 3,
                "description": "Pedido sandbox Pagaê",
            },
            format="json",
        )
        assert checkout_response.status_code == 201, checkout_response.data
        checkout_data = checkout_response.data["data"]
        assert checkout_data["decision"] == "approve"
        assert checkout_data["status"] == "approved"
        assert checkout_data["total_amount"] == 30_000
        assert checkout_data["installment_count"] == 3
        assert checkout_data["pix_code"]
        assert checkout_data["txid"]
        assert len(checkout_data["schedule"]) == 3
        checkout_id = checkout_data["id"]
        txid = checkout_data["txid"]

        # 10. Public checkout page
        public_response = merchant_client.get(f"/api/v1/checkout/{checkout_id}/")
        assert public_response.status_code == 200, public_response.data
        public_data = public_response.data["data"]
        assert public_data["merchant_name"] == "Loja Demo Pagaê"
        assert public_data["customer_name"] == "Cliente Teste"
        assert public_data["first_pix"]["txid"] == txid
        assert len(public_data["schedule"]) == 3

        # 11. Simulate payment of first installment
        payment_response = merchant_client.post(
            "/api/v1/payments/simulate/",
            {"txid": txid},
            format="json",
        )
        assert payment_response.status_code == 200, payment_response.data
        assert payment_response.data["data"]["status"] == "paid"

        # 12. Verify installment status
        from apps.payments.models import Installment, PixCharge

        first_installment = Installment.objects.get(checkout_id=checkout_id, number=1)
        assert first_installment.status == InstallmentStatus.PAID
        first_charge = PixCharge.objects.get(installment=first_installment)
        assert first_charge.status == PixChargeStatus.PAID

        # 13. Verify future installments are still pending
        future_installments = Installment.objects.filter(checkout_id=checkout_id, number__gt=1)
        assert future_installments.count() == 2
        for inst in future_installments:
            assert inst.status == InstallmentStatus.PENDING

        # 14. Verify credit limit was released for the paid installment
        customer.refresh_from_db()
        assert customer.used_limit == 20_000  # 30_000 - 10_000 first installment

        # 15. Verify order was converted
        from apps.checkout.models import Order

        order = Order.objects.get(id=order_id)
        assert order.status == OrderStatus.CONVERTED

        # 16. Dashboard metrics
        dashboard_response = merchant_client.get("/api/v1/merchants/dashboard/")
        assert dashboard_response.status_code == 200, dashboard_response.data
        dashboard = dashboard_response.data["data"]
        assert dashboard["total_sold"] == 30_000
        assert dashboard["orders_created"] == 1
        assert dashboard["installments_paid"] == 1
        assert dashboard["installments_pending"] == 2
        assert dashboard["installments_overdue"] == 0

        # 17. Business rule: no anticipation / settlement on the spot
        assert dashboard.get("pending_settlement", 0) == 0 or dashboard["pending_settlement"] < 30_000
        from apps.settlements.models import Settlement

        assert Settlement.objects.filter(merchant=merchant).count() == 0
