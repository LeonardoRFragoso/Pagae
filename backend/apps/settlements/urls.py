from django.urls import path

from .views import SettleByCheckoutView

urlpatterns = [
    path("settlements/checkout/<uuid:checkout_id>/", SettleByCheckoutView.as_view(), name="settle-by-checkout"),
]
