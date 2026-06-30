from .models import WebhookDelivery


class WebhookDeliveryRepository:
    def create(self, **kwargs) -> WebhookDelivery:
        return WebhookDelivery.objects.create(**kwargs)

    def update(self, delivery: WebhookDelivery, **kwargs) -> WebhookDelivery:
        for key, value in kwargs.items():
            setattr(delivery, key, value)
        delivery.save(update_fields=[*kwargs.keys(), "updated_at"])
        return delivery

    def get_pending(self, limit: int = 100) -> list[WebhookDelivery]:
        return list(
            WebhookDelivery.objects.select_related("merchant")
            .filter(status=WebhookDelivery.PENDING)
            .order_by("created_at")[:limit]
        )
