from __future__ import annotations

import logging
from datetime import date

from apps.customers.repositories import CustomerRepository
from apps.notifications.models import NotificationEventType
from apps.notifications.repositories import NotificationRepository
from apps.notifications.services import NotificationService
from apps.payments.models import Installment, InstallmentStatus
from apps.payments.repositories import InstallmentRepository
from integrations.celcoin import CelcoinClient

from .rules import get_action

logger = logging.getLogger(__name__)


class CollectionsService:
    def __init__(
        self,
        installment_repository: InstallmentRepository | None = None,
        customer_repository: CustomerRepository | None = None,
        notification_service: NotificationService | None = None,
        celcoin: CelcoinClient | None = None,
    ) -> None:
        self.installment_repository = installment_repository or InstallmentRepository()
        self.customer_repository = customer_repository or CustomerRepository()
        self.notification_service = notification_service or NotificationService()
        self.celcoin = celcoin or CelcoinClient()

    def run_daily_overdue_check(self) -> dict[str, int]:
        """Main entry point called by the Celery Beat task each morning."""
        today = date.today()
        stats = {"marked_overdue": 0, "reminders_sent": 0, "qr_refreshed": 0, "limits_suspended": 0}

        # Find all pending installments past their due date
        pending_overdue = list(
            Installment.objects.select_related("checkout__merchant", "customer")
            .filter(due_date__lt=today, status=InstallmentStatus.PENDING)
        )

        for installment in pending_overdue:
            dpd = (today - installment.due_date).days
            self.installment_repository.update(installment, days_past_due=dpd, status=InstallmentStatus.OVERDUE)
            stats["marked_overdue"] += 1

            action = get_action(dpd)
            customer = installment.customer

            if action.suspend_limit and not customer.is_blocked:
                self.customer_repository.update(
                    customer,
                    is_blocked=True,
                    blocked_reason=f"DPD {dpd} — automatic suspension",
                )
                self.notification_service.notify_limit_suspended(customer)
                stats["limits_suspended"] += 1
                logger.info("customer_limit_suspended", extra={"customer_id": str(customer.id), "dpd": dpd})

            if action.send_whatsapp or action.send_email:
                notification_repo = NotificationRepository()
                already_notified = notification_repo.has_recent(
                    customer, NotificationEventType.INSTALLMENT_OVERDUE, within_hours=20
                )
                if not already_notified:
                    self.notification_service.notify_installment_overdue(customer, installment.amount, dpd)
                    stats["reminders_sent"] += 1

            if action.generate_new_qr:
                self._refresh_qr(installment)
                stats["qr_refreshed"] += 1

        logger.info("collections_daily_run", extra={"date": today.isoformat(), **stats})
        return stats

    def run_due_soon_reminders(self) -> int:
        """Send reminders for installments due in the next 1 day."""
        from datetime import timedelta

        tomorrow = date.today() + timedelta(days=1)
        due_soon = list(
            Installment.objects.select_related("customer")
            .filter(due_date=tomorrow, status=InstallmentStatus.PENDING)
        )
        notification_repo = NotificationRepository()
        sent = 0
        for installment in due_soon:
            customer = installment.customer
            already = notification_repo.has_recent(customer, NotificationEventType.INSTALLMENT_DUE, within_hours=20)
            if not already:
                self.notification_service.notify_installment_due(
                    customer,
                    installment.amount,
                    installment.due_date.strftime("%d/%m/%Y"),
                )
                sent += 1
        return sent

    def _refresh_qr(self, installment: Installment) -> None:
        """Cancel existing active charge and create a fresh Pix QR for overdue installment."""
        from apps.payments.models import PixCharge, PixChargeStatus
        from apps.payments.repositories import PixChargeRepository

        charge_repo = PixChargeRepository()
        active = PixCharge.objects.filter(installment=installment, status=PixChargeStatus.ACTIVE).first()
        if active:
            charge_repo.update(active, status=PixChargeStatus.EXPIRED)

        result = self.celcoin.create_dynamic_qr(
            amount_cents=installment.amount,
            description=f"Pagaê parcela {installment.number} (reemissão)",
        )
        charge_repo.create(
            installment=installment,
            celcoin_id=result.celcoin_id,
            txid=result.txid,
            amount=installment.amount,
            qr_code=result.qr_code,
            pix_code=result.pix_code,
            expires_at=result.expires_at,
        )
