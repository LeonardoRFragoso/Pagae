from django.db import models

from apps.customers.models import Customer
from core.models import BaseModel


class InstallmentStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    PAID = "paid", "Paid"
    OVERDUE = "overdue", "Overdue"
    CANCELLED = "cancelled", "Cancelled"
    REFUNDED = "refunded", "Refunded"


class PixChargeStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    PAID = "paid", "Paid"
    EXPIRED = "expired", "Expired"
    CANCELLED = "cancelled", "Cancelled"


class Installment(BaseModel):
    checkout = models.ForeignKey("checkout.CheckoutSession", on_delete=models.CASCADE, related_name="installments")
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="installments")

    number = models.SmallIntegerField()
    amount = models.IntegerField()  # cents
    due_date = models.DateField()

    status = models.CharField(max_length=20, choices=InstallmentStatus.choices, default=InstallmentStatus.PENDING)
    paid_at = models.DateTimeField(null=True, blank=True)
    days_past_due = models.SmallIntegerField(default=0)

    class Meta:
        db_table = "installments"
        verbose_name = "Installment"
        verbose_name_plural = "Installments"
        ordering = ["checkout", "number"]
        unique_together = [["checkout", "number"]]

    def __str__(self) -> str:
        return f"Installment {self.number} of {self.checkout_id}"


class PixCharge(BaseModel):
    installment = models.ForeignKey(Installment, on_delete=models.CASCADE, related_name="pix_charges")

    celcoin_id = models.CharField(max_length=100, unique=True, blank=True)
    txid = models.CharField(max_length=35, unique=True, blank=True)

    amount = models.IntegerField()  # cents
    qr_code = models.TextField()
    pix_code = models.CharField(max_length=255)

    status = models.CharField(max_length=20, choices=PixChargeStatus.choices, default=PixChargeStatus.ACTIVE)
    expires_at = models.DateTimeField()
    paid_at = models.DateTimeField(null=True, blank=True)

    payer_name = models.CharField(max_length=255, blank=True)
    payer_cpf = models.CharField(max_length=14, blank=True)

    class Meta:
        db_table = "pix_charges"
        verbose_name = "Pix Charge"
        verbose_name_plural = "Pix Charges"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Pix {self.txid} ({self.status})"
