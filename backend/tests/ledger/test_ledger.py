import pytest

from apps.checkout.services import CheckoutService
from apps.ledger.models import LedgerAccount
from apps.ledger.services import LedgerService
from apps.merchants.models import MerchantStatus
from apps.merchants.services import MerchantService
from apps.payments.services import PaymentService
from tests.factories import ApprovedCustomerFactory, MerchantFactory, UserFactory

pytestmark = pytest.mark.django_db


class TestLedgerService:
    def test_post_checkout_creates_entries(self):
        user = UserFactory(role="merchant_owner")
        MerchantFactory(user=user, status=MerchantStatus.ACTIVE)
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
        assert result["status"] == "approved"

        from apps.checkout.models import CheckoutSession

        checkout = CheckoutSession.objects.get(id=result["id"])
        entries = LedgerService().repository.get_entries_by_checkout(checkout.id)
        accounts: dict[str, int] = {}
        for e in entries:
            accounts[e.account] = accounts.get(e.account, 0) + e.amount
        assert accounts[LedgerAccount.RECEIVABLE] == 10000
        assert accounts[LedgerAccount.MERCHANT_PAYABLE] == -checkout.net_amount
        assert accounts[LedgerAccount.MDR_REVENUE] == -checkout.mdr_amount

    def test_post_installment_payment_creates_entries(self):
        user = UserFactory(role="merchant_owner")
        MerchantFactory(user=user, status=MerchantStatus.ACTIVE)
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
        txid = result["txid"]
        payment_result = PaymentService().process_payment(txid)

        from apps.payments.models import Installment

        installment = Installment.objects.get(id=payment_result["installment_id"])

        entries = LedgerService().repository.get_entries_by_checkout(installment.checkout_id)
        accounts: dict[str, int] = {}
        for e in entries:
            accounts[e.account] = accounts.get(e.account, 0) + e.amount
        assert accounts[LedgerAccount.CASH] == installment.amount
        assert accounts[LedgerAccount.RECEIVABLE] == 10000 - installment.amount
        assert accounts[LedgerAccount.MERCHANT_PAYABLE] == -installment.checkout.net_amount
        assert accounts[LedgerAccount.MDR_REVENUE] == -installment.checkout.mdr_amount
