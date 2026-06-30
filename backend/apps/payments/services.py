from datetime import date, timedelta
from typing import Any

from django.utils import timezone

from apps.customers.models import Customer
from apps.ledger.services import LedgerService
from apps.webhooks.services import WebhookService

from .models import Installment, InstallmentStatus, PixChargeStatus, TransactionProvider, TransactionStatus
from .providers import PaymentProvider, get_payment_provider
from .repositories import InstallmentRepository, PaymentTransactionRepository, PixChargeRepository


class PaymentService:
    def __init__(
        self,
        installment_repository: InstallmentRepository | None = None,
        charge_repository: PixChargeRepository | None = None,
        transaction_repository: PaymentTransactionRepository | None = None,
        provider: PaymentProvider | None = None,
        ledger_service: LedgerService | None = None,
        webhook_service: WebhookService | None = None,
    ) -> None:
        self.installment_repository = installment_repository or InstallmentRepository()
        self.charge_repository = charge_repository or PixChargeRepository()
        self.transaction_repository = transaction_repository or PaymentTransactionRepository()
        self.provider = provider or get_payment_provider()
        self.ledger_service = ledger_service or LedgerService()
        self.webhook_service = webhook_service or WebhookService()

    def create_installment_plan(
        self,
        checkout: Any,
        customer: Customer,
        total_amount: int,
        installment_count: int,
        installment_amount: int,
    ) -> tuple[list[dict[str, Any]], Any]:
        schedule = []
        first_charge = None
        today = date.today()

        for i in range(1, installment_count + 1):
            # Last installment absorbs rounding differences
            amount = installment_amount if i < installment_count else total_amount - (installment_count - 1) * installment_amount
            due_date = today + timedelta(days=15 * (i - 1))

            installment = self.installment_repository.create(
                checkout=checkout,
                customer=customer,
                number=i,
                amount=amount,
                due_date=due_date,
            )

            charge = self._create_charge(installment, amount, f"Parcela {i}/{installment_count}")
            if i == 1:
                first_charge = charge

            schedule.append(
                {
                    "number": i,
                    "amount": amount,
                    "due_date": due_date,
                    "status": installment.status,
                    "pix_charge_id": str(charge.id),
                }
            )

        return schedule, first_charge

    def _create_charge(self, installment: Installment, amount: int, description: str) -> Any:
        result = self.provider.create_charge(amount_cents=amount, description=description)
        charge = self.charge_repository.create(
            installment=installment,
            celcoin_id=result.provider_transaction_id,
            txid=result.txid,
            amount=amount,
            qr_code=result.qr_code,
            pix_code=result.pix_code,
            status=PixChargeStatus.ACTIVE,
            expires_at=result.expires_at,
        )
        self.transaction_repository.create(
            installment=installment,
            provider=TransactionProvider(self.provider.name),
            provider_transaction_id=result.provider_transaction_id,
            amount=amount,
            status=TransactionStatus.PENDING,
            payload={
                "txid": result.txid,
                "qr_code": result.qr_code,
                "pix_code": result.pix_code,
                "expires_at": result.expires_at.isoformat(),
            },
        )
        return charge

    def process_payment(self, txid: str, paid_at: Any | None = None) -> dict[str, Any]:
        charge = self.charge_repository.get_by_txid(txid)
        if charge is None:
            return {"status": "not_found", "txid": txid}

        installment = charge.installment
        if charge.status == PixChargeStatus.PAID:
            return {"status": "already_paid", "installment_id": str(installment.id)}

        paid_at = paid_at or timezone.now()
        self.charge_repository.update(
            charge,
            status=PixChargeStatus.PAID,
            paid_at=paid_at,
        )
        self.installment_repository.update(
            installment,
            status=InstallmentStatus.PAID,
            paid_at=paid_at,
        )

        transaction = self._get_transaction_for_txid(txid)
        if transaction is None:
            transaction = self.transaction_repository.create(
                installment=installment,
                provider=TransactionProvider(self.provider.name),
                provider_transaction_id="",
                amount=installment.amount,
                status=TransactionStatus.PENDING,
                payload={"txid": txid},
            )
        self.transaction_repository.update(
            transaction,
            status=TransactionStatus.PAID,
            paid_at=paid_at,
            webhook_payload={"txid": txid, "paid_at": str(paid_at)},
        )

        self.ledger_service.post_installment_payment(installment)
        checkout = installment.checkout
        self.webhook_service.enqueue(
            checkout.merchant,
            "installment.paid",
            self.webhook_service.build_payload(
                "installment.paid",
                {
                    "checkout_id": str(checkout.id),
                    "installment_id": str(installment.id),
                    "installment_number": installment.number,
                    "amount": installment.amount,
                    "paid_at": paid_at,
                },
            ),
        )
        return {"status": "paid", "installment_id": str(installment.id)}

    def _get_transaction_for_txid(self, txid: str) -> Any | None:
        return self.transaction_repository.get_by_txid(txid)
