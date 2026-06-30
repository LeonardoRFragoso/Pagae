from django.db import models

from apps.customers.models import Customer
from apps.merchants.models import Merchant
from core.models import BaseModel


class CheckoutStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    APPROVED = "approved", "Approved"
    DENIED = "denied", "Denied"
    EXPIRED = "expired", "Expired"
    COMPLETED = "completed", "Completed"
    CANCELLED = "cancelled", "Cancelled"


class CheckoutSession(BaseModel):
    merchant = models.ForeignKey(Merchant, on_delete=models.PROTECT, related_name="checkout_sessions")
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="checkout_sessions")
    merchant_order_id = models.CharField(max_length=255, blank=True, db_index=True)

    total_amount = models.IntegerField()  # cents
    mdr_amount = models.IntegerField()  # cents
    net_amount = models.IntegerField()  # cents

    installment_count = models.SmallIntegerField()
    installment_amount = models.IntegerField()  # cents

    status = models.CharField(max_length=30, choices=CheckoutStatus.choices, default=CheckoutStatus.PENDING)
    decision = models.CharField(max_length=10, blank=True)  # approve | deny
    denial_reason = models.CharField(max_length=50, blank=True)
    serasa_score_at_decision = models.SmallIntegerField(null=True, blank=True)

    settlement = models.ForeignKey(
        "settlements.Settlement",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="checkouts",
    )
    settled_at = models.DateTimeField(null=True, blank=True)

    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "checkout_sessions"
        verbose_name = "Checkout Session"
        verbose_name_plural = "Checkout Sessions"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["merchant", "created_at"], name="idx_checkout_merchant_created"),
            models.Index(fields=["customer", "created_at"], name="idx_checkout_customer_created"),
            models.Index(fields=["merchant", "merchant_order_id"], name="idx_checkout_merchant_order"),
        ]

    def __str__(self) -> str:
        return f"Checkout {self.id} — {self.total_amount} cents ({self.status})"
