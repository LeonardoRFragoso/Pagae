from django.db import models

from apps.customers.models import Customer
from core.models import BaseModel


class NotificationChannel(models.TextChoices):
    WHATSAPP = "whatsapp", "WhatsApp"
    EMAIL = "email", "Email"


class NotificationStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    SENT = "sent", "Sent"
    DELIVERED = "delivered", "Delivered"
    FAILED = "failed", "Failed"


class NotificationEventType(models.TextChoices):
    CHECKOUT_APPROVED = "checkout_approved", "Checkout Approved"
    CHECKOUT_DENIED = "checkout_denied", "Checkout Denied"
    INSTALLMENT_DUE = "installment_due", "Installment Due"
    INSTALLMENT_OVERDUE = "installment_overdue", "Installment Overdue"
    INSTALLMENT_PAID = "installment_paid", "Installment Paid"
    LIMIT_SUSPENDED = "limit_suspended", "Limit Suspended"


class Notification(BaseModel):
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="notifications")
    channel = models.CharField(max_length=20, choices=NotificationChannel.choices)
    event_type = models.CharField(max_length=50, choices=NotificationEventType.choices)
    status = models.CharField(max_length=20, choices=NotificationStatus.choices, default=NotificationStatus.PENDING)
    provider_id = models.CharField(max_length=100, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "notifications"
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["customer", "event_type"]),
            models.Index(fields=["status", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.channel}/{self.event_type} → {self.customer_id} [{self.status}]"
