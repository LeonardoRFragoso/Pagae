from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.merchants.authentication import ApiKeyAuthentication
from core import responses

from .serializers import CheckoutCreateSerializer, CheckoutSerializer
from .services import CheckoutService


class CheckoutCreateView(APIView):
    authentication_classes = [ApiKeyAuthentication]
    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        serializer = CheckoutCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        api_key = self._extract_key(request)
        service = CheckoutService()
        result = service.create_session(api_key=api_key, data=serializer.validated_data)
        return responses.created(data=CheckoutSerializer(result).data)

    def _extract_key(self, request: Request) -> str:
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            return auth[7:]
        return ""
