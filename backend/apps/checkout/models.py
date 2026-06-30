from django.db import models

from apps.customers.models import Customer
from apps.merchants.models import Merchant
from core.models import BaseModel


class OrderStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    CREATED = "created", "Created"
    CONVERTED = "converted", "Converted"
    CANCELLED = "cancelled", "Cancelled"


class Order(BaseModel):
    """Merchant order created before the public checkout session."""

    merchant = models.ForeignKey(Merchant, on_delete=models.PROTECT, related_name="orders")
    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,
        related_name="orders",
        null=True,
        blank=True,
    )
    merchant_order_id = models.CharField(max_length=255, blank=True, db_index=True)
    total_amount = models.IntegerField()  # cents
    installment_count = models.SmallIntegerField(default=1)
    description = models.CharField(max_length=255, blank=True)
    status = models.CharField(
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.CREATED,
    )
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "orders"
        verbose_name = "Order"
        verbose_name_plural = "Orders"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Order {self.id} — {self.total_amount} cents ({self.status})"


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
    order = models.ForeignKey(
        Order,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="checkout_sessions",
    )
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


class RiskAnalysis(BaseModel):
    """Rule-based credit decision with the reasons that led to it."""

    checkout = models.ForeignKey(
        CheckoutSession,
        on_delete=models.CASCADE,
        related_name="risk_analyses",
    )
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="risk_analyses",
    )
    requested_amount = models.IntegerField()  # cents
    decision = models.CharField(max_length=10)  # approve | deny
    reasons = models.JSONField(default=list)
    score = models.SmallIntegerField(null=True, blank=True)
    approved_limit = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = "risk_analyses"
        verbose_name = "Risk Analysis"
        verbose_name_plural = "Risk Analyses"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Risk {self.id} — {self.decision} ({self.checkout_id})"
