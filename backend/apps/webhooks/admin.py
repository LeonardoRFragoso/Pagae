from django.contrib import admin

from .models import WebhookDelivery


@admin.register(WebhookDelivery)
class WebhookDeliveryAdmin(admin.ModelAdmin):
    list_display = ("id", "merchant", "event_type", "status", "attempts", "delivered_at", "created_at")
    list_filter = ("status", "event_type", "created_at")
    search_fields = ("merchant__trade_name", "event_type")
    readonly_fields = ("id", "created_at", "updated_at")
    ordering = ("-created_at",)
