from typing import Any

from apps.customers.models import Customer

from .models import Notification, NotificationStatus


class NotificationRepository:
    def create(self, **kwargs: Any) -> Notification:
        return Notification.objects.create(**kwargs)

    def update(self, notification: Notification, **kwargs: Any) -> Notification:
        for key, value in kwargs.items():
            setattr(notification, key, value)
        notification.save(update_fields=[*kwargs.keys(), "updated_at"])
        return notification

    def get_pending(self, limit: int = 200) -> list[Notification]:
        return list(Notification.objects.filter(status=NotificationStatus.PENDING).order_by("created_at")[:limit])

    def has_recent(self, customer: Customer, event_type: str, within_hours: int = 24) -> bool:
        from django.utils import timezone
        cutoff = timezone.now() - timezone.timedelta(hours=within_hours)
        return Notification.objects.filter(
            customer=customer,
            event_type=event_type,
            created_at__gte=cutoff,
        ).exists()
