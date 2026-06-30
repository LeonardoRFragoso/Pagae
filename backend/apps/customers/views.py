from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.merchants.authentication import ApiKeyAuthentication
from apps.merchants.models import MerchantApiKey
from core import responses

from .serializers import (
    CustomerCreateSerializer,
    CustomerMerchantSerializer,
    CustomerSerializer,
    CustomerUpdateSerializer,
)
from .services import CustomerService


class IsMerchantApiKey(BasePermission):
    """Allow only requests authenticated via a merchant API key."""

    def has_permission(self, request: Request, view: APIView) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False
        return isinstance(getattr(request, "auth", None), MerchantApiKey)


class CustomerCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        serializer = CustomerCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service = CustomerService()
        customer = service.register(user=request.user, data=serializer.validated_data)
        return responses.created(data=CustomerSerializer(customer).data)


class CustomerMerchantView(APIView):
    authentication_classes = [ApiKeyAuthentication]
    permission_classes = [IsMerchantApiKey]

    def post(self, request: Request) -> Response:
        serializer = CustomerMerchantSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service = CustomerService()
        customer = service.get_or_create_for_merchant(serializer.validated_data)
        return responses.created(data=CustomerSerializer(customer).data)


class CustomerMeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        service = CustomerService()
        customer = service.get_profile(user=request.user)
        return responses.success(data=CustomerSerializer(customer).data)

    def put(self, request: Request) -> Response:
        serializer = CustomerUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        service = CustomerService()
        customer = service.update_profile(user=request.user, data=serializer.validated_data)
        return responses.success(data=CustomerSerializer(customer).data)
