import logging
from typing import TYPE_CHECKING, Any

from core.exceptions import ConflictError, ForbiddenError

from .models import Customer
from .repositories import CustomerRepository

if TYPE_CHECKING:
    from apps.accounts.models import User

logger = logging.getLogger(__name__)


class CustomerService:
    def __init__(self, repository: CustomerRepository | None = None) -> None:
        self.repository = repository or CustomerRepository()

    def register(self, user: "User", data: dict[str, Any]) -> Customer:
        """
        Create a customer profile linked to an existing user account.
        Enforces: one profile per user, unique CPF.
        """
        if not user.is_customer:
            raise ForbiddenError("Only users with the 'customer' role can create a customer profile.")

        if self.repository.get_by_user(user) is not None:
            raise ConflictError("A customer profile already exists for this user.", "profile_exists")

        cpf = data.get("cpf", "").replace(".", "").replace("-", "")
        if self.repository.cpf_exists(cpf):
            raise ConflictError("A customer with this CPF already exists.", "cpf_taken")

        customer = self.repository.create(user=user, cpf=cpf, **{k: v for k, v in data.items() if k != "cpf"})
        logger.info("customer_registered", extra={"customer_id": str(customer.id), "user_id": str(user.id)})
        return customer

    def get_profile(self, user: "User") -> Customer:
        return self.repository.get_by_user_or_raise(user)

    def update_profile(self, user: "User", data: dict[str, Any]) -> Customer:
        customer = self.repository.get_by_user_or_raise(user)
        updatable_fields = {
            "phone", "email", "cep", "street", "number",
            "complement", "neighborhood", "city", "state",
        }
        filtered = {k: v for k, v in data.items() if k in updatable_fields}
        customer = self.repository.update(customer, **filtered)
        logger.info("customer_profile_updated", extra={"customer_id": str(customer.id)})
        return customer
