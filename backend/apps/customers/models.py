from django.conf import settings
from django.db import models

from core.models import BaseModel


class KYCStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"
    MANUAL_REVIEW = "manual_review", "Manual Review"


class RiskTier(models.TextChoices):
    NEW = "new", "New"
    LOW = "low", "Low Risk"
    MEDIUM = "medium", "Medium Risk"
    HIGH = "high", "High Risk"


class Customer(BaseModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="customer_profile",
        null=True,
        blank=True,
    )

    # Personal data
    # TODO: encrypt CPF at rest before production (use django-encrypted-fields or AWS KMS)
    cpf = models.CharField(max_length=14, unique=True, db_index=True)
    full_name = models.CharField(max_length=255)
    birth_date = models.DateField(null=True, blank=True)
    phone = models.CharField(max_length=20)
    email = models.EmailField()

    # Address
    cep = models.CharField(max_length=9, blank=True)
    street = models.CharField(max_length=255, blank=True)
    number = models.CharField(max_length=20, blank=True)
    complement = models.CharField(max_length=100, blank=True)
    neighborhood = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=2, blank=True)

    # KYC
    kyc_status = models.CharField(max_length=20, choices=KYCStatus.choices, default=KYCStatus.PENDING)
    kyc_provider_id = models.CharField(max_length=100, blank=True)
    kyc_approved_at = models.DateTimeField(null=True, blank=True)

    # Credit — all monetary values stored in centavos (integer)
    serasa_score = models.SmallIntegerField(null=True, blank=True)
    risk_tier = models.CharField(max_length=10, choices=RiskTier.choices, default=RiskTier.NEW)
    approved_limit = models.IntegerField(default=0)
    used_limit = models.IntegerField(default=0)
    is_blocked = models.BooleanField(default=False)
    blocked_reason = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = "customers"
        verbose_name = "Customer"
        verbose_name_plural = "Customers"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.full_name} ({self.cpf[-4:]})"

    @property
    def available_limit(self) -> int:
        return max(0, self.approved_limit - self.used_limit)

    @property
    def is_kyc_approved(self) -> bool:
        return self.kyc_status == KYCStatus.APPROVED
