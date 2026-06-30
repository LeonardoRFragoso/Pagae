import pytest

from apps.webhooks.models import WebhookDelivery, WebhookStatus
from apps.webhooks.services import WebhookService
from apps.webhooks.tasks import deliver_webhook
from tests.factories import MerchantFactory, UserFactory

pytestmark = pytest.mark.django_db


class TestWebhookService:
    def test_enqueue_creates_delivery(self, mocker):
        user = UserFactory(role="merchant_owner")
        merchant = MerchantFactory(user=user, webhook_url="https://example.com/webhook")
        service = WebhookService()
        mocker.patch("apps.webhooks.tasks.deliver_webhook.delay")
        delivery = service.enqueue(merchant, "checkout.approved", {"checkout_id": "123"})
        assert delivery is not None
        assert delivery.status == WebhookStatus.PENDING
        assert delivery.event_type == "checkout.approved"

    def test_enqueue_skips_without_webhook_url(self):
        user = UserFactory(role="merchant_owner")
        merchant = MerchantFactory(user=user, webhook_url="")
        service = WebhookService()
        delivery = service.enqueue(merchant, "checkout.approved", {"checkout_id": "123"})
        assert delivery is None

    def test_sign_payload(self):
        user = UserFactory(role="merchant_owner")
        merchant = MerchantFactory(user=user, webhook_secret="super-secret")
        service = WebhookService()
        signature = service.sign_payload({"event": "test"}, merchant.webhook_secret)
        assert len(signature) == 64


class TestWebhookTask:
    def test_deliver_webhook_success(self, mocker):
        user = UserFactory(role="merchant_owner")
        merchant = MerchantFactory(
            user=user,
            webhook_url="https://example.com/webhook",
            webhook_secret="secret",
        )
        delivery = WebhookDelivery.objects.create(
            merchant=merchant,
            event_type="checkout.approved",
            payload={"event": "checkout.approved", "data": {"id": "123"}},
        )
        mock_post = mocker.patch("apps.webhooks.tasks.requests.post")
        mock_post.return_value.status_code = 200
        mock_post.return_value.raise_for_status.return_value = None

        result = deliver_webhook.run(delivery_id=str(delivery.id))

        assert result["status"] == "delivered"
        assert result["http_status"] == 200
        delivery.refresh_from_db()
        assert delivery.status == WebhookStatus.DELIVERED

    def test_deliver_webhook_no_url(self):
        user = UserFactory(role="merchant_owner")
        merchant = MerchantFactory(user=user, webhook_url="")
        delivery = WebhookDelivery.objects.create(merchant=merchant, event_type="checkout.approved", payload={})
        result = deliver_webhook.run(delivery_id=str(delivery.id))
        assert result["status"] == "no_url"

    def test_deliver_webhook_not_found(self):
        result = deliver_webhook.run(delivery_id="123e4567-e89b-12d3-a456-426614174000")
        assert result["status"] == "not_found"
