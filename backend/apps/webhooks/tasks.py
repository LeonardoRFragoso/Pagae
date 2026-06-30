import logging

import requests
from django.utils import timezone

from config.celery import app

from .models import WebhookDelivery, WebhookStatus
from .repositories import WebhookDeliveryRepository
from .services import WebhookService

logger = logging.getLogger(__name__)


@app.task(bind=True, max_retries=5, default_retry_delay=60)
def deliver_webhook(self, delivery_id: str) -> dict:
    repository = WebhookDeliveryRepository()
    service = WebhookService(repository)

    try:
        delivery = WebhookDelivery.objects.select_related("merchant").get(id=delivery_id)
    except WebhookDelivery.DoesNotExist:
        logger.warning("webhook_delivery_not_found", extra={"delivery_id": delivery_id})
        return {"status": "not_found"}

    merchant = delivery.merchant
    if not merchant.webhook_url:
        repository.update(delivery, status=WebhookStatus.EXHAUSTED)
        return {"status": "no_url"}

    signature = ""
    if merchant.webhook_secret:
        signature = service.sign_payload(delivery.payload, merchant.webhook_secret)

    headers = {"Content-Type": "application/json"}
    if signature:
        headers["X-Pagae-Signature"] = signature

    try:
        response = requests.post(
            merchant.webhook_url,
            json=delivery.payload,
            headers=headers,
            timeout=10,
        )
        http_status = response.status_code
        response.raise_for_status()
        repository.update(
            delivery,
            status=WebhookStatus.DELIVERED,
            http_status=http_status,
            attempts=delivery.attempts + 1,
            delivered_at=timezone.now(),
        )
        logger.info(
            "webhook_delivered",
            extra={"delivery_id": delivery_id, "http_status": http_status},
        )
        return {"status": "delivered", "http_status": http_status}
    except requests.HTTPError as exc:
        status = http_status if "http_status" in dir() else None
        repository.update(delivery, attempts=delivery.attempts + 1, http_status=status)
        logger.warning("webhook_http_error", extra={"delivery_id": delivery_id, "http_status": status})
        raise self.retry(countdown=60 * (self.request.retries + 1), exc=exc) from exc
    except requests.RequestException as exc:
        repository.update(delivery, attempts=delivery.attempts + 1)
        logger.warning("webhook_request_error", extra={"delivery_id": delivery_id, "error": str(exc)})
        raise self.retry(countdown=60 * (self.request.retries + 1), exc=exc) from exc
