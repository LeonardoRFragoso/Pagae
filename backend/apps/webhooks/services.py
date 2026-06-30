import hashlib
import hmac
import json
import logging
from typing import Any

from apps.merchants.models import Merchant

from .models import WebhookDelivery
from .repositories import WebhookDeliveryRepository

logger = logging.getLogger(__name__)


class WebhookService:
    def __init__(self, repository: WebhookDeliveryRepository | None = None) -> None:
        self.repository = repository or WebhookDeliveryRepository()

    def enqueue(self, merchant: Merchant, event_type: str, payload: dict[str, Any]) -> WebhookDelivery | None:
        if not merchant.webhook_url:
            return None
        delivery = self.repository.create(
            merchant=merchant,
            event_type=event_type,
            payload=payload,
        )
        logger.info(
            "webhook_enqueued",
            extra={"delivery_id": str(delivery.id), "event_type": event_type, "merchant_id": str(merchant.id)},
        )
        from .tasks import deliver_webhook

        deliver_webhook.delay(str(delivery.id))
        return delivery

    def sign_payload(self, payload: dict[str, Any], secret: str) -> str:
        body = json.dumps(payload, separators=(",", ":"), sort_keys=True)
        return hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()

    def build_payload(self, event_type: str, data: dict[str, Any]) -> dict[str, Any]:
        return {"event": event_type, "data": data}
