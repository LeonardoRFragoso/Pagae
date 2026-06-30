from django.db import models

from apps.merchants.models import Merchant
from core.models import BaseModel


class SettlementStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    PROCESSING = "processing", "Processing"
    COMPLETED = "completed", "Completed"
    FAILED = "failed", "Failed"


class Settlement(BaseModel):
    merchant = models.ForeignKey(Merchant, on_delete=models.CASCADE, related_name="settlements")

    amount = models.IntegerField()  # cents
    period_start = models.DateField()
    period_end = models.DateField()

    status = models.CharField(max_length=20, choices=SettlementStatus.choices, default=SettlementStatus.PENDING)
    pix_e2e_id = models.CharField(max_length=100, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    failure_reason = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "settlements"
        verbose_name = "Settlement"
        verbose_name_plural = "Settlements"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Settlement {self.id} — {self.amount} cents ({self.status})"


class MerchantSettlement(Settlement):
    """Proxy model used to expose the settlement concept in merchant-facing APIs."""

    class Meta:
        proxy = True
        verbose_name = "Merchant Settlement"
        verbose_name_plural = "Merchant Settlements"
