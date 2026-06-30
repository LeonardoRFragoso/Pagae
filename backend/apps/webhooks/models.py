from django.db import models

from apps.merchants.models import Merchant
from core.models import BaseModel


class WebhookStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    DELIVERED = "delivered", "Delivered"
    FAILED = "failed", "Failed"
    EXHAUSTED = "exhausted", "Exhausted"


class WebhookDelivery(BaseModel):
    merchant = models.ForeignKey(Merchant, on_delete=models.CASCADE, related_name="webhook_deliveries")
    event_type = models.CharField(max_length=50)
    payload = models.JSONField()

    status = models.CharField(max_length=20, choices=WebhookStatus.choices, default=WebhookStatus.PENDING)
    http_status = models.SmallIntegerField(null=True, blank=True)
    attempts = models.SmallIntegerField(default=0)
    next_retry = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "webhook_deliveries"
        verbose_name = "Webhook Delivery"
        verbose_name_plural = "Webhook Deliveries"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.event_type} to {self.merchant} — {self.status}"
