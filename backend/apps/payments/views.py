from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from core import responses

from .providers import get_payment_provider
from .services import PaymentService


class CelcoinWebhookView(APIView):
    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        provider = get_payment_provider()
        parsed = provider.parse_webhook(request.data)
        if parsed is None:
            return responses.success(data={"status": "ignored"})

        service = PaymentService(provider=provider)
        result = service.process_payment(txid=parsed["txid"], paid_at=parsed.get("paid_at"))
        return responses.success(data=result)


class PaymentSimulationView(APIView):
    """Sandbox endpoint to simulate a Pix payment for a given txid."""

    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        txid = request.data.get("txid")
        paid_at = request.data.get("paid_at")
        if not txid:
            return responses.error(message="txid is required.", status_code=400)

        service = PaymentService()
        result = service.process_payment(txid=txid, paid_at=paid_at)
        return responses.success(data=result)


class SandboxWebhookView(APIView):
    """Generic fake webhook receiver for local development/tests."""

    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        provider = get_payment_provider()
        parsed = provider.parse_webhook(request.data)
        if parsed is None:
            return responses.success(data={"status": "ignored"})

        service = PaymentService(provider=provider)
        result = service.process_payment(txid=parsed["txid"], paid_at=parsed.get("paid_at"))
        return responses.success(data=result)
