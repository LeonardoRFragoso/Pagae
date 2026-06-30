from django.urls import path

from .views import CelcoinWebhookView, PaymentSimulationView, SandboxWebhookView

urlpatterns = [
    path("payments/simulate/", PaymentSimulationView.as_view(), name="payment-simulation"),
    path("webhooks/celcoin/pix/", CelcoinWebhookView.as_view(), name="celcoin-webhook"),
    path("webhooks/sandbox/", SandboxWebhookView.as_view(), name="sandbox-webhook"),
]
