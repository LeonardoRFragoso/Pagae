from .models import Settlement


class SettlementRepository:
    def create(self, **kwargs) -> Settlement:
        return Settlement.objects.create(**kwargs)

    def update(self, settlement: Settlement, **kwargs) -> Settlement:
        for key, value in kwargs.items():
            setattr(settlement, key, value)
        settlement.save(update_fields=[*kwargs.keys(), "updated_at"])
        return settlement

    def get_pending(self, limit: int = 100) -> list[Settlement]:
        return list(
            Settlement.objects.select_related("merchant")
            .filter(status=Settlement.PENDING)
            .order_by("created_at")[:limit]
        )
