from django.urls import path

from .views import CustomerCreateView, CustomerMeView

urlpatterns = [
    path("customers/", CustomerCreateView.as_view(), name="customer-create"),
    path("customers/me/", CustomerMeView.as_view(), name="customer-me"),
]
