import uuid

from core.exceptions import NotFoundError

from .models import CheckoutSession, Order, RiskAnalysis


class OrderRepository:
    def get_by_id(self, order_id: uuid.UUID) -> Order:
        try:
            return Order.objects.select_related("merchant", "customer").get(id=order_id)
        except Order.DoesNotExist as err:
            raise NotFoundError(f"Order {order_id} not found.", "order_not_found") from err

    def create(self, **kwargs) -> Order:
        return Order.objects.create(**kwargs)

    def update(self, order: Order, **kwargs) -> Order:
        for key, value in kwargs.items():
            setattr(order, key, value)
        order.save(update_fields=[*kwargs.keys(), "updated_at"])
        return order

    def get_by_merchant(self, merchant) -> list[Order]:
        return list(Order.objects.filter(merchant=merchant).order_by("-created_at"))


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


class RiskAnalysisRepository:
    def create(self, **kwargs) -> RiskAnalysis:
        return RiskAnalysis.objects.create(**kwargs)

    def get_by_checkout(self, checkout: CheckoutSession) -> RiskAnalysis | None:
        return RiskAnalysis.objects.filter(checkout=checkout).order_by("-created_at").first()
