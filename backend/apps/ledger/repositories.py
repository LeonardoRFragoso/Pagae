from typing import Any

from .models import LedgerEntry


class LedgerRepository:
    def create(self, **kwargs: Any) -> LedgerEntry:
        return LedgerEntry.objects.create(**kwargs)

    def get_entries_by_checkout(self, checkout_id: Any) -> list[LedgerEntry]:
        return list(LedgerEntry.objects.filter(checkout_id=checkout_id).order_by("-created_at"))
