from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from core import responses
from integrations.celcoin import CelcoinClient

from .services import PaymentService


class CelcoinWebhookView(APIView):
    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        celcoin = CelcoinClient()
        parsed = celcoin.parse_payment_webhook(request.data)
        if parsed is None:
            return responses.success(data={"status": "ignored"})

        service = PaymentService()
        result = service.process_payment(txid=parsed["txid"], paid_at=parsed.get("paid_at"))
        return responses.success(data=result)
