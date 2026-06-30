from django.urls import path

from .views import CheckoutCreateView, CheckoutPublicView, OrderCreateView, OrderListView

urlpatterns = [
    path("orders/", OrderCreateView.as_view(), name="order-create"),
    path("orders/list/", OrderListView.as_view(), name="order-list"),
    path("checkout/", CheckoutCreateView.as_view(), name="checkout-create"),
    path("checkout/<uuid:checkout_id>/", CheckoutPublicView.as_view(), name="checkout-public"),
]
