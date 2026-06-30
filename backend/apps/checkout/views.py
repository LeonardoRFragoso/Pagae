from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.merchants.authentication import ApiKeyAuthentication
from core import responses

from .serializers import (
    CheckoutCreateSerializer,
    CheckoutSerializer,
    OrderCreateSerializer,
    OrderSerializer,
)
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


class OrderCreateView(APIView):
    authentication_classes = [ApiKeyAuthentication]
    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        serializer = OrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        api_key = self._extract_key(request)
        service = CheckoutService()
        order = service.create_order(api_key=api_key, data=serializer.validated_data)
        return responses.created(data=OrderSerializer(order).data)

    def _extract_key(self, request: Request) -> str:
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            return auth[7:]
        return ""


class OrderListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        from apps.merchants.services import MerchantService

        merchant = MerchantService().get_profile(user=request.user)
        orders = CheckoutService().order_repository.get_by_merchant(merchant)
        return responses.success(data=OrderSerializer(orders, many=True).data)


class CheckoutPublicView(APIView):
    permission_classes = [AllowAny]

    def get(self, request: Request, checkout_id: str) -> Response:
        service = CheckoutService()
        result = service.get_public_checkout(checkout_id)
        return responses.success(data=result)
