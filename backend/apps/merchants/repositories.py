import uuid
from typing import TYPE_CHECKING

from core.exceptions import NotFoundError

from .models import Merchant, MerchantApiKey

if TYPE_CHECKING:
    from apps.accounts.models import User


class MerchantRepository:
    def get_by_id(self, merchant_id: uuid.UUID) -> Merchant:
        try:
            return Merchant.objects.select_related("user").get(id=merchant_id)
        except Merchant.DoesNotExist as err:
            raise NotFoundError(f"Merchant {merchant_id} not found.", "merchant_not_found") from err

    def get_by_user(self, user: "User") -> Merchant | None:
        return Merchant.objects.select_related("user").filter(user=user).first()

    def get_by_user_or_raise(self, user: "User") -> Merchant:
        merchant = self.get_by_user(user)
        if merchant is None:
            raise NotFoundError("Merchant profile not found for this user.", "merchant_not_found")
        return merchant

    def get_by_cnpj(self, cnpj: str) -> Merchant | None:
        return Merchant.objects.filter(cnpj=cnpj).first()

    def create(self, user: "User", **kwargs) -> Merchant:
        return Merchant.objects.create(user=user, **kwargs)

    def update(self, merchant: Merchant, **kwargs) -> Merchant:
        for key, value in kwargs.items():
            setattr(merchant, key, value)
        merchant.save(update_fields=[*kwargs.keys(), "updated_at"])
        return merchant

    def cnpj_exists(self, cnpj: str) -> bool:
        return Merchant.objects.filter(cnpj=cnpj).exists()


class ApiKeyRepository:
    def get_active_keys(self, merchant: Merchant) -> list[MerchantApiKey]:
        return list(MerchantApiKey.objects.filter(merchant=merchant, is_active=True).order_by("-created_at"))

    def get_by_prefix(self, key_prefix: str) -> MerchantApiKey | None:
        return MerchantApiKey.objects.select_related("merchant").filter(key_prefix=key_prefix, is_active=True).first()

    def create(self, merchant: Merchant, key_prefix: str, key_hash: str, name: str, environment: str) -> MerchantApiKey:
        return MerchantApiKey.objects.create(
            merchant=merchant,
            key_prefix=key_prefix,
            key_hash=key_hash,
            name=name,
            environment=environment,
        )

    def deactivate(self, api_key: MerchantApiKey) -> None:
        api_key.is_active = False
        api_key.save(update_fields=["is_active"])
