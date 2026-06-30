from typing import Any

from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from core import responses

from .serializers import (
    ApiKeyCreatedSerializer,
    ApiKeyCreateSerializer,
    ApiKeySerializer,
    MerchantCreateSerializer,
    MerchantDashboardSerializer,
    MerchantSerializer,
    MerchantSettlementSerializer,
    MerchantTransactionDetailSerializer,
    MerchantTransactionSerializer,
    MerchantWebhookUpdateSerializer,
)
from .services import MerchantService


class MerchantCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        serializer = MerchantCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service = MerchantService()
        merchant = service.register(user=request.user, data=serializer.validated_data)
        return responses.created(data=MerchantSerializer(merchant).data)


class MerchantMeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        service = MerchantService()
        merchant = service.get_profile(user=request.user)
        return responses.success(data=MerchantSerializer(merchant).data)


class ApiKeyListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        service = MerchantService()
        keys = service.list_api_keys(user=request.user)
        return responses.success(data=ApiKeySerializer(keys, many=True).data)

    def post(self, request: Request) -> Response:
        serializer = ApiKeyCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service = MerchantService()
        result = service.generate_api_key(
            user=request.user,
            name=serializer.validated_data["name"],
            environment=serializer.validated_data["environment"],
        )
        response_data = ApiKeyCreatedSerializer(result.api_key).data
        response_data["full_key"] = result.full_key
        return responses.created(
            data=response_data,
            message="Store this key securely. It will not be shown again.",
        )


class MerchantDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        service = MerchantService()
        data = service.get_dashboard(user=request.user)
        return responses.success(data=MerchantDashboardSerializer(data).data)


class MerchantTransactionListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        service = MerchantService()
        transactions = service.get_transactions(user=request.user)
        return responses.success(data=MerchantTransactionSerializer(transactions, many=True).data)


class MerchantTransactionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, transaction_id: Any) -> Response:
        service = MerchantService()
        transaction = service.get_transaction(user=request.user, transaction_id=transaction_id)
        return responses.success(data=MerchantTransactionDetailSerializer(transaction).data)


class MerchantSettlementListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        service = MerchantService()
        settlements = service.get_settlements(user=request.user)
        return responses.success(data=MerchantSettlementSerializer(settlements, many=True).data)


class MerchantWebhookUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        service = MerchantService()
        merchant = service.get_profile(user=request.user)
        return responses.success(
            data={"webhook_url": merchant.webhook_url, "webhook_secret": merchant.webhook_secret}
        )

    def patch(self, request: Request) -> Response:
        serializer = MerchantWebhookUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service = MerchantService()
        merchant = service.update_webhook(user=request.user, data=serializer.validated_data)
        return responses.success(
            data={"webhook_url": merchant.webhook_url, "webhook_secret": merchant.webhook_secret}
        )


class MerchantWebhookTestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        from apps.webhooks.services import WebhookService

        url = request.data.get("url")
        secret = request.data.get("secret")
        if not url:
            return responses.error(message="URL is required.", status_code=400)
        WebhookService().send(url, secret, "webhook.test", {"message": "Webhook test from Pagaê portal"})
        return responses.success(message="Webhook test queued.")
