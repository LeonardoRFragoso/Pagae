from django.urls import path

from .views import (
    ApiKeyListCreateView,
    MerchantCreateView,
    MerchantDashboardView,
    MerchantMeView,
    MerchantSettlementListView,
    MerchantTransactionDetailView,
    MerchantTransactionListView,
    MerchantWebhookTestView,
    MerchantWebhookUpdateView,
)

urlpatterns = [
    path("merchants/", MerchantCreateView.as_view(), name="merchant-create"),
    path("merchants/me/", MerchantMeView.as_view(), name="merchant-me"),
    path("merchants/api-keys/", ApiKeyListCreateView.as_view(), name="merchant-api-keys"),
    path("merchants/dashboard/", MerchantDashboardView.as_view(), name="merchant-dashboard"),
    path("merchants/transactions/", MerchantTransactionListView.as_view(), name="merchant-transactions"),
    path("merchants/transactions/<uuid:transaction_id>/", MerchantTransactionDetailView.as_view(), name="merchant-transaction-detail"),
    path("merchants/settlements/", MerchantSettlementListView.as_view(), name="merchant-settlements"),
    path("merchants/webhook/", MerchantWebhookUpdateView.as_view(), name="merchant-webhook"),
    path("merchants/webhook/test/", MerchantWebhookTestView.as_view(), name="merchant-webhook-test"),
]
