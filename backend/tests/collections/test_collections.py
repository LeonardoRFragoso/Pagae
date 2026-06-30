from datetime import date, timedelta

import pytest

from apps.collections.rules import DPDAction, get_action
from apps.collections.services import CollectionsService
from apps.merchants.models import MerchantStatus
from apps.merchants.services import MerchantService
from apps.notifications.models import NotificationEventType
from apps.payments.models import Installment, InstallmentStatus
from tests.factories import ApprovedCustomerFactory, MerchantFactory, UserFactory

pytestmark = pytest.mark.django_db


class TestDPDRules:
    def test_no_action_before_due(self):
        action = get_action(0)
        assert action == DPDAction()

    def test_dpd_1_sends_whatsapp_and_refreshes_qr(self):
        action = get_action(1)
        assert action.send_whatsapp is True
        assert action.generate_new_qr is True
        assert action.suspend_limit is False

    def test_dpd_3_adds_email(self):
        action = get_action(3)
        assert action.send_whatsapp is True
        assert action.send_email is True

    def test_dpd_7_suspends_limit(self):
        action = get_action(7)
        assert action.suspend_limit is True

    def test_dpd_10_still_suspends(self):
        action = get_action(10)
        assert action.suspend_limit is True


class TestCollectionsService:
    def _create_checkout_with_overdue(self, days_overdue: int = 1):
        from apps.checkout.services import CheckoutService

        user = UserFactory(role="merchant_owner")
        MerchantFactory(user=user, status=MerchantStatus.ACTIVE)
        key_result = MerchantService().generate_api_key(user=user)
        customer = ApprovedCustomerFactory()
        result = CheckoutService().create_session(
            api_key=key_result.full_key,
            data={"customer": {"cpf": customer.cpf}, "total_amount": 10000, "installment_count": 4},
        )
        installment = Installment.objects.filter(checkout_id=result["id"], number=1).first()
        overdue_date = date.today() - timedelta(days=days_overdue)
        installment.due_date = overdue_date
        installment.save(update_fields=["due_date", "updated_at"])
        return customer, installment

    def test_marks_overdue_and_updates_dpd(self):
        customer, installment = self._create_checkout_with_overdue(days_overdue=2)
        stats = CollectionsService().run_daily_overdue_check()
        assert stats["marked_overdue"] >= 1
        installment.refresh_from_db()
        assert installment.status == InstallmentStatus.OVERDUE
        assert installment.days_past_due == 2

    def test_sends_reminder_notification(self):
        customer, _ = self._create_checkout_with_overdue(days_overdue=1)
        CollectionsService().run_daily_overdue_check()
        assert customer.notifications.filter(event_type=NotificationEventType.INSTALLMENT_OVERDUE).exists()

    def test_suspends_limit_at_dpd_7(self):
        customer, installment = self._create_checkout_with_overdue(days_overdue=7)
        CollectionsService().run_daily_overdue_check()
        customer.refresh_from_db()
        assert customer.is_blocked is True
        assert customer.notifications.filter(event_type=NotificationEventType.LIMIT_SUSPENDED).exists()

    def test_no_duplicate_notifications_same_day(self):
        customer, installment = self._create_checkout_with_overdue(days_overdue=2)
        service = CollectionsService()
        service.run_daily_overdue_check()
        service.run_daily_overdue_check()  # run twice
        notif_count = customer.notifications.filter(event_type=NotificationEventType.INSTALLMENT_OVERDUE).count()
        assert notif_count == 2  # 1 whatsapp + 1 email, no duplicates

    def test_due_soon_reminders(self):
        from apps.checkout.services import CheckoutService

        user = UserFactory(role="merchant_owner")
        MerchantFactory(user=user, status=MerchantStatus.ACTIVE)
        key_result = MerchantService().generate_api_key(user=user)
        customer = ApprovedCustomerFactory()
        result = CheckoutService().create_session(
            api_key=key_result.full_key,
            data={"customer": {"cpf": customer.cpf}, "total_amount": 10000, "installment_count": 4},
        )
        installment = Installment.objects.filter(checkout_id=result["id"], number=1).first()
        tomorrow = date.today() + timedelta(days=1)
        installment.due_date = tomorrow
        installment.save(update_fields=["due_date", "updated_at"])

        sent = CollectionsService().run_due_soon_reminders()
        assert sent >= 1
        assert customer.notifications.filter(event_type=NotificationEventType.INSTALLMENT_DUE).exists()
