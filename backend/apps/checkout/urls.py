from django.urls import path

from .views import CheckoutCreateView

urlpatterns = [
    path("checkout/", CheckoutCreateView.as_view(), name="checkout-create"),
]
