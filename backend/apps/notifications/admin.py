from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("id", "customer", "channel", "event_type", "status", "sent_at", "created_at")
    list_filter = ("channel", "event_type", "status", "created_at")
    search_fields = ("customer__full_name", "customer__cpf", "provider_id")
    readonly_fields = ("id", "created_at", "updated_at")
    ordering = ("-created_at",)
