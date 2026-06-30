import uuid
from typing import TYPE_CHECKING

from django.contrib.auth import get_user_model

from core.exceptions import NotFoundError

from .models import Customer

if TYPE_CHECKING:
    from apps.accounts.models import User

User = get_user_model()


class CustomerRepository:
    def get_by_id(self, customer_id: uuid.UUID) -> Customer:
        try:
            return Customer.objects.select_related("user").get(id=customer_id)
        except Customer.DoesNotExist as err:
            raise NotFoundError(f"Customer {customer_id} not found.", "customer_not_found") from err

    def get_by_cpf(self, cpf: str) -> Customer | None:
        return Customer.objects.select_related("user").filter(cpf=cpf).first()

    def get_by_user(self, user: "User") -> Customer | None:
        return Customer.objects.select_related("user").filter(user=user).first()

    def get_by_user_or_raise(self, user: "User") -> Customer:
        customer = self.get_by_user(user)
        if customer is None:
            raise NotFoundError("Customer profile not found for this user.", "customer_not_found")
        return customer

    def create(self, user: "User", **kwargs) -> Customer:
        return Customer.objects.create(user=user, **kwargs)

    def update(self, customer: Customer, **kwargs) -> Customer:
        for key, value in kwargs.items():
            setattr(customer, key, value)
        customer.save(update_fields=[*kwargs.keys(), "updated_at"])
        return customer

    def cpf_exists(self, cpf: str) -> bool:
        return Customer.objects.filter(cpf=cpf).exists()
