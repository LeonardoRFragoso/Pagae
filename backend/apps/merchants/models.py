from decimal import Decimal

from django.conf import settings
from django.db import models

from core.models import BaseModel


class MerchantStatus(models.TextChoices):
    PENDING = "pending", "Pending Approval"
    ACTIVE = "active", "Active"
    SUSPENDED = "suspended", "Suspended"
    TERMINATED = "terminated", "Terminated"


class MerchantEnvironment(models.TextChoices):
    SANDBOX = "sandbox", "Sandbox"
    PRODUCTION = "production", "Production"


class Merchant(BaseModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="merchant_profile",
    )

    # Legal identity
    legal_name = models.CharField(max_length=255)
    trade_name = models.CharField(max_length=255, blank=True)
    # TODO: encrypt CNPJ at rest before production
    cnpj = models.CharField(max_length=18, unique=True, db_index=True)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    website = models.CharField(max_length=255, blank=True)

    # Bank account for settlement via Pix
    bank_code = models.CharField(max_length=10, blank=True)
    bank_agency = models.CharField(max_length=10, blank=True)
    bank_account = models.CharField(max_length=20, blank=True)
    bank_account_type = models.CharField(max_length=10, blank=True)  # checking | savings
    pix_key = models.CharField(max_length=255, blank=True)

    # Commercial terms (negotiated per merchant)
    mdr_rate = models.DecimalField(max_digits=5, decimal_places=4, default=Decimal("0.0700"))
    settlement_days = models.SmallIntegerField(default=1)

    # Lifecycle
    status = models.CharField(max_length=20, choices=MerchantStatus.choices, default=MerchantStatus.PENDING)
    approved_at = models.DateTimeField(null=True, blank=True)

    # Webhook delivery
    webhook_url = models.CharField(max_length=500, blank=True)
    webhook_secret = models.CharField(max_length=64, blank=True)

    class Meta:
        db_table = "merchants"
        verbose_name = "Merchant"
        verbose_name_plural = "Merchants"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        from core.privacy import mask_cnpj

        return f"{self.trade_name or self.legal_name} ({mask_cnpj(self.cnpj)})"

    @property
    def is_active(self) -> bool:
        return self.status == MerchantStatus.ACTIVE


class MerchantApiKey(BaseModel):
    merchant = models.ForeignKey(Merchant, on_delete=models.CASCADE, related_name="api_keys")

    # Only the prefix is stored in plaintext for display (e.g. "pk_live_abc1xxxx")
    key_prefix = models.CharField(max_length=20)
    # The full key is never stored — only its bcrypt hash for verification
    key_hash = models.CharField(max_length=255)

    name = models.CharField(max_length=100, blank=True)
    environment = models.CharField(
        max_length=10,
        choices=MerchantEnvironment.choices,
        default=MerchantEnvironment.PRODUCTION,
    )
    is_active = models.BooleanField(default=True)
    last_used = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "merchant_api_keys"
        verbose_name = "API Key"
        verbose_name_plural = "API Keys"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.key_prefix}... ({self.merchant})"
