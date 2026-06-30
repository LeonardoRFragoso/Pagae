from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("django-admin/", admin.site.urls),
    path("api/v1/auth/", include("apps.accounts.urls")),
    path("api/v1/", include("apps.customers.urls")),
    path("api/v1/", include("apps.merchants.urls")),
    path("api/v1/", include("apps.checkout.urls")),
    path("api/v1/", include("apps.payments.urls")),
    path("api/v1/", include("apps.settlements.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]
