from apps.checkout.models import CheckoutSession
from apps.payments.models import Installment

from .models import LedgerAccount
from .repositories import LedgerRepository


class LedgerService:
    def __init__(self, repository: LedgerRepository | None = None) -> None:
        self.repository = repository or LedgerRepository()

    def post_checkout(self, checkout: CheckoutSession) -> None:
        merchant = checkout.merchant
        # Debit receivable
        self.repository.create(
            merchant=merchant,
            checkout=checkout,
            account=LedgerAccount.RECEIVABLE,
            amount=checkout.total_amount,
            description=f"Receivable from checkout {checkout.id}",
            reference=str(checkout.id),
        )
        # Credit merchant payable
        self.repository.create(
            merchant=merchant,
            checkout=checkout,
            account=LedgerAccount.MERCHANT_PAYABLE,
            amount=-checkout.net_amount,
            description=f"Merchant payable for checkout {checkout.id}",
            reference=str(checkout.id),
        )
        # Credit MDR revenue
        self.repository.create(
            merchant=merchant,
            checkout=checkout,
            account=LedgerAccount.MDR_REVENUE,
            amount=-checkout.mdr_amount,
            description=f"MDR revenue for checkout {checkout.id}",
            reference=str(checkout.id),
        )

    def post_installment_payment(self, installment: Installment) -> None:
        checkout = installment.checkout
        merchant = checkout.merchant
        # Debit cash, credit receivable
        self.repository.create(
            merchant=merchant,
            checkout=checkout,
            installment=installment,
            account=LedgerAccount.CASH,
            amount=installment.amount,
            description=f"Cash from installment {installment.number}",
            reference=str(installment.id),
        )
        self.repository.create(
            merchant=merchant,
            checkout=checkout,
            installment=installment,
            account=LedgerAccount.RECEIVABLE,
            amount=-installment.amount,
            description=f"Reduce receivable for installment {installment.number}",
            reference=str(installment.id),
        )

    def post_settlement(self, checkout: CheckoutSession) -> None:
        merchant = checkout.merchant
        # Debit merchant payable, credit cash
        self.repository.create(
            merchant=merchant,
            checkout=checkout,
            account=LedgerAccount.MERCHANT_PAYABLE,
            amount=checkout.net_amount,
            description=f"Settle merchant payable for checkout {checkout.id}",
            reference=str(checkout.id),
        )
        self.repository.create(
            merchant=merchant,
            checkout=checkout,
            account=LedgerAccount.CASH,
            amount=-checkout.net_amount,
            description=f"Cash out for settlement of checkout {checkout.id}",
            reference=str(checkout.id),
        )
