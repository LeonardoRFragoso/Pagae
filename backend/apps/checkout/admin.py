from django.contrib import admin

from .models import CheckoutSession


@admin.register(CheckoutSession)
class CheckoutSessionAdmin(admin.ModelAdmin):
    list_display = ("id", "merchant", "customer", "total_amount", "status", "decision", "created_at")
    list_filter = ("status", "decision", "created_at")
    search_fields = ("merchant__trade_name", "customer__cpf", "merchant_order_id")
    readonly_fields = ("id", "created_at", "updated_at")
    ordering = ("-created_at",)
