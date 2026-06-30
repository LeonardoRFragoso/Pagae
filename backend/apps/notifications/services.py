from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from django.utils import timezone

from integrations.brevo import BrevoClient
from integrations.zapi import ZAPIClient

from .models import Notification, NotificationChannel, NotificationEventType, NotificationStatus
from .repositories import NotificationRepository

if TYPE_CHECKING:
    from apps.customers.models import Customer

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(
        self,
        repository: NotificationRepository | None = None,
        zapi: ZAPIClient | None = None,
        brevo: BrevoClient | None = None,
    ) -> None:
        self.repository = repository or NotificationRepository()
        self.zapi = zapi or ZAPIClient()
        self.brevo = brevo or BrevoClient()

    def notify_checkout_approved(self, customer: Customer, merchant_name: str, total_cents: int) -> None:
        self._send_whatsapp(
            customer=customer,
            event_type=NotificationEventType.CHECKOUT_APPROVED,
            metadata={"merchant_name": merchant_name, "total_cents": total_cents},
            send_fn=lambda: self.zapi.send_checkout_approved(
                customer.phone, customer.full_name, merchant_name, total_cents
            ),
        )
        self._send_email(
            customer=customer,
            event_type=NotificationEventType.CHECKOUT_APPROVED,
            metadata={"merchant_name": merchant_name, "total_cents": total_cents},
            send_fn=lambda: self.brevo.send_checkout_approved(
                customer.email, customer.full_name, merchant_name, total_cents
            ),
        )

    def notify_installment_due(self, customer: Customer, amount_cents: int, due_date: str) -> None:
        self._send_whatsapp(
            customer=customer,
            event_type=NotificationEventType.INSTALLMENT_DUE,
            metadata={"amount_cents": amount_cents, "due_date": due_date},
            send_fn=lambda: self.zapi.send_payment_reminder(
                customer.phone, customer.full_name, amount_cents, due_date
            ),
        )
        self._send_email(
            customer=customer,
            event_type=NotificationEventType.INSTALLMENT_DUE,
            metadata={"amount_cents": amount_cents, "due_date": due_date},
            send_fn=lambda: self.brevo.send_payment_reminder(
                customer.email, customer.full_name, amount_cents, due_date
            ),
        )

    def notify_installment_overdue(self, customer: Customer, amount_cents: int, days_past_due: int) -> None:
        self._send_whatsapp(
            customer=customer,
            event_type=NotificationEventType.INSTALLMENT_OVERDUE,
            metadata={"amount_cents": amount_cents, "days_past_due": days_past_due},
            send_fn=lambda: self.zapi.send_overdue_reminder(
                customer.phone, customer.full_name, amount_cents, days_past_due
            ),
        )
        self._send_email(
            customer=customer,
            event_type=NotificationEventType.INSTALLMENT_OVERDUE,
            metadata={"amount_cents": amount_cents, "days_past_due": days_past_due},
            send_fn=lambda: self.brevo.send_overdue_reminder(
                customer.email, customer.full_name, amount_cents, days_past_due
            ),
        )

    def notify_limit_suspended(self, customer: Customer) -> None:
        self._send_whatsapp(
            customer=customer,
            event_type=NotificationEventType.LIMIT_SUSPENDED,
            metadata={},
            send_fn=lambda: self.zapi.send_text(
                customer.phone,
                f"⛔ {customer.full_name}, seu limite no Pagaê foi suspenso por inadimplência. "
                f"Regularize seus pagamentos em atraso para reativação.",
            ),
        )

    def _send_whatsapp(
        self,
        customer: Customer,
        event_type: str,
        metadata: dict[str, Any],
        send_fn: Any,
    ) -> Notification | None:
        if not customer.phone:
            return None
        notification = self.repository.create(
            customer=customer,
            channel=NotificationChannel.WHATSAPP,
            event_type=event_type,
            metadata=metadata,
        )
        try:
            result = send_fn()
            self.repository.update(
                notification,
                status=NotificationStatus.SENT,
                provider_id=result.get("zaapId", ""),
                sent_at=timezone.now(),
            )
        except Exception:
            logger.exception("whatsapp_send_failed", extra={"customer_id": str(customer.id)})
            self.repository.update(notification, status=NotificationStatus.FAILED)
        return notification

    def _send_email(
        self,
        customer: Customer,
        event_type: str,
        metadata: dict[str, Any],
        send_fn: Any,
    ) -> Notification | None:
        if not customer.email:
            return None
        notification = self.repository.create(
            customer=customer,
            channel=NotificationChannel.EMAIL,
            event_type=event_type,
            metadata=metadata,
        )
        try:
            result = send_fn()
            self.repository.update(
                notification,
                status=NotificationStatus.SENT,
                provider_id=result.get("messageId", ""),
                sent_at=timezone.now(),
            )
        except Exception:
            logger.exception("email_send_failed", extra={"customer_id": str(customer.id)})
            self.repository.update(notification, status=NotificationStatus.FAILED)
        return notification
