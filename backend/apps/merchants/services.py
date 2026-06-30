import hashlib
import logging
import re
import secrets
from datetime import timedelta
from typing import TYPE_CHECKING, Any, NamedTuple

from django.db.models import Sum

from core.exceptions import ConflictError, ForbiddenError

from .models import Merchant, MerchantApiKey
from .repositories import ApiKeyRepository, MerchantRepository

if TYPE_CHECKING:
    from apps.accounts.models import User

logger = logging.getLogger(__name__)

_KEY_PREFIX_TAG = "pk_live_"
_KEY_PREFIX_TAG_SANDBOX = "pk_test_"
_KEY_RANDOM_BYTES = 24  # produces 32 hex chars after hexlify


class GeneratedApiKey(NamedTuple):
    """Returned once on creation. The full_key is never stored and must be shown to the user immediately."""

    api_key: MerchantApiKey
    full_key: str


def _hash_key(full_key: str) -> str:
    """SHA-256 hash of the full API key for storage. Fast + irreversible."""
    return hashlib.sha256(full_key.encode()).hexdigest()


class MerchantService:
    def __init__(
        self,
        repository: MerchantRepository | None = None,
        key_repository: ApiKeyRepository | None = None,
    ) -> None:
        self.repository = repository or MerchantRepository()
        self.key_repository = key_repository or ApiKeyRepository()

    def register(self, user: "User", data: dict[str, Any]) -> Merchant:
        if not user.is_merchant_owner:
            raise ForbiddenError("Only users with the 'merchant_owner' role can create a merchant profile.")

        if self.repository.get_by_user(user) is not None:
            raise ConflictError("A merchant profile already exists for this user.", "profile_exists")

        cnpj = re.sub(r"\D", "", data.get("cnpj", ""))
        if self.repository.cnpj_exists(cnpj):
            raise ConflictError("A merchant with this CNPJ already exists.", "cnpj_taken")

        merchant = self.repository.create(user=user, cnpj=cnpj, **{k: v for k, v in data.items() if k != "cnpj"})
        logger.info("merchant_registered", extra={"merchant_id": str(merchant.id), "cnpj": cnpj[-4:]})
        return merchant

    def get_profile(self, user: "User") -> Merchant:
        return self.repository.get_by_user_or_raise(user)

    def generate_api_key(self, user: "User", name: str = "", environment: str = "production") -> GeneratedApiKey:
        merchant = self.repository.get_by_user_or_raise(user)

        tag = _KEY_PREFIX_TAG if environment == "production" else _KEY_PREFIX_TAG_SANDBOX
        random_part = secrets.token_hex(_KEY_RANDOM_BYTES)
        full_key = f"{tag}{random_part}"

        key_prefix = full_key[:16]
        key_hash = _hash_key(full_key)

        api_key = self.key_repository.create(
            merchant=merchant,
            key_prefix=key_prefix,
            key_hash=key_hash,
            name=name,
            environment=environment,
        )
        logger.info(
            "api_key_generated",
            extra={"merchant_id": str(merchant.id), "key_prefix": key_prefix, "environment": environment},
        )
        return GeneratedApiKey(api_key=api_key, full_key=full_key)

    def list_api_keys(self, user: "User") -> list[MerchantApiKey]:
        merchant = self.repository.get_by_user_or_raise(user)
        return self.key_repository.get_active_keys(merchant)

    def verify_api_key(self, full_key: str) -> MerchantApiKey | None:
        """Authenticate an inbound API key. Updates last_used timestamp on success."""
        if len(full_key) < 16:
            return None

        key_prefix = full_key[:16]
        api_key = self.key_repository.get_by_prefix(key_prefix)
        if api_key is None:
            return None

        if _hash_key(full_key) != api_key.key_hash:
            return None

        from django.utils import timezone

        api_key.last_used = timezone.now()
        api_key.save(update_fields=["last_used"])
        return api_key

    def get_dashboard(self, user: "User") -> dict[str, Any]:
        from django.utils import timezone

        from apps.checkout.models import CheckoutStatus

        merchant = self.repository.get_by_user_or_raise(user)
        now = timezone.now()
        today = now.date()
        sessions = merchant.checkout_sessions.all()
        approved_sessions = sessions.filter(status=CheckoutStatus.APPROVED)

        gmv_today = self._sum_amount(approved_sessions.filter(created_at__date=today))
        gmv_week = self._sum_amount(
            approved_sessions.filter(created_at__date__gte=today - timedelta(days=7))
        )
        gmv_month = self._sum_amount(
            approved_sessions.filter(created_at__date__gte=today - timedelta(days=30))
        )

        total = sessions.count()
        approved = approved_sessions.count()
        approval_rate = round(approved / total * 100, 2) if total else 0.0

        pending_settlement = approved_sessions.filter(settled_at__isnull=True).aggregate(
            total=Sum("net_amount")
        )["total"] or 0

        return {
            "gmv_today": gmv_today,
            "gmv_week": gmv_week,
            "gmv_month": gmv_month,
            "approval_rate": approval_rate,
            "total_transactions": total,
            "pending_settlement": pending_settlement,
        }

    def _sum_amount(self, queryset) -> int:
        return queryset.aggregate(total=Sum("total_amount"))["total"] or 0

    def get_transactions(self, user: "User"):
        merchant = self.repository.get_by_user_or_raise(user)
        return merchant.checkout_sessions.select_related("customer").order_by("-created_at")

    def get_transaction(self, user: "User", transaction_id: Any) -> Any:
        from apps.checkout.models import CheckoutSession
        from core.exceptions import NotFoundError

        merchant = self.repository.get_by_user_or_raise(user)
        try:
            return merchant.checkout_sessions.select_related("customer").prefetch_related("installments").get(
                id=transaction_id
            )
        except CheckoutSession.DoesNotExist as err:
            raise NotFoundError("Transaction not found.", "transaction_not_found") from err

    def get_settlements(self, user: "User"):
        merchant = self.repository.get_by_user_or_raise(user)
        return merchant.settlements.order_by("-created_at")

    def update_webhook(self, user: "User", data: dict[str, Any]) -> Merchant:
        merchant = self.repository.get_by_user_or_raise(user)
        return self.repository.update(
            merchant,
            webhook_url=data.get("webhook_url", ""),
            webhook_secret=data.get("webhook_secret", ""),
        )
