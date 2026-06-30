from django.db import models

from apps.checkout.models import CheckoutSession
from apps.merchants.models import Merchant
from apps.payments.models import Installment
from core.models import BaseModel


class LedgerAccount(models.TextChoices):
    RECEIVABLE = "receivable", "Receivable"
    MERCHANT_PAYABLE = "merchant_payable", "Merchant Payable"
    MDR_REVENUE = "mdr_revenue", "MDR Revenue"
    CASH = "cash", "Cash"


class LedgerEntry(BaseModel):
    merchant = models.ForeignKey(Merchant, on_delete=models.PROTECT, related_name="ledger_entries")
    checkout = models.ForeignKey(
        CheckoutSession,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="ledger_entries",
    )
    installment = models.ForeignKey(
        Installment,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="ledger_entries",
    )

    account = models.CharField(max_length=30, choices=LedgerAccount.choices)
    amount = models.IntegerField()  # cents, positive = debit, negative = credit
    description = models.CharField(max_length=255)
    reference = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "ledger_entries"
        verbose_name = "Ledger Entry"
        verbose_name_plural = "Ledger Entries"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Ledger {self.account} {self.amount} — {self.description}"
