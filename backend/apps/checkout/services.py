import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from apps.customers.models import Customer
from apps.customers.repositories import CustomerRepository
from apps.ledger.services import LedgerService
from apps.merchants.services import MerchantService
from apps.notifications.services import NotificationService
from apps.payments.services import PaymentService
from apps.webhooks.services import WebhookService
from core.exceptions import ForbiddenError, NotFoundError

from .credit import CreditEngine
from .models import CheckoutStatus
from .repositories import CheckoutRepository

logger = logging.getLogger(__name__)


class CheckoutService:
    def __init__(
        self,
        repository: CheckoutRepository | None = None,
        customer_repository: CustomerRepository | None = None,
        merchant_service: MerchantService | None = None,
        payment_service: PaymentService | None = None,
        credit_engine: CreditEngine | None = None,
        ledger_service: LedgerService | None = None,
        webhook_service: WebhookService | None = None,
        notification_service: NotificationService | None = None,
    ) -> None:
        self.repository = repository or CheckoutRepository()
        self.customer_repository = customer_repository or CustomerRepository()
        self.merchant_service = merchant_service or MerchantService()
        self.payment_service = payment_service or PaymentService()
        self.credit_engine = credit_engine or CreditEngine()
        self.ledger_service = ledger_service or LedgerService()
        self.webhook_service = webhook_service or WebhookService()
        self.notification_service = notification_service or NotificationService()

    def create_session(self, api_key: str, data: dict[str, Any]) -> dict[str, Any]:
        api_key_obj = self.merchant_service.verify_api_key(api_key)
        if api_key_obj is None:
            raise ForbiddenError("Invalid API key.")
        merchant = api_key_obj.merchant
        if not merchant.is_active:
            raise ForbiddenError("Merchant is not active.")

        customer = self._resolve_customer(data["customer"])
        if customer is None:
            raise NotFoundError("Customer not found.", "customer_not_found")

        total_amount = data["total_amount"]
        installment_count = data["installment_count"]
        installment_amount = total_amount // installment_count
        mdr_amount = int(total_amount * float(merchant.mdr_rate))
        net_amount = total_amount - mdr_amount

        decision = self.credit_engine.decide(customer, total_amount)

        checkout = self.repository.create(
            merchant=merchant,
            customer=customer,
            merchant_order_id=data.get("merchant_order_id", ""),
            total_amount=total_amount,
            mdr_amount=mdr_amount,
            net_amount=net_amount,
            installment_count=installment_count,
            installment_amount=installment_amount,
            status=CheckoutStatus.APPROVED if decision.result == "approve" else CheckoutStatus.DENIED,
            decision=decision.result,
            denial_reason=decision.reason,
            serasa_score_at_decision=decision.score,
            expires_at=datetime.now(UTC) + timedelta(minutes=30),
        )

        schedule: list[dict[str, Any]] = []
        txid = ""
        qr_code = ""
        pix_code = ""

        if decision.result == "approve":
            self.credit_engine.refresh_limit(customer, total_amount)
            self.ledger_service.post_checkout(checkout)
            schedule, first_charge = self.payment_service.create_installment_plan(
                checkout=checkout,
                customer=customer,
                total_amount=total_amount,
                installment_count=installment_count,
                installment_amount=installment_amount,
            )
            txid = first_charge.txid
            qr_code = first_charge.qr_code
            pix_code = first_charge.pix_code
            self.webhook_service.enqueue(
                merchant,
                "checkout.approved",
                self.webhook_service.build_payload(
                    "checkout.approved",
                    {
                        "checkout_id": str(checkout.id),
                        "merchant_order_id": checkout.merchant_order_id,
                        "total_amount": checkout.total_amount,
                        "installment_count": checkout.installment_count,
                        "status": checkout.status,
                    },
                ),
            )
            self.notification_service.notify_checkout_approved(
                customer,
                merchant.trade_name or merchant.legal_name,
                total_amount,
            )
            logger.info(
                "checkout_approved",
                extra={
                    "checkout_id": str(checkout.id),
                    "merchant_id": str(merchant.id),
                    "customer_id": str(customer.id),
                    "amount": total_amount,
                },
            )
        else:
            logger.info(
                "checkout_denied",
                extra={
                    "checkout_id": str(checkout.id),
                    "customer_id": str(customer.id),
                    "reason": decision.reason,
                },
            )

        return {
            "id": checkout.id,
            "status": checkout.status,
            "decision": checkout.decision,
            "denial_reason": checkout.denial_reason,
            "total_amount": checkout.total_amount,
            "installment_count": checkout.installment_count,
            "installment_amount": checkout.installment_amount,
            "schedule": schedule,
            "txid": txid,
            "qr_code": qr_code,
            "pix_code": pix_code,
            "expires_at": checkout.expires_at,
        }

    def _resolve_customer(self, identifier: dict[str, Any]) -> Customer | None:
        if identifier.get("cpf"):
            cpf = identifier["cpf"].replace(".", "").replace("-", "")
            return self.customer_repository.get_by_cpf(cpf)
        if identifier.get("email"):
            return Customer.objects.filter(email=identifier["email"]).first()
        if identifier.get("phone"):
            return Customer.objects.filter(phone=identifier["phone"]).first()
        return None
