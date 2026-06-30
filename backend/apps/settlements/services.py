from datetime import date

from apps.checkout.models import CheckoutSession
from apps.ledger.services import LedgerService
from apps.webhooks.services import WebhookService
from integrations.celcoin import CelcoinClient

from .models import Settlement, SettlementStatus
from .repositories import SettlementRepository


class SettlementService:
    def __init__(
        self,
        repository: SettlementRepository | None = None,
        celcoin: CelcoinClient | None = None,
        ledger_service: LedgerService | None = None,
        webhook_service: WebhookService | None = None,
    ) -> None:
        self.repository = repository or SettlementRepository()
        self.celcoin = celcoin or CelcoinClient()
        self.ledger_service = ledger_service or LedgerService()
        self.webhook_service = webhook_service or WebhookService()

    def create_for_checkout(self, checkout: CheckoutSession) -> Settlement:
        return self.repository.create(
            merchant=checkout.merchant,
            amount=checkout.net_amount,
            period_start=date.today(),
            period_end=date.today(),
            status=SettlementStatus.PENDING,
        )

    def settle(self, settlement: Settlement) -> Settlement:
        merchant = settlement.merchant
        settlement = self.repository.update(settlement, status=SettlementStatus.PROCESSING)

        result = self.celcoin.outbound_pix(
            pix_key=merchant.pix_key,
            amount_cents=settlement.amount,
            description=f"Settlement {settlement.id}",
        )

        if result.get("status") == "completed":
            settlement = self.repository.update(
                settlement,
                status=SettlementStatus.COMPLETED,
                pix_e2e_id=result.get("e2e_id", ""),
                paid_at=result.get("paid_at"),
            )

            # Link settlement to all pending checkouts of this merchant
            for checkout in merchant.checkout_sessions.filter(settlement__isnull=True):
                checkout.settlement = settlement
                checkout.settled_at = settlement.paid_at
                checkout.save(update_fields=["settlement", "settled_at", "updated_at"])
                self.ledger_service.post_settlement(checkout)

            self.webhook_service.enqueue(
                merchant,
                "settlement.completed",
                self.webhook_service.build_payload(
                    "settlement.completed",
                    {
                        "settlement_id": str(settlement.id),
                        "amount": settlement.amount,
                        "pix_e2e_id": settlement.pix_e2e_id,
                        "paid_at": settlement.paid_at,
                    },
                ),
            )
        else:
            settlement = self.repository.update(
                settlement,
                status=SettlementStatus.FAILED,
                failure_reason=result.get("failure_reason", "unknown"),
            )

        return settlement
