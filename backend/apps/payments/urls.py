from django.urls import path

from .views import CelcoinWebhookView

urlpatterns = [
    path("webhooks/celcoin/pix/", CelcoinWebhookView.as_view(), name="celcoin-webhook"),
]
