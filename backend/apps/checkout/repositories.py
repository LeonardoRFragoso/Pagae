import uuid

from core.exceptions import NotFoundError

from .models import CheckoutSession


class CheckoutRepository:
    def get_by_id(self, checkout_id: uuid.UUID) -> CheckoutSession:
        try:
            return CheckoutSession.objects.select_related("merchant", "customer").get(id=checkout_id)
        except CheckoutSession.DoesNotExist as err:
            raise NotFoundError(f"Checkout {checkout_id} not found.", "checkout_not_found") from err

    def create(self, **kwargs) -> CheckoutSession:
        return CheckoutSession.objects.create(**kwargs)

    def update(self, checkout: CheckoutSession, **kwargs) -> CheckoutSession:
        for key, value in kwargs.items():
            setattr(checkout, key, value)
        checkout.save(update_fields=[*kwargs.keys(), "updated_at"])
        return checkout
