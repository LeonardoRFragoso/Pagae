from django.urls import path

from .views import CustomerCreateView, CustomerMeView, CustomerMerchantView

urlpatterns = [
    path("customers/", CustomerCreateView.as_view(), name="customer-create"),
    path("customers/merchant/", CustomerMerchantView.as_view(), name="customer-merchant"),
    path("customers/me/", CustomerMeView.as_view(), name="customer-me"),
]
