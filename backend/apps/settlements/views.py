from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import UserRole
from apps.checkout.repositories import CheckoutRepository
from core import responses
from core.exceptions import ForbiddenError

from .services import SettlementService


class SettleByCheckoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, checkout_id: str) -> Response:
        if request.user.role != UserRole.MERCHANT_OWNER:
            raise ForbiddenError("Only merchant owners can trigger settlements.")

        checkout_repository = CheckoutRepository()
        checkout = checkout_repository.get_by_id(checkout_id)
        if checkout.merchant.user_id != request.user.id:
            raise ForbiddenError("Checkout does not belong to this merchant.")

        service = SettlementService()
        settlement = service.create_for_checkout(checkout)
        settlement = service.settle(settlement)
        return responses.created(
            data={
                "id": settlement.id,
                "status": settlement.status,
                "amount": settlement.amount,
                "pix_e2e_id": settlement.pix_e2e_id,
            }
        )
