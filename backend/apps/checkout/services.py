import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from apps.customers.models import Customer
from apps.customers.repositories import CustomerRepository
from apps.customers.services import CustomerService
from apps.ledger.services import LedgerService
from apps.merchants.services import MerchantService
from apps.notifications.services import NotificationService
from apps.payments.models import PixChargeStatus
from apps.payments.services import PaymentService
from apps.webhooks.services import WebhookService
from core.exceptions import ForbiddenError, NotFoundError

from .credit import CreditEngine
from .models import CheckoutStatus, OrderStatus
from .repositories import CheckoutRepository, OrderRepository, RiskAnalysisRepository

logger = logging.getLogger(__name__)


class CheckoutService:
    def __init__(
        self,
        repository: CheckoutRepository | None = None,
        order_repository: OrderRepository | None = None,
        risk_repository: RiskAnalysisRepository | None = None,
        customer_repository: CustomerRepository | None = None,
        merchant_service: MerchantService | None = None,
        payment_service: PaymentService | None = None,
        credit_engine: CreditEngine | None = None,
        ledger_service: LedgerService | None = None,
        webhook_service: WebhookService | None = None,
        notification_service: NotificationService | None = None,
    ) -> None:
        self.repository = repository or CheckoutRepository()
        self.order_repository = order_repository or OrderRepository()
        self.risk_repository = risk_repository or RiskAnalysisRepository()
        self.customer_repository = customer_repository or CustomerRepository()
        self.merchant_service = merchant_service or MerchantService()
        self.payment_service = payment_service or PaymentService()
        self.credit_engine = credit_engine or CreditEngine()
        self.ledger_service = ledger_service or LedgerService()
        self.webhook_service = webhook_service or WebhookService()
        self.notification_service = notification_service or NotificationService()

    def _authenticate_merchant(self, api_key: str) -> Any:
        api_key_obj = self.merchant_service.verify_api_key(api_key)
        if api_key_obj is None:
            raise ForbiddenError("Invalid API key.")
        if not api_key_obj.merchant.is_active:
            raise ForbiddenError("Merchant is not active.")
        return api_key_obj.merchant

    def create_order(self, api_key: str, data: dict[str, Any]) -> Any:
        merchant = self._authenticate_merchant(api_key)
        customer = self._resolve_customer(data.get("customer", {}))
        order = self.order_repository.create(
            merchant=merchant,
            customer=customer,
            merchant_order_id=data.get("merchant_order_id", ""),
            total_amount=data["total_amount"],
            installment_count=data.get("installment_count", 1),
            description=data.get("description", ""),
            status=OrderStatus.CREATED,
            expires_at=datetime.now(UTC) + timedelta(minutes=30),
        )
        logger.info(
            "order_created",
            extra={"order_id": str(order.id), "merchant_id": str(merchant.id)},
        )
        return order

    def create_session(self, api_key: str, data: dict[str, Any]) -> dict[str, Any]:
        merchant = self._authenticate_merchant(api_key)

        order = None
        if data.get("order_id"):
            order = self.order_repository.get_by_id(data["order_id"])
            if order.merchant_id != merchant.id:
                raise ForbiddenError("Order does not belong to this merchant.")

        customer = self._resolve_customer(data.get("customer", {}))
        if customer is None and order and order.customer:
            customer = order.customer
        if customer is None:
            raise NotFoundError("Customer not found.", "customer_not_found")

        total_amount = data.get("total_amount", order.total_amount if order else 0)
        installment_count = data.get(
            "installment_count",
            order.installment_count if order else data.get("installment_count", 1),
        )
        installment_amount = total_amount // installment_count
        mdr_amount = int(total_amount * float(merchant.mdr_rate))
        net_amount = total_amount - mdr_amount

        decision = self.credit_engine.decide(customer, total_amount)

        order = order or self.order_repository.create(
            merchant=merchant,
            customer=customer,
            merchant_order_id=data.get("merchant_order_id", ""),
            total_amount=total_amount,
            installment_count=installment_count,
            description=data.get("description", ""),
            status=OrderStatus.CREATED,
            expires_at=datetime.now(UTC) + timedelta(minutes=30),
        )

        checkout = self.repository.create(
            merchant=merchant,
            customer=customer,
            order=order,
            merchant_order_id=order.merchant_order_id,
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

        self.risk_repository.create(
            checkout=checkout,
            customer=customer,
            requested_amount=total_amount,
            decision=decision.result,
            reasons=decision.reasons,
            score=decision.score,
            approved_limit=decision.approved_limit,
        )

        schedule: list[dict[str, Any]] = []
        txid = ""
        qr_code = ""
        pix_code = ""

        if decision.result == "approve":
            self.order_repository.update(order, status=OrderStatus.CONVERTED)
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
                        "order_id": str(order.id),
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
                    "order_id": str(order.id),
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
                    "reasons": decision.reasons,
                },
            )

        return {
            "id": checkout.id,
            "order_id": order.id,
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

    def get_public_checkout(self, checkout_id: str) -> dict[str, Any]:
        checkout = self.repository.get_by_id(checkout_id)
        first_charge = None
        first_installment = checkout.installments.filter(number=1).first()
        if first_installment:
            first_charge = first_installment.pix_charges.filter(
                status=PixChargeStatus.ACTIVE
            ).first()

        schedule = [
            {
                "number": i.number,
                "amount": i.amount,
                "due_date": i.due_date,
                "status": i.status,
            }
            for i in checkout.installments.all().order_by("number")
        ]

        return {
            "id": checkout.id,
            "status": checkout.status,
            "decision": checkout.decision,
            "denial_reason": checkout.denial_reason,
            "total_amount": checkout.total_amount,
            "installment_count": checkout.installment_count,
            "installment_amount": checkout.installment_amount,
            "merchant_name": checkout.merchant.trade_name or checkout.merchant.legal_name,
            "customer_name": checkout.customer.full_name,
            "expires_at": checkout.expires_at,
            "schedule": schedule,
            "first_pix": {
                "txid": first_charge.txid if first_charge else None,
                "qr_code": first_charge.qr_code if first_charge else None,
                "pix_code": first_charge.pix_code if first_charge else None,
                "amount": first_charge.amount if first_charge else None,
            },
        }

    def _resolve_customer(self, identifier: dict[str, Any]) -> Customer | None:
        if not identifier:
            return None

        cpf = identifier.get("cpf", "").replace(".", "").replace("-", "")
        if cpf:
            customer = self.customer_repository.get_by_cpf(cpf)
            if customer is None:
                customer = CustomerService().get_or_create_for_merchant(
                    {
                        "cpf": cpf,
                        "full_name": identifier.get("full_name", ""),
                        "email": identifier.get("email", ""),
                        "phone": identifier.get("phone", ""),
                    }
                )
            else:
                updatable = {
                    "full_name": identifier.get("full_name", customer.full_name),
                    "email": identifier.get("email", customer.email),
                    "phone": identifier.get("phone", customer.phone),
                }
                customer = self.customer_repository.update(customer, **updatable)
            return customer

        if identifier.get("email"):
            customer = Customer.objects.filter(email=identifier["email"]).first()
            if customer:
                return customer
        if identifier.get("phone"):
            customer = Customer.objects.filter(phone=identifier["phone"]).first()
            if customer:
                return customer
        return None
