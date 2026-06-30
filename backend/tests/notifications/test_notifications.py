import pytest

from apps.notifications.models import NotificationChannel, NotificationEventType, NotificationStatus
from apps.notifications.services import NotificationService
from tests.factories import ApprovedCustomerFactory

pytestmark = pytest.mark.django_db


class TestNotificationService:
    def test_notify_checkout_approved_creates_whatsapp_and_email(self):
        customer = ApprovedCustomerFactory()
        service = NotificationService()
        service.notify_checkout_approved(customer, "Loja Teste", 10000)

        notifs = list(customer.notifications.all())
        channels = {n.channel for n in notifs}
        assert NotificationChannel.WHATSAPP in channels
        assert NotificationChannel.EMAIL in channels
        for n in notifs:
            assert n.event_type == NotificationEventType.CHECKOUT_APPROVED
            assert n.status == NotificationStatus.SENT

    def test_notify_installment_overdue_creates_notifications(self):
        customer = ApprovedCustomerFactory()
        service = NotificationService()
        service.notify_installment_overdue(customer, 2500, 3)

        notifs = list(customer.notifications.filter(event_type=NotificationEventType.INSTALLMENT_OVERDUE))
        assert len(notifs) == 2  # whatsapp + email

    def test_notify_limit_suspended_whatsapp_only(self):
        customer = ApprovedCustomerFactory()
        service = NotificationService()
        service.notify_limit_suspended(customer)

        notifs = list(customer.notifications.filter(event_type=NotificationEventType.LIMIT_SUSPENDED))
        assert len(notifs) == 1
        assert notifs[0].channel == NotificationChannel.WHATSAPP

    def test_no_email_when_customer_has_no_email(self):
        customer = ApprovedCustomerFactory(email="")
        service = NotificationService()
        service.notify_installment_due(customer, 2500, "25/12/2026")

        notifs = list(customer.notifications.all())
        assert all(n.channel == NotificationChannel.WHATSAPP for n in notifs)

    def test_has_recent_deduplication(self):
        customer = ApprovedCustomerFactory()
        from apps.notifications.repositories import NotificationRepository

        repo = NotificationRepository()
        assert not repo.has_recent(customer, NotificationEventType.INSTALLMENT_OVERDUE)
        repo.create(
            customer=customer,
            channel=NotificationChannel.WHATSAPP,
            event_type=NotificationEventType.INSTALLMENT_OVERDUE,
        )
        assert repo.has_recent(customer, NotificationEventType.INSTALLMENT_OVERDUE)
