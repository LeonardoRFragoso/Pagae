from django.contrib import admin

from .models import Settlement


@admin.register(Settlement)
class SettlementAdmin(admin.ModelAdmin):
    list_display = ("id", "merchant", "amount", "status", "period_start", "period_end", "paid_at")
    list_filter = ("status", "period_start")
    search_fields = ("merchant__trade_name",)
    readonly_fields = ("id", "created_at", "updated_at")
    ordering = ("-created_at",)
